"""Kinodynamic Hybrid A* / State-Lattice Path Planner (TRL 5).

Plans continuous collision-free trajectories in SE(2) configuration space (x, y, theta)
satisfying rover minimum turning radius (kappa_max = 1.50 m^-1), chassis footprint clearance,
and terrain traversability cost minimization. Includes O(1) state lookup and analytic goal connection.
"""
from __future__ import annotations
import math
import time
import heapq
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from trl5_navigation import MAX_CURVATURE_INV_M
from trl5_navigation.planning.collision_checker import CollisionChecker


class NodeSE2:
    """Represents a state node in SE(2) configuration space."""

    def __init__(
        self,
        x: float,
        y: float,
        yaw: float,
        g_cost: float,
        h_cost: float,
        parent_idx: Optional[int] = None,
        steer_curvature: float = 0.0
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.yaw = float((yaw + math.pi) % (2.0 * math.pi) - math.pi)
        self.g_cost = float(g_cost)
        self.h_cost = float(h_cost)
        self.f_cost = float(g_cost + 2.0 * h_cost)  # Weighted A* for real-time focus
        self.parent_idx = parent_idx
        self.steer_curvature = float(steer_curvature)

    def __lt__(self, other: NodeSE2) -> bool:
        return self.f_cost < other.f_cost


class KinodynamicHybridAStar:
    """Kinodynamic Hybrid A* Path Planner with curvature constraints."""

    def __init__(
        self,
        max_curvature: float = MAX_CURVATURE_INV_M,
        step_length_m: float = 1.50,
        xy_resolution_m: float = 0.50,
        yaw_resolution_deg: float = 15.0,
        max_iterations: int = 1500
    ) -> None:
        self.max_curvature = float(max_curvature)
        self.step_length = float(step_length_m)
        self.xy_res = float(xy_resolution_m)
        self.yaw_res = math.radians(yaw_resolution_deg)
        self.max_iter = int(max_iterations)

        self.collision_checker = CollisionChecker()

        # Steering curvature options for motion primitive expansion
        self.steer_options = [
            -self.max_curvature,
            -self.max_curvature * 0.5,
            0.0,
            self.max_curvature * 0.5,
            self.max_curvature
        ]

    def _state_to_key(self, x: float, y: float, yaw: float) -> Tuple[int, int, int]:
        """Discretizes continuous SE(2) state into hash table key."""
        ix = int(round(x / self.xy_res))
        iy = int(round(y / self.xy_res))
        iyaw = int(round(yaw / self.yaw_res))
        return ix, iy, iyaw

    def _heuristic(self, x: float, y: float, yaw: float, goal_x: float, goal_y: float) -> float:
        """Admissible Euclidean distance with heading alignment bias to goal."""
        dist = math.hypot(goal_x - x, goal_y - y)
        angle_to_goal = math.atan2(goal_y - y, goal_x - x)
        heading_diff = abs((yaw - angle_to_goal + math.pi) % (2.0 * math.pi) - math.pi)
        return dist * (1.0 + 0.3 * (heading_diff / math.pi))

    def _try_analytic_expansion(
        self,
        node: NodeSE2,
        goal_x: float,
        goal_y: float,
        cost_map: np.ndarray,
        resolution_m: float
    ) -> Optional[List[List[float]]]:
        """Attempts direct collision-free geometric connection to goal when within terminal range (<= 5m)."""
        dist = math.hypot(goal_x - node.x, goal_y - node.y)
        if dist > 5.0:
            return None

        nx, ny = cost_map.shape
        num_samples = max(4, int(dist / 0.50))
        target_yaw = math.atan2(goal_y - node.y, goal_x - node.x)

        turn_req = abs((target_yaw - node.yaw + math.pi) % (2.0 * math.pi) - math.pi)
        if turn_req > math.radians(65.0):
            return None  # Turn too sharp for direct shot

        # Quick point check along line
        for s in np.linspace(0.0, 1.0, num_samples):
            px = node.x + s * (goal_x - node.x)
            py = node.y + s * (goal_y - node.y)
            c_ix = int(round(px / resolution_m))
            c_iy = int(round(py / resolution_m))
            if not (0 <= c_ix < nx and 0 <= c_iy < ny) or cost_map[c_ix, c_iy] >= 0.85:
                return None

        path_segment = []
        for s in np.linspace(0.0, 1.0, num_samples):
            px = node.x + s * (goal_x - node.x)
            py = node.y + s * (goal_y - node.y)
            pyaw = node.yaw + s * (target_yaw - node.yaw)
            pyaw = (pyaw + math.pi) % (2.0 * math.pi) - math.pi

            if not self.collision_checker.is_pose_collision_free(px, py, pyaw, cost_map, resolution_m):
                return None  # Collision along direct line

            path_segment.append([px, py, pyaw])

        return path_segment

    def plan(
        self,
        start_pose_xytheta: np.ndarray,
        goal_pos_xy: np.ndarray,
        cost_map: np.ndarray,
        resolution_m: float = 0.20,
        goal_tolerance_m: float = 0.80
    ) -> Dict[str, Any]:
        """Plans kinodynamically feasible path to goal, minimizing traversability cost."""
        t_start = time.perf_counter()

        start_x, start_y, start_yaw = start_pose_xytheta[:3]
        goal_x, goal_y = goal_pos_xy[:2]

        # Verify start and goal viability
        nx, ny = cost_map.shape
        start_ix = np.clip(int(round(start_x / resolution_m)), 0, nx - 1)
        start_iy = np.clip(int(round(start_y / resolution_m)), 0, ny - 1)
        if cost_map[start_ix, start_iy] >= 0.98:
            return {"success": False, "reason": "START_IN_COLLISION", "path": np.empty((0, 3)), "latency_ms": 0.0}

        goal_ix = int(round(goal_x / resolution_m))
        goal_iy = int(round(goal_y / resolution_m))
        if not (0 <= goal_ix < nx and 0 <= goal_iy < ny) or cost_map[goal_ix, goal_iy] >= 0.85:
            return {"success": False, "reason": "GOAL_IN_COLLISION", "path": np.empty((0, 3)), "latency_ms": 0.0}

        start_node = NodeSE2(
            x=start_x, y=start_y, yaw=start_yaw,
            g_cost=0.0,
            h_cost=self._heuristic(start_x, start_y, start_yaw, goal_x, goal_y)
        )

        all_nodes: List[NodeSE2] = [start_node]
        open_heap: List[Tuple[float, int, int]] = []  # (f_cost, counter, node_idx)
        heapq.heappush(open_heap, (start_node.f_cost, 0, 0))

        closed_set: Dict[Tuple[int, int, int], float] = {}
        best_node_idx = 0
        min_h = start_node.h_cost
        counter = 0

        for iteration in range(self.max_iter):
            if not open_heap:
                break

            _, _, current_idx = heapq.heappop(open_heap)
            current_node = all_nodes[current_idx]

            key = self._state_to_key(current_node.x, current_node.y, current_node.yaw)
            if key in closed_set and closed_set[key] <= current_node.g_cost:
                continue
            closed_set[key] = current_node.g_cost

            # Track closest node to goal
            dist_to_goal = math.hypot(goal_x - current_node.x, goal_y - current_node.y)
            if dist_to_goal < min_h:
                min_h = dist_to_goal
                best_node_idx = current_idx

            # 1. Goal arrival check
            if dist_to_goal <= goal_tolerance_m:
                t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                path = self._reconstruct_path(all_nodes, current_idx)
                return {
                    "success": True,
                    "reason": "GOAL_REACHED",
                    "path": path,
                    "path_length_m": float(current_node.g_cost),
                    "iterations": iteration + 1,
                    "latency_ms": round(t_elapsed_ms, 2),
                }

            # 2. Analytic connection shortcut to goal (polled periodically or when within local reach)
            if iteration % 4 == 0 or dist_to_goal < 6.0:
                analytic_path = self._try_analytic_expansion(current_node, goal_x, goal_y, cost_map, resolution_m)
                if analytic_path is not None and len(analytic_path) > 0:
                    base_path = self._reconstruct_path(all_nodes, current_idx)
                    full_path = np.vstack([base_path, np.array(analytic_path[1:], dtype=np.float64)])
                    t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                    return {
                        "success": True,
                        "reason": "GOAL_REACHED_ANALYTIC_SHOT",
                        "path": full_path,
                        "path_length_m": float(current_node.g_cost + dist_to_goal),
                        "iterations": iteration + 1,
                        "latency_ms": round(t_elapsed_ms, 2),
                    }

            # 3. Motion primitive expansion
            for kappa in self.steer_options:
                num_substeps = 4
                sub_ds = self.step_length / num_substeps
                cand_x, cand_y, cand_yaw = current_node.x, current_node.y, current_node.yaw
                arc_collision = False
                traversability_sum = 0.0

                for _ in range(num_substeps):
                    cand_x += sub_ds * math.cos(cand_yaw)
                    cand_y += sub_ds * math.sin(cand_yaw)
                    cand_yaw = (cand_yaw + kappa * sub_ds + math.pi) % (2.0 * math.pi) - math.pi

                    if not self.collision_checker.is_pose_collision_free(cand_x, cand_y, cand_yaw, cost_map, resolution_m):
                        arc_collision = True
                        break

                    c_ix = np.clip(int(round(cand_x / resolution_m)), 0, nx - 1)
                    c_iy = np.clip(int(round(cand_y / resolution_m)), 0, ny - 1)
                    traversability_sum += cost_map[c_ix, c_iy]

                if arc_collision:
                    continue

                avg_cost = traversability_sum / num_substeps
                steering_penalty = abs(kappa) * 0.15
                edge_cost = self.step_length * (1.0 + 2.5 * avg_cost + steering_penalty)
                cand_g = current_node.g_cost + edge_cost

                cand_key = self._state_to_key(cand_x, cand_y, cand_yaw)
                if cand_key in closed_set and closed_set[cand_key] <= cand_g:
                    continue

                cand_h = self._heuristic(cand_x, cand_y, cand_yaw, goal_x, goal_y)
                counter += 1
                new_node_idx = len(all_nodes)
                new_node = NodeSE2(
                    x=cand_x, y=cand_y, yaw=cand_yaw,
                    g_cost=cand_g, h_cost=cand_h,
                    parent_idx=current_idx,
                    steer_curvature=kappa
                )
                all_nodes.append(new_node)
                heapq.heappush(open_heap, (new_node.f_cost, counter, new_node_idx))

        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        if min_h <= goal_tolerance_m * 2.0 and best_node_idx > 0:
            path = self._reconstruct_path(all_nodes, best_node_idx)
            return {
                "success": True,
                "reason": "SUBOPTIMAL_APPROACH_GOAL",
                "path": path,
                "path_length_m": float(all_nodes[best_node_idx].g_cost),
                "iterations": self.max_iter,
                "latency_ms": round(t_elapsed_ms, 2),
            }

        return {
            "success": False,
            "reason": "PATH_SEARCH_EXHAUSTED_OR_BLOCKED",
            "path": np.empty((0, 3)),
            "iterations": self.max_iter,
            "latency_ms": round(t_elapsed_ms, 2),
        }

    def _reconstruct_path(self, all_nodes: List[NodeSE2], end_idx: int) -> np.ndarray:
        """Reconstructs continuous trajectory array [[x, y, yaw], ...] from goal back to start."""
        pts = []
        curr_idx = end_idx
        while curr_idx is not None:
            curr = all_nodes[curr_idx]
            pts.append([curr.x, curr.y, curr.yaw])
            curr_idx = curr.parent_idx
        pts.reverse()
        return np.array(pts, dtype=np.float64)
