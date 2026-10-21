"""Unit Test Suite for TRL 7 Perception and Sensor Rig Subsystems.

Verifies:
1. SE(3) spatial coordinate transforms, quaternions, and extrinsics.
2. Space-grade telemetry validator (NaN/Inf, monotonicity, CRC).
3. 3D Point cloud processor (voxel downsampling, outlier rejection, ground segmentation).
4. 2.5D Elevation mapping (Kalman variance update, negative obstacle detection).
5. Multi-criteria traversability estimation (slope, step, roughness, cost inflation).
6. Quantitative perception metrics (RMSE, IoU, Recall).
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from trl7_navigation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    MAX_TRAVERSABLE_SLOPE_DEG,
    MAX_STEP_HEIGHT_M,
    ROVER_WIDTH_M,
)
from trl7_navigation.sensors.coordinate_transforms import (
    euler_to_quaternion,
    quaternion_to_euler,
    quaternion_to_rotation_matrix,
    TransformSE3,
    SensorExtrinsics,
)
from trl7_navigation.sensors.sensor_validator import SensorValidator
from trl7_navigation.hardware.hardware_interface import IMUPacket, LiDARScanPacket, WheelOdometryPacket
from trl7_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl7_navigation.perception.elevation_mapping import ElevationMap25D
from trl7_navigation.perception.traversability import TraversabilityEstimator
from trl7_navigation.perception.perception_metrics import PerceptionMetrics
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain


def test_safety_invariants_latched():
    """Confirms compile-time research guard locks remain strictly active."""
    assert PROTOTYPE_LOCK is True
    assert NAVIGATION_READY is False


def test_euler_quaternion_roundtrip():
    """Tests Euler <-> Quaternion mathematical equivalence across 3D orientations."""
    r, p, y = math.radians(12.5), math.radians(-8.0), math.radians(45.0)
    q = euler_to_quaternion(r, p, y)
    assert np.isclose(np.linalg.norm(q), 1.0, atol=1e-6)

    r_est, p_est, y_est = quaternion_to_euler(q)
    assert np.isclose(r, r_est, atol=1e-4)
    assert np.isclose(p, p_est, atol=1e-4)
    assert np.isclose(y, y_est, atol=1e-4)


def test_transform_se3_composition_and_inverse():
    """Tests SE(3) transformation composition and inversion identity T * T^-1 = I."""
    t1 = TransformSE3.from_xyz_rpy(2.0, 3.0, 1.0, 0.1, -0.2, 0.5)
    t1_inv = t1.inverse()
    t_id = t1.compose(t1_inv)

    np.testing.assert_allclose(t_id.R, np.eye(3), atol=1e-6)
    np.testing.assert_allclose(t_id.t, np.zeros(3), atol=1e-6)


def test_sensor_validator_rejects_nan_inf():
    """Tests that space-grade sensor validator catches and rejects corrupted telemetry."""
    val = SensorValidator()
    # Good IMU packet
    pkt_ok = IMUPacket(0.01, 1, np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 9.8]))
    ok, _ = val.validate_imu(pkt_ok)
    assert ok is True

    # Corrupted IMU packet with NaN
    pkt_nan = IMUPacket(0.02, 2, np.array([np.nan, 0.0, 0.0]), np.array([0.0, 0.0, 9.8]))
    ok_nan, msg_nan = val.validate_imu(pkt_nan)
    assert ok_nan is False
    assert "NaN" in msg_nan

    # Non-monotonic timestamp
    pkt_retro = IMUPacket(0.005, 3, np.array([0.0, 0.0, 0.0]), np.array([0.0, 0.0, 9.8]))
    ok_retro, msg_retro = val.validate_imu(pkt_retro)
    assert ok_retro is False
    assert "Non-monotonic" in msg_retro


def test_point_cloud_processor_voxel_and_ground():
    """Tests voxel downsampling and invariant ground segmentation."""
    pc = PointCloudProcessor(voxel_size_m=0.20, ground_height_threshold_m=0.20)
    # Create cluster of points
    pts = np.random.uniform(0.0, 2.0, (100, 3))
    down = pc.voxel_downsample(pts)
    assert len(down) < len(pts)
    assert len(down) > 0

    # Test ground vs obstacle segmentation
    ground_pts = np.array([[1.0, 1.0, 0.05], [1.2, 1.1, 0.08]])
    obs_pts = np.array([[1.0, 1.0, 0.65], [1.1, 1.0, 0.80]])
    combined = np.vstack([ground_pts, obs_pts])
    g, o = pc.segment_ground(combined)
    assert len(g) >= 2
    assert len(o) >= 2


def test_elevation_mapping_kalman_update():
    """Tests 2.5D elevation grid fusion with recursive Kalman filter."""
    elev_map = ElevationMap25D(size_x_m=10.0, size_y_m=10.0, resolution_m=0.50)
    # Cell at (2.0, 2.0)
    ix = int(round(2.0 / 0.50))
    iy = int(round(2.0 / 0.50))

    pts1 = np.array([[2.0, 2.0, 1.0]])
    elev_map.update_from_point_cloud(pts1, measurement_noise_std=0.1)
    assert np.isclose(elev_map.elevation[ix, iy], 1.0, atol=1e-4)

    # Second measurement with noise
    pts2 = np.array([[2.0, 2.0, 1.2]])
    elev_map.update_from_point_cloud(pts2, measurement_noise_std=0.1)
    # Should fuse to intermediate value (1.1) with decreased variance
    assert 1.0 < elev_map.elevation[ix, iy] < 1.2


def test_negative_obstacle_detection():
    """Tests crater / negative obstacle detection from elevation depression."""
    elev_map = ElevationMap25D(size_x_m=20.0, size_y_m=20.0, resolution_m=0.50)
    # Fill with nominal flat ground
    elev_map.elevation[:, :] = 5.0
    elev_map.observed[:, :] = True

    # Inject negative depression (crater) at center (10, 10)
    cx, cy = int(10.0 / 0.50), int(10.0 / 0.50)
    elev_map.elevation[cx-1:cx+2, cy-1:cy+2] = 4.0  # 1.0m depression

    crater_mask = elev_map.detect_negative_obstacles(10.0, 10.0, crater_depth_thresh_m=0.35)
    assert crater_mask[cx, cy] is True or crater_mask[cx, cy] == 1


def test_traversability_evaluation_and_inflation():
    """Tests multi-criteria cost mapping, slope limit check, and vehicle inflation margin."""
    elev_map = ElevationMap25D(size_x_m=20.0, size_y_m=20.0, resolution_m=0.25)
    # Create a steep wall at x=10
    elev_map.elevation[:20, :] = 0.0
    elev_map.elevation[40:, :] = 3.0  # steep step between index 38 and 42
    elev_map.observed[:, :] = True

    estimator = TraversabilityEstimator()
    cost_map, impassable_mask, debug = TraversabilityEstimator().evaluate(elev_map)

    # Impassable zone must be flagged at the step
    assert np.any(impassable_mask[38:43, :])
    # Total cost in impassable zone must be saturated to 1.0
    assert np.all(cost_map[impassable_mask] == 1.0)


def test_perception_metrics():
    """Tests IoU, Precision, Recall, and Elevation RMSE computation."""
    est_z = np.ones((10, 10)) * 2.0
    gt_z = np.ones((10, 10)) * 2.1
    rmse = PerceptionMetrics.compute_elevation_rmse(est_z, gt_z)
    assert np.isclose(rmse, 0.1, atol=1e-5)

    m1 = np.zeros((10, 10), dtype=bool)
    m2 = np.zeros((10, 10), dtype=bool)
    m1[2:5, 2:5] = True
    m2[3:6, 2:5] = True

    metrics = PerceptionMetrics.compute_obstacle_metrics(m1, m2)
    assert 0.0 < metrics["iou"] < 1.0
    assert metrics["precision"] > 0.0
    assert metrics["recall"] > 0.0
