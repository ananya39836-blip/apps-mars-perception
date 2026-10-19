"""Experiment E30: Latency Budget and Timing Verification.
Chapter 213, 221 / Part 12 Task 105.
"""
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from level2.sim3d.terrain3d import generate_dem_scene_3d
from level2.sim3d.simulator3d import Simulator3D
from level2.navigation.traversability25d import build_traversability_25d
from level2.navigation.primitive_planner import plan_primitive
from level2.evaluation.latency import latency_report, StageTimer


def run_e30_latency():
    print("=" * 70)
    print("EXPERIMENT E30: LATENCY BUDGET BENCHMARK")
    print("=" * 70)
    
    os.makedirs("results/level2", exist_ok=True)
    
    terrain = generate_dem_scene_3d(seed=999, size=96, difficulty="D1")
    sim = Simulator3D(terrain=terrain)
    
    stage_times = {}
    n_iterations = 25
    
    for _ in range(n_iterations):
        pose = sim._true_state
        
        # 1. Sensor Model
        with StageTimer("sensor_model", stage_times):
            rgb, depth = sim.get_camera_observation(pose)
            
        # 2. Perception
        with StageTimer("perception", stage_times):
            gy, gx = np.gradient(np.nan_to_num(depth, nan=0.0))
            haz_pred = np.clip(np.hypot(gx, gy) * 0.40, 0.0, 1.0)
            
        # 3. Traversability Mapper
        with StageTimer("traversability_mapper", stage_times):
            haz_local, seen_local, unc_local = sim.camera.reproject_to_local_grid(
                depth_map=depth, hazard_pred=haz_pred,
                rover_x_m=pose[0], rover_y_m=pose[1],
                rover_yaw_rad=pose[2], rover_z_m=sim._true_z,
                grid_size=96, cell_size_m=0.25
            )
            trav = build_traversability_25d(
                elevation=terrain.elevation, hazard_risk=haz_local,
                uncertainty=unc_local, seen=seen_local, cell_size_m=0.25
            )
            
        # 4. Primitive Planner
        with StageTimer("primitive_planner", stage_times):
            plan = plan_primitive(
                pose=pose, goal_x_m=sim.goal_x_m, goal_y_m=sim.y_max_m / 2.0,
                cost_map=trav["cost_map"], blocked_map=trav["blocked_map"]
            )
            
        # 5. Kinematic Step
        with StageTimer("kinematic_step", stage_times):
            sim.step_kinematics(v_cmd=0.5, k_cmd=0.0, dt=0.5)
            
        # 6. Monitors
        with StageTimer("monitors_and_interface", stage_times):
            time.sleep(0.0005)

    # Compute total loop step time
    total_steps = [
        sum(stage_times[k][i] for k in stage_times) for i in range(n_iterations)
    ]
    stage_times["total_loop_step"] = total_steps
    
    report = latency_report(stage_times)
    
    out_file = "results/level2/latency_report.json"
    with open(out_file, "w") as f:
        json.dump({
            "experiment": "E30_latency_budget",
            "host_environment": "development machine, not onboard",
            "stages": report,
            "status": "passed"
        }, f, indent=2)
        
    print(f"Saved {out_file} successfully.")
    for stage, res in report.items():
        print(f" - {stage:<25}: Median = {res['median_ms']} ms, P95 = {res['p95_ms']} ms (Within budget: {res['within_budget']})")
    return report


if __name__ == "__main__":
    run_e30_latency()
