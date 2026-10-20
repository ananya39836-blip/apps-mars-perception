"""SE(3) Coordinate Transformation Utilities for Planetary Navigation (TRL 5).

Defines rigid-body spatial transformations between:
- World Frame (W): East-North-Up global inertial frame.
- Map Frame (M): Local navigation grid frame.
- Base / Body Frame (B): Rover center-of-mass, +X forward, +Y left, +Z up.
- LiDAR Frame (L): Mast-mounted LiDAR.
- Camera Frame (C): Mast-mounted stereo depth camera.
- IMU Frame (I): Internal tactical IMU.
"""
from __future__ import annotations
import math
from typing import Tuple
import numpy as np


def euler_to_rot_matrix(roll_rad: float, pitch_rad: float, yaw_rad: float) -> np.ndarray:
    """Computes standard 3x3 rotation matrix R_z(yaw) * R_y(pitch) * R_x(roll)."""
    cr, sr = math.cos(roll_rad), math.sin(roll_rad)
    cp, sp = math.cos(pitch_rad), math.sin(pitch_rad)
    cy, sy = math.cos(yaw_rad), math.sin(yaw_rad)

    R_x = np.array([[1.0, 0.0, 0.0],
                    [0.0, cr, -sr],
                    [0.0, sr, cr]], dtype=np.float64)

    R_y = np.array([[cp, 0.0, sp],
                    [0.0, 1.0, 0.0],
                    [-sp, 0.0, cp]], dtype=np.float64)

    R_z = np.array([[cy, -sy, 0.0],
                    [sy, cy, 0.0],
                    [0.0, 0.0, 1.0]], dtype=np.float64)

    return R_z @ R_y @ R_x


def make_se3_transform(translation: np.ndarray, euler_rpy_rad: Tuple[float, float, float]) -> np.ndarray:
    """Constructs 4x4 homogeneous transformation matrix T in SE(3)."""
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = euler_to_rot_matrix(*euler_rpy_rad)
    T[:3, 3] = translation[:3]
    return T


def invert_se3_transform(T: np.ndarray) -> np.ndarray:
    """Inverts a 4x4 homogeneous transformation matrix: T^-1 = [R^T, -R^T * p; 0, 1]."""
    T_inv = np.eye(4, dtype=np.float64)
    R = T[:3, :3]
    p = T[:3, 3]
    R_T = R.T
    T_inv[:3, :3] = R_T
    T_inv[:3, 3] = -R_T @ p
    return T_inv


def transform_points(points_xyz: np.ndarray, T: np.ndarray) -> np.ndarray:
    """Applies SE(3) transformation T to an (N, 3) array of 3D points."""
    if points_xyz.size == 0:
        return np.empty((0, 3), dtype=np.float64)
    pts_homo = np.hstack([points_xyz, np.ones((len(points_xyz), 1), dtype=np.float64)])
    transformed = (T @ pts_homo.T).T
    return transformed[:, :3]


# Standard static extrinsic calibration transforms relative to Base Frame (B)
# LiDAR: +0.35m forward, 0.0m lateral, +0.85m vertical, pitched down 15 deg (-0.2618 rad)
T_BASE_LIDAR = make_se3_transform(
    translation=np.array([0.35, 0.0, 0.85]),
    euler_rpy_rad=(0.0, math.radians(-15.0), 0.0)
)

# Camera: +0.45m forward, 0.0m lateral, +0.75m vertical, pitched down 20 deg (-0.3491 rad)
T_BASE_CAMERA = make_se3_transform(
    translation=np.array([0.45, 0.0, 0.75]),
    euler_rpy_rad=(0.0, math.radians(-20.0), 0.0)
)

# IMU: CoM offset (0.0, 0.0, +0.25m), aligned with body axes
T_BASE_IMU = make_se3_transform(
    translation=np.array([0.0, 0.0, 0.25]),
    euler_rpy_rad=(0.0, 0.0, 0.0)
)
