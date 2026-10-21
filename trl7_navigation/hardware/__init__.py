"""Hardware abstraction and physical driver package for TRL 7 operational prototype."""
from trl7_navigation.hardware.hardware_interface import (
    PacketHeader,
    IMUPacket,
    LiDARScanPacket,
    DepthFramePacket,
    WheelOdometryPacket,
    ActuatorCommand,
    ActuatorTelemetry,
    ISensorHAL,
    IActuatorHAL,
)
from trl7_navigation.hardware.simulated_hal import SimulatedHAL, compute_crc16
from trl7_navigation.hardware.physical_sensor_driver import (
    SerialIMUDriver,
    EthernetLiDARDriver,
    MotorControllerCAN,
    EStopMonitor,
)

__all__ = [
    "PacketHeader",
    "IMUPacket",
    "LiDARScanPacket",
    "DepthFramePacket",
    "WheelOdometryPacket",
    "ActuatorCommand",
    "ActuatorTelemetry",
    "ISensorHAL",
    "IActuatorHAL",
    "SimulatedHAL",
    "compute_crc16",
    "SerialIMUDriver",
    "EthernetLiDARDriver",
    "MotorControllerCAN",
    "EStopMonitor",
]
