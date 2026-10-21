"""Sensors, transforms, and space-grade validation package for TRL 7 operational prototype."""
from trl7_navigation.sensors.coordinate_transforms import (
    euler_to_quaternion,
    quaternion_to_euler,
    quaternion_to_rotation_matrix,
    TransformSE3,
    SensorExtrinsics,
)
from trl7_navigation.sensors.sensor_validator import SensorValidator
from trl7_navigation.sensors.sensor_rig import IntegratedSensorRig

__all__ = [
    "euler_to_quaternion",
    "quaternion_to_euler",
    "quaternion_to_rotation_matrix",
    "TransformSE3",
    "SensorExtrinsics",
    "SensorValidator",
    "IntegratedSensorRig",
]
