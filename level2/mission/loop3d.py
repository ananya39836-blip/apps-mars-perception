"""Level 2 Closed-Loop 3D Kinodynamic Mission Loop with JSONL Telemetry Logging.
Chapters 71, 84, 95, 209, 211, 213 (Part 12).
"""
import json
import math
import os
import time
from typing import Dict, List, Tuple
import numpy as np

from level2.sim3d.simulator3d import Simulator3D
from level2.navigation.traversability25d import build_traversability_25d
from level2.navigation.primitive_planner import plan_primitive
from level2.evaluation.temporal_fusion import TemporalMapFusion
from level2.interface.schema import build_message, validate_message
from level1.navigation.monitors import Watchdog, stalled


def run_mission_3d(simulator: Simulator3D, cfg: dict, rng,
                   max_steps: int = 150, dt: float = 0.50,
                   log_jsonl_path: str = None) -> dict:
    """Executes continuous closed-loop 3D navigation mission.
    
    Outcomes:
        'success' | 'collision' | 'tip_over' | 'no_path' | 'safe_stop' | 'timeout'
    """
    params = simulator.params
    grid_size = simulator._terrain.H
    cell_size = simulator._terrain.cell_size_m
    
    # Internal rover belief systems
    fusion = TemporalMapFusion(shape=(grid_size, grid_size))
    watchdog = Watchdog(
        k_progress=cfg.get("k_progress", 14),
        k_outage=cfg.get("k_outage", 3),
        max_replans=cfg.get("max_replans", 60)
    )
    
    # Believed rover state initialized from simulator start
    believed_pose = (simulator._true_state[0], simulator._true_state[1], simulator._true_state[2])
    
    goal_x_m = simulator.goal_x_m
    goal_y_m = simulator.y_max_m / 2.0
    
    log_records = []
    positions = []
    discovered_count = 0
    collided = False
    tipped = False
    status = "running"
    
    jsonl_file = None
    if log_jsonl_path:
        os.makedirs(os.path.dirname(log_jsonl_path), exist_ok=True)
        jsonl_file = open(log_jsonl_path, "w", encoding="utf-8")

    def end_mission(outcome: str, reason: str, t_step: int) -> dict:
        if jsonl_file:
            jsonl_file.close()
        return {
            "outcome": outcome,
            "reason": reason,
            "steps": t_step,
            "final_true_pos": (simulator._true_state[0], simulator._true_state[1], simulator._true_z),
            "final_believed_pos": (believed_pose[0], believed_pose[1]),
            "collided": collided,
            "tipped": tipped,
            "discovered_count": discovered_count,
            "log": log_records
        }

    for t in range(max_steps):
        sensor_ok = (t not in cfg.get("sensor_fail_steps", ()))
        
        # 1. Pose Error Model: believed pose = true pose + Gaussian odometry noise
        pose_sigma = cfg.get("pose_sigma_m", 0.0)
        if pose_sigma > 0.0:
            err_x = float(rng.normal(0.0, pose_sigma))
            err_y = float(rng.normal(0.0, pose_sigma))
            err_th = float(rng.normal(0.0, 0.02))
            believed_pose = (
                simulator._true_state[0] + err_x,
                simulator._true_state[1] + err_y,
                simulator._true_state[2] + err_th
            )
        else:
            believed_pose = simulator._true_state

        positions.append((believed_pose[0], believed_pose[1]))

        # 2. Camera Observation
        rgb_img, depth_img = simulator.get_camera_observation(believed_pose, sensor_ok=sensor_ok)
        
        # 3. Perception Module (Heuristic gradient & novelty detection on camera frame)
        if sensor_ok and np.any(np.isfinite(depth_img)):
            gy, gx = np.gradient(np.nan_to_num(depth_img, nan=0.0))
            depth_grad = np.hypot(gx, gy)
            # System C: calibrated uncertainty gating
            raw_hazard_prob = np.clip(depth_grad * 0.40, 0.0, 1.0)
        else:
            raw_hazard_prob = np.zeros_like(depth_img)

        # 4. Dense Visible Sector & Uncertainty Mapping
        haz_local, seen_local, unc_local = simulator.get_local_observation(
            believed_pose, sensor_ok=sensor_ok
        )


        # 5. Temporal Map Fusion
        fuse_res = fusion.update(
            new_hazard=haz_local, observed_mask=seen_local,
            fuse_mode=cfg.get("fuse_mode", "union"),
            pose_sigma_cells=pose_sigma / cell_size,
            new_uncertainty=unc_local
        )
        if fuse_res["newly_unsafe_count"] > 0:
            discovered_count += 1

        # 6. Build 2.5D Traversability Map
        trav = build_traversability_25d(
            elevation=simulator._terrain.elevation,
            hazard_risk=fusion.hazard_belief,
            uncertainty=fusion.uncertainty_belief,
            seen=fusion.seen_mask,
            cell_size_m=cell_size,
            w=cfg.get("w"),
            allow_unknown=cfg.get("allow_unknown", False),
            max_slope_deg=params.max_safe_slope_deg,
            max_step_m=params.max_step_height_m
        )

        # 7. Kinodynamic Primitive Local Planning
        plan = plan_primitive(
            pose=believed_pose,
            goal_x_m=goal_x_m, goal_y_m=goal_y_m,
            cost_map=trav["cost_map"],
            blocked_map=trav["blocked_map"],
            hazard_risk=fusion.hazard_belief,
            p_budget=cfg.get("p_budget", 0.50),
            cell_size_m=cell_size,
            k_max=params.k_max,
            prim_length_m=1.50,
            body_length=params.body_length,
            body_width=params.body_width
        )

        # 8. Interface Message Validation
        msg = build_message(
            msg_type="plan_record", seq=t + 1, step=t, producer="primitive_planner",
            body={
                "status": plan["status"],
                "score": plan["score"] if plan["score"] is not None else 0.0,
                "p_proxy": plan["p_proxy"] if plan["p_proxy"] is not None else 0.0
            }
        )
        val_status = validate_message(msg, last_seq=t)
        if val_status != "ok":
            return end_mission("safe_stop", f"interface_violation: {val_status}", t)

        # 9. Watchdog & Stall Monitors
        grid_col = int(round(believed_pose[0] / cell_size))
        replan_flag = bool(plan["status"] != "ok")
        stop_reason = watchdog.update(col=grid_col, sensor_ok=sensor_ok, replanned=replan_flag)
        if stop_reason:
            return end_mission("safe_stop", f"watchdog_{stop_reason}", t)

        # Check local oscillation stall
        if stalled(positions, window=14, min_unique=3):
            return end_mission("safe_stop", "watchdog_stalled", t)

        if plan["status"] != "ok":
            return end_mission("no_path" if plan["status"] == "no_primitive" else "rejected_budget", plan["status"], t)

        # 10. Execute Commanded Motion via Simulator Kinematics
        best_prim = plan["primitive"]
        v_cmd = params.v_max
        k_cmd = best_prim["curvature"]
        
        sim_res = simulator.step_kinematics(v_cmd=v_cmd, k_cmd=k_cmd, dt=dt)
        
        # Telemetry record for step
        telemetry = {
            "step": t,
            "time_s": round(t * dt, 2),
            "true_pose": [round(simulator._true_state[0], 3), round(simulator._true_state[1], 3), round(simulator._true_z, 3)],
            "believed_pose": [round(believed_pose[0], 3), round(believed_pose[1], 3), round(believed_pose[2], 3)],
            "v_cmd": v_cmd,
            "k_cmd": k_cmd,
            "pitch_deg": round(sim_res["pitch_deg"], 2),
            "roll_deg": round(sim_res["roll_deg"], 2),
            "slope_deg": round(sim_res["slope_deg"], 2),
            "slip_factor": round(sim_res["slip_factor"], 3),
            "clips": sim_res["clips"],
            "plan_status": plan["status"],
            "navigation_ready": False
        }
        log_records.append(telemetry)
        if jsonl_file:
            jsonl_file.write(json.dumps(telemetry) + "\n")

        # Check physics termination events
        if sim_res["is_tipped"]:
            tipped = True
            return end_mission("tip_over", "vehicle_rollover_on_steep_slope", t + 1)
            
        if sim_res["collided"]:
            collided = True
            return end_mission("collision", "obstacle_rock_collision", t + 1)
            
        if sim_res["is_goal"]:
            return end_mission("success", "goal_boundary_reached", t + 1)

    return end_mission("timeout", "maximum_step_budget_exceeded", max_steps)
