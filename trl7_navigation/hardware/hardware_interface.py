"""Hardware Abstraction Layer (HAL) Interfaces for TRL 7 Operational Prototype.

Defines abstract base classes, telemetry packet structures, and CCSDS-like framing
for space-grade sensors and drive actuators.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import struct
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


@dataclass
class PacketHeader:
    """CCSDS-style Telemetry Packet Header."""
    version: int = 0
    packet_type: int = 0  # 0 = Telemetry, 1 = Command
    apid: int = 0x101     # Application Process Identifier
    seq_count: int = 0
    packet_length: int = 0
    timestamp_s: float = 0.0

    def pack(self) -> bytes:
        """Serializes primary header into 6 bytes + 8-byte timestamp."""
        # 16-bit packet ID: (version << 13) | (packet_type << 12) | (apid & 0x7FF)
        packet_id = ((self.version & 0x07) << 13) | ((self.packet_type & 0x01) << 12) | (self.apid & 0x07FF)
        # 16-bit sequence control: (3 << 14) | (seq_count & 0x3FFF)
        seq_ctrl = (0x03 << 14) | (self.seq_count & 0x3FFF)
        return struct.pack(">HHI d", packet_id, seq_ctrl, self.packet_length, self.timestamp_s)

    @classmethod
    def unpack(cls, buffer: bytes) -> PacketHeader:
        """Deserializes header from bytes."""
        packet_id, seq_ctrl, pkt_len, ts = struct.unpack(">HHI d", buffer[:16])
        version = (packet_id >> 13) & 0x07
        packet_type = (packet_id >> 12) & 0x01
        apid = packet_id & 0x07FF
        seq_count = seq_ctrl & 0x3FFF
        return cls(version=version, packet_type=packet_type, apid=apid, seq_count=seq_count, packet_length=pkt_len, timestamp_s=ts)


@dataclass
class IMUPacket:
    """Inertial Measurement Unit measurement packet."""
    timestamp_s: float
    seq: int
    gyro_rad_s: np.ndarray        # [wx, wy, wz]
    accel_m_s2: np.ndarray        # [ax, ay, az]
    temperature_c: float = 20.0
    status: str = "HEALTHY"
    crc16: int = 0


@dataclass
class LiDARScanPacket:
    """3D LiDAR point cloud scan packet."""
    timestamp_s: float
    seq: int
    points_xyz: np.ndarray        # (N, 3) float64 point cloud in sensor frame
    intensities: np.ndarray       # (N,) float34 return intensities
    valid_returns: int
    sensor_id: str = "LIDAR_3D"
    status: str = "HEALTHY"


@dataclass
class DepthFramePacket:
    """Stereo Depth Camera packet."""
    timestamp_s: float
    seq: int
    depth_image: np.ndarray       # (H, W) float64 depth in meters
    fx: float = 400.0
    fy: float = 400.0
    cx: float = 320.0
    cy: float = 240.0
    status: str = "HEALTHY"


@dataclass
class WheelOdometryPacket:
    """Wheel telemetry packet (6 drive wheels + 4 corner steering)."""
    timestamp_s: float
    seq: int
    wheel_speeds_rad_s: np.ndarray    # (6,) angular velocities
    steering_angles_rad: np.ndarray   # (4,) corner steering angles
    linear_velocity_m_s: float
    angular_velocity_rad_s: float
    status: str = "HEALTHY"


@dataclass
class ActuatorCommand:
    """Discrete command sent to rover locomotion controller."""
    timestamp_s: float
    seq: int
    linear_velocity_m_s: float
    steering_angle_rad: float
    curvature_inv_m: float = 0.0
    e_stop: bool = False
    brake_engaged: bool = False


@dataclass
class ActuatorTelemetry:
    """Telemetry returned by the drive chassis."""
    timestamp_s: float
    seq: int
    linear_velocity_m_s: float
    steering_angle_rad: float
    motor_currents_a: np.ndarray   # (6,) drive motor currents
    temperature_c: float
    fault_code: int = 0
    e_stop_active: bool = False


class ISensorHAL(ABC):
    """Abstract interface to rover perception and navigation sensors."""

    @abstractmethod
    def read_imu(self) -> IMUPacket:
        """Reads latest IMU packet."""
        pass

    @abstractmethod
    def read_lidar(self) -> Optional[LiDARScanPacket]:
        """Reads latest 3D LiDAR scan packet."""
        pass

    @abstractmethod
    def read_depth_camera(self) -> Optional[DepthFramePacket]:
        """Reads latest stereo depth camera frame."""
        pass

    @abstractmethod
    def read_wheel_odometry(self) -> WheelOdometryPacket:
        """Reads latest wheel odometry telemetry."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Returns True if all required sensors report healthy status."""
        pass


class IActuatorHAL(ABC):
    """Abstract interface to rover locomotion and steering actuators."""

    @abstractmethod
    def send_command(self, cmd: ActuatorCommand) -> bool:
        """Transmits locomotion command to motor controllers."""
        pass

    @abstractmethod
    def emergency_stop(self) -> None:
        """Immediately commands zero-velocity and locks friction brakes."""
        pass

    @abstractmethod
    def read_telemetry(self) -> ActuatorTelemetry:
        """Reads feedback from motor controllers and chassis sensors."""
        pass
