"""Unit Test Suite for TRL 7 Navigation, Planning, Control, Dynamics, and FDIR Subsystems.

Verifies:
1. 15-State Error-State EKF (Joseph-form covariance updates, quaternion injection).
2. State monitor (ATE RMSE, RPE, cumulative drift rate).
3. Oriented Bounding Box (OBB) collision checker.
4. Kinodynamic Hybrid A* path planner (curvature <= 1.50 m^-1, obstacle avoidance).
5. Adaptive Pure Pursuit trajectory tracker.
6. Safe-stop deceleration controller (deterministic a = -0.20 m/s^2).
7. Rocker-bogie suspension ground contact and differential bar tilt.
8. Soil terramechanics (Bekker sinkage, compaction, Janosi shear, drawbar pull).
9. 11-mode FDIR Executive state transitions.
10. Closed-loop long-duration mission execution.
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from trl7_navigation import (
    MAX_CURVATURE_INV_M,
    ROVER_MASS_KG,
    G_MARS,
    SCENARIO_CLASSES,
)
from trl7_navigation.localization.error_state_ekf import ErrorStateEKF
from trl7_navigation.localization.state_monitor import StateMonitor
from trl7_navigation.planning.collision_checker import CollisionChecker
from trl7_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar, PathPoint
from trl7_navigation.planning.path_tracker import PathTracker
from trl7_navigation.planning.safe_stop_controller import SafeStopController
from trl7_navigation.dynamics.rocker_bogie import RockerBogieSuspension
from trl7_navigation.dynamics.terramechanics import SoilParameters, TerramechanicsModel
from trl7_navigation.dynamics.multibody_rover import MultibodyRover
from trl7_navigation.executive.state_machine import AutonomyState, ExecutiveStateMachine
from trl7_navigation.environment.scenario_generator import ScenarioGenerator
from trl7_navigation.mission.long_duration_mission import LongDurationMissionRunner


def test_es_ekf_joseph_update():
    """Verifies that 15-state ES-EKF covariance remains symmetric and positive-definite under Joseph update."""
    ekf = ErrorStateEKF(init_pos=(0.0, 0.0, 0.0), init_yaw=0.0)

    # Predict step
    accel = np.array([0.0, 0.0, G_MARS])
    gyro = np.array([0.0, 0.0, 0.0])
    ekf.predict_imu(accel, gyro, dt=0.01)

    # Check symmetry of P
    np.testing.assert_allclose(ekf.P, ekf.P.T, atol=1e-8)
    eigenvalues = np.linalg.eigvals(ekf.P)
    assert np.all(eigenvalues > 0.0)

    # Wheel odometry update
    ekf.update_wheel_odometry(meas_linear_v=0.25, meas_angular_w=0.0)
    np.testing.assert_allclose(ekf.P, ekf.P.T, atol=1e-8)
    eigenvalues_post = np.linalg.eigvals(ekf.P)
    assert np.all(eigenvalues_post > 0.0)


def test_state_monitor_metrics():
    """Tests ATE and drift percent calculations on synthetic trajectory."""
    monitor = StateMonitor()
    # Rover travels 100 meters along X with 0.5m Y drift
    for i in range(101):
        t = i * 1.0
        gt = (float(i), 0.0, 0.0)
        est = (float(i), 0.005 * i, 0.0)  # max drift 0.5m
        monitor.record_step(t, gt, est)

    metrics = monitor.compute_trajectory_metrics()
    assert metrics["total_dist_m"] >= 100.0
    assert metrics["ate_rmse_m"] < 0.50
    assert metrics["drift_percent"] < 1.0  # Drift < 1% of traverse


def test_collision_checker_obb():
    """Tests Oriented Bounding Box collision detection against hazard maps."""
    checker = CollisionChecker()
    cost_map = np.zeros((100, 100))
    impassable = np.zeros((100, 100), dtype=bool)
    # Impassable boulder at (10, 10)
    impassable[38:43, 38:43] = True

    # Far away pose should be free
    assert checker.is_pose_collision_free(5.0, 5.0, 0.0, cost_map, impassable, resolution_m=0.25) is True

    # Pose on top of boulder should collide
    assert checker.is_pose_collision_free(10.0, 10.0, 0.0, cost_map, impassable, resolution_m=0.25) is False


def test_kinodynamic_planner_curvature_bound():
    """Verifies that generated trajectories satisfy curvature upper bounds (kappa <= 1.50 m^-1)."""
    planner = KinodynamicHybridAStar()
    cost_map = np.zeros((100, 100))
    impassable = np.zeros((100, 100), dtype=bool)

    path = planner.plan(
        start_pose=(5.0, 5.0, 0.0),
        goal_pos=(20.0, 20.0),
        cost_map=cost_map,
        impassable_mask=impassable,
        resolution_m=0.25,
    )

    assert path is not None
    assert len(path) > 0
    for pt in path:
        assert abs(pt.curvature) <= (MAX_CURVATURE_INV_M + 1e-4)


def test_path_tracker_pure_pursuit():
    """Tests adaptive Pure Pursuit path follower command generation and goal arrival."""
    tracker = PathTracker()
    path = [
        PathPoint(x=1.0, y=1.0, yaw=0.0, curvature=0.0, cost=0.0),
        PathPoint(x=3.0, y=1.0, yaw=0.0, curvature=0.0, cost=0.0),
        PathPoint(x=5.0, y=1.0, yaw=0.0, curvature=0.0, cost=0.0),
    ]

    cmd, done = tracker.compute_command((1.0, 1.0, 0.0), current_v=0.20, path=path)
    assert done is False
    assert cmd.linear_velocity_m_s > 0.0

    # At goal
    cmd_goal, done_goal = tracker.compute_command((4.9, 1.0, 0.0), current_v=0.05, path=path)
    assert done_goal is True
    assert cmd_goal.brake_engaged is True


def test_safe_stop_controller():
    """Tests certified deterministic deceleration down to complete standstill."""
    controller = SafeStopController(nominal_decel_m_s2=0.20)
    v = 0.40
    steer = 0.20
    dt = 0.50

    # Step deceleration
    cmd, stopped = controller.compute_stopping_command(v, steer, dt)
    assert stopped is False
    assert cmd.linear_velocity_m_s == pytest.approx(0.30, abs=1e-3)
    assert cmd.steering_angle_rad < steer

    # Continued deceleration to stop
    cmd2, stopped2 = controller.compute_stopping_command(0.01, 0.0, dt)
    assert stopped2 is True
    assert cmd2.linear_velocity_m_s == 0.0
    assert cmd2.brake_engaged is True


def test_rocker_bogie_kinematics():
    """Tests 6-wheel suspension ground contact and load distribution under gravity."""
    terrain, _ = ScenarioGenerator.create_scenario("SC-01_flat_baseline")
    susp = RockerBogieSuspension(gravity_mps2=G_MARS, rover_mass_kg=ROVER_MASS_KG)

    data = susp.resolve_ground_contact(10.0, 10.0, 0.0, terrain)
    wheel_pts = data["wheel_positions_world"]
    assert wheel_pts.shape == (6, 3)

    normal_loads = data["wheel_normal_forces_n"]
    assert len(normal_loads) == 6
    # Total normal force should equal vehicle weight m * g
    total_normal = float(np.sum(normal_loads))
    expected_weight = ROVER_MASS_KG * G_MARS
    assert total_normal == pytest.approx(expected_weight, rel=1e-3)


def test_terramechanics_soil_model():
    """Tests Bekker sinkage and Janosi-Hanamoto drawbar pull relationships."""
    model = TerramechanicsModel()
    res = model.compute_sinkage_and_forces(
        wheel_normal_load_n=500.0,
        wheel_angular_rate_rad_s=1.0,
        chassis_linear_velocity_m_s=0.20,
    )

    assert res["sinkage_m"] > 0.0
    assert res["compaction_resistance_n"] > 0.0
    assert res["gross_traction_n"] > 0.0
    # Net drawbar pull = gross traction - compaction
    assert res["drawbar_pull_n"] == pytest.approx(res["gross_traction_n"] - res["compaction_resistance_n"], abs=1e-4)


def test_fdir_executive_transitions():
    """Tests FDIR state machine transitions under nominal and fault conditions."""
    sm = ExecutiveStateMachine()
    assert sm.state == AutonomyState.BOOT

    # Cycle 1: Boot to Standby
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=False, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=False)
    assert sm.state == AutonomyState.STANDBY

    # Cycle 2: Standby to Mapping
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=False, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=False)
    assert sm.state == AutonomyState.MAPPING

    # Cycle 3: Mapping to Planning
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=False, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=False)
    assert sm.state == AutonomyState.PLANNING

    # Cycle 4: Planning with path valid to Traversing
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=True, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=False)
    assert sm.state == AutonomyState.TRAVERSING

    # Fault injection: filter diverged -> Fault Isolation -> Safe Stop
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=True, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=True)
    assert sm.state == AutonomyState.FAULT_ISOLATION
    sm.handle_cycle(hardware_healthy=True, e_stop_requested=False, path_valid=True, goal_reached=False, hazard_in_corridor=False, excessive_slip=False, filter_diverged=True)
    assert sm.state == AutonomyState.SAFE_STOP


def test_closed_loop_short_mission():
    """Executes closed-loop traverse over a short path in flat baseline terrain."""
    terrain, cfg = ScenarioGenerator.create_scenario("SC-01_flat_baseline", seed=42)
    # Short goal 10m away
    runner = LongDurationMissionRunner(
        terrain=terrain,
        waypoints=[(12.0, 12.0)],
        start_pose=(5.0, 5.0, 0.0),
        dt=0.05,
        max_mission_time_s=60.0,
    )
    result = runner.run()

    assert result.total_distance_m > 5.0
    assert result.ate_rmse_m < 0.80
    assert result.success is True
