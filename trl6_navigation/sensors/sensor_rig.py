"""Space-Grade Multi-Sensor Simulation Rig (TRL 6).

Generates synthetic measurements for:
1. 3D Navigation LiDAR (16-beam, range noise, incidence angle & dust dropouts)
2. Stereo RGB-D Depth Camera (Quadratic disparity uncertainty sigma_Z proportional to Z^2)
3. Tactical 6-Axis IMU (Allan variance drift, Martian surface gravity g = 3.71 m/s^2)
4. Wheel Odometry (Wheel encoders with non-linear longitudinal slip)
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional
import numpy as np

from trl6_navigation import G_MARS, ROVER_WHEEL_RADIUS_M
from trl6_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl6_navigation.sensors.coordinate_transforms import (
    make_se3_transform,
    transform_points_se3,
    T_BASE_LIDAR,
    T_BASE_CAMERA,
    T_BASE_IMU,
)


class MultiSensorRig:
    """Manages multi-sensor simulation rig under Martian environmental conditions."""

    def __init__(
        self,
        terrain: PlanetaryTerrain,
        noise_multiplier: float = 1.0,
        lidar_dropout_prob: float = 0.0,
        seed: int = 42
    ) -> None:
        self.terrain = terrain
        self.noise_mult = float(noise_multiplier)
        self.lidar_dropout_prob = float(lidar_dropout_prob)
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

        # Tactical IMU stochastic bias states (Allan variance integration)
        self.accel_bias = self.rng.normal(0.0, 0.015 * self.noise_mult, size=3)
        self.gyro_bias = self.rng.normal(0.0, 0.005 * self.noise_mult, size=3)

    def sample_lidar(
        self,
        rover_pose_xytheta: np.ndarray,
        num_elevation_beams: int = 16,
        num_azimuth_steps: int = 64,
        max_range_m: float = 20.0
    ) -> Dict[str, Any]:
        """Simulates 3D LiDAR point cloud scan in sensor frame and world frame."""
        rx, ry, r_yaw = float(rover_pose_xytheta[0]), float(rover_pose_xytheta[1]), float(rover_pose_xytheta[2])
        rover_z = self.terrain.get_elevation_at(rx, ry)

        # World-to-base transformation matrix
        T_world_base = make_se3_transform(
            np.array([rx, ry, rover_z]),
            rpy_rad=(0.0, 0.0, r_yaw)
        )
        T_world_lidar = T_world_base @ T_BASE_LIDAR
        lidar_origin_w = T_world_lidar[:3, 3]

        elevation_angles = np.linspace(math.radians(-15.0), math.radians(5.0), num_elevation_beams)
        azimuth_angles = np.linspace(0.0, 2 * math.pi, num_azimuth_steps, endpoint=False)

        points_lidar: List[List[float]] = []
        intensities: List[float] = []

        # Ray-march terrain intersections
        step_m = 0.25
        for el in elevation_angles:
            for az in azimuth_angles:
                # Stochastic dropout check (atmospheric dust / beam divergence)
                if self.rng.uniform(0.0, 1.0) < self.lidar_dropout_prob:
                    continue

                # Ray unit vector in local LiDAR frame (+X forward, +Y left, +Z up)
                ray_l = np.array([
                    math.cos(el) * math.cos(az),
                    math.cos(el) * math.sin(az),
                    math.sin(el)
                ])

                # Rotate ray into world coordinates
                ray_w = T_world_lidar[:3, :3] @ ray_l

                # Ray marching
                hit = False
                dist = 0.5
                while dist <= max_range_m:
                    test_pt = lidar_origin_w + dist * ray_w
                    if not (0.0 <= test_pt[0] < self.terrain.size_x and 0.0 <= test_pt[1] < self.terrain.size_y):
                        break

                    terr_z = self.terrain.get_elevation_at(test_pt[0], test_pt[1])
                    if test_pt[2] <= terr_z:
                        # Ground/obstacle surface hit
                        # Range noise increases quadratically with distance
                        sigma_r = 0.02 * self.noise_mult * (1.0 + (dist / max_range_m) ** 1.5)
                        noisy_dist = dist + self.rng.normal(0.0, sigma_r)
                        pt_hit_l = ray_l * noisy_dist
                        points_lidar.append(pt_hit_l.tolist())

                        # Synthetic reflectance intensity
                        intensity = max(0.1, 1.0 - (dist / max_range_m))
                        intensities.append(float(intensity))
                        hit = True
                        break
                    dist += step_m

        pts_arr_lidar = np.array(points_lidar, dtype=np.float64) if points_lidar else np.zeros((0, 3))
        pts_arr_world = transform_points_se3(pts_arr_lidar, T_world_lidar)

        return {
            "timestamp": 0.0,
            "points_lidar": pts_arr_lidar,
            "points_world": pts_arr_world,
            "intensities": np.array(intensities, dtype=np.float64),
            "T_world_lidar": T_world_lidar,
            "num_returns": len(points_lidar),
        }

    def sample_stereo_camera(
        self,
        rover_pose_xytheta: np.ndarray,
        resolution_wh: Tuple[int, int] = (32, 24),
        max_depth_m: float = 12.0
    ) -> Dict[str, Any]:
        """Simulates stereo depth camera with optical disparity error growth sigma_Z proportional to Z^2."""
        rx, ry, r_yaw = float(rover_pose_xytheta[0]), float(rover_pose_xytheta[1]), float(rover_pose_xytheta[2])
        rover_z = self.terrain.get_elevation_at(rx, ry)

        T_world_base = make_se3_transform(
            np.array([rx, ry, rover_z]),
            rpy_rad=(0.0, 0.0, r_yaw)
        )
        T_world_cam = T_world_base @ T_BASE_CAMERA
        cam_origin_w = T_world_cam[:3, 3]

        w, h = resolution_wh
        depth_map = np.zeros((h, w), dtype=np.float64)
        fov_h_rad = math.radians(65.0)
        fov_v_rad = math.radians(45.0)

        for v_idx, y_ang in enumerate(np.linspace(-fov_v_rad / 2, fov_v_rad / 2, h)):
            for u_idx, x_ang in enumerate(np.linspace(-fov_h_rad / 2, fov_h_rad / 2, w)):
                # Camera optical frame: +Z optical depth, +X right, +Y down
                ray_c = np.array([math.tan(x_ang), math.tan(y_ang), 1.0])
                ray_c = ray_c / np.linalg.norm(ray_c)

                # World ray
                ray_w = T_world_cam[:3, :3] @ ray_c

                d = 0.5
                dist_hit = max_depth_m
                while d <= max_depth_m:
                    test_pt = cam_origin_w + d * ray_w
                    if 0.0 <= test_pt[0] < self.terrain.size_x and 0.0 <= test_pt[1] < self.terrain.size_y:
                        if test_pt[2] <= self.terrain.get_elevation_at(test_pt[0], test_pt[1]):
                            # Disparity noise: sigma_Z = (Z^2 / (f * B)) * sigma_d
                            sigma_z = 0.015 * (d**2 / 10.0) * self.noise_mult
                            dist_hit = max(0.1, d + self.rng.normal(0.0, sigma_z))
                            break
                    d += 0.25
                depth_map[v_idx, u_idx] = dist_hit

        return {
            "timestamp": 0.0,
            "depth_map": depth_map,
            "resolution": resolution_wh,
            "T_world_camera": T_world_cam,
        }

    def sample_imu(
        self,
        rover_pose_xytheta: np.ndarray,
        forward_speed_mps: float,
        yaw_rate_rps: float,
        dt_s: float = 0.01
    ) -> Dict[str, Any]:
        """Simulates tactical 6-axis IMU with Allan variance drift and Martian surface gravity."""
        # Random walk bias integration
        self.accel_bias += self.rng.normal(0.0, 0.001 * math.sqrt(dt_s) * self.noise_mult, size=3)
        self.gyro_bias += self.rng.normal(0.0, 0.0005 * math.sqrt(dt_s) * self.noise_mult, size=3)

        # Body-frame Martian gravity reaction (+Z upward in body coordinates)
        g_body = np.array([0.0, 0.0, G_MARS])

        # Centripetal acceleration: a_y = v * omega
        a_centripetal = forward_speed_mps * yaw_rate_rps
        a_true = np.array([0.0, a_centripetal, 0.0]) + g_body

        # Rate gyro: omega_z
        w_true = np.array([0.0, 0.0, yaw_rate_rps])

        # Add stochastic white noise & bias
        a_meas = a_true + self.accel_bias + self.rng.normal(0.0, 0.02 * self.noise_mult, size=3)
        w_meas = w_true + self.gyro_bias + self.rng.normal(0.0, 0.005 * self.noise_mult, size=3)

        return {
            "meas_accel_mps2": a_meas,
            "meas_gyro_rps": w_meas,
            "accel_bias": self.accel_bias.copy(),
            "gyro_bias": self.gyro_bias.copy(),
            "g_mars": G_MARS,
        }

    def sample_wheel_odometry(
        self,
        true_speed_mps: float,
        true_yaw_rate_rps: float,
        slip_ratio: float = 0.05
    ) -> Dict[str, Any]:
        """Simulates wheel encoder odometry subject to non-linear slip disturbances."""
        # Apparent wheel speed v_wheel = v_true / (1 - slip)
        eff_slip = np.clip(slip_ratio, 0.0, 0.85)
        apparent_speed = true_speed_mps / max(0.1, (1.0 - eff_slip))

        # Add encoder discretization & quantization noise
        speed_meas = apparent_speed + self.rng.normal(0.0, 0.01 * self.noise_mult)
        yaw_rate_meas = true_yaw_rate_rps + self.rng.normal(0.0, 0.008 * self.noise_mult)

        return {
            "meas_linear_mps": float(speed_meas),
            "meas_angular_rps": float(yaw_rate_meas),
            "wheel_radius_m": ROVER_WHEEL_RADIUS_M,
            "injected_slip_ratio": float(slip_ratio),
        }
