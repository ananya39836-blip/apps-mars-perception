"""Experiment E28: Closed-Loop 3D Kinematic Benchmark.
Chapter 219 (Part 12).
Compares System A (Classical), System B (Argmax), and System C (Proposed APPS) on continuous 3D DEMs.
"""
import json
import math
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from level2.sim3d.terrain3d import generate_dem_scene_3d
from level2.sim3d.simulator3d import Simulator3D
from level2.mission.loop3d import run_mission_3d
from level2.evaluation.stats2 import boot_clusters_3d, boot_paired_diff_3d, wilson_interval, rule_of_three


def run_e28_benchmark(n_scenes: int = 15, seed_base: int = 8200):
    print("=" * 70)
    print("EXPERIMENT E28: CLOSED-LOOP 3D KINEMATICS BENCHMARK")
    print("=" * 70)
    
    os.makedirs("results/level2", exist_ok=True)
    
    difficulties = ["D1", "D2", "D3", "D5"]
    test_scenes = []
    
    print(f"Generating {n_scenes} continuous 3D DEM scenes across difficulties...")
    for i in range(n_scenes):
        diff = difficulties[i % len(difficulties)]
        seed = seed_base + i
        terrain = generate_dem_scene_3d(seed=seed, size=96, difficulty=diff)
        test_scenes.append({"scene_id": f"scene_3d_{i+1:03d}", "seed": seed, "diff": diff, "terrain": terrain})

    systems = {
        "System_A": {
            "name": "Classical Traversability",
            "cfg": dict(w=dict(d=1.0, r=4.0, u=0.0, e=1.0, ks=0.5, g=1.5, r_block=0.40, u_block=1.1, p_budget=0.80),
                        fuse_mode="union", allow_unknown=False)
        },
        "System_B": {
            "name": "Standard ML Baseline (Argmax)",
            "cfg": dict(w=dict(d=1.0, r=4.0, u=0.0, e=1.0, ks=0.5, g=1.5, r_block=0.50, u_block=1.1, p_budget=1.00),
                        fuse_mode="latest", allow_unknown=False)
        },
        "System_C": {
            "name": "Proposed Uncertainty-Gated APPS",
            "cfg": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, g=1.5, r_block=0.30, u_block=0.35, p_budget=0.50),
                        fuse_mode="union", allow_unknown=False)
        }
    }

    raw_episodes = {sys_id: [] for sys_id in systems}

    for sc in test_scenes:
        for sys_id, sys_info in systems.items():
            sim = Simulator3D(terrain=sc["terrain"])
            res = run_mission_3d(
                sim, sys_info["cfg"],
                rng=np.random.default_rng(sc["seed"] + 11),
                max_steps=120, dt=0.50
            )
            raw_episodes[sys_id].append({
                "scene_id": sc["scene_id"],
                "outcome": res["outcome"],
                "collided": int(res["collided"]),
                "tipped": int(res["tipped"]),
                "hazard_event": int(res["collided"] or res["tipped"]),
                "success": int(res["outcome"] == "success"),
                "no_path": int(res["outcome"] in ("no_path", "rejected_budget")),
                "steps": res["steps"]
            })

    # Summary metrics per system
    summary = {}
    for sys_id, eps in raw_episodes.items():
        n = len(eps)
        n_haz = sum(e["hazard_event"] for e in eps)
        n_col = sum(e["collided"] for e in eps)
        n_tip = sum(e["tipped"] for e in eps)
        n_succ = sum(e["success"] for e in eps)
        n_nopath = sum(e["no_path"] for e in eps)
        
        haz_rate, haz_lo, haz_hi = boot_clusters_3d(eps, "hazard_event", n_boot=1000)
        w_lo, w_hi = wilson_interval(n_haz, n)
        r3 = rule_of_three(n) if n_haz == 0 else None
        
        summary[sys_id] = {
            "n_episodes": n,
            "success_rate": round(n_succ / n, 4),
            "hazard_rate": round(haz_rate, 4),
            "hazard_ci_95": [round(haz_lo, 4), round(haz_hi, 4)],
            "collision_count": n_col,
            "tip_over_count": n_tip,
            "wilson_rare_interval": [round(w_lo, 4), round(w_hi, 4)],
            "rule_of_three_bound": round(r3, 4) if r3 is not None else None,
            "no_path_rate": round(n_nopath / n, 4)
        }
        print(f"[{sys_id}] Hazard Rate: {haz_rate*100:.1f}% | Success: {n_succ/n*100:.1f}% | No-Path: {n_nopath/n*100:.1f}%")

    # Paired difference (B minus C)
    paired_diff = boot_paired_diff_3d(raw_episodes["System_B"], raw_episodes["System_C"], "hazard_event", n_boot=1000)
    print(f"\nPaired Difference (System B - System C Hazard Rate): {paired_diff['mean_diff']*100:.1f}% (CI: {paired_diff['ci_95']})")

    out_file = "results/level2/e28_kinematics_results.json"
    with open(out_file, "w") as f:
        json.dump({
            "experiment": "E28_3d_kinematic_navigation",
            "n_scenes": n_scenes,
            "systems": summary,
            "paired_B_minus_C": paired_diff,
            "status": "passed"
        }, f, indent=2)

    print(f"Saved {out_file} successfully.")
    return summary


if __name__ == "__main__":
    run_e28_benchmark()
