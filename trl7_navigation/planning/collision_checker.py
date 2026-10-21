"""Oriented Bounding Box (OBB) Swept Collision Checker (TRL 7).

Evaluates physical chassis clearance of the 6-wheel rocker-bogie planetary rover
(2.8m length x 2.2m width) against the 2.5D traversability cost map and hazard obstacles.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    ROVER_LENGTH_M,
    ROVER_WIDTH_M,
    SAFETY_CLEARANCE_MARGIN_M,
)


class CollisionChecker:
    """Rigorous Oriented Bounding Box collision checker across raster maps."""

    def __init__(
        self,
        length_m: float = ROVER_LENGTH_M,
        width_m: float = ROVER_WIDTH_M,
        margin_m: float = SAFETY_CLEARANCE_MARGIN_M,
    ) -> None:
        self.half_l = (float(length_m) * 0.5) + float(margin_m)
        self.half_w = (float(width_m) * 0.5) + float(margin_m)

        # 8 boundary sample offsets relative to vehicle center in body frame
        self.body_samples = np.array([
            [ self.half_l,  self.half_w],
            [ self.half_l, -self.half_w],
            [-self.half_l,  self.half_w],
            [-self.half_l, -self.half_w],
            [ self.half_l,  0.0],
            [-self.half_l,  0.0],
            [ 0.0,          self.half_w],
            [ 0.0,         -self.half_w],
            [ 0.0,          0.0],
        ], dtype=np.float64)

    def is_pose_collision_free(
        self,
        x: float,
        y: float,
        yaw: float,
        cost_map: np.ndarray,
        impassable_mask: np.ndarray,
        resolution_m: float,
        cost_threshold: float = 0.88,
    ) -> bool:
        """Checks if vehicle body at pose (x, y, yaw) intersects impassable hazards."""
        nx, ny = cost_map.shape
        cy = math.cos(yaw)
        sy = math.sin(yaw)

        # Rotate body samples to world frame
        for bx, by in self.body_samples:
            wx = x + (cy * bx - sy * by)
            wy = y + (sy * bx + cy * by)

            ix = int(round(wx / resolution_m))
            iy = int(round(wy / resolution_m))

            if not (0 <= ix < nx and 0 <= iy < ny):
                return False  # Off map is unsafe

            if impassable_mask[ix, iy]:
                return False

            if cost_map[ix, iy] >= cost_threshold:
                return False

        return True

    def is_segment_collision_free(
        self,
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        cost_map: np.ndarray,
        impassable_mask: np.ndarray,
        resolution_m: float,
        step_m: float = 0.20,
    ) -> bool:
        """Sweeps pose between p1 and p2 ensuring collision-free transition."""
        x1, y1, yaw1 = p1
        x2, y2, yaw2 = p2

        dist = math.hypot(x2 - x1, y2 - y1)
        steps = max(2, int(math.ceil(dist / step_m)))

        # Unwrapped yaw interpolation
        dyaw = (yaw2 - yaw1 + math.pi) % (2.0 * math.pi) - math.pi

        for s in range(steps + 1):
            alpha = s / steps
            x = x1 + alpha * (x2 - x1)
            y = y1 + alpha * (y2 - y1)
            yaw = yaw1 + alpha * dyaw

            if not self.is_pose_collision_free(x, y, yaw, cost_map, impassable_mask, resolution_m):
                return False

        return True
