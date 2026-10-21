"""Rigorous SE(3) Spatial Coordinate Transformations for TRL 7 Planetary Rover.

Defines spatial frames, rigid-body transformations, rotation representations
(quaternions, Euler angles, DCM matrices), and transform chaining:
- World Frame (W): Local Tangent Plane (X=East, Y=North, Z=Up)
- Body Frame (B): Center of mass (X=Forward, Y=Left, Z=Up)
- LiDAR Frame (L): Mounted on mast (X=Forward, Y=Left, Z=Up)
- Camera Frame (C): Optical frame (Z=Forward, X=Right, Y=Down)
- IMU Frame (I): Co-located near navigation center
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np


def euler_to_quaternion(roll_rad: float, pitch_rad: float, yaw_rad: float) -> np.ndarray:
    """Converts intrinsic Z-Y-X Euler angles (yaw, pitch, roll) to unit quaternion [qw, qx, qy, qz]."""
    cr = math.cos(roll_rad * 0.5)
    sr = math.sin(roll_rad * 0.5)
    cp = math.cos(pitch_rad * 0.5)
    sp = math.sin(pitch_rad * 0.5)
    cy = math.cos(yaw_rad * 0.5)
    sy = math.sin(yaw_rad * 0.5)

    qw = cr * cp * cy + sr * sp * sy
    qx = sr * cp * cy - cr * sp * sy
    qy = cr * sp * cy + sr * cp * sy
    qz = cr * cp * sy - sr * sp * cy

    q = np.array([qw, qx, qy, qz], dtype=np.float64)
    norm = np.linalg.norm(q)
    return q / (norm if norm > 1e-12 else 1.0)


def quaternion_to_euler(q: np.ndarray) -> Tuple[float, float, float]:
    """Converts unit quaternion [qw, qx, qy, qz] to Euler angles (roll, pitch, yaw) in radians."""
    qw, qx, qy, qz = q[0], q[1], q[2], q[3]

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (qw * qx + qy * qz)
    cosr_cosp = 1.0 - 2.0 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (qw * qy - qz * qx)
    sinp = np.clip(sinp, -1.0, 1.0)
    pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def quaternion_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """Computes 3x3 direction cosine rotation matrix from unit quaternion [qw, qx, qy, qz]."""
    qw, qx, qy, qz = q[0], q[1], q[2], q[3]
    return np.array([
        [1.0 - 2.0*(qy**2 + qz**2), 2.0*(qx*qy - qz*qw),       2.0*(qx*qz + qy*qw)],
        [2.0*(qx*qy + qz*qw),       1.0 - 2.0*(qx**2 + qz**2), 2.0*(qy*qz - qx*qw)],
        [2.0*(qx*qz - qy*qw),       2.0*(qy*qz + qx*qw),       1.0 - 2.0*(qx**2 + qy**2)],
    ], dtype=np.float64)


class TransformSE3:
    """Rigid body SE(3) transformation represented by a rotation matrix R and translation vector t."""

    def __init__(self, rotation_matrix: Optional[np.ndarray] = None, translation: Optional[np.ndarray] = None) -> None:
        self.R = np.eye(3, dtype=np.float64) if rotation_matrix is None else np.array(rotation_matrix, dtype=np.float64)
        self.t = np.zeros(3, dtype=np.float64) if translation is None else np.array(translation, dtype=np.float64).flatten()

    @classmethod
    def from_xyz_rpy(cls, x: float, y: float, z: float, roll: float, pitch: float, yaw: float) -> TransformSE3:
        """Constructs SE(3) transform from position and Euler angles."""
        q = euler_to_quaternion(roll, pitch, yaw)
        R = quaternion_to_rotation_matrix(q)
        t = np.array([x, y, z], dtype=np.float64)
        return cls(R, t)

    def inverse(self) -> TransformSE3:
        """Computes inverse transformation T^-1 = [R^T, -R^T * t]."""
        R_inv = self.R.T
        t_inv = -R_inv @ self.t
        return TransformSE3(R_inv, t_inv)

    def compose(self, other: TransformSE3) -> TransformSE3:
        """Composes this transform with another: T_result = self * other."""
        R_res = self.R @ other.R
        t_res = self.R @ other.t + self.t
        return TransformSE3(R_res, t_res)

    def transform_points(self, points_xyz: np.ndarray) -> np.ndarray:
        """Transforms an (N, 3) array of 3D points: p' = R * p + t."""
        if len(points_xyz) == 0:
            return np.zeros((0, 3), dtype=np.float64)
        pts = np.asarray(points_xyz, dtype=np.float64)
        return (self.R @ pts.T).T + self.t


class SensorExtrinsics:
    """Extrinsic spatial calibration for perception and navigation sensors relative to Body Frame."""

    def __init__(self) -> None:
        # LiDAR mounted forward and elevated: x=+1.0m, y=0.0m, z=+1.8m
        self.T_body_lidar = TransformSE3.from_xyz_rpy(1.0, 0.0, 1.8, 0.0, 0.0, 0.0)

        # Stereo camera mounted forward and elevated: x=+0.9m, y=0.0m, z=+1.6m
        # Standard optical frame convention: Z forward, X right, Y down
        # Rotation from optical frame to body frame:
        # X_body = Z_opt, Y_body = -X_opt, Z_body = -Y_opt
        R_opt_to_body = np.array([
            [0.0, 0.0, 1.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
        ], dtype=np.float64)
        self.T_body_cam = TransformSE3(R_opt_to_body, np.array([0.9, 0.0, 1.6]))

        # IMU mounted near chassis center of rotation: x=+0.2m, y=0.0m, z=+0.4m
        self.T_body_imu = TransformSE3.from_xyz_rpy(0.2, 0.0, 0.4, 0.0, 0.0, 0.0)

    def lidar_to_world(self, points_lidar: np.ndarray, rover_pose: Tuple[float, float, float, float, float, float]) -> np.ndarray:
        """Transforms LiDAR points directly to World Frame given rover pose (x, y, z, roll, pitch, yaw)."""
        x, y, z, roll, pitch, yaw = rover_pose
        T_world_body = TransformSE3.from_xyz_rpy(x, y, z, roll, pitch, yaw)
        T_world_lidar = T_world_body.compose(self.T_body_lidar)
        return T_world_lidar.transform_points(points_lidar)
