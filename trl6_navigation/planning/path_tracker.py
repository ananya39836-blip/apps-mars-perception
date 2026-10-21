"""Adaptive Pure Pursuit Path Tracking Controller (TRL 6).

Implements:
1. Dynamic lookahead distance adaptation based on speed and local terrain cost
2. Curvature-dependent speed derating on sharp turns to prevent chassis tip-over
3. Terrain-cost speed damping in hazardous regolith
"""
from __future__ import annotations
import math
from typing import Dict, Any, Optional
import numpy as np

from trl6_navigation import (
    MAX_SPEED_MPS,
    NOMINAL_SPEED_MPS,
    MAX_CURVATURE_INV_M,
    ROVER_WHEELBASE_M,
)


class PathTracker:
    """Adaptive Pure Pursuit trajectory tracking controller."""

    def __init__(
        self,
        wheelbase_m: float = ROVER_WHEELBASE_M,
        max_speed_mps: float = MAX_SPEED_MPS,
        nominal_speed_mps: float = NOMINAL_SPEED_MPS,
        min_lookahead_m: float = 1.0,
        max_lookahead_m: float = 3.5,
        lookahead_ratio_s: float = 2.0
    ) -> None:
        self.L = float(wheelbase_m)
        self.v_max = float(max_speed_mps)
        self.v_nom = float(nominal_speed_mps)
        self.ld_min = float(min_lookahead_m)
        self.ld_max = float(max_lookahead_m)
        self.k_ld = float(lookahead_ratio_s)
        self.max_kappa = float(MAX_CURVATURE_INV_M)

    def compute_control_command(
        self,
        current_pose_xytheta: np.ndarray,
        current_speed_mps: float,
        planned_path: np.ndarray,
        local_terrain_cost: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates linear velocity (v) and angular rate (w) steering commands."""
        if len(planned_path) == 0:
            return {
                "cmd_v_mps": 0.0,
                "cmd_w_rps": 0.0,
                "target_point": current_pose_xytheta[:2].copy(),
                "curvature": 0.0,
                "reached_end": True,
            }

        cx, cy, cyaw = float(current_pose_xytheta[0]), float(current_pose_xytheta[1]), float(current_pose_xytheta[2])

        # Dynamic lookahead distance
        ld = np.clip(self.k_ld * max(0.1, current_speed_mps), self.ld_min, self.ld_max)
        # Contract lookahead on high terrain cost to prevent corner-cutting into hazards
        ld *= max(0.60, 1.0 - 0.40 * float(local_terrain_cost))

        # Find closest path waypoint
        dists = np.hypot(planned_path[:, 0] - cx, planned_path[:, 1] - cy)
        closest_idx = int(np.argmin(dists))

        # Check if rover has reached the terminal waypoint
        dist_to_end = math.hypot(planned_path[-1, 0] - cx, planned_path[-1, 1] - cy)
        if dist_to_end <= 0.60:
            return {
                "cmd_v_mps": 0.0,
                "cmd_w_rps": 0.0,
                "target_point": planned_path[-1, :2].copy(),
                "curvature": 0.0,
                "reached_end": True,
            }

        # Search forward along path for the lookahead anchor point
        target_idx = closest_idx
        for idx in range(closest_idx, len(planned_path)):
            d = math.hypot(planned_path[idx, 0] - cx, planned_path[idx, 1] - cy)
            if d >= ld:
                target_idx = idx
                break
        else:
            target_idx = len(planned_path) - 1

        tx, ty = float(planned_path[target_idx, 0]), float(planned_path[target_idx, 1])

        # Angle from rover heading to target point
        angle_to_target = math.atan2(ty - cy, tx - cx)
        alpha = (angle_to_target - cyaw + math.pi) % (2.0 * math.pi) - math.pi

        # Pure Pursuit curvature: kappa = 2 * sin(alpha) / ld
        actual_ld = max(0.5, math.hypot(tx - cx, ty - cy))
        kappa = 2.0 * math.sin(alpha) / actual_ld
        kappa = float(np.clip(kappa, -self.max_kappa, self.max_kappa))

        # Curvature speed derating on sharp turns to prevent chassis tip-over
        turn_derate = 1.0 / (1.0 + 3.0 * abs(kappa))
        cost_derate = max(0.3, 1.0 - 0.65 * float(local_terrain_cost))

        v_cmd = self.v_nom * turn_derate * cost_derate
        v_cmd = float(np.clip(v_cmd, 0.05, self.v_max))

        # Angular rate: w = v * kappa
        w_cmd = float(v_cmd * kappa)

        return {
            "cmd_v_mps": round(v_cmd, 4),
            "cmd_w_rps": round(w_cmd, 4),
            "target_point": np.array([tx, ty]),
            "curvature": round(kappa, 4),
            "reached_end": False,
        }
