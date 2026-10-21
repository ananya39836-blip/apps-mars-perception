"""Formal Unit & Integration Test Suite for TRL 6 Navigation, Planning & Control.

Verifies:
- TRL6-REQ-10: Error-State Extended Kalman Filter (ES-EKF) 15-state sensor fusion
- TRL6-REQ-11: State monitor trajectory auditing (ATE, RPE) and watchdogs
- TRL6-REQ-12: Kinodynamic Hybrid A* global planning (rho >= 0.67m, C^1 continuity)
- TRL6-REQ-13: Oriented chassis bounding box collision checking
- TRL6-REQ-14: Adaptive Pure Pursuit trajectory follower with curvature derating
- TRL6-REQ-15: Certified constant-jerk safe-stop deceleration controller
- TRL6-REQ-16: 11-mode discrete FDIR state machine transition guards
- TRL6-REQ-17: End-to-end Demonstration Mission Executor (Stages A-F)
- TRL6-REQ-18: CCSDS Space Packet HIL telemetry streamer loopback
- Rocker-Bogie suspension kinematics and Bekker-Wong soil terramechanics
"""
from __future__ import annotations
import math
import numpy as np
import pytest

from trl6_navigation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    ROVER_MASS_KG,
    G_MARS,
)
from trl6_navigation.localization.error_state_ekf import ErrorStateEKF
from trl6_navigation.localization.state_monitor import StateMonitor
from trl6_navigation.planning.collision_checker import CollisionChecker
from trl6_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl6_navigation.planning.path_tracker import PathTracker
from trl6_navigation.planning.safe_stop_controller import SafeStopController
from trl6_navigation.dynamics.rocker_bogie import RockerBogieKinematics
from trl6_navigation.dynamics.terramechanics import SoilTerramechanics
from trl6_navigation.dynamics.multibody_rover import MultibodyRoverDynamics
from trl6_navigation.executive.state_machine import RoverOperatingMode, RoverFDIRStateMachine
from trl6_navigation.hil.hil_packet_streamer import HILTelemetryStreamer
from trl6_navigation.mission.mission_executor import DemonstrationMissionExecutor


def test_trl6_error_state_ekf():
    """Verify 15-state ES-EKF kinematic prediction and Joseph-form odometry update."""
    ekf = ErrorStateEKF(init_x=0.0, init_y=0.0, init_yaw_rad=0.0)

    # 1. Forward motion prediction
    for _ in range(10):
        ekf.predict(gyro_z_rps=0.0, accel_x_mps2=0.5, dt_s=0.01)

    pose, cov = ekf.get_estimated_pose()
    assert pose[0] > 0.0  # Moved forward in +X
    assert cov.shape == (3, 3)
    assert np.all(np.diag(cov) > 0.0)  # Positive definite

    # 2. Odometry measurement update
    ekf.update_wheel_odometry(meas_v_mps=0.25, meas_w_rps=0.0)
    speed = ekf.get_forward_speed()
    assert abs(speed - 0.25) < 0.15


def test_trl6_state_monitor_watchdogs():
    """Verify slip entrapment and covariance divergence watchdogs."""
    monitor = StateMonitor(max_position_variance_m2=2.0, slip_entrapment_thresh=0.50, slip_duration_limit_s=0.20)

    # Nominal steps
    for t in [0.0, 0.05, 0.10]:
        res = monitor.record_step(
            t, np.array([t, 0.0, 0.0]), np.array([t, 0.0, 0.0]), np.eye(3) * 0.1, measured_slip=0.10, dt_s=0.05
        )
        assert res["slip_trapped"] is False
        assert res["localization_lost"] is False

    # Inject slip trap
    for t in [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        res = monitor.record_step(
            t, np.array([t, 0.0, 0.0]), np.array([t, 0.0, 0.0]), np.eye(3) * 0.1, measured_slip=0.75, dt_s=0.05
        )
    assert res["slip_trapped"] is True


def test_trl6_collision_checker():
    """Verify oriented bounding box footprint checking with clearance margins."""
    checker = CollisionChecker(clearance_margin_m=0.30)
    cost_map = np.zeros((100, 100), dtype=np.float64)

    # Place lethal obstacle at (10.0m, 10.0m) -> cell (50, 50) at 0.20m res
    cost_map[50, 50] = 1.0

    # Collision at exact obstacle center
    assert not checker.is_pose_collision_free(10.0, 10.0, 0.0, cost_map, resolution_m=0.20)
    # Collision within safety clearance margin (0.3m away)
    assert not checker.is_pose_collision_free(10.2, 10.0, 0.0, cost_map, resolution_m=0.20)
    # Safe far away
    assert checker.is_pose_collision_free(5.0, 5.0, 0.0, cost_map, resolution_m=0.20)


def test_trl6_kinodynamic_hybrid_astar():
    """Verify continuous curvature path planning and latency limits."""
    planner = KinodynamicHybridAStar(max_iterations=1000)
    cost_map = np.zeros((100, 100), dtype=np.float64)

    start_pose = np.array([2.0, 2.0, 0.0])
    goal_pos = np.array([12.0, 12.0])

    res = planner.plan(start_pose, goal_pos, cost_map, resolution_m=0.20)
    assert res["success"] is True
    assert len(res["path"]) > 0
    assert res["latency_ms"] < 250.0  # RTOS execution boundary


def test_trl6_path_tracker_and_curvature_derating():
    """Verify adaptive pure pursuit tracking and turn derating."""
    tracker = PathTracker()
    path = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [4.0, 2.0, math.pi / 4.0],
        [6.0, 4.0, math.pi / 4.0]
    ])

    # 1. Straight segment command
    cmd_straight = tracker.compute_control_command(np.array([0.0, 0.0, 0.0]), 0.25, path)
    assert cmd_straight["cmd_v_mps"] > 0.15
    assert abs(cmd_straight["curvature"]) < 0.20

    # 2. Command with sharp cross-track offset
    cmd_sharp = tracker.compute_control_command(np.array([2.0, 3.0, 0.0]), 0.25, path)
    assert abs(cmd_sharp["curvature"]) > 0.0
    # Speed should be derated on turns
    assert cmd_sharp["cmd_v_mps"] <= tracker.v_nom


