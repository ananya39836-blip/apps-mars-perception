"""Automated 20-Scenario Validation Campaign Runner (TRL 6).

Executes reproducible closed-loop Monte Carlo trials across all 20 standardized scenario
classes, evaluating mission success rates, physical collision rates, and 95% Wilson CIs.
"""
from __future__ import annotations
import json
import math
import os
import time
from typing import Dict, Any, List, Optional
import numpy as np

from trl6_navigation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    SCENARIO_CLASSES,
    SAFETY_CLEARANCE_MARGIN_M,
)
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
from trl6_navigation.experiments.ablations import AblationConfig


class CampaignRunner:
    """Manages multi-seed automated validation campaigns across all 20 scenario classes."""

    def __init__(
        self,
        output_dir: str = "results/trl6",
        seeds_count: int = 3,
        base_seed: int = 100
    ) -> None:
        self.output_dir = output_dir
        self.seeds_count = int(seeds_count)
        self.base_seed = int(base_seed)
        os.makedirs(self.output_dir, exist_ok=True)

    def run_single_trial(
        self,
        scenario_id: str,
        seed: int,
        ablation_cfg: Optional[AblationConfig] = None
    ) -> Dict[str, Any]:
        """Runs a complete end-to-end closed-loop navigation trial."""
        cfg = ablation_cfg if ablation_cfg is not None else AblationConfig()
        terrain, meta = ScenarioGenerator.build_scenario(scenario_id, seed=seed)

        start_state = meta["start_state"].copy()
        goal_pos = meta["goal_pos"].copy()

        # Instantiate subsystems
        validator = SensorDataValidator()
        rig = MultiSensorRig(
            terrain=terrain,
            noise_multiplier=meta["sensor_noise_factor"],
            lidar_dropout_prob=meta["lidar_dropout_prob"],
            seed=seed
        )
        pc_proc = PointCloudProcessor(voxel_size_m=0.20)
        elev_map = ElevationMap25D(size_x_m=terrain.size_x, size_y_m=terrain.size_y, resolution_m=terrain.res)
        trav_est = TraversabilityEstimator(w_slope=0.0 if cfg.disable_slope_cost else 0.35)

        ekf = ErrorStateEKF(init_x=start_state[0], init_y=start_state[1], init_yaw_rad=start_state[2])
        monitor = StateMonitor()
        planner = KinodynamicHybridAStar(step_length_m=1.60, xy_resolution_m=0.60, max_iterations=4500)
        checker = CollisionChecker(clearance_margin_m=SAFETY_CLEARANCE_MARGIN_M)
        physical_checker = CollisionChecker(clearance_margin_m=0.0)
        tracker = PathTracker()
        stop_ctrl = SafeStopController()
        fsm = RoverFDIRStateMachine(experiment_id=f"{scenario_id}_seed{seed}")

        fsm.transition_to(RoverOperatingMode.SELF_TEST, "Executing pre-traverse self-tests")
        fsm.transition_to(RoverOperatingMode.IDLE, "Self-tests verified; awaiting navigation dispatch")

        # True simulation state: [x, y, yaw, speed]
        sim_x, sim_y, sim_yaw = float(start_state[0]), float(start_state[1]), float(start_state[2])
        sim_speed = 0.0

        # Initialize touchdown patch
        for dx_m in np.arange(-2.5, 2.5, terrain.res):
            for dy_m in np.arange(-2.5, 2.5, terrain.res):
                px, py = sim_x + dx_m, sim_y + dy_m
                if 0 <= px < terrain.size_x and 0 <= py < terrain.size_y:
                    ix, iy = elev_map.world_to_grid(px, py)
                    if elev_map.is_in_bounds(ix, iy):
                        elev_map.elevation[ix, iy] = terrain.get_elevation_at(px, py)
                        elev_map.variance[ix, iy] = 0.01
                        elev_map.hit_count[ix, iy] = 10

        # Initial perception & prior map build
        fsm.transition_to(RoverOperatingMode.PERCEPTION, "Acquiring initial LiDAR scan")
        lidar_data = rig.sample_lidar(np.array([sim_x, sim_y, sim_yaw]))
        val_lidar = validator.validate_lidar_frame(lidar_data, current_time_s=0.0)
        proc_out = pc_proc.process_point_cloud(val_lidar.cleaned_data["points_lidar"], lidar_data["T_world_lidar"])
        elev_map.update_from_point_cloud(proc_out["points_world"], lidar_data["T_world_lidar"][:3, 3])
        elev_map.mark_obstacles(proc_out["obstacle_points"])
        elev_map.detect_negative_obstacles(np.array([sim_x, sim_y]))
        trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

        # Initial path planning
        fsm.transition_to(RoverOperatingMode.PLANNING, "Computing initial Kinodynamic Hybrid A* trajectory")
        plan_res = planner.plan(
            start_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
            goal_pos_xy=goal_pos,
            cost_map=trav_info["cost_map"],
            resolution_m=elev_map.res
        )

        planned_path = plan_res["path"]
        planning_latencies = [plan_res["latency_ms"]]
        replan_count = 0
        collision_count = 0
        min_clearance_m = 99.0

        dt_s = 0.25
        max_steps = 450
        sim_time = 0.0
        success = False
        failure_reason = "TIMEOUT_MAX_STEPS"

        fsm.transition_to(RoverOperatingMode.EXECUTION, "Beginning trajectory execution")

        for step in range(max_steps):
            sim_time += dt_s

            # 1. State Estimation (IMU + Odometry)
            slip_ratio = 0.45 if (meta["slip_disturbance_active"] and 20.0 <= sim_x <= 32.0) else 0.05
            raw_imu = rig.sample_imu(np.array([sim_x, sim_y, sim_yaw]), sim_speed, 0.0, dt_s=dt_s)
            raw_odom = rig.sample_wheel_odometry(sim_speed, 0.0, slip_ratio=slip_ratio)

            val_imu = validator.validate_imu_frame(raw_imu, current_time_s=sim_time)
            val_odom = validator.validate_odometry_frame(raw_odom, current_time_s=sim_time)

            if cfg.use_oracle_state_estimator:
                est_pose = np.array([sim_x, sim_y, sim_yaw])
                est_cov = np.diag([0.01, 0.01, 0.001])
            elif cfg.disable_sensor_fusion:
                # Dead reckoning with raw wheel odometry alone
                est_x = sim_x + val_odom.cleaned_data["meas_linear_mps"] * math.cos(sim_yaw) * dt_s
                est_y = sim_y + val_odom.cleaned_data["meas_linear_mps"] * math.sin(sim_yaw) * dt_s
                est_pose = np.array([est_x, est_y, sim_yaw])
                est_cov = np.diag([0.2, 0.2, 0.05])
            else:
                ekf.predict(val_imu.cleaned_data["meas_gyro_rps"][2], val_imu.cleaned_data["meas_accel_mps2"][0], dt_s=dt_s)
                ekf.update_wheel_odometry(val_odom.cleaned_data["meas_linear_mps"], val_odom.cleaned_data["meas_angular_rps"])
                est_pose, est_cov = ekf.get_estimated_pose()

            # Record state monitor
            mon_audit = monitor.record_step(
                timestamp_s=sim_time,
                estimated_pose_xytheta=est_pose,
                ground_truth_pose_xytheta=np.array([sim_x, sim_y, sim_yaw]),
                pose_covariance=est_cov,
                measured_slip=slip_ratio,
                dt_s=dt_s
            )

            # Check watchdogs
            if mon_audit["slip_trapped"]:
                fsm.trigger_emergency_safe_stop("SLIP_ENTRAPMENT_WATCHDOG_TRIPPED")
            if mon_audit["localization_lost"]:
                fsm.trigger_emergency_safe_stop("LOCALIZATION_COVARIANCE_DIVERGENCE")

            # Check critical fault scenario trigger
            if meta["critical_fault_active"] and step >= 20:
                fsm.trigger_critical_fault("INDUCED_HARDWARE_FAILURE_SENSOR_OFFLINE")
                failure_reason = "CRITICAL_FAULT_INDUCED"
                break

            # 2. Dynamic Obstacle Injection & Perception Update
            if meta["pop_up_obstacle_active"] and step == 20:
                terrain.add_boulder(sim_x + 3.2, sim_y + 3.2, radius_m=0.85, height_m=0.6)

            # Direct wheel-ground contact elevation tracking under chassis
            for dx_m, dy_m in [(-0.5, -0.4), (-0.5, 0.4), (0.0, -0.4), (0.0, 0.4), (0.5, -0.4), (0.5, 0.4)]:
                wx = sim_x + (dx_m * math.cos(sim_yaw) - dy_m * math.sin(sim_yaw))
                wy = sim_y + (dx_m * math.sin(sim_yaw) + dy_m * math.cos(sim_yaw))
                ix, iy = elev_map.world_to_grid(wx, wy)
                if elev_map.is_in_bounds(ix, iy):
                    elev_map.elevation[ix, iy] = terrain.get_elevation_at(wx, wy)
                    elev_map.variance[ix, iy] = 0.01
                    elev_map.hit_count[ix, iy] = max(10, elev_map.hit_count[ix, iy])

            if not cfg.disable_dynamic_obstacle_updates and (step % 5 == 0):
                lidar_sample = rig.sample_lidar(np.array([sim_x, sim_y, sim_yaw]))
                val_scan = validator.validate_lidar_frame(lidar_sample, current_time_s=sim_time)
                if val_scan.cleaned_data["num_returns"] > 0:
                    p_res = pc_proc.process_point_cloud(val_scan.cleaned_data["points_lidar"], lidar_sample["T_world_lidar"])
                    elev_map.update_from_point_cloud(p_res["points_world"], lidar_sample["T_world_lidar"][:3, 3])
                    elev_map.mark_obstacles(p_res["obstacle_points"])
                    elev_map.detect_negative_obstacles(np.array([sim_x, sim_y]))
                    elev_map.clear_dynamic_obstacles_along_rays(np.array([sim_x, sim_y]), p_res["ground_points"])
                    trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

            # 3. Lookahead Path Obstacle Check & Dynamic Replanning Trigger
            dist_to_goal = math.hypot(goal_pos[0] - sim_x, goal_pos[1] - sim_y)
            if dist_to_goal <= 0.60:
                fsm.transition_to(RoverOperatingMode.MISSION_COMPLETE, "Goal location reached within acceptance tolerance")
                success = True
                failure_reason = "NONE_MISSION_SUCCESS"
                break

            # Continuous forward corridor safety check
            path_blocked = False
            if len(planned_path) > 0 and not cfg.disable_replanning:
                dists_to_path = np.hypot(planned_path[:, 0] - sim_x, planned_path[:, 1] - sim_y)
                cur_wp_idx = int(np.argmin(dists_to_path))
                for pt in planned_path[cur_wp_idx + 1:]:
                    d_pt = math.hypot(pt[0] - sim_x, pt[1] - sim_y)
                    if d_pt > 6.0:
                        continue
                    if 0.2 <= d_pt <= 6.0:
                        if not checker.is_pose_collision_free(pt[0], pt[1], pt[2], trav_info["cost_map"], elev_map.res):
                            path_blocked = True
                            break

            if path_blocked or (not cfg.disable_replanning and step > 0 and (step % 20 == 0) and len(planned_path) == 0):
                fsm.transition_to(RoverOperatingMode.REPLANNING, "Obstacle observed intersecting planned trajectory")
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
                    fsm.transition_to(RoverOperatingMode.EXECUTION, "Replanning succeeded; resuming motion")
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

            # Check obstacle clearance along current pose
            cur_ix = np.clip(int(round(sim_x / elev_map.res)), 0, elev_map.nx - 1)
            cur_iy = np.clip(int(round(sim_y / elev_map.res)), 0, elev_map.ny - 1)
            dist_to_obs = float(trav_info["clearance_dist_m"][cur_ix, cur_iy])
            min_clearance_m = min(min_clearance_m, dist_to_obs)

            # Physical collision audit against ground-truth obstacles and rollover slope (> 30 deg)
            ground_truth_lethal = terrain.rock_mask | (terrain.compute_slope_degrees() > 30.0)
            if not physical_checker.is_pose_collision_free(sim_x, sim_y, sim_yaw, ground_truth_lethal.astype(float), elev_map.res, cost_threshold=0.50):
                collision_count += 1
                fsm.trigger_critical_fault("PHYSICAL_CHASSIS_COLLISION_DETECTED")
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
                    fsm.transition_to(RoverOperatingMode.MISSION_COMPLETE, "Path finished at goal")
                    success = True
                    failure_reason = "NONE_MISSION_SUCCESS"
                else:
                    failure_reason = "PATH_FINISHED_BEFORE_GOAL"
                break

            # Update simulation dynamics
            sim_speed = ctrl_cmd["cmd_v_mps"]
            sim_yaw = (sim_yaw + ctrl_cmd["cmd_w_rps"] * dt_s + math.pi) % (2.0 * math.pi) - math.pi
            sim_x += sim_speed * math.cos(sim_yaw) * dt_s
            sim_y += sim_speed * math.sin(sim_yaw) * dt_s

        # Final metrics evaluation
        traj_metrics = monitor.compute_trajectory_metrics()
        perc_eval = PerceptionMetrics.evaluate_obstacle_detection(elev_map.obstacle_mask, terrain.rock_mask)
        elev_eval = PerceptionMetrics.evaluate_elevation_reconstruction(elev_map, terrain)

        # A scenario is safely handled if:
        # 1. Mission was successful (reached goal without collision) OR
        # 2. Rover came to a certified complete SAFE_STOP with 0 collisions when hazards or faults blocked the path
        if collision_count == 0 and (success or fsm.is_safe_stopped or fsm.current_mode in (RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT)):
            safe_handled = True
        else:
            safe_handled = False

        trial_record = {
            "scenario_id": scenario_id,
            "seed": seed,
            "success": success,
            "safe_handled": safe_handled,
            "failure_reason": failure_reason,
            "final_operating_mode": fsm.current_mode.value,
            "collision_count": collision_count,
            "min_obstacle_clearance_m": round(min_clearance_m, 3),
            "sim_duration_s": round(sim_time, 2),
            "replan_count": replan_count,
            "ate_rmse_m": traj_metrics["ate_rmse_m"],
            "ate_max_m": traj_metrics["ate_max_m"],
            "rpe_trans_m": traj_metrics["rpe_trans_m"],
            "rpe_rot_deg": traj_metrics["rpe_rot_deg"],
            "mean_planning_latency_ms": round(float(np.mean(planning_latencies)), 2),
            "max_planning_latency_ms": round(float(np.max(planning_latencies)), 2),
            "obstacle_iou": perc_eval["iou"],
            "obstacle_precision": perc_eval["precision"],
            "obstacle_recall": perc_eval["recall"],
            "elevation_rmse_m": elev_eval["rmse_m"],
        }

        return trial_record

    def run_full_campaign(self) -> Dict[str, Any]:
        """Executes the full 20-scenario multi-seed validation campaign."""
        all_results: List[Dict[str, Any]] = []
        scenario_summaries: Dict[str, Any] = {}

        for sc_id in SCENARIO_CLASSES:
            sc_trials = []
            for s_idx in range(self.seeds_count):
                seed = self.base_seed + s_idx * 17
                record = self.run_single_trial(sc_id, seed=seed)
                sc_trials.append(record)
                all_results.append(record)

            num_runs = len(sc_trials)
            success_count = sum(1 for t in sc_trials if t["safe_handled"])
            rate = float(success_count / num_runs)

            # Wilson score interval for 95% confidence
            z = 1.96
            denom = 1.0 + (z**2) / num_runs
            center = (rate + (z**2) / (2.0 * num_runs)) / denom
            half_w = (z / denom) * math.sqrt((rate * (1.0 - rate) / num_runs) + (z**2) / (4.0 * num_runs**2))
            ci_low = max(0.0, center - half_w)
            ci_high = min(1.0, center + half_w)

            scenario_summaries[sc_id] = {
                "total_runs": num_runs,
                "success_count": success_count,
                "success_rate_pct": round(rate * 100.0, 1),
                "wilson_ci_95": [round(ci_low * 100.0, 1), round(ci_high * 100.0, 1)],
                "total_collisions": sum(t["collision_count"] for t in sc_trials),
                "mean_ate_rmse_m": round(float(np.mean([t["ate_rmse_m"] for t in sc_trials])), 4),
                "mean_planning_latency_ms": round(float(np.mean([t["mean_planning_latency_ms"] for t in sc_trials])), 2),
                "mean_min_clearance_m": round(float(np.mean([t["min_obstacle_clearance_m"] for t in sc_trials])), 3),
            }

        # Save machine-readable JSON manifest
        manifest_path = os.path.join(self.output_dir, "campaign_manifest.json")
        summary_path = os.path.join(self.output_dir, "campaign_summary.json")

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(scenario_summaries, f, indent=2)

        return {
            "total_trials": len(all_results),
            "scenarios_evaluated": len(SCENARIO_CLASSES),
            "manifest_path": manifest_path,
            "summary_path": summary_path,
            "summaries": scenario_summaries,
        }
