"""Algorithmic Ablation Study Engine (TRL 6).

Systematically disables individual autonomy subsystems under identical environmental
conditions (SC-04 Dense Obstacle Field) to isolate and quantify each module's technical contribution:
- Full proposed system (all capabilities enabled)
- Ablation A: No slope traversability cost (w_slope = 0.0)
- Ablation B: No dynamic online obstacle map updating
- Ablation C: No online evasive path replanning
- Ablation D: No sensor fusion (dead reckoning with raw wheel odometry alone)
- Ablation E: Oracle state estimation (perfect ground truth pose upper bound)
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class AblationConfig:
    """Configures subsystem enabling/disabling for ablation testing."""
    disable_slope_cost: bool = False
    disable_dynamic_obstacle_updates: bool = False
    disable_replanning: bool = False
    disable_sensor_fusion: bool = False
    use_oracle_state_estimator: bool = False


class AblationRunner:
    """Executes standardized algorithmic ablation matrix."""

    def __init__(self, output_dir: str = "results/trl6") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_all_ablations(self, seed: int = 100) -> Dict[str, Any]:
        """Runs the 6 standardized ablation conditions on SC-04."""
        from trl6_navigation.experiments.campaign_runner import CampaignRunner

        runner = CampaignRunner(output_dir=self.output_dir, seeds_count=1, base_seed=seed)
        scenario_id = "SC-04_dense_obstacle_field"

        configs = {
            "proposed_full": AblationConfig(),
            "ablation_a_no_slope_cost": AblationConfig(disable_slope_cost=True),
            "ablation_b_no_dynamic_obstacles": AblationConfig(disable_dynamic_obstacle_updates=True),
            "ablation_c_no_replanning": AblationConfig(disable_replanning=True),
            "ablation_d_no_sensor_fusion": AblationConfig(disable_sensor_fusion=True),
            "ablation_e_oracle_localization": AblationConfig(use_oracle_state_estimator=True),
        }

        results: Dict[str, Any] = {}
        for name, cfg in configs.items():
            record = runner.run_single_trial(scenario_id, seed=seed, ablation_cfg=cfg)
            results[name] = {
                "condition": name,
                "safe_handled": record["safe_handled"],
                "success": record["success"],
                "failure_reason": record["failure_reason"],
                "collision_count": record["collision_count"],
                "min_clearance_m": record["min_obstacle_clearance_m"],
                "ate_rmse_m": record["ate_rmse_m"],
                "planning_latency_ms": record["mean_planning_latency_ms"],
            }

        out_path = os.path.join(self.output_dir, "ablation_study.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results
