"""Rigid-Body SE(3) Coordinate Frame Transformations (TRL 6).

Implements homogeneous transformations between the following right-handed Cartesian frames:
- World / Map Frame (W): Origin at staging site (+X East, +Y North, +Z Up)
- Rover Base Frame (B): Origin at rover chassis center (+X Fwd, +Y Left, +Z Up)
- LiDAR Frame (L): Origin at nav-mast optical center
- Stereo Camera Frame (C): Origin at camera optical center
- Tactical IMU Frame (I): Origin at IMU body casing
"""
from __future__ import annotations
import math
from typing import Tuple
import numpy as np


def make_se3_transform(
    translation_xyz: np.ndarray,
    rpy_rad: Tuple[float, float, float] = (0.0, 0.0, 0.0)
) -> np.ndarray:
    """Constructs a 4x4 homogeneous transformation matrix in SE(3)."""
    roll, pitch, yaw = rpy_rad
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    # Z-Y-X Euler rotation matrix
    R = np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ], dtype=np.float64)

    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = R
    T[:3, 3] = translation_xyz
    return T


def invert_se3_transform(T: np.ndarray) -> np.ndarray:
    """Computes exact analytical inverse of a 4x4 homogeneous matrix in SE(3)."""
    R = T[:3, :3]
    p = T[:3, 3]

    T_inv = np.eye(4, dtype=np.float64)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ p
    return T_inv


def transform_points_se3(points: np.ndarray, T: np.ndarray) -> np.ndarray:
    """Transforms an (N, 3) array of 3D Cartesian points using a 4x4 SE(3) matrix."""
    if len(points) == 0:
        return np.zeros((0, 3), dtype=np.float64)

    N = points.shape[0]
    pts_hom = np.hstack([points[:, :3], np.ones((N, 1), dtype=np.float64)])
    pts_trans = (T @ pts_hom.T).T
    return pts_trans[:, :3]


# Extrinsic Sensor Calibrations Relative to Rover Base Chassis (B)
# LiDAR Mast Extrinsics: X=+0.40m forward, Y=0.0m, Z=+1.25m up, pitch down 15 deg
T_BASE_LIDAR: np.ndarray = make_se3_transform(
    np.array([0.40, 0.0, 1.25]),
    rpy_rad=(0.0, math.radians(-15.0), 0.0)
)

# Stereo Camera Extrinsics: X=+0.45m forward, Y=0.0m, Z=+1.20m up, pitch down 20 deg
T_BASE_CAMERA: np.ndarray = make_se3_transform(
    np.array([0.45, 0.0, 1.20]),
    rpy_rad=(0.0, math.radians(-20.0), 0.0)
)

# Tactical IMU Extrinsics: X=0.0m, Y=0.0m, Z=+0.15m up (aligned with base chassis)
T_BASE_IMU: np.ndarray = make_se3_transform(
    np.array([0.0, 0.0, 0.15]),
    rpy_rad=(0.0, 0.0, 0.0)
)
