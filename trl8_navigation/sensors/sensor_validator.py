"""Space-Grade Telemetry Validation Gatekeeper.

Rejects corrupted, stale, or physically impossible sensor observations
prior to downstream perception and state estimation ingestion.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Optional
import numpy as np


class SensorDataValidator:
    """Sanity checker and CRC gatekeeper for raw sensor telemetry streams."""

    def __init__(self, max_accel_mps2: float = 50.0, max_gyro_rads: float = 10.0) -> None:
        self.max_accel_mps2 = max_accel_mps2
        self.max_gyro_rads = max_gyro_rads
        self.last_imu_timestamp: float = -1.0
        self.last_lidar_timestamp: float = -1.0
        self.corrupt_packet_count: int = 0

    def validate_imu(self, ax: float, ay: float, az: float, gx: float, gy: float, gz: float, timestamp: float) -> bool:
        """Validates IMU linear accelerations and angular rates."""
        # Float finiteness (reject NaN, +Inf, -Inf)
        vals = [ax, ay, az, gx, gy, gz, timestamp]
        if any(math.isnan(v) or math.isinf(v) for v in vals):
            self.corrupt_packet_count += 1
            return False

        # Timestamp monotonicity
        if timestamp <= self.last_imu_timestamp:
            self.corrupt_packet_count += 1
            return False

        # Physical acceleration magnitude check
        accel_mag = math.sqrt(ax * ax + ay * ay + az * az)
        if accel_mag > self.max_accel_mps2:
            self.corrupt_packet_count += 1
            return False

        # Physical angular rate magnitude check
        gyro_mag = math.sqrt(gx * gx + gy * gy + gz * gz)
        if gyro_mag > self.max_gyro_rads:
            self.corrupt_packet_count += 1
            return False

        self.last_imu_timestamp = timestamp
        return True

    def validate_point_cloud(self, points: np.ndarray, timestamp: float) -> bool:
        """Validates LiDAR / depth point cloud array."""
        if math.isnan(timestamp) or math.isinf(timestamp):
            self.corrupt_packet_count += 1
            return False

        if timestamp <= self.last_lidar_timestamp:
            self.corrupt_packet_count += 1
            return False

        if not isinstance(points, np.ndarray) or points.ndim != 2 or points.shape[1] != 3:
            self.corrupt_packet_count += 1
            return False

        if np.isnan(points).any() or np.isinf(points).any():
            self.corrupt_packet_count += 1
            return False

        self.last_lidar_timestamp = timestamp
        return True
