"""Sensor Rig Extrinsic Calibration Parameters."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class SensorRigCalibration:
    """Rigid body transformation extrinsics from Body origin to sensor mount frames."""
    # Body to LiDAR mast mount [x, y, z] (m) and [roll, pitch, yaw] (rad)
    r_body_lidar: np.ndarray = np.array([1.0, 0.0, 1.8], dtype=np.float64)
    rpy_body_lidar: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    
    # Body to Stereo Camera Mast mount
    r_body_camera: np.ndarray = np.array([1.1, 0.0, 1.7], dtype=np.float64)
    rpy_body_camera: np.ndarray = np.array([0.0, 0.1745, 0.0], dtype=np.float64) # 10 deg pitch down
    
    # Body to IMU center
    r_body_imu: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    rpy_body_imu: np.ndarray = np.array([0.0, 0.0, 0.0], dtype=np.float64)
