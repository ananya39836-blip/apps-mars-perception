"""Physical Sensor Driver Emulation for Operational Analog Field Deployments (TRL 7).

Provides drivers and communication handlers for hardware interfaces commonly
employed in terrestrial planetary analog field testbeds (basalt quarry, Mars yard):
- Serial IMU Driver (UART/RS-422 with NMEA / binary packet parsing)
- Ethernet LiDAR Driver (UDP packet stream listener & parser)
- CANopen Motor Controller Driver (with CAN 2.0B frame handling)
- Hardware E-Stop and Deadman Heartbeat Monitor
"""
from __future__ import annotations
import math
import struct
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation.hardware.hardware_interface import (
    IMUPacket,
    LiDARScanPacket,
    ActuatorCommand,
    ActuatorTelemetry,
)


class SerialIMUDriver:
    """Serial port driver emulator for high-grade tactical IMUs (e.g. MicroStrain 3DM)."""

    def __init__(self, port: str = "COM3", baudrate: int = 115200, timeout_s: float = 0.05) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.is_connected = True
        self.packet_count = 0

    def parse_packet(self, raw_bytes: bytes) -> Optional[IMUPacket]:
        """Parses binary telemetry packet containing header, timestamp, gyro, accel, and checksum."""
        if len(raw_bytes) < 36:
            return None

        # Check sync bytes 0x75 0x65
        sync1, sync2 = raw_bytes[0], raw_bytes[1]
        if sync1 != 0x75 or sync2 != 0x65:
            return None

        try:
            ts, gx, gy, gz, ax, ay, az = struct.unpack(">d3f3f", raw_bytes[2:34])
            chk = struct.unpack(">H", raw_bytes[34:36])[0]
            self.packet_count += 1
            return IMUPacket(
                timestamp_s=float(ts),
                seq=self.packet_count,
                gyro_rad_s=np.array([gx, gy, gz], dtype=np.float64),
                accel_m_s2=np.array([ax, ay, az], dtype=np.float64),
                status="HEALTHY",
            )
        except Exception:
            return None


class EthernetLiDARDriver:
    """Ethernet UDP packet listener and point cloud assembler for 3D LiDAR."""

    def __init__(self, ip: str = "192.168.1.201", port: int = 2368) -> None:
        self.ip = ip
        self.port = port
        self.is_connected = True
        self.scan_count = 0

    def parse_udp_payload(self, payload: bytes) -> Optional[np.ndarray]:
        """Parses a UDP packet containing spherical coordinate returns into XYZ points."""
        if len(payload) < 1200:
            return None
        # Extract laser firing data
        points = []
        n_blocks = min(12, len(payload) // 100)
        for b in range(n_blocks):
            base = b * 100
            azimuth_raw = struct.unpack_from("<H", payload, base + 2)[0]
            azimuth = math.radians(azimuth_raw / 100.0)
            for c in range(16):
                dist_raw = struct.unpack_from("<H", payload, base + 4 + c * 3)[0]
                dist = dist_raw * 0.002  # 2mm resolution
                elev = math.radians(-15.0 + c * 2.0)
                if 0.5 <= dist <= 30.0:
                    px = dist * math.cos(elev) * math.cos(azimuth)
                    py = dist * math.cos(elev) * math.sin(azimuth)
                    pz = dist * math.sin(elev)
                    points.append([px, py, pz])

        return np.array(points, dtype=np.float64) if points else None


class MotorControllerCAN:
    """CANopen / CAN 2.0B locomotion actuator driver with heartbeat watchdog."""

    def __init__(self, node_id: int = 0x20, baudrate: int = 500000) -> None:
        self.node_id = node_id
        self.baudrate = baudrate
        self.last_cmd_time_s = time.time()
        self.heartbeat_timeout_s = 0.250  # 250 ms watchdog
        self.is_e_stopped = False

    def build_velocity_can_frame(self, speed_mps: float, steer_rad: float) -> Tuple[int, bytes]:
        """Encodes speed and steering into standard 8-byte CAN frame."""
        can_id = 0x200 + self.node_id
        speed_int16 = int(np.clip(speed_mps * 1000.0, -32768, 32767))
        steer_int16 = int(np.clip(steer_rad * 1000.0, -32768, 32767))
        payload = struct.pack("<hh4x", speed_int16, steer_int16)
        self.last_cmd_time_s = time.time()
        return can_id, payload

    def check_watchdog(self) -> bool:
        """Returns True if within watchdog timeout; trips E-Stop if timed out."""
        elapsed = time.time() - self.last_cmd_time_s
        if elapsed > self.heartbeat_timeout_s:
            self.is_e_stopped = True
            return False
        return True


class EStopMonitor:
    """Hardware Emergency Stop & Deadman Heartbeat Monitor."""

    def __init__(self, timeout_s: float = 0.50) -> None:
        self.timeout_s = timeout_s
        self.last_heartbeat_time = time.time()
        self.hardware_e_stop_pressed = False

    def pulse_heartbeat(self) -> None:
        self.last_heartbeat_time = time.time()

    def trip_estop(self) -> None:
        self.hardware_e_stop_pressed = True

    def reset_estop(self) -> None:
        self.hardware_e_stop_pressed = False
        self.last_heartbeat_time = time.time()

    def is_safe(self) -> bool:
        if self.hardware_e_stop_pressed:
            return False
        if (time.time() - self.last_heartbeat_time) > self.timeout_s:
            return False
        return True
