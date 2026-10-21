"""Comparative Baseline Algorithms for TRL 7 Benchmark Studies.

Implements benchmark baselines to quantify the performance advantage of the
integrated TRL 7 autonomy pipeline:
1. Dead-Reckoning Pure Odometry Baseline
2. Reactive Bug / Potential Field Local Planner
3. Standard Geometric 2D Grid A* (without kinodynamic curvature constraints)
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class PureOdometryBaseline:
    """Simple dead-reckoning state estimator integrating wheel speeds without EKF fusion."""

    def __init__(self, start_pose: Tuple[float, float, float] = (5.0, 5.0, 0.0)) -> None:
        self.x = float(start_pose[0])
        self.y = float(start_pose[1])
        self.yaw = float(start_pose[2])

    def step(self, forward_speed_m_s: float, angular_speed_rad_s: float, dt: float) -> Tuple[float, float, float]:
        self.yaw += angular_speed_rad_s * dt
        self.x += forward_speed_m_s * math.cos(self.yaw) * dt
        self.y += forward_speed_m_s * math.sin(self.yaw) * dt
        return self.x, self.y, self.yaw


class GeometricGridAStar:
    """Standard 2D grid A* without vehicle kinematic turning radius constraints."""

    def __init__(self) -> None:
        pass

    def plan(
        self,
        start_pos: Tuple[float, float],
        goal_pos: Tuple[float, float],
        impassable_mask: np.ndarray,
        resolution_m: float,
    ) -> Optional[List[Tuple[float, float]]]:
        """Plans 8-connected grid path on binary obstacle mask."""
        import heapq
        sx = int(round(start_pos[0] / resolution_m))
        sy = int(round(start_pos[1] / resolution_m))
        gx = int(round(goal_pos[0] / resolution_m))
        gy = int(round(goal_pos[1] / resolution_m))

        nx, ny = impassable_mask.shape
        if not (0 <= sx < nx and 0 <= sy < ny and 0 <= gx < nx and 0 <= gy < ny):
            return None
        if impassable_mask[sx, sy] or impassable_mask[gx, gy]:
            return None

        open_set = [(math.hypot(gx - sx, gy - sy), 0.0, (sx, sy))]
        came_from = {}
        cost_so_far = {(sx, sy): 0.0}

        dirs = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]

        while open_set:
            _, current_cost, current = heapq.heappop(open_set)

            if current == (gx, gy):
                # Reconstruct path
                path = []
                c = current
                while c in came_from:
                    path.append((c[0] * resolution_m, c[1] * resolution_m))
                    c = came_from[c]
                path.append((sx * resolution_m, sy * resolution_m))
                path.reverse()
                return path

            for dx, dy in dirs:
                nbr = (current[0] + dx, current[1] + dy)
                if not (0 <= nbr[0] < nx and 0 <= nbr[1] < ny):
                    continue
                if impassable_mask[nbr[0], nbr[1]]:
                    continue

                step_cost = math.hypot(dx, dy)
                new_cost = current_cost + step_cost
                if nbr not in cost_so_far or new_cost < cost_so_far[nbr]:
                    cost_so_far[nbr] = new_cost
                    priority = new_cost + math.hypot(gx - nbr[0], gy - nbr[1])
                    heapq.heappush(open_set, (priority, new_cost, nbr))
                    came_from[nbr] = current

        return None
