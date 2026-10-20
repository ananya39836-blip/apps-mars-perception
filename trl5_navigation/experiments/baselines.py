"""Comparative Navigation Baselines for Planetary Benchmarking (TRL 5).

Implements three reference navigation baselines evaluated under identical conditions:
1. Baseline 1: Straight-Line Waypoint Follower.
2. Baseline 2: Standard 2D Grid A* (geometric, no vehicle kinodynamics).
3. Baseline 3: Terrain-Cost 2D Grid A* (slope-weighted, no continuous curvature).
"""
from __future__ import annotations
import math
import heapq
from typing import Dict, Any, List, Tuple
import numpy as np


class StraightLineBaseline:
    """Baseline 1: Direct straight-line path interpolation without obstacle avoidance."""

    @staticmethod
    def plan(start_pos_xy: np.ndarray, goal_pos_xy: np.ndarray, num_points: int = 40) -> np.ndarray:
        xs = np.linspace(start_pos_xy[0], goal_pos_xy[0], num_points)
        ys = np.linspace(start_pos_xy[1], goal_pos_xy[1], num_points)
        yaws = np.full(num_points, math.atan2(goal_pos_xy[1] - start_pos_xy[1], goal_pos_xy[0] - start_pos_xy[0]))
        return np.column_stack([xs, ys, yaws])


class GridAStarBaseline:
    """Baseline 2 & 3: Discrete 2D 8-connected Grid A* pathfinder."""

    @staticmethod
    def plan(
        start_pos_xy: np.ndarray,
        goal_pos_xy: np.ndarray,
        cost_map: np.ndarray,
        resolution_m: float = 0.20,
        use_terrain_cost: bool = True
    ) -> Dict[str, Any]:
        """Plans discrete 8-connected grid path with optional terrain cost weighting."""
        nx, ny = cost_map.shape
        start_ix = int(round(start_pos_xy[0] / resolution_m))
        start_iy = int(round(start_pos_xy[1] / resolution_m))
        goal_ix = int(round(goal_pos_xy[0] / resolution_m))
        goal_iy = int(round(goal_pos_xy[1] / resolution_m))

        start_ix = np.clip(start_ix, 0, nx - 1)
        start_iy = np.clip(start_iy, 0, ny - 1)
        goal_ix = np.clip(goal_ix, 0, nx - 1)
        goal_iy = np.clip(goal_iy, 0, ny - 1)

        if cost_map[start_ix, start_iy] >= 0.85 or cost_map[goal_ix, goal_iy] >= 0.85:
            return {"success": False, "path": np.empty((0, 3)), "reason": "ENDPOINT_IN_COLLISION"}

        open_set: List[Tuple[float, int, int]] = []
        heapq.heappush(open_set, (0.0, start_ix, start_iy))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {(start_ix, start_iy): 0.0}

        def heuristic(ix: int, iy: int) -> float:
            return math.hypot(goal_ix - ix, goal_iy - iy) * resolution_m

        directions = [
            (1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
            (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)
        ]

        while open_set:
            _, cx, cy = heapq.heappop(open_set)

            if (cx, cy) == (goal_ix, goal_iy) or math.hypot(goal_ix - cx, goal_iy - cy) <= 2:
                # Reconstruct path
                path_pts = []
                curr = (cx, cy)
                while curr in came_from:
                    px, py = curr[0] * resolution_m, curr[1] * resolution_m
                    path_pts.append([px, py, 0.0])
                    curr = came_from[curr]
                path_pts.append([start_ix * resolution_m, start_iy * resolution_m, 0.0])
                path_pts.reverse()

                # Recompute yaw headings
                path_arr = np.array(path_pts, dtype=np.float64)
                if len(path_arr) >= 2:
                    dx = np.diff(path_arr[:, 0])
                    dy = np.diff(path_arr[:, 1])
                    yaws = np.arctan2(dy, dx)
                    path_arr[:-1, 2] = yaws
                    path_arr[-1, 2] = yaws[-1] if len(yaws) > 0 else 0.0

                return {"success": True, "path": path_arr, "reason": "GOAL_REACHED"}

            for dx, dy, step_dist in directions:
                nx_idx, ny_idx = cx + dx, cy + dy
                if not (0 <= nx_idx < nx and 0 <= ny_idx < ny):
                    continue

                cell_cost = cost_map[nx_idx, ny_idx]
                if cell_cost >= 0.85:
                    continue  # Lethal obstacle

                terrain_weight = (1.0 + 4.0 * cell_cost) if use_terrain_cost else 1.0
                tentative_g = g_score[(cx, cy)] + step_dist * resolution_m * terrain_weight

                neighbor = (nx_idx, ny_idx)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = (cx, cy)
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(nx_idx, ny_idx)
                    heapq.heappush(open_set, (f_score, nx_idx, ny_idx))

        return {"success": False, "path": np.empty((0, 3)), "reason": "PATH_SEARCH_EXHAUSTED"}
