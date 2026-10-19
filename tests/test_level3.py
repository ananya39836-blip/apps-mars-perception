"""Automated Unit and Integration Test Suite for APPS Level 3.
Chapters 220 to 269 & Appendix CT (Part 17).

Tests:
1. 6-DOF Multibody Dynamics & FASM Stability
2. Rocker-Bogie Passive Suspension Kinematics
3. Bekker-Wong Terramechanics & Drawbar Pull
4. Slip-Sinkage Watchdog & Entrapment Safing
5. Tactical IMU Bias Drift & Allan Variance
6. 3D Flash LiDAR Point Cloud Scanning
7. Atmospheric Dust Extinction & Solar Glare
8. Negative Obstacle Sentinel (Drop-off Detection)
9. Factor Graph State Estimation & Covariance
10. 3D Voxel Grid & Continuous ESDF Distance Field
11. Kinodynamic State-Lattice Planner & Clearance
12. Certified Safe Stopping Profile (ICS Avoidance)
13. Level 3 Label Evaluator (KEYS_L3)
"""
import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level3.physics.multibody_6dof import RigidBody6DOF
from level3.physics.rocker_bogie import RockerBogieSuspension
from level3.physics.terramechanics import TerramechanicsModel, REGOLITH_PRESETS
from level3.monitors.slip_watchdog import SlipEntrapmentWatchdog
from level3.sensing.multimodal_sensor import TacticalIMU, FlashLiDAR3D
from level3.sensing.degradations import (
    apply_atmospheric_dust_extinction, apply_solar_glare_blooming, NegativeObstacleSentinel
)
from level3.estimation.factor_graph import FactorGraphEstimator
from level3.mapping.octomap_3d import VoxelMap3D
from level3.planning.state_lattice_3d import StateLatticePlanner3D
from level3.planning.nmpc_trajectory import SafeStoppingTrajectoryGenerator
from level3.evaluation.label_script_l3 import level3_label, KEYS_L3


# ---------------- 1. 6-DOF Multibody Dynamics ----------------
def test_t30_multibody_6dof_dynamics():
    rb = RigidBody6DOF(mass_kg=185.0)
    rb.set_pose(0.0, 0.0, 0.50, 0.0, 0.0, 0.0)

    # Apply 100N forward force
    f_ext = np.array([100.0, 0.0, 185.0 * 3.71]) # counter-grav + forward
    m_ext = np.zeros(3)
    res = rb.step(f_ext, m_ext, dt=0.05)

    assert res["status"] == "ok"
    assert res["linear_velocity"][0] > 0.0 # moving forward
    assert res["fasm"] > 10.0 # stable
    assert not res["is_tipover"]


# ---------------- 2. Rocker-Bogie Suspension Kinematics ----------------
def test_t31_rocker_bogie_suspension():
    susp = RockerBogieSuspension(wheelbase_m=1.20, track_width_m=0.90)
    # Front wheels elevated over 0.15m obstacle
    wheel_z = {
        "FL": 0.15, "FR": 0.15,
        "ML": 0.00, "MR": 0.00,
        "RL": 0.00, "RR": 0.00
    }
    eq = susp.resolve_suspension_equilibrium(wheel_z)

    # Differential bar pitch averaging
    assert eq["chassis_pitch_rad"] > 0.0 # pitched upward
    assert math.isclose(eq["chassis_roll_rad"], 0.0, abs_tol=1e-3) # symmetrical
    # All 6 wheels maintain positive normal contact force
    for w_name, load in eq["wheel_normal_loads_N"].items():
        assert load > 15.0


