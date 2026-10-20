"""Ablation Studies Module for Planetary Rover Autonomy (TRL 5).

Evaluates component contributions by selectively disabling architectural elements:
- Ablation A: Disable terrain slope cost.
- Ablation B: Disable dynamic obstacle map updates.
- Ablation C: Disable closed-loop replanning.
- Ablation D: Disable sensor fusion (raw noisy odometry alone).
- Ablation E: Replace EKF state estimator with ground-truth simulator oracle.
"""
from __future__ import annotations
from typing import Dict, Any, List


class AblationConfig:
    """Configures specific ablation modes for controlled comparative trials."""

    def __init__(
        self,
        disable_slope_cost: bool = False,
        disable_dynamic_obstacle_updates: bool = False,
        disable_replanning: bool = False,
        disable_sensor_fusion: bool = False,
        use_oracle_state_estimator: bool = False
    ) -> None:
        self.disable_slope_cost = bool(disable_slope_cost)
        self.disable_dynamic_obstacle_updates = bool(disable_dynamic_obstacle_updates)
        self.disable_replanning = bool(disable_replanning)
        self.disable_sensor_fusion = bool(disable_sensor_fusion)
        self.use_oracle_state_estimator = bool(use_oracle_state_estimator)

    @classmethod
    def standard_ablations(cls) -> Dict[str, AblationConfig]:
        """Returns standard library of ablation experiments."""
        return {
            "proposed_full": cls(),
            "ablation_a_no_slope_cost": cls(disable_slope_cost=True),
            "ablation_b_no_dynamic_obstacles": cls(disable_dynamic_obstacle_updates=True),
            "ablation_c_no_replanning": cls(disable_replanning=True),
            "ablation_d_no_sensor_fusion": cls(disable_sensor_fusion=True),
            "ablation_e_oracle_localization": cls(use_oracle_state_estimator=True),
        }
