"""Experiment E14: Systematic Weight, Rejection, and Footprint Ablations.
Part 6 Chapter 105 & Part 9 Chapter 156 (Task 77).
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from level1.terrain.generator_v2 import make_scene_v2
from level1.mission.simulator import Simulator
from level1.mission.loop import run_mission
from level1.evaluation.report_generator import mission_metrics


def run_e14_ablation(n_scenes: int = 15, base_seed: int = 8000) -> dict:
    print(f"Executing Experiment E14: Ablation Program on {n_scenes} scenes...", flush=True)
    rng_master = np.random.default_rng(base_seed)
    scenes = []
    for s_idx in range(n_scenes):
        seed = int(rng_master.integers(1, 1000000))
        rng = np.random.default_rng(seed)
        start_row = int(rng.integers(20, 76))
        img, depth, lab, truth_haz, meta = make_scene_v2(rng, difficulty="D2", start_row=start_row)
        scenes.append(dict(scene_id=f"scene_{s_idx:03d}", truth=truth_haz, start_row=start_row, seed=seed))

    variants = {
        "V0_base_C": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50), fp=1, fuse="union"),
        "V1_wu_zero": dict(w=dict(d=1.0, r=3.0, u=0.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50), fp=1, fuse="union"),
        "V2_wr_zero": dict(w=dict(d=1.0, r=0.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50), fp=1, fuse="union"),
        "V3_no_u_block": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=1.10, p_budget=0.50), fp=1, fuse="union"),
        "V4_no_rejection": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=1.00), fp=1, fuse="union"),
        "V5_no_footprint": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50), fp=0, fuse="union"),
        "V6_latest_fusion": dict(w=dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50), fp=1, fuse="latest")
    }

    results = {v_id: [] for v_id in variants}
    sensor_cfg = dict(fov_deg=90.0, range=16.0, miss0=0.02, miss_slope=0.25, false_alarm=0.01)

    for sc in scenes:
        truth = sc["truth"]
        start = (sc["start_row"], 0)
        sim = Simulator(truth)

        for v_id, v_params in variants.items():
            cfg = dict(
                sense=True,
                sensor=sensor_cfg,
                w=v_params["w"],
                h_weight=1.80,
                fuse=v_params["fuse"],
                footprint_radius=v_params["fp"],
                allow_unknown=False
            )
            res = run_mission(sim, cfg, np.random.default_rng(sc["seed"]), start, max_steps=150)
            results[v_id].append(res)

    summary = {v_id: mission_metrics(res_list) for v_id, res_list in results.items()}
    out_payload = dict(
        experiment_id="E14_ablation_program",
        n_scenes=n_scenes,
        summary=summary
    )
    
    os.makedirs("results/level1", exist_ok=True)
    out_path = "results/level1/e14_ablation_results.json"
    with open(out_path, "w") as f:
        json.dump(out_payload, f, indent=1)
    print(f"E14 completed. Results saved to {out_path}", flush=True)
    return out_payload


if __name__ == "__main__":
    run_e14_ablation(n_scenes=15)
