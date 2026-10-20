"""Oriented Footprint Collision Checking and Clearance Auditing (TRL 5).

Audits swept oriented bounding box chassis footprints against 2.5D elevation
and traversability cost grids enforcing configurable clearance safety margins.
"""
from __future__ import annotations
import math
from typing import Tuple, List
import numpy as np

from trl5_navigation import ROVER_LENGTH_M, ROVER_WIDTH_M, SAFETY_CLEARANCE_MARGIN_M
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


class CollisionChecker:
    """Performs oriented polygonal chassis collision checks against cost maps."""

    def __init__(
        self,
        rover_length_m: float = ROVER_LENGTH_M,
        rover_width_m: float = ROVER_WIDTH_M,
        clearance_margin_m: float = SAFETY_CLEARANCE_MARGIN_M
    ) -> None:
        self.length = float(rover_length_m)
        self.width = float(rover_width_m)
        self.margin = float(clearance_margin_m)

        # Effective collision box dimensions including safety margin
        self.eff_half_len = (self.length / 2.0) + self.margin
        self.eff_half_wid = (self.width / 2.0) + self.margin

    def get_chassis_corners_world(self, x: float, y: float, yaw: float) -> np.ndarray:
        """Computes the 4 corners of the oriented rover chassis in world coordinates."""
        cos_y = math.cos(yaw)
        sin_y = math.sin(yaw)

        # Local corner offsets (+X forward, +Y left)
        local_corners = np.array([
            [self.eff_half_len, self.eff_half_wid],
            [self.eff_half_len, -self.eff_half_wid],
            [-self.eff_half_len, -self.eff_half_wid],
            [-self.eff_half_len, self.eff_half_wid]
        ], dtype=np.float64)

        R = np.array([[cos_y, -sin_y], [sin_y, cos_y]], dtype=np.float64)
        corners_world = (R @ local_corners.T).T + np.array([x, y])
        return corners_world

    def is_pose_collision_free(
        self,
        x: float,
        y: float,
        yaw: float,
        cost_map: np.ndarray,
        resolution_m: float = 0.20,
        cost_threshold: float = 0.95
    ) -> bool:
        """Audits whether rover footprint at (x, y, yaw) intersects lethal obstacles or excessive cost."""
        nx, ny = cost_map.shape
        cos_y = math.cos(yaw)
        sin_y = math.sin(yaw)

        # 1. Fast check at rover center position
        c_ix = int(round(x / resolution_m))
        c_iy = int(round(y / resolution_m))
        if 0 <= c_ix < nx and 0 <= c_iy < ny:
            if cost_map[c_ix, c_iy] >= cost_threshold:
                return False
        else:
            return False

        # 2. Sample points across the interior of the oriented footprint (ensuring center and boundary are checked)
        num_len_samples = max(5, int(self.eff_half_len * 2.0 / resolution_m) | 1)
        num_wid_samples = max(5, int(self.eff_half_wid * 2.0 / resolution_m) | 1)

        dx_samples = np.linspace(-self.eff_half_len, self.eff_half_len, num_len_samples)
        dy_samples = np.linspace(-self.eff_half_wid, self.eff_half_wid, num_wid_samples)

        for dx in dx_samples:
            for dy in dy_samples:
                px = x + (dx * cos_y - dy * sin_y)
                py = y + (dx * sin_y + dy * cos_y)

                ix = int(round(px / resolution_m))
                iy = int(round(py / resolution_m))

                # Boundary check: out-of-bounds is considered lethal
                if not (0 <= ix < nx and 0 <= iy < ny):
                    return False

                if cost_map[ix, iy] >= cost_threshold:
                    return False

        return True
