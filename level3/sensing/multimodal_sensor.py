"""Multi-Modal Active Perception Sensor Suite for APPS Level 3.
Chapters 230, 233 & 234 (Part 14).

Simulates synchronized multi-sensor streams:
- High-Resolution Stereo Navcam
- 3D Flash LiDAR / Time-of-Flight Scanner
- Tactical 6-Axis Inertial Measurement Unit (IMU)
- High-rate Wheel Encoders
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class TacticalIMU:
    """Tactical-grade 6-axis IMU with Allan variance stochastic errors, bias drift and random walk."""

    def __init__(self, gyro_bias_std: float = 0.002, accel_bias_std: float = 0.02,
                 gyro_noise_std: float = 0.005, accel_noise_std: float = 0.05,
                 rate_hz: float = 200.0):
        self.dt = 1.0 / rate_hz
        self.gyro_bias_std = gyro_bias_std
        self.accel_bias_std = accel_bias_std
        self.gyro_noise_std = gyro_noise_std
        self.accel_noise_std = accel_noise_std

        # Internal state biases
        self.bg = np.zeros(3, dtype=np.float64) # Gyro bias
        self.ba = np.zeros(3, dtype=np.float64) # Accel bias

    def update(self, true_accel: np.ndarray, true_omega: np.ndarray,
               rng: np.random.Generator = None) -> Dict[str, np.ndarray]:
        """Generate corrupted IMU specific force and angular velocity observations."""
        if rng is None:
            rng = np.random.default_rng()

        # Random walk on biases
        self.bg += rng.normal(0.0, self.gyro_bias_std * math.sqrt(self.dt), size=3)
        self.ba += rng.normal(0.0, self.accel_bias_std * math.sqrt(self.dt), size=3)

        # White measurement noise
        noise_g = rng.normal(0.0, self.gyro_noise_std, size=3)
        noise_a = rng.normal(0.0, self.accel_noise_std, size=3)

        meas_omega = true_omega + self.bg + noise_g
        meas_accel = true_accel + self.ba + noise_a

        return {
            "gyro_meas_rad_s": meas_omega,
            "accel_meas_m_s2": meas_accel,
            "gyro_bias": self.bg.copy(),
            "accel_bias": self.ba.copy()
        }


class FlashLiDAR3D:
    """3D Flash LiDAR / Time-of-Flight sensor generating dense range point clouds with incidence drop-off."""

    def __init__(self, hfov_deg: float = 70.0, vfov_deg: float = 40.0,
                 channels_h: int = 64, channels_v: int = 32,
                 max_range_m: float = 18.0, range_noise_m: float = 0.02):
        self.hfov = math.radians(hfov_deg)
        self.vfov = math.radians(vfov_deg)
        self.ch_h = channels_h
        self.ch_v = channels_v
        self.max_range = float(max_range_m)
        self.range_noise = float(range_noise_m)

    def scan_dem(self, terrain_elevation: np.ndarray, cell_size_m: float,
                 sensor_pose: Tuple[float, float, float, float],
                 rng: np.random.Generator = None) -> np.ndarray:
        """Scan 3D digital elevation model and return (N, 4) point cloud: [X, Y, Z, Intensity]."""
        if rng is None:
            rng = np.random.default_rng()

        sx, sy, sz, syaw = sensor_pose
        H, W = terrain_elevation.shape
        points = []

        az_angles = np.linspace(-self.hfov / 2.0, self.hfov / 2.0, self.ch_h)
        el_angles = np.linspace(-self.vfov / 2.0, self.vfov / 2.0, self.ch_v)

        for el in el_angles:
            for az in az_angles:
                ray_yaw = syaw + az
                ray_dx = math.cos(el) * math.cos(ray_yaw)
                ray_dy = math.cos(el) * math.sin(ray_yaw)
                ray_dz = math.sin(el)

                # Ray trace against terrain surface
                for dist in np.linspace(0.5, self.max_range, 30):
                    px = sx + ray_dx * dist
                    py = sy + ray_dy * dist
                    pz = sz + ray_dz * dist

                    gx = int(round(px / cell_size_m))
                    gy = int(round(py / cell_size_m))

                    if 0 <= gx < W and 0 <= gy < H:
                        dem_z = terrain_elevation[gy, gx]
                        if pz <= dem_z:
                            # Hit detected
                            noise = float(rng.normal(0.0, self.range_noise))
                            noisy_dist = dist + noise
                            hit_x = sx + ray_dx * noisy_dist
                            hit_y = sy + ray_dy * noisy_dist
                            hit_z = sz + ray_dz * noisy_dist
                            intensity = float(max(0.1, 1.0 - (dist / self.max_range)**1.5))
                            points.append([hit_x, hit_y, hit_z, intensity])
                            break

        if not points:
            return np.zeros((0, 4), dtype=np.float32)
        return np.array(points, dtype=np.float32)