# ---------------- 3. Bekker-Wong Terramechanics & Drawbar Pull ----------------
def test_t32_terramechanics_soil_model():
    tm = TerramechanicsModel(wheel_radius_m=0.15, wheel_width_m=0.12)
    soil = REGOLITH_PRESETS["drift_sand"]

    res = tm.evaluate_wheel_soil(
        normal_load_N=114.4, forward_speed_m_s=0.10,
        wheel_spin_rad_s=1.0, soil=soil
    )
    # Slip should be positive: r*w = 0.15 m/s > 0.10 m/s -> s ~ 0.33
    assert res["slip_ratio"] > 0.20
    assert res["sinkage_m"] > 0.005
    assert res["compaction_resistance_N"] > 0.0
    assert res["drawbar_pull_N"] > 0.0 # positive pull under moderate slip


# ---------------- 4. Slip-Sinkage Watchdog ----------------
def test_t33_slip_watchdog():
    watchdog = SlipEntrapmentWatchdog(sustained_steps_limit=3)

    # Normal step
    trig_norm = watchdog.update({"FL": 0.10, "FR": 0.10}, {"FL": 0.02}, net_dp_N=50.0)
    assert trig_norm is None

    # High slip entrapment
    for _ in range(2):
        watchdog.update({"FL": 0.85, "FR": 0.85}, {"FL": 0.09}, net_dp_N=-10.0)
    trig_stop = watchdog.update({"FL": 0.85, "FR": 0.85}, {"FL": 0.09}, net_dp_N=-10.0)
    assert trig_stop == "emergency_safe_stop"


# ---------------- 5. Tactical IMU Stochastic Errors ----------------
def test_t34_tactical_imu_and_bias():
    imu = TacticalIMU(rate_hz=200.0)
    rng = np.random.default_rng(1234)

    true_acc = np.array([0.0, 0.0, 3.71])
    true_w = np.array([0.0, 0.0, 0.10])

    obs = imu.update(true_acc, true_w, rng=rng)
    assert "gyro_meas_rad_s" in obs
    assert "accel_meas_m_s2" in obs
    assert math.isclose(obs["gyro_meas_rad_s"][2], 0.10, abs_tol=0.05)


# ---------------- 6. 3D Flash LiDAR Point Cloud ----------------
def test_t35_flash_lidar_point_cloud():
    lidar = FlashLiDAR3D(channels_h=16, channels_v=8, max_range_m=10.0)
    # Flat DEM
    terrain = np.zeros((32, 32), dtype=np.float32)
    pts = lidar.scan_dem(terrain, cell_size_m=0.25, sensor_pose=(2.0, 2.0, 0.8, 0.0))

    assert pts.shape[0] > 10
    assert pts.shape[1] == 4 # X, Y, Z, Intensity


# ---------------- 7. Atmospheric Dust Extinction & Glare ----------------
def test_t36_environmental_degradations():
    clean_img = np.ones((64, 64, 3), dtype=np.float32) * 0.80

    # Dust storm: contrast drops
    dusty_img = apply_atmospheric_dust_extinction(clean_img, optical_depth_tau=1.5)
    assert np.all(dusty_img >= 0.0) and np.all(dusty_img <= 1.0)
    assert not np.allclose(clean_img, dusty_img)

    # Solar glare
    glare_img = apply_solar_glare_blooming(clean_img, sun_in_fov=True, sun_pixel=(32, 32))
    assert glare_img[32, 32, 0] > clean_img[32, 32, 0]


# ---------------- 8. Negative Obstacle Sentinel ----------------
def test_t37_negative_obstacle_sentinel():
    sentinel = NegativeObstacleSentinel(drop_threshold_m=0.25, cell_size_m=0.25)
    # Flat terrain with a 0.50m trench at x=4m
    dem = np.zeros((32, 32), dtype=np.float32)
    dem[:, 16:] = -0.50 # drop cliff

    audit = sentinel.audit_radial_profiles(dem, rover_x_m=2.0, rover_y_m=4.0, rover_yaw_rad=0.0)
    assert audit["negative_obstacles_found"] > 0
    assert np.any(audit["hazard_mask"])


