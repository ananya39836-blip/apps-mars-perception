"""Experiment E15: In-Loop Fault Injection Campaign.
Part 6 Chapter 105, Part 8 Chapter 135 & Part 9 Chapter 156 (Task 67/76).
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


def run_e15_faults(n_scenes: int = 15, base_seed: int = 9000) -> dict:
    print(f"Executing Experiment E15: Fault Injection Campaign on {n_scenes} scenes...", flush=True)
    rng_master = np.random.default_rng(base_seed)
    scenes = []
    for s_idx in range(n_scenes):
        seed = int(rng_master.integers(1, 1000000))
        rng = np.random.default_rng(seed)
        start_row = int(rng.integers(20, 76))
        img, depth, lab, truth_haz, meta = make_scene_v2(rng, difficulty="D1", start_row=start_row)
        scenes.append(dict(scene_id=f"scene_{s_idx:03d}", truth=truth_haz, start_row=start_row, seed=seed))

    fault_modes = {
        "nominal_clean": dict(fail_steps=(), pose_sigma=0.0),
        "sensor_outage_steps_8_to_14": dict(fail_steps=tuple(range(8, 15)), pose_sigma=0.0),
        "pose_noise_sigma_1": dict(fail_steps=(), pose_sigma=1.0),
        "pose_noise_sigma_2": dict(fail_steps=(), pose_sigma=2.0)
    }

    results = {f_id: [] for f_id in fault_modes}
    sensor_cfg = dict(fov_deg=90.0, range=16.0, miss0=0.02, miss_slope=0.25, false_alarm=0.01)
    base_w = dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, r_block=0.30, u_block=0.35, p_budget=0.50)

    for sc in scenes:
        truth = sc["truth"]
        start = (sc["start_row"], 0)
        sim = Simulator(truth)

        for f_id, f_cfg in fault_modes.items():
            cfg = dict(
                sense=True,
                sensor=sensor_cfg,
                w=base_w,
                h_weight=1.80,
                fuse="union",
                footprint_radius=1,
                allow_unknown=False,
                pose_sigma=f_cfg["pose_sigma"]
            )
            res = run_mission(sim, cfg, np.random.default_rng(sc["seed"]), start, sensor_fail=f_cfg["fail_steps"], max_steps=150)
            results[f_id].append(res)

    summary = {f_id: mission_metrics(res_list) for f_id, res_list in results.items()}
    out_payload = dict(
        experiment_id="E15_fault_injection_campaign",
        n_scenes=n_scenes,
        summary=summary
    )
    
    os.makedirs("results/level1", exist_ok=True)
    out_path = "results/level1/e15_fault_results.json"
    with open(out_path, "w") as f:
        json.dump(out_payload, f, indent=1)
    print(f"E15 completed. Results saved to {out_path}", flush=True)
    return out_payload


if __name__ == "__main__":
    run_e15_faults(n_scenes=15)
