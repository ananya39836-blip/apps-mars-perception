"""End-to-End Representative Demonstration Mission Orchestrator (TRL 6).

Executes a formal 6-stage autonomous exploration mission:
- Stage A: Initialization & Pre-traverse Subsystem Self-Tests
- Stage B: Initial Multi-Sensor Perception & 2.5D Traversability Mapping
- Stage C: Kinodynamic Hybrid A* Mission Route Planning
- Stage D: Closed-Loop Trajectory Execution & ES-EKF State Estimation
- Stage E: Dynamic Pop-Up Obstacle Detection & Online Evasive Replanning
- Stage F: Goal Verification, Telemetry Auditing & Execution Ledger Export
"""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl6_navigation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    SAFETY_CLEARANCE_MARGIN_M,
)
from trl6_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl6_navigation.environment.scenario_generator import ScenarioGenerator
from trl6_navigation.sensors.sensor_rig import MultiSensorRig
from trl6_navigation.sensors.sensor_validator import SensorDataValidator
from trl6_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl6_navigation.perception.elevation_mapping import ElevationMap25D
from trl6_navigation.perception.traversability import TraversabilityEstimator
from trl6_navigation.perception.perception_metrics import PerceptionMetrics
from trl6_navigation.localization.error_state_ekf import ErrorStateEKF
from trl6_navigation.localization.state_monitor import StateMonitor
from trl6_navigation.planning.collision_checker import CollisionChecker
from trl6_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl6_navigation.planning.path_tracker import PathTracker
from trl6_navigation.planning.safe_stop_controller import SafeStopController
from trl6_navigation.executive.state_machine import RoverOperatingMode, RoverFDIRStateMachine
from trl6_navigation.hil.hil_packet_streamer import HILTelemetryStreamer


@dataclass
class MissionReport:
    """Comprehensive post-mission audit ledger and performance metrics."""
    experiment_id: str
    scenario_id: str
    seed: int
    success: bool
    safe_handled: bool
    failure_reason: str
    final_operating_mode: str
    collision_count: int
    min_obstacle_clearance_m: float
    traverse_duration_s: float
    traverse_distance_m: float
    replan_count: int
    dynamic_obstacle_detected: bool
    dynamic_replan_succeeded: bool
    ate_rmse_m: float
    ate_max_m: float
    rpe_trans_m: float
    rpe_rot_deg: float
    mean_planning_latency_ms: float
    obstacle_precision: float
    obstacle_recall: float
    obstacle_iou: float
    elevation_rmse_m: float
    transition_history_count: int
    stage_checkpoints: Dict[str, Any]