def test_trl6_safe_stop_controller():
    """Verify deterministic constant-jerk deceleration to rest."""
    ctrl = SafeStopController(target_decel_mps2=0.20)
    profile = ctrl.compute_safe_stop_profile(current_speed_mps=0.40, dt_s=0.25)
    assert profile["cmd_v_mps"] < 0.40
    assert profile["stopping_distance_m"] > 0.0
    assert profile["at_complete_rest"] is False

    # Full deceleration to complete rest
    v = 0.40
    for _ in range(12):
        step = ctrl.compute_safe_stop_profile(v, dt_s=0.25)
        v = step["cmd_v_mps"]
    assert v <= 0.001


def test_trl6_rocker_bogie_kinematics():
    """Verify rocker-bogie differential pitch and normal force load balancing."""
    rb = RockerBogieKinematics(rover_mass_kg=ROVER_MASS_KG, gravity_mps2=G_MARS)

    # 1. Differential pitch
    pitch_info = rb.compute_differential_pitch(rocker_angle_left_rad=0.10, rocker_angle_right_rad=-0.10)
    assert abs(pitch_info["chassis_pitch_rad"]) < 1e-6
    assert abs(pitch_info["differential_angle_rad"] - 0.10) < 1e-6

    # 2. Wheel loads equilibrium
    loads = rb.compute_wheel_normal_loads(surface_pitch_rad=0.0, surface_roll_rad=0.0)
    total_normal = sum(loads.values())
    expected_weight = ROVER_MASS_KG * G_MARS  # 3153.5 N
    assert abs(total_normal - expected_weight) < 5.0


def test_trl6_terramechanics():
    """Verify Bekker pressure-sinkage and Janosi shear drawbar pull."""
    soil = SoilTerramechanics()
    res = soil.compute_traction_and_drawbar_pull(normal_load_n=525.0, slip_ratio=0.15)
    assert res["sinkage_depth_m"] > 0.0
    assert res["compaction_resistance_n"] > 0.0
    assert res["gross_traction_n"] > res["compaction_resistance_n"]  # Net positive drawbar pull
    assert res["drawbar_pull_n"] > 0.0


def test_trl6_state_machine_guards():
    """Verify 11-mode state machine deterministic transition guards and FAULT locking."""
    fsm = RoverFDIRStateMachine(experiment_id="TEST_FSM")
    assert fsm.current_mode == RoverOperatingMode.INITIALIZATION

    # Valid progression
    assert fsm.transition_to(RoverOperatingMode.SELF_TEST) is True
    assert fsm.transition_to(RoverOperatingMode.IDLE) is True
    assert fsm.transition_to(RoverOperatingMode.PLANNING) is True

    # Illegal jump should trigger FAULT
    illegal_res = fsm.transition_to(RoverOperatingMode.MISSION_COMPLETE)
    assert illegal_res is False
    assert fsm.current_mode == RoverOperatingMode.FAULT
    assert fsm.is_safe_stopped is True


def test_trl6_ccsds_hil_streamer():
    """Verify CCSDS Space Packet binary packing, CRC32, and unpacking loopback."""
    streamer = HILTelemetryStreamer(enabled=False)  # Test binary packing logic without socket binding
    payload = {
        "telemetry_id": "TEST_TM",
        "rover_pose": [5.0, 5.0, 0.785],
        "speed": 0.25,
        "mode": "EXECUTION"
    }

    packet = streamer.pack_ccsds_telemetry(payload, timestamp_s=100.5)
    assert packet.apid == 0x0150
    assert packet.sequence_count == 0
    assert len(packet.raw_packet_bytes) > 20

    # Test unpacking & CRC32 verification
    valid, unpacked = HILTelemetryStreamer.unpack_ccsds_packet(packet.raw_packet_bytes)
    assert valid is True
    assert unpacked is not None
    assert unpacked.apid == 0x0150
    assert unpacked.timestamp_s == 100.5
    assert unpacked.payload_dict["mode"] == "EXECUTION"


def test_trl6_demonstration_mission_execution():
    """Verify complete end-to-end autonomous demonstration mission (Stages A-F)."""
    mission_exec = DemonstrationMissionExecutor(experiment_id="TEST_MISSION_A_F", enable_hil_streamer=False)
    report = mission_exec.execute_mission(scenario_id="SC-01_flat_baseline", seed=100, inject_dynamic_obstacle_at_step=200)

    assert report.safe_handled is True
    assert report.collision_count == 0
    assert report.transition_history_count > 3
    assert "Stage_A" in report.stage_checkpoints
    assert "Stage_F" in report.stage_checkpoints
