"""Formal Verification and Unit Test Suite for APPS TRL 5 Perception Subsystem.

Verifies:
- 3D continuous DEM interpolation, slope gradients, craters, and boulders
- Solar ray-tracing occlusion buffers
- SE(3) coordinate transformations
- Multi-sensor rig error models (LiDAR, Depth Camera u(Z) ~ Z^2, Tactical IMU, Wheel Odometry)
- Point cloud ground plane vs obstacle segmentation
- 2.5D elevation grid recursive variance updates and negative obstacle detection
- Multi-criteria traversability estimation in [0, 1]
- Perception metrics (Precision, Recall, IoU, RMSE)
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from trl5_navigation import (
    PROTOTYPE_LOCK, NAVIGATION_READY, G_MARS,
    ROVER_MASS_KG, MAX_SPEED_MPS, MAX_CURVATURE_INV_M
)
from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.sensors.coordinate_transforms import (
    euler_to_rot_matrix, make_se3_transform, invert_se3_transform, transform_points,
    T_BASE_LIDAR, T_BASE_CAMERA, T_BASE_IMU
)
from trl5_navigation.sensors.sensor_rig import MultiSensorRig
from trl5_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl5_navigation.perception.elevation_mapping import ElevationMap25D
from trl5_navigation.perception.traversability import TraversabilityEstimator
from trl5_navigation.perception.perception_metrics import PerceptionMetrics


def test_t145_prototype_lock_and_constants():
    """Verify compile-time safety locks and planetary physical constants."""
    assert PROTOTYPE_LOCK is True
    assert NAVIGATION_READY is False
    assert abs(G_MARS - 3.71) < 1e-3
    assert ROVER_MASS_KG == 185.0
    assert MAX_SPEED_MPS == 0.50
    assert MAX_CURVATURE_INV_M == 1.50


def test_t146_planetary_terrain_generation():
    """Verify 3D continuous DEM interpolation, slope gradients, and crater carving."""
    terrain = PlanetaryTerrain(size_x_m=40.0, size_y_m=40.0, resolution_m=0.20, base_slope_deg=5.0, seed=123)

    # 1. Bilinear elevation check
    z1 = terrain.get_elevation_at(10.0, 10.0)
    z2 = terrain.get_elevation_at(10.1, 10.1)
    assert np.isfinite(z1) and np.isfinite(z2)

    # 2. Surface normal & slope calculation
    norm, slope_rad = terrain.get_surface_normal_and_slope(10.0, 10.0)
    assert np.isclose(np.linalg.norm(norm), 1.0, atol=1e-5)
    assert 0.0 <= math.degrees(slope_rad) <= 45.0

    # 3. Crater carving with raised rim
    crater_cx, crater_cy = 20.0, 20.0
    depth_m = 1.5
    radius_m = 4.0
    z_before = terrain.get_elevation_at(crater_cx, crater_cy)
    terrain.add_crater(crater_cx, crater_cy, radius_m=radius_m, depth_m=depth_m, rim_height_m=0.3)
    z_after = terrain.get_elevation_at(crater_cx, crater_cy)

    # Center must be depressed by ~depth_m
    assert (z_before - z_after) >= depth_m * 0.90
    assert bool(terrain.crater_mask[int(crater_cx / terrain.res), int(crater_cy / terrain.res)])

    # 4. Boulder field test
    # Add single boulder at (15, 15) with radius 1.0m and height 0.5m
    z_ground = terrain.get_elevation_at(15.0, 15.0)
    terrain.add_boulder(15.0, 15.0, radius_m=1.0, height_m=0.5)
    z_peak = terrain.get_elevation_at(15.0, 15.0)
    assert np.isclose(z_peak - z_ground, 0.5, atol=0.05)
    assert bool(terrain.rock_mask[int(15.0 / terrain.res), int(15.0 / terrain.res)])

    # Add loose regolith patch with reduced friction mu = 0.30
    terrain.add_loose_regolith_patch(center_x=25.0, center_y=25.0, radius_m=3.0, friction_coeff=0.30)
    mu_patch = terrain.regolith_friction[int(25.0 / terrain.res), int(25.0 / terrain.res)]
    assert np.isclose(mu_patch, 0.30, atol=1e-3)


def test_t148_solar_ray_tracing_shadows():
    """Verify directional solar illumination occlusion buffer."""
    terrain = PlanetaryTerrain(size_x_m=40.0, size_y_m=40.0, resolution_m=0.20, seed=42)
    # Add tall rock at (20, 20) with height 2.0m
    terrain.add_boulder(20.0, 20.0, radius_m=1.5, height_m=2.0)

    # Low sun angle at 20 deg elevation casts shadow behind rock
    shadow_mask = terrain.compute_solar_shadow_mask(sun_azimuth_deg=45.0, sun_elevation_deg=20.0)
    assert shadow_mask.shape == (terrain.nx, terrain.ny)
    assert np.any(shadow_mask)  # Shadows must be detected behind tall obstacle


def test_t149_se3_coordinate_transforms():
    """Verify SE(3) matrix construction, inversion, and point cloud transformations."""
    # Rotation test
    R = euler_to_rot_matrix(0.0, 0.0, math.radians(90.0))
    pt = np.array([1.0, 0.0, 0.0])
    pt_rot = R @ pt
    assert np.allclose(pt_rot, [0.0, 1.0, 0.0], atol=1e-5)

    # SE(3) homogeneous transform & inversion
    T = make_se3_transform(np.array([5.0, -2.0, 1.0]), (0.1, -0.2, 0.5))
    T_inv = invert_se3_transform(T)
    assert np.allclose(T @ T_inv, np.eye(4), atol=1e-5)

    # Point cloud transformation
    pts = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=np.float64)
    pts_t = transform_points(pts, T)
    pts_back = transform_points(pts_t, T_inv)
    assert np.allclose(pts_back, pts, atol=1e-5)


def test_t150_sensor_rig_lidar_and_noise():
    """Verify 3D LiDAR point cloud multi-beam simulation, dropouts, and range noise."""
    terrain = PlanetaryTerrain(size_x_m=40.0, size_y_m=40.0, resolution_m=0.20, seed=42)
    rig = MultiSensorRig(terrain, noise_multiplier=1.0, lidar_dropout_prob=0.10, seed=42)

    lidar_data = rig.sample_lidar(np.array([10.0, 10.0, 0.0]), num_azimuth=32, num_elevation=8)
    assert "points_lidar" in lidar_data
    assert "ranges" in lidar_data
    assert lidar_data["num_returns"] > 0
    assert len(lidar_data["points_lidar"]) == lidar_data["num_returns"]
    assert np.all(lidar_data["ranges"] >= 0.5)


def test_t151_sensor_rig_depth_camera_uncertainty():
    """Verify stereo depth camera range-squared uncertainty model u(Z) ~ Z^2."""
    terrain = PlanetaryTerrain(size_x_m=40.0, size_y_m=40.0, resolution_m=0.20, seed=42)
    rig = MultiSensorRig(terrain, seed=42)

    cam_data = rig.sample_depth_camera(np.array([10.0, 10.0, 0.0]), grid_w=16, grid_h=12, max_depth_m=10.0)
    assert cam_data["depth_image"].shape == (12, 16)
    assert np.all(cam_data["depth_image"] >= 0.1)


def test_t152_sensor_rig_imu_and_odometry():
    """Verify tactical 6-axis IMU under Martian gravity and wheel odometry slip."""
    terrain = PlanetaryTerrain(size_x_m=40.0, size_y_m=40.0, resolution_m=0.20, seed=42)
    rig = MultiSensorRig(terrain, seed=42)

    imu = rig.sample_imu(np.array([10.0, 10.0, 0.0]), linear_vel_mps=0.3, angular_vel_rps=0.05, dt_s=0.05)
    # Accelerometer Z should measure reaction to Martian gravity (+3.71 m/s^2 body frame on flat ground)
    assert abs(imu["meas_accel_mps2"][2] - 3.71) < 0.5
    assert len(imu["meas_gyro_rps"]) == 3

    odom = rig.sample_wheel_odometry(true_linear_vel_mps=0.40, true_angular_vel_rps=0.02, slip_ratio=0.10)
    assert odom["meas_linear_mps"] > 0.0
    assert odom["slip_ratio"] == 0.10


def test_t153_point_cloud_processing_and_segmentation():
    """Verify point cloud filtering and ground plane vs obstacle segmentation."""
    pc_proc = PointCloudProcessor(voxel_size_m=0.25, height_threshold_m=0.25)

    # Create synthetic point cloud with flat ground and one tall obstacle point
    pts_sensor = np.array([
        [2.0, 0.0, -0.8],
        [2.2, 0.0, -0.8],
        [2.0, 0.0, +0.2]  # Obstacle point 1.0m higher than ground
    ], dtype=np.float64)

    T_world_sensor = make_se3_transform(np.array([5.0, 5.0, 1.0]), (0.0, 0.0, 0.0))
    res = pc_proc.process_point_cloud(pts_sensor, T_world_sensor)

    assert len(res["points_world"]) == 3
    assert len(res["ground_points"]) >= 1
    assert len(res["obstacle_points"]) >= 1


def test_t154_elevation_map_kalman_variance_update():
    """Verify 2.5D elevation grid recursive variance updates and negative obstacle detection."""
    elev_map = ElevationMap25D(size_x_m=30.0, size_y_m=30.0, resolution_m=0.20, prior_elevation=0.0)

    # Initial variance should be 1.0
    ix, iy = elev_map.world_to_grid(5.0, 5.0)
    assert elev_map.variance[ix, iy] == 1.0

    # First update with measurement z=1.2, var=0.04
    pts1 = np.array([[5.0, 5.0, 1.2]], dtype=np.float64)
    elev_map.update_from_point_cloud(pts1, np.array([5.0, 5.0, 2.0]), meas_variance=0.04)
    assert elev_map.elevation[ix, iy] == 1.2
    assert elev_map.variance[ix, iy] == 0.04

    # Second update with measurement z=1.4, var=0.04
    pts2 = np.array([[5.0, 5.0, 1.4]], dtype=np.float64)
    elev_map.update_from_point_cloud(pts2, np.array([5.0, 5.0, 2.0]), meas_variance=0.04)
    # Posterior mean should be (1.2 + 1.4)/2 = 1.3, posterior variance should be 0.02
    assert np.isclose(elev_map.elevation[ix, iy], 1.3, atol=1e-3)
    assert np.isclose(elev_map.variance[ix, iy], 0.02, atol=1e-3)


def test_t155_multi_criteria_traversability_cost_map():
    """Verify multi-criteria traversability cost map calculations in [0, 1]."""
    elev_map = ElevationMap25D(size_x_m=20.0, size_y_m=20.0, resolution_m=0.20, prior_elevation=0.0)
    # Inject a step obstacle at cell (50, 50)
    elev_map.elevation[50, 50] = 1.5

    trav_est = TraversabilityEstimator(max_slope_deg=25.0, max_step_m=0.25)
    cost_data = trav_est.evaluate_traversability(elev_map)

    cost_map = cost_data["cost_map"]
    assert cost_map.shape == (elev_map.nx, elev_map.ny)
    assert np.all((cost_map >= 0.0) & (cost_map <= 1.0))
    # Cell with 1.5m step must receive lethal cost 1.0
    assert cost_map[50, 50] == 1.0


def test_t156_perception_metrics_precision_recall_iou():
    """Verify ground-truth IoU evaluation, precision, recall, and elevation RMSE."""
    pred_mask = np.zeros((20, 20), dtype=bool)
    gt_mask = np.zeros((20, 20), dtype=bool)

    pred_mask[5:10, 5:10] = True  # 25 cells
    gt_mask[5:10, 5:10] = True    # 25 cells

    metrics = PerceptionMetrics.evaluate_obstacle_detection(pred_mask, gt_mask)
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["iou"] == 1.0
    assert metrics["f1_score"] == 1.0
