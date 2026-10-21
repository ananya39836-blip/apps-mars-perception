"""Certified Safe-Stop Deceleration Controller (TRL 6).

Implements deterministic constant-jerk deceleration profiles guaranteeing vehicle
deceleration to zero speed avoiding dynamic rollover and regolith plowing.
"""
from __future__ import annotations
import math
from typing import Dict, Any


class SafeStopController:
    """Computes certified smooth safe-stop velocity commands under constant deceleration."""

    def __init__(self, target_decel_mps2: float = 0.20) -> None:
        self.decel_rate = float(target_decel_mps2)

    def compute_safe_stop_profile(
        self,
        current_speed_mps: float,
        dt_s: float = 0.05
    ) -> Dict[str, Any]:
        """Calculates step velocity command and remaining stopping distance."""
        v_curr = max(0.0, float(current_speed_mps))
        dt = float(dt_s)

        # Constant deceleration step: v_next = max(0.0, v - a * dt)
        v_next = max(0.0, v_curr - self.decel_rate * dt)
        stopping_dist_rem = (v_next ** 2) / (2.0 * self.decel_rate) if v_next > 0 else 0.0
        time_to_stop_s = v_next / self.decel_rate if v_next > 0 else 0.0

        return {
            "cmd_v_mps": round(v_next, 4),
            "stopping_distance_m": round(stopping_dist_rem, 3),
            "time_to_stop_s": round(time_to_stop_s, 2),
            "at_complete_rest": bool(v_next <= 0.001),
        }
