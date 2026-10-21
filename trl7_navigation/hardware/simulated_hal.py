"""Simulated Hardware Abstraction Layer (Simulated HAL) for TRL 7.

Bridges the simulated planetary terrain and vehicle physics to the standard
ISensorHAL and IActuatorHAL interfaces, executing discrete time steps,
injecting realistic sensor noise models, and handling fault states.
"""
from __future__ import annotations
import math
import struct
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    G_MARS,
    G_EARTH,
    MAX_SPEED_MPS,
    MAX_STEERING_ANGLE_RAD,
    ROVER_WHEEL_RADIUS_M,
    ROVER_TRACK_GAUGE_M,
    ROVER_WHEELBASE_M,
)
from trl7_navigation.hardware.hardware_interface import (
    ISensorHAL,
    IActuatorHAL,
    IMUPacket,
    LiDARScanPacket,
    DepthFramePacket,
    WheelOdometryPacket,
    ActuatorCommand,
    ActuatorTelemetry,
)
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain


def compute_crc16(data: bytes) -> int:
    """Computes standard CCITT-16 CRC checksum."""
    crc = 0xFFFF
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


class SimulatedHAL(ISensorHAL, IActuatorHAL):
    """Simulated hardware interface executing space-grade sensor and drive models."""

    def __init__(
        self,
        terrain: PlanetaryTerrain,
        start_pose: Tuple[float, float, float] = (5.0, 5.0, 0.0),
        dt: float = 0.01,  # 100 Hz simulation cycle
        gravity_mps2: float = G_MARS,
        imu_noise_multiplier: float = 1.0,
        lidar_noise_m: float = 0.02,
        lidar_dropout_prob: float = 0.0,
        slip_bias: float = 0.05,
        seed: int = 42,
    ) -> None:
        self.terrain = terrain
        self.dt = float(dt)
        self.gravity = float(gravity_mps2)
        self.imu_noise_mult = float(imu_noise_multiplier)
        self.lidar_noise_m = float(lidar_noise_m)
        self.lidar_dropout_prob = float(lidar_dropout_prob)
        self.slip_bias = float(slip_bias)
        self.rng = np.random.default_rng(seed)

        # Ground-truth rover state
        self.sim_time: float = 0.0
        self.seq_imu: int = 0
        self.seq_lidar: int = 0
        self.seq_camera: int = 0
        self.seq_odom: int = 0
        self.seq_act: int = 0

        # Pose: x, y, z, roll, pitch, yaw
        self.x = float(start_pose[0])
        self.y = float(start_pose[1])
        self.z = float(self.terrain.get_elevation_at(self.x, self.y))
        self.yaw = float(start_pose[2])
        self.roll = 0.0
        self.pitch = 0.0

        # Velocities
        self.v_linear: float = 0.0
        self.v_angular: float = 0.0
        self.accel_body = np.zeros(3, dtype=np.float64)

        # Actuator command & state
        self.current_cmd_v: float = 0.0
        self.current_cmd_steer: float = 0.0
        self.e_stop_latched: bool = False
        self.fault_code: int = 0

        # IMU Allan variance parameters
        self.gyro_bias = np.array([0.001, -0.0015, 0.0008], dtype=np.float64)
        self.accel_bias = np.array([0.015, -0.012, 0.025], dtype=np.float64)
        self.gyro_noise_density = 0.003 * self.imu_noise_mult  # rad/s/sqrt(Hz)
        self.accel_noise_density = 0.025 * self.imu_noise_mult # m/s^2/sqrt(Hz)

    def set_fault(self, fault_code: int) -> None:
        """Injects hardware fault code (e.g. 0x01 = STALL, 0x02 = ESTOP)."""
        self.fault_code = fault_code
        if fault_code != 0:
            self.e_stop_latched = True

    # ---------------------------------------------------------
    # IActuatorHAL Implementation
    # ---------------------------------------------------------
    def send_command(self, cmd: ActuatorCommand) -> bool:
        """Applies drive and steer command with rate limits and safety check."""
        if self.e_stop_latched or cmd.e_stop:
            self.emergency_stop()
            return False

        # Apply velocity rate limit (accel max 0.4 m/s^2)
        v_clamped = np.clip(cmd.linear_velocity_m_s, -MAX_SPEED_MPS, MAX_SPEED_MPS)
        dv_max = 0.40 * self.dt
        self.v_linear = float(np.clip(v_clamped, self.v_linear - dv_max, self.v_linear + dv_max))

        # Apply steering rate limit (max 0.8 rad/s)
        steer_clamped = np.clip(cmd.steering_angle_rad, -MAX_STEERING_ANGLE_RAD, MAX_STEERING_ANGLE_RAD)
        dsteer_max = 0.80 * self.dt
        self.current_cmd_steer = float(np.clip(steer_clamped, self.current_cmd_steer - dsteer_max, self.current_cmd_steer + dsteer_max))

        # Kinematic differential steering
        self.v_angular = (self.v_linear / ROVER_WHEELBASE_M) * math.tan(self.current_cmd_steer)
        return True

    def emergency_stop(self) -> None:
        """Engages emergency stop and halts immediately."""
        self.e_stop_latched = True
        self.v_linear = 0.0
        self.v_angular = 0.0

    def read_telemetry(self) -> ActuatorTelemetry:
        """Reads motor telemetry."""
        self.seq_act += 1
        currents = np.ones(6) * (2.5 + 4.0 * abs(self.v_linear))
        return ActuatorTelemetry(
            timestamp_s=self.sim_time,
            seq=self.seq_act,
            linear_velocity_m_s=self.v_linear,
            steering_angle_rad=self.current_cmd_steer,
            motor_currents_a=currents,
            temperature_c=25.0 + 5.0 * abs(self.v_linear),
            fault_code=self.fault_code,
            e_stop_active=self.e_stop_latched,
        )

    # ---------------------------------------------------------
    # ISensorHAL Implementation
    # ---------------------------------------------------------
    def read_imu(self) -> IMUPacket:
        """Reads IMU measurements with bias and white noise."""
        self.seq_imu += 1
        # Angular velocity in body frame
        true_w = np.array([0.0, 0.0, self.v_angular], dtype=np.float64)
        gyro_noise = self.rng.normal(0.0, self.gyro_noise_density / math.sqrt(self.dt), 3)
        meas_w = true_w + self.gyro_bias + gyro_noise

        # Specific force: body accel + gravity vector projected into body
        # Gravity in world is [0, 0, -g]
        # Body orientation roll, pitch, yaw
        cr = math.cos(self.roll)
        sr = math.sin(self.roll)
        cp = math.cos(self.pitch)
        sp = math.sin(self.pitch)

        g_body = np.array([
            -self.gravity * sp,
            self.gravity * cp * sr,
            self.gravity * cp * cr,
        ], dtype=np.float64)

        accel_noise = self.rng.normal(0.0, self.accel_noise_density / math.sqrt(self.dt), 3)
        meas_a = self.accel_body + g_body + self.accel_bias + accel_noise

        raw_bytes = struct.pack(">3d3d", *meas_w, *meas_a)
        crc = compute_crc16(raw_bytes)

        return IMUPacket(
            timestamp_s=self.sim_time,
            seq=self.seq_imu,
            gyro_rad_s=meas_w,
            accel_m_s2=meas_a,
            temperature_c=20.0,
            status="FAULT" if self.fault_code != 0 else "HEALTHY",
            crc16=crc,
        )

    def read_lidar(self) -> Optional[LiDARScanPacket]:
        """Simulates 3D LiDAR point cloud scan in body/sensor frame."""
        self.seq_lidar += 1
        # Sensor dropout check
        if self.lidar_dropout_prob > 0.0 and self.rng.uniform(0.0, 1.0) < self.lidar_dropout_prob:
            return None

        # Direct sampling of terrain ahead of rover within FOV
        ranges = np.linspace(1.2, 18.0, 12)
        az_angles = np.linspace(-math.radians(35.0), math.radians(35.0), 16)
        points = []
        intensities = []

        cy = math.cos(self.yaw)
        sy = math.sin(self.yaw)
        sx_w = self.x + cy * 1.0
        sy_w = self.y + sy * 1.0
        sz_w = self.z + 1.8

        for az in az_angles:
            world_az = self.yaw + az
            c_waz = math.cos(world_az)
            s_waz = math.sin(world_az)
            for r in ranges:
                wx = sx_w + r * c_waz
                wy = sy_w + r * s_waz
                if 0.0 <= wx < self.terrain.size_x and 0.0 <= wy < self.terrain.size_y:
                    wz = self.terrain.get_elevation_at(wx, wy)
                    dwx = wx - sx_w
                    dwy = wy - sy_w
                    dwz = wz - sz_w
                    bx = cy * dwx + sy * dwy + float(self.rng.normal(0.0, self.lidar_noise_m))
                    by = -sy * dwx + cy * dwy + float(self.rng.normal(0.0, self.lidar_noise_m))
                    bz = dwz + float(self.rng.normal(0.0, self.lidar_noise_m))
                    points.append([bx, by, bz])
                    intensities.append(0.85)

        pts_arr = np.array(points, dtype=np.float64) if points else np.zeros((0, 3), dtype=np.float64)
        ints_arr = np.array(intensities, dtype=np.float64) if intensities else np.zeros(0, dtype=np.float64)

        return LiDARScanPacket(
            timestamp_s=self.sim_time,
            seq=self.seq_lidar,
            points_xyz=pts_arr,
            intensities=ints_arr,
            valid_returns=len(pts_arr),
            status="HEALTHY",
        )

    def read_depth_camera(self) -> Optional[DepthFramePacket]:
        """Simulates forward stereo depth camera grid."""
        self.seq_camera += 1
        h, w = 16, 24
        depth_img = np.ones((h, w), dtype=np.float64) * 12.0
        return DepthFramePacket(
            timestamp_s=self.sim_time,
            seq=self.seq_camera,
            depth_image=depth_img,
        )

    def read_wheel_odometry(self) -> WheelOdometryPacket:
        """Reads wheel encoder speeds and estimated odometry velocity."""
        self.seq_odom += 1
        # Slipping regolith reduces effective ground speed
        local_friction = 0.85
        if 0.0 <= self.x < self.terrain.size_x and 0.0 <= self.y < self.terrain.size_y:
            ix = int(np.clip(self.x / self.terrain.res, 0, self.terrain.nx - 1))
            iy = int(np.clip(self.y / self.terrain.res, 0, self.terrain.ny - 1))
            local_friction = self.terrain.regolith_friction[ix, iy]

        slip = self.slip_bias + (1.0 - local_friction) * 0.4
        meas_v = self.v_linear * (1.0 + self.rng.normal(0.0, 0.02) + slip)
        wheel_w = (meas_v / ROVER_WHEEL_RADIUS_M) * np.ones(6)
        steers = np.ones(4) * self.current_cmd_steer

        return WheelOdometryPacket(
            timestamp_s=self.sim_time,
            seq=self.seq_odom,
            wheel_speeds_rad_s=wheel_w,
            steering_angles_rad=steers,
            linear_velocity_m_s=meas_v,
            angular_velocity_rad_s=self.v_angular,
            status="HEALTHY",
        )

    def is_healthy(self) -> bool:
        return (not self.e_stop_latched) and (self.fault_code == 0)

    # ---------------------------------------------------------
    # Physics Integration Step
    # ---------------------------------------------------------
    def step_physics(self, dt: Optional[float] = None) -> None:
        """Integrates vehicle pose forward by dt seconds."""
        h = self.dt if dt is None else float(dt)
        self.sim_time += h

        if self.e_stop_latched:
            return

        # Local friction and slip check
        local_friction = 0.85
        if 0.0 <= self.x < self.terrain.size_x and 0.0 <= self.y < self.terrain.size_y:
            ix = int(np.clip(self.x / self.terrain.res, 0, self.terrain.nx - 1))
            iy = int(np.clip(self.y / self.terrain.res, 0, self.terrain.ny - 1))
            local_friction = self.terrain.regolith_friction[ix, iy]

        effective_v = self.v_linear * max(0.2, local_friction - self.slip_bias)

        # Update pose (Euler integration on SE(2) + DEM elevation projection)
        self.yaw += self.v_angular * h
        self.yaw = (self.yaw + math.pi) % (2.0 * math.pi) - math.pi

        self.x += effective_v * math.cos(self.yaw) * h
        self.y += effective_v * math.sin(self.yaw) * h

        # Clamp inside terrain domain
        self.x = float(np.clip(self.x, 0.5, self.terrain.size_x - 0.5))
        self.y = float(np.clip(self.y, 0.5, self.terrain.size_y - 0.5))

        self.z = float(self.terrain.get_elevation_at(self.x, self.y))

        # Approximate vehicle pitch and roll from local terrain gradient
        d = 1.0  # wheelbase baseline offset
        z_fwd = self.terrain.get_elevation_at(self.x + d * math.cos(self.yaw), self.y + d * math.sin(self.yaw))
        z_bwd = self.terrain.get_elevation_at(self.x - d * math.cos(self.yaw), self.y - d * math.sin(self.yaw))
        self.pitch = math.atan2(z_fwd - z_bwd, 2.0 * d)

        z_rgt = self.terrain.get_elevation_at(self.x + d * math.sin(self.yaw), self.y - d * math.cos(self.yaw))
        z_lft = self.terrain.get_elevation_at(self.x - d * math.sin(self.yaw), self.y + d * math.cos(self.yaw))
        self.roll = math.atan2(z_rgt - z_lft, 2.0 * d)
