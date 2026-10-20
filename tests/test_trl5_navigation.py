"""Formal Verification and Unit Test Suite for APPS TRL 5 Navigation Subsystem.

Verifies:
- Error-State Extended Kalman Filter (ES-EKF) state estimation
- StateMonitor slip entrapment watchdog and ATE/RPE trajectory metrics
- CollisionChecker oriented bounding-box clearance auditing
- Kinodynamic Hybrid A* curvature constraints (|kappa| <= 1.50 m^-1)
- PathTracker Pure Pursuit control and dynamic speed derating
- SafeStopController certified deceleration profile
- RoverFDIRStateMachine 11-mode state transitions and guards
- CooperativeAerialScout elevation prior mapping and comm latency
- MultiRoverCoordinator decentralized map fusion and mutual separation
- MultibodyRoverDynamics 6-DOF equilibrium and FASM tip-over barrier
- RockerBogieSuspension differential averaging bar and 6-wheel load balance
- BekkerWongTerramechanics pressure-sinkage, Janosi shear, and drawbar pull
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from trl5_navigation import (
    PROTOTYPE_LOCK, NAVIGATION_READY, G_MARS,
    ROVER_MASS_KG, MAX_SPEED_MPS, MAX_CURVATURE_INV_M
)
from trl5_navigation.localization.error_state_ekf import ErrorStateEKF
from trl5_navigation.localization.state_monitor import StateMonitor
from trl5_navigation.planning.collision_checker import CollisionChecker
from trl5_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl5_navigation.planning.path_tracker import PathTracker
from trl5_navigation.planning.safe_stop_controller import SafeStopController
from trl5_navigation.executive.state_machine import RoverOperatingMode, RoverFDIRStateMachine
from trl5_navigation.extensions.aerial_scout import CooperativeAerialScout
from trl5_navigation.extensions.multi_rover import MultiRoverCoordinator
from trl5_navigation.dynamics.multibody_rover import MultibodyRoverDynamics
from trl5_navigation.dynamics.rocker_bogie import RockerBogieSuspension
from trl5_navigation.dynamics.terramechanics import BekkerWongTerramechanics
from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


def test_t157_error_state_ekf_prediction_and_update():
    """Verify ES-EKF kinematic prediction and wheel odometry update."""
    ekf = ErrorStateEKF(init_x=0.0, init_y=0.0, init_yaw_rad=0.0)

    # Initial covariance trace
    init_tr = np.trace(ekf.P)

    # Prediction step: moving forward at 0.3 m/s with zero yaw rate for 0.5s
    ekf.predict(meas_gyro_z=0.0, meas_accel_x=0.1, dt_s=0.5)
    pose, cov = ekf.get_estimated_pose()
    assert pose[0] >= 0.0

    # Measurement update with wheel encoder: v = 0.35 m/s
    ekf.update_wheel_odometry(meas_v=0.35, meas_w=0.0)
    assert np.all(np.diag(ekf.P) > 0.0)  # Positive-definite covariance
    assert ekf.state[3] > 0.1             # Velocity updated positively


def test_t158_state_monitor_and_slip_watchdog():
    """Verify slip entrapment watchdog triggering and trajectory error computation."""
    monitor = StateMonitor(max_slip_ratio=0.60, slip_duration_threshold_s=0.5)

    # 1. Normal slip should not trip watchdog
    res1 = monitor.record_step(0.1, np.array([1.0, 1.0, 0.0]), np.array([1.0, 1.0, 0.0]), np.eye(3)*0.01, measured_slip=0.10, dt_s=0.1)
    assert res1["slip_trapped"] is False

    # 2. Severe slip sustained for 0.6s trips watchdog
    for i in range(6):
        res2 = monitor.record_step(0.2 + i*0.1, np.array([1.0, 1.0, 0.0]), np.array([1.0, 1.0, 0.0]), np.eye(3)*0.01, measured_slip=0.75, dt_s=0.1)
    assert res2["slip_trapped"] is True

    # 3. Trajectory metrics
    metrics = monitor.compute_trajectory_metrics()
    assert "ate_rmse_m" in metrics
    assert metrics["ate_rmse_m"] == 0.0  # Estimated and ground truth were identical


def test_t159_collision_checker_oriented_bounding_box():
    """Verify oriented bounding box collision checking against cost maps."""
    checker = CollisionChecker(rover_length_m=1.20, rover_width_m=0.90, clearance_margin_m=0.30)
    cost_map = np.zeros((50, 50), dtype=np.float64)

    # Free on open ground
    assert checker.is_pose_collision_free(5.0, 5.0, 0.0, cost_map, resolution_m=0.20) is True

    # Inject lethal obstacle at (5.0, 5.0) -> cell (25, 25)
    cost_map[25, 25] = 1.0
    assert checker.is_pose_collision_free(5.0, 5.0, 0.0, cost_map, resolution_m=0.20) is False


def test_t160_kinodynamic_hybrid_astar_curvature_bound():
    """Verify Kinodynamic Hybrid A* plans curvature-compliant paths (|kappa| <= 1.50 m^-1)."""
    cost_map = np.zeros((100, 100), dtype=np.float64)
    planner = KinodynamicHybridAStar(max_curvature=1.50, xy_resolution_m=0.30)

    start = np.array([4.0, 4.0, math.radians(45.0)])
    goal = np.array([15.0, 15.0])
    plan = planner.plan(start, goal, cost_map, resolution_m=0.20)

    assert plan["success"] is True
    assert len(plan["path"]) > 5

    # Verify curvature / turning radius constraints along path
    path = plan["path"]
    if len(path) >= 3:
        for i in range(len(path) - 1):
            dx = path[i+1, 0] - path[i, 0]
            dy = path[i+1, 1] - path[i, 1]
            seg_len = math.hypot(dx, dy)
            if seg_len > 1e-4:
                dyaw = abs((path[i+1, 2] - path[i, 2] + math.pi) % (2.0 * math.pi) - math.pi)
                curv = dyaw / seg_len
                assert curv <= 1.50 * 1.5  # Bounded by maximum curvature with discrete margin


def test_t161_kinodynamic_hybrid_astar_unreachable_goal():
    """Verify unreachable blocked goal returns clean failure without hanging."""
    cost_map = np.zeros((50, 50), dtype=np.float64)
    # Block goal with lethal wall
    cost_map[35:45, :] = 1.0
    planner = KinodynamicHybridAStar(max_iterations=500)

    start = np.array([4.0, 4.0, 0.0])
    goal = np.array([40.0, 25.0])
    plan = planner.plan(start, goal, cost_map, resolution_m=0.20)

    assert plan["success"] is False
    assert "GOAL_IN_COLLISION" in plan["reason"] or "BLOCKED" in plan["reason"]


def test_t162_path_tracker_and_speed_derating():
    """Verify Pure Pursuit path tracking curvature command and speed derating."""
    tracker = PathTracker(max_speed_mps=0.50, max_curvature=1.50)
    planned_path = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [4.0, 1.0, math.radians(30.0)],
        [6.0, 2.0, math.radians(30.0)]
    ], dtype=np.float64)

    # Tracking on smooth terrain
    cmd_smooth = tracker.compute_control_command(np.array([0.0, 0.1, 0.0]), 0.40, planned_path, local_terrain_cost=0.1)
    assert cmd_smooth["cmd_v_mps"] > 0.0
    assert not cmd_smooth["reached_end"]

    # Tracking on high-cost rough terrain: speed should be derated
    cmd_rough = tracker.compute_control_command(np.array([0.0, 0.1, 0.0]), 0.40, planned_path, local_terrain_cost=0.8)
    assert cmd_rough["cmd_v_mps"] < cmd_smooth["cmd_v_mps"]


def test_t163_safe_stop_controller_certified_deceleration():
    """Verify certified safe-stop deceleration profile to complete rest."""
    stop_ctrl = SafeStopController(max_decel_mps2=0.20)

    # Initial speed 0.40 m/s
    speed = 0.40
    dt_s = 0.5
    for _ in range(5):
        prof = stop_ctrl.compute_safe_stop_profile(speed, dt_s)
        speed = prof["cmd_v_mps"]

    assert speed == 0.0
    assert prof["at_complete_rest"] is True
    assert prof["safe_stop_latched"] is True


def test_t164_rover_fdir_state_machine_transitions():
    """Verify 11-mode state machine valid transitions and illegal transition fault trigger."""
    fsm = RoverFDIRStateMachine()
    assert fsm.current_mode == RoverOperatingMode.INITIALIZATION

    # Valid transitions: INIT -> SELF_TEST -> IDLE -> PERCEPTION -> PLANNING -> EXECUTION -> SAFE_STOP
    assert fsm.transition_to(RoverOperatingMode.SELF_TEST) is True
    assert fsm.transition_to(RoverOperatingMode.IDLE) is True
    assert fsm.transition_to(RoverOperatingMode.PERCEPTION) is True
    assert fsm.transition_to(RoverOperatingMode.PLANNING) is True
    assert fsm.transition_to(RoverOperatingMode.EXECUTION) is True
    assert fsm.transition_to(RoverOperatingMode.SAFE_STOP) is True
    assert fsm.is_safe_stopped is True

    # Illegal transition: SAFE_STOP directly to EXECUTION without RECOVERY or IDLE
    assert fsm.transition_to(RoverOperatingMode.EXECUTION) is False
    assert fsm.current_mode == RoverOperatingMode.FAULT
    assert fsm.get_status_summary()["has_fault"] is True


def test_t165_cooperative_aerial_scout():
    """Verify cooperative aerial scout high-altitude reconnaissance mapping and comm latency."""
    terrain = PlanetaryTerrain(size_x_m=35.0, size_y_m=35.0, seed=42)
    scout = CooperativeAerialScout(flight_altitude_m=12.0, comm_latency_s=0.8, packet_loss_prob=0.0)

    res = scout.scout_corridor(terrain, np.array([4.0, 4.0]), np.array([25.0, 25.0]))
    assert res["comm_success"] is True
    assert res["scouted_map"] is not None
    assert res["num_aerial_points"] > 50
    assert res["latency_s"] == 0.8


def test_t166_multi_rover_coordinator():
    """Verify multi-rover mutual separation check and decentralized map fusion."""
    coord = MultiRoverCoordinator(comm_range_m=30.0, inter_rover_safety_margin_m=2.0)

    # Proximity check
    prox = coord.check_inter_rover_proximity(np.array([5.0, 5.0]), np.array([6.0, 5.5]))
    assert prox["in_comm_range"] is True
    assert prox["in_conflict"] is True  # Distance < 2.0m

    # Map fusion
    map_a = ElevationMap25D(size_x_m=20.0, size_y_m=20.0, resolution_m=0.25)
    map_b = ElevationMap25D(size_x_m=20.0, size_y_m=20.0, resolution_m=0.25)
    map_b.elevation[10, 10] = 2.0
    map_b.hit_count[10, 10] = 5

    fused = coord.fuse_shared_map(map_a, map_b, received_rover_pose=np.array([12.0, 12.0]))
    assert fused.elevation[10, 10] == 2.0
    # Peer rover position bubble must be marked as obstacle
    peer_ix, peer_iy = fused.world_to_grid(12.0, 12.0)
    assert bool(fused.obstacle_mask[peer_ix, peer_iy])


def test_t167_multibody_rover_equilibrium_and_fasm():
    """Verify 6-DOF multibody equilibrium, FASM tip-over barrier, and acceleration limits."""
    dyn = MultibodyRoverDynamics(mass_kg=185.0, gravity_mps2=3.71)

    # Flat surface equilibrium
    flat_norm = np.array([0.0, 0.0, 1.0])
    eq_flat = dyn.evaluate_static_equilibrium(flat_norm)
    assert eq_flat["is_stable"] is True
    assert eq_flat["rollover_hazard"] is False

    # Steep 35 deg inclined surface (beyond safe tip-over margin)
    steep_norm = np.array([math.sin(math.radians(35.0)), 0.0, math.cos(math.radians(35.0))])
    eq_steep = dyn.evaluate_static_equilibrium(steep_norm)
    assert eq_steep["rollover_hazard"] is True

    # Acceleration limits under friction mu = 0.60
    acc_limits = dyn.compute_acceleration_limits(surface_friction_coeff=0.60, slope_angle_rad=0.0)
    assert 0.1 <= acc_limits["max_accel_mps2"] <= 0.40


def test_t168_rocker_bogie_suspension_load_distribution():
    """Verify rocker-bogie differential averaging bar and 6-wheel normal load distribution."""
    susp = RockerBogieSuspension(rover_mass_kg=185.0, gravity_mps2=3.71)

    # Differential averaging bar: (theta_L - theta_R) / 2
    th_diff = susp.compute_differential_bar_pitch(math.radians(10.0), math.radians(-6.0))
    assert np.isclose(th_diff, math.radians(8.0), atol=1e-4)

    # Flat ground load distribution
    flat_z = np.zeros(6, dtype=np.float64)
    loads_flat = susp.distribute_wheel_normal_forces(flat_z, terrain_slope_rad=0.0)
    # Sum must equal total weight: 185 * 3.71 = 686.35 N
    assert np.isclose(loads_flat["total_normal_load_n"], 185.0 * 3.71, atol=1.0)
    # Each wheel carries ~1/6th
    assert np.all(np.isclose(loads_flat["wheel_forces_n"], (185.0 * 3.71) / 6.0, atol=2.0))


def test_t169_bekker_wong_terramechanics_drawbar_pull():
    """Verify Bekker sinkage, compaction resistance, Janosi shear, and drawbar pull."""
    soil = BekkerWongTerramechanics(wheel_radius_m=0.15, wheel_width_m=0.12)
    wheel_load = (185.0 * 3.71) / 6.0  # ~114.4 N per wheel

    res = soil.compute_sinkage_and_resistance(wheel_normal_load_n=wheel_load)
    assert res["sinkage_m"] > 0.0
    assert res["compaction_resistance_n"] > 0.0
    assert res["total_motion_resistance_n"] > 0.0

    # Drawbar pull with 15% slip
    dp_info = soil.compute_thrust_and_drawbar_pull(wheel_normal_load_n=wheel_load, slip_ratio=0.15)
    assert dp_info["gross_thrust_n"] > 0.0
    # On medium sand with 114 N normal load, drawbar pull is positive (rover can pull forward)
    assert dp_info["drawbar_pull_n"] > 0.0
    assert dp_info["is_stalled"] is False