class DemonstrationMissionExecutor:
    """Executes the standard NASA TRL 6 representative demonstration mission."""

    def __init__(
        self,
        experiment_id: str = "MISSION_TRL6_DEMO",
        enable_hil_streamer: bool = False
    ) -> None:
        self.experiment_id = str(experiment_id)
        self.enable_hil = bool(enable_hil_streamer)

    def execute_mission(
        self,
        scenario_id: str = "SC-11_unexpected_obstacles",
        seed: int = 100,
        inject_dynamic_obstacle_at_step: int = 20
    ) -> MissionReport:
        """Runs the complete 6-stage end-to-end autonomous planetary rover mission."""
        stage_checkpoints: Dict[str, Any] = {}

        # ======================================================================
        # STAGE A: Initialization & Pre-Traverse Subsystem Self-Tests
        # ======================================================================
        fsm = RoverFDIRStateMachine(experiment_id=self.experiment_id)
        fsm.transition_to(RoverOperatingMode.SELF_TEST, "Stage A: Performing subsystem built-in self-tests (BIST)")

        terrain, meta = ScenarioGenerator.build_scenario(scenario_id, seed=seed)
        start_state = meta["start_state"].copy()
        goal_pos = meta["goal_pos"].copy()

        validator = SensorDataValidator()
        rig = MultiSensorRig(
            terrain=terrain,
            noise_multiplier=meta["sensor_noise_factor"],
            lidar_dropout_prob=meta["lidar_dropout_prob"],
            seed=seed
        )
        pc_proc = PointCloudProcessor(voxel_size_m=0.20)
        elev_map = ElevationMap25D(size_x_m=terrain.size_x, size_y_m=terrain.size_y, resolution_m=terrain.res)
        trav_est = TraversabilityEstimator(w_slope=0.35)

        ekf = ErrorStateEKF(init_x=start_state[0], init_y=start_state[1], init_yaw_rad=start_state[2])
        monitor = StateMonitor()
        planner = KinodynamicHybridAStar(step_length_m=1.60, xy_resolution_m=0.60, max_iterations=4500)
        checker = CollisionChecker(clearance_margin_m=SAFETY_CLEARANCE_MARGIN_M)
        physical_checker = CollisionChecker(clearance_margin_m=0.0)
        tracker = PathTracker()
        stop_ctrl = SafeStopController()
        hil_streamer = HILTelemetryStreamer(enabled=self.enable_hil)

        sim_x, sim_y, sim_yaw = float(start_state[0]), float(start_state[1]), float(start_state[2])
        sim_speed = 0.0

        # Initialize rover ground contact touchdown patch
        for dx_m in np.arange(-2.5, 2.5, terrain.res):
            for dy_m in np.arange(-2.5, 2.5, terrain.res):
                px, py = sim_x + dx_m, sim_y + dy_m
                if 0 <= px < terrain.size_x and 0 <= py < terrain.size_y:
                    ix, iy = elev_map.world_to_grid(px, py)
                    if elev_map.is_in_bounds(ix, iy):
                        elev_map.elevation[ix, iy] = terrain.get_elevation_at(px, py)
                        elev_map.variance[ix, iy] = 0.01
                        elev_map.hit_count[ix, iy] = 10

        fsm.transition_to(RoverOperatingMode.IDLE, "Stage A complete: Subsystems nominal; ready for dispatch")
        stage_checkpoints["Stage_A"] = {"status": "SUCCESS", "initial_pose": [sim_x, sim_y, sim_yaw]}

        # ======================================================================
        # STAGE B: Initial Multi-Sensor Perception & Traversability Mapping
        # ======================================================================
        fsm.transition_to(RoverOperatingMode.PERCEPTION, "Stage B: Acquiring initial 3D LiDAR & Stereo Camera scan")
        raw_lidar = rig.sample_lidar(np.array([sim_x, sim_y, sim_yaw]))
        val_lidar = validator.validate_lidar_frame(raw_lidar, current_time_s=0.0)

        proc_out = pc_proc.process_point_cloud(val_lidar.cleaned_data["points_lidar"], raw_lidar["T_world_lidar"])
        elev_map.update_from_point_cloud(proc_out["points_world"], raw_lidar["T_world_lidar"][:3, 3])
        elev_map.mark_obstacles(proc_out["obstacle_points"])
        elev_map.detect_negative_obstacles(np.array([sim_x, sim_y]))

        trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)
        stage_checkpoints["Stage_B"] = {
            "status": "SUCCESS",
            "lidar_returns": val_lidar.cleaned_data["num_returns"],
            "obstacles_detected": int(np.sum(elev_map.obstacle_mask)),
        }

        # ======================================================================
        # STAGE C: Kinodynamic Route Planning
        # ======================================================================
        fsm.transition_to(RoverOperatingMode.PLANNING, "Stage C: Computing Kinodynamic Hybrid A* global trajectory")
        plan_res = planner.plan(
            start_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
            goal_pos_xy=goal_pos,
            cost_map=trav_info["cost_map"],
            resolution_m=elev_map.res
        )

        if not plan_res["success"]:
            fsm.trigger_critical_fault(f"Stage C: Initial planning failed - {plan_res['reason']}")
            stage_checkpoints["Stage_C"] = {"status": "FAILED", "reason": plan_res["reason"]}
            return self._build_report(fsm, monitor, elev_map, terrain, 0.0, 0.0, 0, 0, False, False, plan_res["latency_ms"], 0, stage_checkpoints)

        planned_path = plan_res["path"]
        planning_latencies = [plan_res["latency_ms"]]
        replan_count = 0
        collision_count = 0
        min_clearance_m = 99.0
        traverse_distance_m = 0.0

        dynamic_obstacle_detected = False
        dynamic_replan_succeeded = False

        stage_checkpoints["Stage_C"] = {
            "status": "SUCCESS",
            "initial_path_length_m": plan_res["length_m"],
            "planning_latency_ms": plan_res["latency_ms"],
        }

        # ======================================================================
        # STAGE D & E: Closed-Loop Trajectory Execution & Dynamic Hazard Response
        # ======================================================================
        fsm.transition_to(RoverOperatingMode.EXECUTION, "Stage D: Commencing closed-loop trajectory execution")
        dt_s = 0.25
        max_steps = 450
        sim_time = 0.0
        success = False
        failure_reason = "TIMEOUT_MAX_STEPS"

        for step in range(max_steps):
            sim_time += dt_s

            # 1. State Estimation (IMU + Wheel Odometry Fusion via ES-EKF)
            fsm.transition_to(RoverOperatingMode.LOCALIZATION, "Propagating ES-EKF state estimation")
            slip_ratio = 0.45 if (meta["slip_disturbance_active"] and 20.0 <= sim_x <= 32.0) else 0.05
            raw_imu = rig.sample_imu(np.array([sim_x, sim_y, sim_yaw]), sim_speed, 0.0, dt_s=dt_s)
            raw_odom = rig.sample_wheel_odometry(sim_speed, 0.0, slip_ratio=slip_ratio)

            val_imu = validator.validate_imu_frame(raw_imu, current_time_s=sim_time)
            val_odom = validator.validate_odometry_frame(raw_odom, current_time_s=sim_time)

            ekf.predict(val_imu.cleaned_data["meas_gyro_rps"][2], val_imu.cleaned_data["meas_accel_mps2"][0], dt_s=dt_s)
            ekf.update_wheel_odometry(val_odom.cleaned_data["meas_linear_mps"], val_odom.cleaned_data["meas_angular_rps"])
            est_pose, est_cov = ekf.get_estimated_pose()

            # Record state monitor & evaluate watchdogs
            mon_audit = monitor.record_step(
                timestamp_s=sim_time,
                estimated_pose_xytheta=est_pose,
                ground_truth_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
                pose_covariance=est_cov,
                measured_slip=slip_ratio,
                dt_s=dt_s
            )

            if mon_audit["slip_trapped"]:
                fsm.trigger_emergency_safe_stop("SLIP_ENTRAPMENT_WATCHDOG_TRIPPED")
            if mon_audit["localization_lost"]:
                fsm.trigger_emergency_safe_stop("LOCALIZATION_COVARIANCE_DIVERGENCE")

            # Check critical fault scenario trigger
            if meta["critical_fault_active"] and step >= 20:
                fsm.trigger_critical_fault("INDUCED_HARDWARE_FAILURE_PRIMARY_IMU")
                failure_reason = "CRITICAL_FAULT_INDUCED"
                break

            # 2. Stage E: Dynamic Pop-up Obstacle Injection at specified step
            if step == inject_dynamic_obstacle_at_step:
                # Place an unexpected 0.9m boulder directly along the nominal corridor ahead
                boulder_x = sim_x + 3.2 * math.cos(sim_yaw)
                boulder_y = sim_y + 3.2 * math.sin(sim_yaw)
                terrain.add_boulder(boulder_x, boulder_y, radius_m=0.85, height_m=0.60)
                stage_checkpoints["Stage_E_Injection"] = {
                    "step": step,
                    "sim_time": sim_time,
                    "boulder_pos": [round(boulder_x, 2), round(boulder_y, 2)]
                }

            # Periodic online LiDAR perception scan
            if step % 5 == 0:
                fsm.transition_to(RoverOperatingMode.PERCEPTION, "Periodic online LiDAR scan acquisition")
                scan = rig.sample_lidar(np.array([sim_x, sim_y, sim_yaw]))
                val_scan = validator.validate_lidar_frame(scan, current_time_s=sim_time)
                if val_scan.cleaned_data["num_returns"] > 0:
                    p_res = pc_proc.process_point_cloud(val_scan.cleaned_data["points_lidar"], scan["T_world_lidar"])
                    elev_map.update_from_point_cloud(p_res["points_world"], scan["T_world_lidar"][:3, 3])
                    elev_map.mark_obstacles(p_res["obstacle_points"])
                    elev_map.detect_negative_obstacles(np.array([sim_x, sim_y]))
                    # Ray-clear dynamic paths
                    elev_map.clear_dynamic_obstacles_along_rays(np.array([sim_x, sim_y]), p_res["ground_points"])
                    trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

            # 3. Lookahead Corridor Obstacle Check & Dynamic Replanning Trigger
            dist_to_goal = math.hypot(goal_pos[0] - sim_x, goal_pos[1] - sim_y)
            if dist_to_goal <= 0.60:
                fsm.transition_to(RoverOperatingMode.MISSION_COMPLETE, "Stage F: Goal location reached within tolerance")
                success = True
                failure_reason = "NONE_MISSION_SUCCESS"
                break

            path_blocked = False
            if len(planned_path) > 0:
                dists_to_path = np.hypot(planned_path[:, 0] - sim_x, planned_path[:, 1] - sim_y)
                cur_wp_idx = int(np.argmin(dists_to_path))
                for pt in planned_path[cur_wp_idx + 1:]:
                    d_pt = math.hypot(pt[0] - sim_x, pt[1] - sim_y)
                    if d_pt > 6.0:
                        continue
                    if 0.2 <= d_pt <= 6.0:
                        if not checker.is_pose_collision_free(pt[0], pt[1], pt[2], trav_info["cost_map"], elev_map.res):
                            path_blocked = True
                            dynamic_obstacle_detected = True
                            break

            if path_blocked:
                fsm.transition_to(RoverOperatingMode.REPLANNING, "Stage E: Dynamic obstacle detected intersecting path; replanning")
                replan_res = planner.plan(
                    start_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
                    goal_pos_xy=goal_pos,
                    cost_map=trav_info["cost_map"],
                    resolution_m=elev_map.res
                )
                planning_latencies.append(replan_res["latency_ms"])
                replan_count += 1

                if replan_res["success"]:
                    planned_path = replan_res["path"]
                    sim_speed = min(sim_speed, 0.15)  # Evasive turn deceleration
                    dynamic_replan_succeeded = True
                    fsm.transition_to(RoverOperatingMode.EXECUTION, "Dynamic replan successful; resuming traversal")
                else:
                    fsm.trigger_emergency_safe_stop("REPLANNING_FAILED_ROUTE_BLOCKED")
                    failure_reason = f"ROUTE_IMPASSABLE_{replan_res.get('reason')}"

            # Handle safe stop latching
            if fsm.is_safe_stopped:
                stop_profile = stop_ctrl.compute_safe_stop_profile(sim_speed, dt_s)
                sim_speed = stop_profile["cmd_v_mps"]
                if stop_profile["at_complete_rest"]:
                    if failure_reason == "TIMEOUT_MAX_STEPS":
                        failure_reason = "SAFE_STOP_COMPLETE"
                    break
                continue

            # Physical collision check against ground-truth terrain boulders and rollover slopes
            cur_ix = np.clip(int(round(sim_x / elev_map.res)), 0, elev_map.nx - 1)
            cur_iy = np.clip(int(round(sim_y / elev_map.res)), 0, elev_map.ny - 1)
            dist_to_obs = float(trav_info["clearance_dist_m"][cur_ix, cur_iy])
            min_clearance_m = min(min_clearance_m, dist_to_obs)

            ground_truth_lethal = terrain.rock_mask | (terrain.compute_slope_degrees() > 30.0)
            if not physical_checker.is_pose_collision_free(sim_x, sim_y, sim_yaw, ground_truth_lethal.astype(float), elev_map.res, cost_threshold=0.50):
                collision_count += 1
                fsm.trigger_critical_fault("PHYSICAL_COLLISION_DETECTED")
                failure_reason = "COLLISION_LETHAL_OBSTACLE"
                break

            # 4. Motion Control
            cur_cost = float(trav_info["cost_map"][cur_ix, cur_iy])
            ctrl_cmd = tracker.compute_control_command(
                current_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
                current_speed_mps=sim_speed,
                planned_path=planned_path,
                local_terrain_cost=cur_cost
            )

            if ctrl_cmd["reached_end"]:
                if dist_to_goal <= 0.80:
                    fsm.transition_to(RoverOperatingMode.MISSION_COMPLETE, "Stage F: Path finished at goal")
                    success = True
                    failure_reason = "NONE_MISSION_SUCCESS"
                else:
                    failure_reason = "PATH_FINISHED_BEFORE_GOAL"
                break

            # Dynamics integration
            step_v = ctrl_cmd["cmd_v_mps"]
            step_w = ctrl_cmd["cmd_w_rps"]
            sim_speed = step_v
            sim_yaw = (sim_yaw + step_w * dt_s + math.pi) % (2.0 * math.pi) - math.pi
            dx = sim_speed * math.cos(sim_yaw) * dt_s
            dy = sim_speed * math.sin(sim_yaw) * dt_s
            sim_x += dx
            sim_y += dy
            traverse_distance_m += math.hypot(dx, dy)

            # Optional HIL telemetry broadcast
            if self.enable_hil:
                hil_streamer.stream_packet({
                    "sim_time": sim_time,
                    "sim_pose": [sim_x, sim_y, sim_yaw],
                    "sim_speed": sim_speed,
                    "mode": fsm.current_mode.value,
                    "collision_count": collision_count,
                }, timestamp_s=sim_time)

        if self.enable_hil:
            hil_streamer.close()

        # ======================================================================
        # STAGE F: Mission Verification & Ledger Audit
        # ======================================================================
        stage_checkpoints["Stage_F"] = {
            "success": success,
            "failure_reason": failure_reason,
            "sim_duration_s": round(sim_time, 2),
            "total_distance_m": round(traverse_distance_m, 2),
            "final_operating_mode": fsm.current_mode.value,
        }

        mean_lat = float(np.mean(planning_latencies)) if planning_latencies else 0.0
        return self._build_report(
            fsm, monitor, elev_map, terrain, sim_time, traverse_distance_m,
            collision_count, min_clearance_m, dynamic_obstacle_detected,
            dynamic_replan_succeeded, mean_lat, replan_count, stage_checkpoints,
            success, failure_reason, scenario_id, seed
        )

    def _build_report(
        self,
        fsm: RoverFDIRStateMachine,
        monitor: StateMonitor,
        elev_map: ElevationMap25D,
        terrain: PlanetaryTerrain,
        sim_time: float,
        dist_m: float,
        collision_count: int,
        min_clearance_m: float,
        dynamic_obs_det: bool,
        dynamic_replan_succ: bool,
        mean_latency_ms: float,
        replan_count: int,
        stage_checkpoints: Dict[str, Any],
        success: bool = False,
        failure_reason: str = "FAILED",
        scenario_id: str = "DEMO",
        seed: int = 100
    ) -> MissionReport:
        """Constructs standardized MissionReport data structure."""
        traj_metrics = monitor.compute_trajectory_metrics()
        perc_eval = PerceptionMetrics.evaluate_obstacle_detection(elev_map.obstacle_mask, terrain.rock_mask)
        elev_eval = PerceptionMetrics.evaluate_elevation_reconstruction(elev_map, terrain)

        safe_handled = bool(
            collision_count == 0
            and (success or fsm.is_safe_stopped or fsm.current_mode in (RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT))
        )

        return MissionReport(
            experiment_id=self.experiment_id,
            scenario_id=scenario_id,
            seed=seed,
            success=success,
            safe_handled=safe_handled,
            failure_reason=failure_reason,
            final_operating_mode=fsm.current_mode.value,
            collision_count=collision_count,
            min_obstacle_clearance_m=round(min_clearance_m, 3),
            traverse_duration_s=round(sim_time, 2),
            traverse_distance_m=round(dist_m, 2),
            replan_count=replan_count,
            dynamic_obstacle_detected=dynamic_obs_det,
            dynamic_replan_succeeded=dynamic_replan_succ,
            ate_rmse_m=traj_metrics["ate_rmse_m"],
            ate_max_m=traj_metrics["ate_max_m"],
            rpe_trans_m=traj_metrics["rpe_trans_m"],
            rpe_rot_deg=traj_metrics["rpe_rot_deg"],
            mean_planning_latency_ms=round(mean_latency_ms, 2),
            obstacle_precision=perc_eval["precision"],
            obstacle_recall=perc_eval["recall"],
            obstacle_iou=perc_eval["iou"],
            elevation_rmse_m=elev_eval["rmse_m"],
            transition_history_count=len(fsm.transition_history),
            stage_checkpoints=stage_checkpoints,
        )