# ---------------- 9. Factor Graph State Estimation ----------------
def test_t38_factor_graph_estimator():
    fge = FactorGraphEstimator(init_pose=(0.0, 0.0, 0.0))

    # Add IMU propagation
    fge.add_imu_factor(accel_meas=np.array([0.2, 0.0, 3.71]), gyro_meas=np.array([0.0, 0.0, 0.02]), dt=0.10)
    # Add Visual Odometry correction
    fge.add_visual_odometry_factor(delta_pose_se3=(0.02, 0.0, 0.0, 0.002), confidence=0.95)

    opt = fge.get_optimized_state()
    assert opt["status"] == "ok"
    assert opt["position"][0] > 0.0
    assert opt["pos_cov_trace"] < 1.0


# ---------------- 10. 3D Voxel Grid & Continuous ESDF ----------------
def test_t39_voxel_map_and_esdf():
    vmap = VoxelMap3D(size_x_m=8.0, size_y_m=8.0, size_z_m=2.0, resolution_m=0.25)

    # Insert point cloud at (4.0, 4.0, 0.5)
    pts = np.array([[4.0, 4.0, 0.5, 1.0]], dtype=np.float32)
    vmap.insert_point_cloud(pts, sensor_origin=(0.0, 0.0, 0.8))

    slice_2d = vmap.compute_esdf_2d_slice(height_m=0.50)
    assert "esdf_distance_m" in slice_2d
    assert slice_2d["obstacle_mask"][16, 16] # center voxel occupied
    assert slice_2d["esdf_distance_m"][0, 0] > 0.0 # distance away from obstacle is positive


# ---------------- 11. 3D Kinodynamic State-Lattice Planner ----------------
def test_t40_state_lattice_3d_planner():
    planner = StateLatticePlanner3D(k_max=1.0, prim_length_m=1.5, n_primitives=5, cell_size_m=0.25)

    # Empty ESDF field (all cells have 5.0m clearance)
    esdf = np.full((32, 32), 5.0, dtype=np.float32)
    unc = np.full((32, 32), 0.10, dtype=np.float32)

    plan = planner.plan(
        rover_pose=(2.0, 4.0, 0.0),
        goal_pos=(7.0, 4.0),
        esdf_dist_m=esdf,
        uncertainty_map=unc
    )
    assert plan["status"] == "ok"
    assert plan["clearance_ok"]
    assert math.isclose(plan["k_cmd"], 0.0, abs_tol=0.3)


# ---------------- 12. Certified Safe Stopping Trajectory ----------------
def test_t41_safe_stopping_profile():
    gen = SafeStoppingTrajectoryGenerator(max_decel_m_s2=0.25, r_chassis_m=0.50)
    esdf = np.full((32, 32), 3.0, dtype=np.float32)

    stop_prof = gen.generate_safe_stop_profile(
        current_v=0.30, current_pose=(2.0, 4.0, 0.0),
        curvature=0.0, esdf_dist_m=esdf, cell_size_m=0.25
    )
    assert stop_prof["ics_free"]
    assert stop_prof["stopping_dist_m"] > 0.10
    assert stop_prof["stopping_time_s"] > 0.50


# ---------------- 13. Level 3 Label Evaluator ----------------
def test_t42_level3_label_evaluator():
    ev_all_pass = {k: dict(exists=True, executed=True, passed=True) for k in KEYS_L3}
    assert level3_label(ev_all_pass) == "L3-met (internal)"

    # One key missing
    ev_missing = dict(ev_all_pass)
    ev_missing.pop("terramechanics_model")
    assert level3_label(ev_missing) == "L3-not-met"

    # One key unexecuted
    ev_unexec = dict(ev_all_pass)
    ev_unexec["multibody_dynamics"] = dict(exists=True, executed=False, passed=True)
    assert level3_label(ev_unexec) == "L3-partial"

    # One key failed
    ev_fail = dict(ev_all_pass)
    ev_fail["slip_watchdog"] = dict(exists=True, executed=True, passed=False)
    assert level3_label(ev_fail) == "L3-not-met"
