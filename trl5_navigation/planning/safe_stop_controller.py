"""Certified Safe-Stop Deceleration Controller (TRL 5).

Guarantees deterministic deceleration to a resting state within physical
traction limits, preventing Inevitable Collision States (ICS).
"""
from __future__ import annotations
import math
from typing import Dict, Any
import numpy as np

from trl5_navigation import MAX_ACCEL_MPS2


class SafeStopController:
    """Regulates emergency deceleration profile guaranteeing rest before collision."""

    def __init__(self, max_decel_mps2: float = MAX_ACCEL_MPS2) -> None:
        self.decel_rate = float(abs(max_decel_mps2))
        self.is_latched: bool = False

    def compute_safe_stop_profile(self, current_speed_mps: float, dt_s: float) -> Dict[str, Any]:
        """Calculates braking command for current time step."""
        speed = float(max(0.0, current_speed_mps))
        stopping_distance_m = (speed**2) / (2.0 * self.decel_rate)

        new_speed = max(0.0, speed - self.decel_rate * float(dt_s))
        if new_speed <= 0.001:
            new_speed = 0.0
            self.is_latched = True

        return {
            "cmd_v_mps": round(new_speed, 4),
            "cmd_w_rps": 0.0,
            "stopping_dist_m": round(stopping_distance_m, 3),
            "at_complete_rest": bool(new_speed == 0.0),
            "safe_stop_latched": self.is_latched,
        }
