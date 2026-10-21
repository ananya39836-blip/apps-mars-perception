"""Integrated Multi-Sensor Rig for TRL 7 Operational Rover.

Coordinates physical or simulated sensor streams, enforces validation filters,
and computes synchronized multi-sensor observations in world and body frames.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation.hardware.hardware_interface import (
    ISensorHAL,
    IMUPacket,
    LiDARScanPacket,
    DepthFramePacket,
    WheelOdometryPacket,
)
from trl7_navigation.sensors.coordinate_transforms import SensorExtrinsics, TransformSE3
from trl7_navigation.sensors.sensor_validator import SensorValidator


class IntegratedSensorRig:
    """Manages sensor sampling, frame transformations, and validation gating."""

    def __init__(self, hal: ISensorHAL) -> None:
        self.hal = hal
        self.extrinsics = SensorExtrinsics()
        self.validator = SensorValidator()

        # Telemetry cache
        self.latest_imu: Optional[IMUPacket] = None
        self.latest_lidar_world: Optional[np.ndarray] = None
        self.latest_odom: Optional[WheelOdometryPacket] = None

    def poll_sensors(
        self,
        rover_pose_w: Tuple[float, float, float, float, float, float]
    ) -> Dict[str, Any]:
        """Polls sensor hardware, validates packets, and transforms into world coordinates."""
        # 1. IMU
        raw_imu = self.hal.read_imu()
        imu_valid, imu_msg = self.validator.validate_imu(raw_imu)
        if imu_valid:
            self.latest_imu = raw_imu

        # 2. Wheel Odometry
        raw_odom = self.hal.read_wheel_odometry()
        odom_valid, odom_msg = self.validator.validate_odometry(raw_odom)
        if odom_valid:
            self.latest_odom = raw_odom

        # 3. 3D LiDAR
        raw_lidar = self.hal.read_lidar()
        lidar_world = np.zeros((0, 3), dtype=np.float64)
        if raw_lidar is not None:
            lidar_valid, lidar_msg, clean_pts = self.validator.validate_lidar(raw_lidar)
            if lidar_valid and len(clean_pts) > 0:
                lidar_world = self.extrinsics.lidar_to_world(clean_pts, rover_pose_w)
                self.latest_lidar_world = lidar_world

        # 4. Depth Camera
        raw_depth = self.hal.read_depth_camera()

        return {
            "imu": self.latest_imu,
            "imu_valid": imu_valid,
            "odom": self.latest_odom,
            "odom_valid": odom_valid,
            "lidar_points_world": lidar_world,
            "depth_camera": raw_depth,
            "hardware_healthy": self.hal.is_healthy(),
        }
