"""Comparative Baselines Benchmark Engine (TRL 6).

Benchmarks the proposed Kinodynamic Hybrid A* against 3 established industry paradigms:
1. Baseline 1: Straight-Line direct trajectory (disregards obstacles and terrain)
2. Baseline 2: 2D Grid-based A* (8-connected grid, sharp point turns)
3. Baseline 3: Terrain-Aware 2D Grid A* (grid search with continuous slope penalty)
4. Proposed: Kinodynamic Hybrid A* (continuous SE(2) bicycle kinematics, rho >= 0.67m)
"""
from __future__ import annotations
import heapq
import json
import math
import os
import time
from typing import Dict, Any, List, Tuple
import numpy as np

from trl6_navigation.environment.scenario_generator import ScenarioGenerator
from trl6_navigation.perception.elevation_mapping import ElevationMap25D
from trl6_navigation.perception.traversability import TraversabilityEstimator
from trl6_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar
from trl6_navigation.planning.collision_checker import CollisionChecker


class ComparativeBaselinesRunner:
    """Executes standardized comparative evaluations against classical navigation approaches."""

    def __init__(self, output_dir: str = "results/trl6") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def run_baseline_straight_line(
        start_xy: np.ndarray,
        goal_xy: np.ndarray,
        cost_map: np.ndarray,
        res: float = 0.20
    ) -> Dict[str, Any]:
        """Baseline 1: Direct straight line from start to goal."""
        t0 = time.perf_counter()
        dist = math.hypot(goal_xy[0] - start_xy[0], goal_xy[1] - start_xy[1])
        num_pts = max(10, int(dist / 0.5))
        xs = np.linspace(start_xy[0], goal_xy[0], num_pts)
        ys = np.linspace(start_xy[1], goal_xy[1], num_pts)
        yaws = np.ones(num_pts) * math.atan2(goal_xy[1] - start_xy[1], goal_xy[0] - start_xy[0])
        path = np.column_stack([xs, ys, yaws])

        checker = CollisionChecker(clearance_margin_m=0.0)
        collisions = 0
        for pt in path:
            if not checker.is_pose_collision_free(pt[0], pt[1], pt[2], cost_map, res, cost_threshold=0.98):
                collisions += 1

        t1 = time.perf_counter()
        return {
            "name": "Baseline_1_StraightLine",
            "success": bool(collisions == 0),
            "collisions": collisions,
            "path_length_m": round(float(dist), 2),
            "latency_ms": round((t1 - t0) * 1000.0, 2),
            "curvature_continuous": False,
        }

    @staticmethod
    def run_baseline_grid_astar(
        start_xy: np.ndarray,
        goal_xy: np.ndarray,
        cost_map: np.ndarray,
        res: float = 0.20
    ) -> Dict[str, Any]:
        """Baseline 2: Standard 8-connected 2D grid A* (sharp discrete turns)."""
        t0 = time.perf_counter()
        nx, ny = cost_map.shape
        sx, sy = int(round(start_xy[0] / res)), int(round(start_xy[1] / res))
        gx, gy = int(round(goal_xy[0] / res)), int(round(goal_xy[1] / res))

        open_set = []
        heapq.heappush(open_set, (0.0, (sx, sy)))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score = {(sx, sy): 0.0}

        def h(c):
            return math.hypot(c[0] - gx, c[1] - gy)

        found = False
        while open_set:
            _, current = heapq.heappop(open_set)
            if math.hypot(current[0] - gx, current[1] - gy) <= 3:
                found = True
                gx, gy = current[0], current[1]
                break

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx_idx, ny_idx = current[0] + dx, current[1] + dy
                if 0 <= nx_idx < nx and 0 <= ny_idx < ny:
                    if cost_map[nx_idx, ny_idx] >= 0.98:
                        continue
                    step_cost = math.hypot(dx, dy)
                    tentative_g = g_score[current] + step_cost
                    if (nx_idx, ny_idx) not in g_score or tentative_g < g_score[(nx_idx, ny_idx)]:
                        came_from[(nx_idx, ny_idx)] = current
                        g_score[(nx_idx, ny_idx)] = tentative_g
                        f_score = tentative_g + h((nx_idx, ny_idx))
                        heapq.heappush(open_set, (f_score, (nx_idx, ny_idx)))

        t1 = time.perf_counter()
        # Reconstruct
        pts = []
        curr = (gx, gy)
        while curr in came_from:
            pts.append([curr[0] * res, curr[1] * res, 0.0])
            curr = came_from[curr]
        pts.reverse()

        path_len = float(len(pts) * res) if pts else 0.0
        return {
            "name": "Baseline_2_Grid_AStar",
            "success": found,
            "collisions": 0 if found else 1,
            "path_length_m": round(path_len, 2),
            "latency_ms": round((t1 - t0) * 1000.0, 2),
            "curvature_continuous": False,  # Sharp 45/90 deg angles
        }

    @staticmethod
    def run_baseline_terrain_astar(
        start_xy: np.ndarray,
        goal_xy: np.ndarray,
        cost_map: np.ndarray,
        res: float = 0.20
    ) -> Dict[str, Any]:
        """Baseline 3: Grid A* incorporating continuous slope traversability costs."""
        t0 = time.perf_counter()
        nx, ny = cost_map.shape
        sx, sy = int(round(start_xy[0] / res)), int(round(start_xy[1] / res))
        gx, gy = int(round(goal_xy[0] / res)), int(round(goal_xy[1] / res))

        open_set = []
        heapq.heappush(open_set, (0.0, (sx, sy)))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score = {(sx, sy): 0.0}

        def h(c):
            return math.hypot(c[0] - gx, c[1] - gy)

        found = False
        while open_set:
            _, current = heapq.heappop(open_set)
            if math.hypot(current[0] - gx, current[1] - gy) <= 3:
                found = True
                gx, gy = current[0], current[1]
                break

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nx_idx, ny_idx = current[0] + dx, current[1] + dy
                if 0 <= nx_idx < nx and 0 <= ny_idx < ny:
                    if cost_map[nx_idx, ny_idx] >= 0.98:
                        continue
                    cell_cost = cost_map[nx_idx, ny_idx]
                    step_cost = math.hypot(dx, dy) * (1.0 + 5.0 * cell_cost)
                    tentative_g = g_score[current] + step_cost
                    if (nx_idx, ny_idx) not in g_score or tentative_g < g_score[(nx_idx, ny_idx)]:
                        came_from[(nx_idx, ny_idx)] = current
                        g_score[(nx_idx, ny_idx)] = tentative_g
                        f_score = tentative_g + h((nx_idx, ny_idx))
                        heapq.heappush(open_set, (f_score, (nx_idx, ny_idx)))

        t1 = time.perf_counter()
        pts = []
        curr = (gx, gy)
        while curr in came_from:
            pts.append([curr[0] * res, curr[1] * res, 0.0])
            curr = came_from[curr]
        pts.reverse()

        path_len = float(len(pts) * res) if pts else 0.0
        return {
            "name": "Baseline_3_Terrain_AStar",
            "success": found,
            "collisions": 0 if found else 1,
            "path_length_m": round(path_len, 2),
            "latency_ms": round((t1 - t0) * 1000.0, 2),
            "curvature_continuous": False,
        }

    def run_comparative_benchmark(self, seed: int = 100) -> Dict[str, Any]:
        """Runs all 3 baselines and the proposed Kinodynamic Hybrid A* on SC-04."""
        terrain, meta = ScenarioGenerator.build_scenario("SC-04_dense_obstacle_field", seed=seed)
        start_pose = meta["start_state"][:3]
        goal_pos = meta["goal_pos"]

        # Build terrain cost
        elev_map = ElevationMap25D(terrain.size_x, terrain.size_y, terrain.res)
        elev_map.elevation = terrain.elevation.copy()
        elev_map.obstacle_mask = terrain.rock_mask.copy()
        elev_map.hit_count[:, :] = 10
        trav_est = TraversabilityEstimator()
        trav_info = trav_est.evaluate_traversability(elev_map, terrain.regolith_friction)

        # 1. Straight Line
        b1 = self.run_baseline_straight_line(start_pose[:2], goal_pos, trav_info["cost_map"], terrain.res)

        # 2. Grid A*
        b2 = self.run_baseline_grid_astar(start_pose[:2], goal_pos, trav_info["cost_map"], terrain.res)

        # 3. Terrain A*
        b3 = self.run_baseline_terrain_astar(start_pose[:2], goal_pos, trav_info["cost_map"], terrain.res)

        # 4. Proposed Kinodynamic Hybrid A*
        planner = KinodynamicHybridAStar()
        p_res = planner.plan(start_pose, goal_pos, trav_info["cost_map"], terrain.res)
        proposed = {
            "name": "Proposed_Kinodynamic_Hybrid_AStar",
            "success": p_res["success"],
            "collisions": 0 if p_res["success"] else 1,
            "path_length_m": p_res["length_m"],
            "latency_ms": p_res["latency_ms"],
            "curvature_continuous": True,
        }

        results = {
            "scenario": "SC-04_dense_obstacle_field",
            "seed": seed,
            "baselines": {
                "Baseline_1_StraightLine": b1,
                "Baseline_2_Grid_AStar": b2,
                "Baseline_3_Terrain_AStar": b3,
                "Proposed_Kinodynamic_Hybrid_AStar": proposed,
            }
        }

        out_path = os.path.join(self.output_dir, "baseline_comparison.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        return results
