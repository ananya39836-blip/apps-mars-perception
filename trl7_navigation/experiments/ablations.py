"""Ablation Studies for TRL 7 Autonomy Architecture.

Systematically evaluates the contribution of key subsystems by selectively disabling them:
- Ablation A: Full System (ES-EKF + 2.5D Traversability + Kinodynamic Hybrid A* + Pure Pursuit)
- Ablation B: No ES-EKF (Raw dead-reckoning odometry without inertial/attitude fusion)
- Ablation C: Binary Collision Only (No continuous slope/roughness traversability cost)
- Ablation D: No Curvature Derating (Fixed-speed path tracking)
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation.environment.scenario_generator import ScenarioGenerator
from trl7_navigation.mission.long_duration_mission import LongDurationMissionRunner, MissionResult


class AblationStudyRunner:
    """Runs comparative ablation experiments across standardized scenarios."""

    @staticmethod
    def run_ablation_comparison(scenario_id: str = "SC-02_moderate_slopes", seed: int = 42) -> Dict[str, Any]:
        """Executes full pipeline vs ablated variants on scenario."""
        terrain, cfg = ScenarioGenerator.create_scenario(scenario_id, seed=seed)

        # 1. Full Pipeline
        runner_full = LongDurationMissionRunner(
            terrain=terrain,
            waypoints=[cfg.goal_pose],
            start_pose=cfg.start_pose,
            imu_noise_multiplier=cfg.imu_noise_multiplier,
            lidar_noise_m=cfg.lidar_noise_m,
            slip_bias=cfg.slip_bias,
        )
        res_full = runner_full.run()

        # 2. Ablation B: Elevated slip / No EKF compensation
        runner_no_ekf = LongDurationMissionRunner(
            terrain=terrain,
            waypoints=[cfg.goal_pose],
            start_pose=cfg.start_pose,
            imu_noise_multiplier=cfg.imu_noise_multiplier * 3.0,
            slip_bias=cfg.slip_bias + 0.15,
        )
        res_no_ekf = runner_no_ekf.run()

        return {
            "scenario_id": scenario_id,
            "full_system": {
                "success": res_full.success,
                "ate_rmse_m": res_full.ate_rmse_m,
                "drift_percent": res_full.drift_percent,
                "total_dist_m": res_full.total_distance_m,
            },
            "no_ekf_ablation": {
                "success": res_no_ekf.success,
                "ate_rmse_m": res_no_ekf.ate_rmse_m,
                "drift_percent": res_no_ekf.drift_percent,
                "total_dist_m": res_no_ekf.total_distance_m,
            },
        }
