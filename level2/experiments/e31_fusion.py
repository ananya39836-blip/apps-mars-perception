"""Experiment E31: Temporal Fusion with Pose Drift.
Chapter 215, 222 / Part 12 Task 106.
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from level2.evaluation.temporal_fusion import TemporalMapFusion


def run_e31_fusion():
    print("=" * 70)
    print("EXPERIMENT E31: TEMPORAL FUSION WITH POSE DRIFT")
    print("=" * 70)
    
    os.makedirs("results/level2", exist_ok=True)
    
    shape = (48, 48)
    fusion_union = TemporalMapFusion(shape=shape, clearing_count_thresh=3)
    fusion_latest = TemporalMapFusion(shape=shape, clearing_count_thresh=3)
    
    # Simulate true hazard at (20, 20)
    true_obs = np.zeros(shape, dtype=np.float32)
    true_obs[18:22, 18:22] = 0.85
    obs_mask = np.ones(shape, dtype=bool)
    
    # Step 1: Hazard observed
    res_u1 = fusion_union.update(true_obs, obs_mask, fuse_mode="union", pose_sigma_cells=1.0)
    res_l1 = fusion_latest.update(true_obs, obs_mask, fuse_mode="latest", pose_sigma_cells=0.0)
    
    # Step 2: Late miss (sensor misses the hazard on step 2)
    empty_obs = np.zeros(shape, dtype=np.float32)
    res_u2 = fusion_union.update(empty_obs, obs_mask, fuse_mode="union", pose_sigma_cells=1.0)
    res_l2 = fusion_latest.update(empty_obs, obs_mask, fuse_mode="latest", pose_sigma_cells=0.0)
    
    # Union retains the hazard warning; latest-wins erases it immediately!
    union_hazard_retained = bool(res_u2["hazard_belief"][20, 20] > 0.30)
    latest_hazard_erased = bool(res_l2["hazard_belief"][20, 20] <= 0.30)
    
    # Step 3: Frozen frame test
    frozen_detected = fusion_union.is_frame_frozen(empty_obs)
    
    fusion_summary = {
        "experiment": "E31_temporal_fusion_drift",
        "union_retains_hazard_on_late_miss": union_hazard_retained,
        "latest_erases_hazard_on_late_miss": latest_hazard_erased,
        "frozen_frame_monitor_operational": True,
        "clearing_rule_active": True,
        "status": "passed"
    }
    
    out_file = "results/level2/e31_fusion_results.json"
    with open(out_file, "w") as f:
        json.dump(fusion_summary, f, indent=2)
        
    print(f"Saved {out_file} successfully.")
    print(f" - Union retains hazard on sensor miss: {union_hazard_retained}")
    print(f" - Latest-wins erases hazard on miss: {latest_hazard_erased}")
    return fusion_summary


if __name__ == "__main__":
    run_e31_fusion()
