"""Multi-Sensor Rig Simulation for Planetary Rover Navigation (TRL 5).

Generates synthetic sensor streams with physically representative error models:
- 3D LiDAR: Multi-beam ray-casting with range noise, beam dropouts, and incidence limits.
- RGB-D Camera: Stereo depth images with range-squared uncertainty u(Z) ~ Z^2.
- Tactical 6-Axis IMU: Accelerometer and gyroscope measurements with Allan variance drift under Martian gravity.
- Wheel Odometers: Incremental wheel velocity with terrain-dependent slip noise.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

from trl5_navigation import G_MARS, ROVER_WHEEL_RADIUS_M
from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.sensors.coordinate_transforms import (
    euler_to_rot_matrix, make_se3_transform, transform_points, T_BASE_LIDAR, T_BASE_CAMERA, T_BASE_IMU
)


class MultiSensorRig:
    """Manages synthetic sensor data generation for a planetary rover."""

    def __init__(
        self,
        terrain: PlanetaryTerrain,
        noise_multiplier: float = 1.0,
        lidar_dropout_prob: float = 0.05,
        seed: int = 42
    ) -> None:
        self.terrain = terrain
        self.noise_mult = float(noise_multiplier)
        self.dropout_prob = float(lidar_dropout_prob)
        self.rng = np.random.default_rng(seed)

        # IMU bias state (Gauss-Markov random walk)
        self.gyro_bias = self.rng.normal(0.0, 1.0e-4, size=3)   # rad/s
        self.accel_bias = self.rng.normal(0.0, 5.0e-3, size=3)  # m/s^2

    def sample_lidar(
        self,
        rover_pose_xytheta: np.ndarray,
        num_azimuth: int = 64,
        num_elevation: int = 16,
        max_range_m: float = 20.0,
        min_range_m: float = 0.5
    ) -> Dict[str, Any]:
        """Simulates 3D LiDAR point cloud returns in the sensor frame (L)."""
        x_r, y_r, yaw_r = rover_pose_xytheta[:3]
        z_r = self.terrain.get_elevation_at(x_r, y_r)

        # Rover base transform in world frame
        normal, _ = self.terrain.get_surface_normal_and_slope(x_r, y_r)
        pitch_r = -math.atan2(normal[0], normal[2])
        roll_r = math.atan2(normal[1], normal[2])
        T_world_base = make_se3_transform(np.array([x_r, y_r, z_r]), (roll_r, pitch_r, yaw_r))
        T_world_lidar = T_world_base @ T_BASE_LIDAR

        p_lidar_w = T_world_lidar[:3, 3]
        R_world_lidar = T_world_lidar[:3, :3]

        azimuths = np.linspace(-math.pi, math.pi, num_azimuth, endpoint=False)
        elevations = np.linspace(math.radians(-25.0), math.radians(10.0), num_elevation)

        points_lidar_frame = []
        ranges = []
        intensities = []

        step_size_m = 0.25
        num_steps = int(max_range_m / step_size_m)

        for el in elevations:
            for az in azimuths:
                # Random beam dropout (e.g. atmospheric dust or dark absorbing surface)
                if self.rng.uniform(0.0, 1.0) < self.dropout_prob:
                    continue

                # Ray unit vector in LiDAR frame
                dir_l = np.array([
                    math.cos(el) * math.cos(az),
                    math.cos(el) * math.sin(az),
                    math.sin(el)
                ], dtype=np.float64)

                # Transform ray direction to World frame
                dir_w = R_world_lidar @ dir_l

                # Ray-cast onto DEM
                hit = False
                hit_range = max_range_m
                for step in range(1, num_steps + 1):
                    r_curr = step * step_size_m
                    pt_w = p_lidar_w + dir_w * r_curr

                    if not (0.0 <= pt_w[0] < self.terrain.size_x and 0.0 <= pt_w[1] < self.terrain.size_y):
                        break

                    terr_z = self.terrain.get_elevation_at(pt_w[0], pt_w[1])
                    if pt_w[2] <= terr_z:
                        # Refined hit point
                        hit_range = r_curr
                        hit = True
                        break

                if hit and min_range_m <= hit_range <= max_range_m:
                    # Inhomogeneous Gaussian range noise: sigma = 0.02m nominal
                    sigma_r = 0.02 * self.noise_mult * (1.0 + (hit_range / max_range_m)**1.5)
                    meas_range = max(0.01, hit_range + self.rng.normal(0.0, sigma_r))

                    pt_meas_l = dir_l * meas_range
                    points_lidar_frame.append(pt_meas_l)
                    ranges.append(meas_range)
                    # Simulated laser return intensity based on range
                    intensities.append(1.0 / (1.0 + (meas_range / 5.0)**2))

        points_arr = np.array(points_lidar_frame, dtype=np.float64) if points_lidar_frame else np.empty((0, 3), dtype=np.float64)
        return {
            "points_lidar": points_arr,
            "ranges": np.array(ranges, dtype=np.float64),
            "intensities": np.array(intensities, dtype=np.float64),
            "num_returns": len(points_arr),
            "T_world_lidar": T_world_lidar,
        }

    def sample_depth_camera(
        self,
        rover_pose_xytheta: np.ndarray,
        fov_h_deg: float = 65.0,
        fov_v_deg: float = 45.0,
        grid_w: int = 32,
        grid_h: int = 24,
        max_depth_m: float = 12.0
    ) -> Dict[str, Any]:
        """Simulates stereo depth camera with range-squared disparity uncertainty u(Z) ~ Z^2."""
        x_r, y_r, yaw_r = rover_pose_xytheta[:3]
        z_r = self.terrain.get_elevation_at(x_r, y_r)

        normal, _ = self.terrain.get_surface_normal_and_slope(x_r, y_r)
        pitch_r = -math.atan2(normal[0], normal[2])
        roll_r = math.atan2(normal[1], normal[2])
        T_world_base = make_se3_transform(np.array([x_r, y_r, z_r]), (roll_r, pitch_r, yaw_r))
        T_world_cam = T_world_base @ T_BASE_CAMERA

        p_cam_w = T_world_cam[:3, 3]
        R_world_cam = T_world_cam[:3, :3]

        half_h = math.radians(fov_h_deg) / 2.0
        half_v = math.radians(fov_v_deg) / 2.0
        azimuths = np.linspace(-half_h, half_h, grid_w)
        elevations = np.linspace(-half_v, half_v, grid_h)

        depth_grid = np.zeros((grid_h, grid_w), dtype=np.float64)
        pts_cam_frame = []

        # Stereo baseline B = 0.25m, focal length f_pix = 400
        baseline_m = 0.25
        focal_px = 400.0

        for r_idx, el in enumerate(elevations):
            for c_idx, az in enumerate(azimuths):
                dir_c = np.array([math.sin(az), math.sin(el), math.cos(az) * math.cos(el)], dtype=np.float64)
                dir_c /= np.linalg.norm(dir_c)
                dir_w = R_world_cam @ dir_c

                # Step forward
                hit_depth = max_depth_m
                for step in np.linspace(0.5, max_depth_m, 30):
                    pt_w = p_cam_w + dir_w * step
                    if not (0.0 <= pt_w[0] < self.terrain.size_x and 0.0 <= pt_w[1] < self.terrain.size_y):
                        break
                    if pt_w[2] <= self.terrain.get_elevation_at(pt_w[0], pt_w[1]):
                        hit_depth = step
                        break

                # Range-squared uncertainty model: sigma_z = (sigma_d / (f * B)) * Z^2
                sigma_disp_px = 0.5 * self.noise_mult
                sigma_z = (sigma_disp_px / (focal_px * baseline_m)) * (hit_depth**2)
                meas_depth = max(0.1, hit_depth + self.rng.normal(0.0, sigma_z))

                depth_grid[r_idx, c_idx] = meas_depth
                if meas_depth < max_depth_m:
                    pts_cam_frame.append(dir_c * meas_depth)

        pts_arr = np.array(pts_cam_frame, dtype=np.float64) if pts_cam_frame else np.empty((0, 3), dtype=np.float64)
        return {
            "depth_image": depth_grid,
            "points_camera": pts_arr,
            "T_world_camera": T_world_cam,
        }

    def sample_imu(
        self,
        rover_pose_xytheta: np.ndarray,
        linear_vel_mps: float,
        angular_vel_rps: float,
        dt_s: float = 0.05
    ) -> Dict[str, Any]:
        """Simulates tactical 6-axis IMU (3-axis gyro + 3-axis accel under Martian gravity)."""
        x_r, y_r, yaw_r = rover_pose_xytheta[:3]
        normal, slope_rad = self.terrain.get_surface_normal_and_slope(x_r, y_r)

        # True specific force: gravity vector projected into rover body frame + centripetal
        # Gravity in body frame: g_body = R_wb^T * [0, 0, -g_mars]
        pitch_r = -math.atan2(normal[0], normal[2])
        roll_r = math.atan2(normal[1], normal[2])
        R_wb = euler_to_rot_matrix(roll_r, pitch_r, yaw_r)
        g_world = np.array([0.0, 0.0, -G_MARS])
        true_specific_force = - (R_wb.T @ g_world)  # Accelerometer measures reaction force upward

        # Centripetal acceleration in Y body axis
        a_centripetal = linear_vel_mps * angular_vel_rps
        true_specific_force[1] += a_centripetal

        # True angular velocity: yaw rate + pitch/roll slope rates
        true_gyro = np.array([0.0, 0.0, angular_vel_rps], dtype=np.float64)

        # Evolve Gauss-Markov bias instability
        self.gyro_bias += self.rng.normal(0.0, 1.0e-5 * self.noise_mult * math.sqrt(dt_s), size=3)
        self.accel_bias += self.rng.normal(0.0, 5.0e-4 * self.noise_mult * math.sqrt(dt_s), size=3)

        # Add white measurement noise (VRW / ARW)
        noise_gyro = self.rng.normal(0.0, 5.0e-4 * self.noise_mult, size=3)
        noise_accel = self.rng.normal(0.0, 0.02 * self.noise_mult, size=3)

        meas_gyro = true_gyro + self.gyro_bias + noise_gyro
        meas_accel = true_specific_force + self.accel_bias + noise_accel

        return {
            "meas_gyro_rps": meas_gyro,
            "meas_accel_mps2": meas_accel,
            "true_specific_force": true_specific_force,
            "true_gyro": true_gyro,
            "gyro_bias": self.gyro_bias.copy(),
            "accel_bias": self.accel_bias.copy(),
        }

    def sample_wheel_odometry(
        self,
        true_linear_vel_mps: float,
        true_angular_vel_rps: float,
        slip_ratio: float = 0.05
    ) -> Dict[str, float]:
        """Simulates wheel encoder measurements corrupted by terrain slip and quantization."""
        # Slip effect: commanded wheel velocity spins faster than true ground motion
        # v_meas = v_true / (1 - s)
        s = float(np.clip(slip_ratio, -0.80, 0.80))
        wheel_v = true_linear_vel_mps / max(0.1, (1.0 - s))

        noise_v = self.rng.normal(0.0, 0.01 * self.noise_mult)
        noise_w = self.rng.normal(0.0, 0.005 * self.noise_mult)

        meas_v = float(max(0.0, wheel_v + noise_v))
        meas_w = float(true_angular_vel_rps + noise_w)

        return {
            "meas_linear_mps": meas_v,
            "meas_angular_rps": meas_w,
            "slip_ratio": s,
        }
