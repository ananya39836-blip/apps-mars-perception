"""Closed-Loop Trajectory Tracking Controller (TRL 5).

Implements adaptive Pure Pursuit path tracking with lookahead regulation,
cross-track error compensation, and terrain-cost speed derating.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation import MAX_SPEED_MPS, MAX_CURVATURE_INV_M


class PathTracker:
    """Adaptive Pure Pursuit path tracking controller for differential/skid-steer rovers."""

    def __init__(
        self,
        lookahead_base_m: float = 1.0,
        max_speed_mps: float = MAX_SPEED_MPS,
        max_curvature: float = MAX_CURVATURE_INV_M
    ) -> None:
        self.lookahead_base = float(lookahead_base_m)
        self.max_speed = float(max_speed_mps)
        self.max_curv = float(max_curvature)

    def compute_control_command(
        self,
        current_pose_xytheta: np.ndarray,
        current_speed_mps: float,
        planned_path: np.ndarray,
        local_terrain_cost: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates commanded linear velocity v and angular velocity w."""
        if len(planned_path) == 0:
            return {"cmd_v_mps": 0.0, "cmd_w_rps": 0.0, "cross_track_error_m": 0.0, "reached_end": True}

        rx, ry, ryaw = current_pose_xytheta[:3]

        # Find closest point along path
        dists = np.hypot(planned_path[:, 0] - rx, planned_path[:, 1] - ry)
        min_idx = int(np.argmin(dists))
        cross_track_err = float(dists[min_idx])

        # Goal arrival check
        dist_to_final = math.hypot(planned_path[-1, 0] - rx, planned_path[-1, 1] - ry)
        if dist_to_final <= 0.60:
            return {
                "cmd_v_mps": 0.0,
                "cmd_w_rps": 0.0,
                "cross_track_error_m": round(cross_track_err, 3),
                "reached_end": True,
            }

        # Adaptive lookahead distance: contract lookahead near terrain hazards to prevent corner-cutting
        terrain_factor = 1.0 - 0.45 * float(np.clip(local_terrain_cost, 0.0, 1.0))
        lookahead_dist = max(0.50, (self.lookahead_base * terrain_factor) + 0.3 * current_speed_mps)

        # Search forward along path for lookahead target point
        target_idx = min_idx
        for i in range(min_idx, len(planned_path)):
            if dists[i] >= lookahead_dist:
                target_idx = i
                break
        else:
            target_idx = len(planned_path) - 1

        target_x, target_y = planned_path[target_idx, 0], planned_path[target_idx, 1]

        # Angle to target in rover local frame
        dx = target_x - rx
        dy = target_y - ry
        alpha = math.atan2(dy, dx) - ryaw
        alpha = (alpha + math.pi) % (2.0 * math.pi) - math.pi

        # Pure Pursuit curvature: kappa = 2 * sin(alpha) / L_d
        actual_lookahead = max(0.3, math.hypot(dx, dy))
        curvature = 2.0 * math.sin(alpha) / actual_lookahead
        curvature = float(np.clip(curvature, -self.max_curv, self.max_curv))

        # Dynamic speed derating: reduce speed significantly on sharp turns or high terrain cost
        turn_derate = 1.0 / (1.0 + 3.0 * abs(curvature))
        terrain_derate = max(0.15, 1.0 - 0.75 * float(np.clip(local_terrain_cost, 0.0, 1.0)))
        v_cmd = self.max_speed * turn_derate * terrain_derate

        # Commanded angular rate: w = v * kappa
        w_cmd = v_cmd * curvature

        return {
            "cmd_v_mps": round(v_cmd, 3),
            "cmd_w_rps": round(w_cmd, 3),
            "curvature": round(curvature, 3),
            "cross_track_error_m": round(cross_track_err, 3),
            "lookahead_target": np.array([target_x, target_y]),
            "reached_end": False,
        }
