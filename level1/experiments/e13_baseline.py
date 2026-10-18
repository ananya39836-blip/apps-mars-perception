"""Experiment E13: Closed-Loop Baseline Comparison (F, O, K0, K1, A, B, C).
Part 6 Chapter 98 & Part 9 Task 74.
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


def run_e13_experiment(n_scenes: int = 15, base_seed: int = 7000, difficulty: str = "D1") -> dict:
    """Run E13 comparison across Systems on identical scenes."""
    print(f"Executing Experiment E13: {n_scenes} scenes, difficulty={difficulty}...", flush=True)
    rng_master = np.random.default_rng(base_seed)
    scenes = []
    for s_idx in range(n_scenes):
        seed = int(rng_master.integers(1, 1000000))
        rng = np.random.default_rng(seed)
        start_row = int(rng.integers(20, 76))
        img, depth, lab, truth_haz, meta = make_scene_v2(rng, difficulty=difficulty, start_row=start_row)
        scenes.append(dict(scene_id=f"scene_{s_idx:03d}", truth=truth_haz, start_row=start_row, seed=seed))

    results = {"F": [], "O": [], "K0": [], "K1": [], "B": [], "C": []}
    
    # Common configurations
    sensor_cfg = dict(fov_deg=90.0, range=16.0, miss0=0.02, miss_slope=0.25, false_alarm=0.01)
    base_w = dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50)

    for sc in scenes:
        truth = sc["truth"]
        start = (sc["start_row"], 0)
        sim = Simulator(truth)

        # 1. System F: Fixed route (no sensing, straight line)
        cfg_f = dict(sense=False, w=dict(d=1.0, r=0.0, u=0.0, r_block=1.1, u_block=1.1), h_weight=0.0)
        res_f = run_mission(sim, cfg_f, np.random.default_rng(sc["seed"]), start, max_steps=150)
        results["F"].append(res_f)

        # 2. System O: Oracle (full visibility truth perception)
        cfg_o = dict(sense=False, w=dict(d=1.0, r=10.0, u=0.0, r_block=0.5, u_block=1.1), h_weight=0.0)
        res_o = run_mission(sim, cfg_o, np.random.default_rng(sc["seed"]), start, known_map=truth, max_steps=150)
        results["O"].append(res_o)

        # 3. System K0: Stale prior map without sensing
        stale_map = truth.copy()
        # Perturb 10% of cells
        p_err = np.random.default_rng(sc["seed"] + 1).random(truth.shape) < 0.08
        stale_map ^= p_err
        cfg_k0 = dict(sense=False, w=dict(d=1.0, r=5.0, u=0.0, r_block=0.5, u_block=1.1), h_weight=0.0)
        res_k0 = run_mission(sim, cfg_k0, np.random.default_rng(sc["seed"]), start, known_map=stale_map, max_steps=150)
        results["K0"].append(res_k0)

        # 4. System K1: Stale prior with active sensing and replanning
        cfg_k1 = dict(sense=True, sensor=sensor_cfg, w=dict(d=1.0, r=5.0, u=0.0, r_block=0.5, u_block=1.1), h_weight=1.8, fuse="union")
        res_k1 = run_mission(sim, cfg_k1, np.random.default_rng(sc["seed"]), start, known_map=stale_map, max_steps=150)
        results["K1"].append(res_k1)

        # 5. System B: Standard ML argmax (no uncertainty cost, no rejection)
        cfg_b = dict(sense=True, sensor=sensor_cfg, w=dict(d=1.0, r=4.0, u=0.0, r_block=0.5, u_block=1.1, p_budget=1.0), h_weight=1.8, fuse="latest")
        res_b = run_mission(sim, cfg_b, np.random.default_rng(sc["seed"]), start, max_steps=150)
        results["B"].append(res_b)

        # 6. System C: APPS Proposed (gated risk, uncertainty penalty, rejection, union fusion, footprint)
        cfg_c = dict(sense=True, sensor=sensor_cfg, w=base_w, h_weight=1.8, fuse="union", footprint_radius=1, allow_unknown=False)
        res_c = run_mission(sim, cfg_c, np.random.default_rng(sc["seed"]), start, max_steps=150)
        results["C"].append(res_c)

    summary = {sys_id: mission_metrics(res_list) for sys_id, res_list in results.items()}
    out_payload = dict(
        experiment_id="E13_closed_loop_baseline",
        difficulty=difficulty,
        n_scenes=n_scenes,
        summary=summary
    )
    
    os.makedirs("results/level1", exist_ok=True)
    out_path = "results/level1/e13_baseline_results.json"
    with open(out_path, "w") as f:
        json.dump(out_payload, f, indent=1)
    print(f"E13 completed. Results saved to {out_path}", flush=True)
    return out_payload


if __name__ == "__main__":
    run_e13_experiment(n_scenes=15)
