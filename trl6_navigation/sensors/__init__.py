"""Space-Grade Multi-Sensor Simulation & Telemetry Validation Module (TRL 6)."""
from __future__ import annotations

from trl6_navigation.sensors.coordinate_transforms import (
    make_se3_transform,
    invert_se3_transform,
    transform_points_se3,
    T_BASE_LIDAR,
    T_BASE_CAMERA,
    T_BASE_IMU,
)
from trl6_navigation.sensors.sensor_rig import MultiSensorRig
from trl6_navigation.sensors.sensor_validator import SensorDataValidator, ValidatedSensorFrame

__all__ = [
    "make_se3_transform",
    "invert_se3_transform",
    "transform_points_se3",
    "T_BASE_LIDAR",
    "T_BASE_CAMERA",
    "T_BASE_IMU",
    "MultiSensorRig",
    "SensorDataValidator",
    "ValidatedSensorFrame",
]
