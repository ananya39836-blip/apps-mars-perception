"""Validation Campaign Runner across 20 Operational Scenarios (TRL 7).

Executes standardized Monte-Carlo validation campaigns over all 20 scenario classes
(SC-01 to SC-20) across multiple random seeds, collecting rigorous statistical evidence:
- Success rate with Wilson score 95% confidence intervals
- Absolute Trajectory Error (ATE RMSE) [meters]
- Final waypoint arrival accuracy [meters]
- Dead-reckoning drift percentage [%]
- FDIR recovery actions and safe stops
"""
from __future__ import annotations
import csv
import json
import math
import os
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import SCENARIO_CLASSES
from trl7_navigation.environment.scenario_generator import ScenarioGenerator
from trl7_navigation.mission.long_duration_mission import LongDurationMissionRunner, MissionResult


def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Computes Wilson score interval for binomial proportions.
    
    Returns:
        Tuple[point_estimate, ci_lower, ci_upper]
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    p = k / n
    z = 1.95996  # 95% confidence z-score
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2.0 * n)) / denom
    half_width = (z * math.sqrt((p * (1.0 - p) / n) + (z**2) / (4.0 * (n**2)))) / denom
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    return p, lower, upper


class CampaignRunner:
    """Executes multi-scenario validation campaigns and records verifiable artifacts."""

    def __init__(self, output_dir: str = "results/trl7") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_full_campaign(
        self,
        scenarios: Optional[List[str]] = None,
        seeds: Optional[List[int]] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Runs validation campaign across selected or all 20 scenarios."""
        target_scenarios = scenarios if scenarios is not None else list(SCENARIO_CLASSES)
        target_seeds = seeds if seeds is not None else [42, 101, 2024]

        campaign_start_t = time.time()
        results_by_scenario: Dict[str, List[Dict[str, Any]]] = {}
        all_runs: List[Dict[str, Any]] = []

        total_runs = len(target_scenarios) * len(target_seeds)
        completed_runs = 0

        for sc_id in target_scenarios:
            results_by_scenario[sc_id] = []
            for seed in target_seeds:
                completed_runs += 1
                if verbose:
                    print(f"[{completed_runs}/{total_runs}] Running {sc_id} (seed={seed})...", flush=True)

                terrain, cfg = ScenarioGenerator.create_scenario(sc_id, seed=seed)

                # Determine waypoints
                waypoints = cfg.waypoints if cfg.waypoints else [cfg.goal_pose]

                runner = LongDurationMissionRunner(
                    terrain=terrain,
                    waypoints=waypoints,
                    start_pose=cfg.start_pose,
                    dt=0.05,
                    max_mission_time_s=160.0 if "extended" in sc_id else 80.0,
                    imu_noise_multiplier=cfg.imu_noise_multiplier,
                    lidar_noise_m=cfg.lidar_noise_m,
                    lidar_dropout_prob=cfg.lidar_dropout_prob,
                    slip_bias=cfg.slip_bias,
                    inject_fault=cfg.inject_fault,
                    inject_fault_time_s=cfg.inject_fault_time_s,
                )

                t0 = time.time()
                res: MissionResult = runner.run()
                wall_time = time.time() - t0

                run_data = {
                    "scenario_id": sc_id,
                    "seed": seed,
                    "success": res.success,
                    "final_state": res.final_state,
                    "sim_time_s": res.total_time_s,
                    "wall_time_s": wall_time,
                    "distance_m": res.total_distance_m,
                    "avg_speed_mps": res.average_speed_mps,
                    "ate_rmse_m": res.ate_rmse_m,
                    "final_error_m": res.final_error_m,
                    "drift_percent": res.drift_percent,
                    "replans": res.replans_count,
                    "fault_events": res.fault_events,
                }
                results_by_scenario[sc_id].append(run_data)
                all_runs.append(run_data)

        # Aggregate per-scenario statistics
        summary_per_scenario: Dict[str, Dict[str, Any]] = {}
        total_successes = 0

        for sc_id, runs in results_by_scenario.items():
            n = len(runs)
            k = sum(1 for r in runs if r["success"])
            total_successes += k
            p, lo, hi = compute_wilson_ci(k, n)

            distances = [r["distance_m"] for r in runs]
            ate_rmses = [r["ate_rmse_m"] for r in runs]
            replans = [r["replans"] for r in runs]

            summary_per_scenario[sc_id] = {
                "n_runs": n,
                "n_success": k,
                "success_rate": p,
                "wilson_ci_95": [lo, hi],
                "mean_distance_m": float(np.mean(distances)),
                "std_distance_m": float(np.std(distances)),
                "mean_ate_rmse_m": float(np.mean(ate_rmses)),
                "std_ate_rmse_m": float(np.std(ate_rmses)),
                "mean_replans": float(np.mean(replans)),
            }

        # Overall campaign statistics
        overall_p, overall_lo, overall_hi = compute_wilson_ci(total_successes, total_runs)
        overall_summary = {
            "campaign_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_scenarios": len(target_scenarios),
            "total_runs": total_runs,
            "overall_success_rate": overall_p,
            "overall_wilson_ci_95": [overall_lo, overall_hi],
            "total_wall_time_s": time.time() - campaign_start_t,
            "scenarios": summary_per_scenario,
        }

        # Write results files
        json_path = os.path.join(self.output_dir, "campaign_summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(overall_summary, f, indent=2)

        csv_path = os.path.join(self.output_dir, "campaign_all_runs.csv")
        if all_runs:
            fieldnames = list(all_runs[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_runs)

        if verbose:
            print(f"\nValidation Campaign Complete!")
            print(f"Overall Success Rate: {overall_p*100:.1f}% [95% CI: {overall_lo*100:.1f}% - {overall_hi*100:.1f}%]")
            print(f"Artifacts saved to {json_path} and {csv_path}")

        return overall_summary
