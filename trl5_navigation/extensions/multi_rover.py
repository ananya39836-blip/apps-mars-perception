"""Multi-Rover Coordination & Decentralized Map Fusion (Level 5 / TRL 5 Extension).

Simulates a heterogeneous multi-rover team (Rover Alpha & Rover Beta) with independent
state estimation, decentralized map sharing, communication latency, and spatial collision deconfliction.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from trl5_navigation import ROVER_LENGTH_M, ROVER_WIDTH_M, SAFETY_CLEARANCE_MARGIN_M
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


class MultiRoverCoordinator:
    """Coordinates multi-rover map updates and mutual collision avoidance."""

    def __init__(
        self,
        comm_range_m: float = 40.0,
        comm_latency_s: float = 0.5,
        inter_rover_safety_margin_m: float = 2.0
    ) -> None:
        self.comm_range = float(comm_range_m)
        self.comm_latency = float(comm_latency_s)
        self.safety_margin = float(inter_rover_safety_margin_m)

    def check_inter_rover_proximity(
        self,
        rover1_pos_xy: np.ndarray,
        rover2_pos_xy: np.ndarray
    ) -> Dict[str, Any]:
        """Audits mutual separation distance between rovers and flags potential conflict."""
        dist = float(np.linalg.norm(rover1_pos_xy[:2] - rover2_pos_xy[:2]))
        in_comm_range = dist <= self.comm_range
        in_conflict = dist < self.safety_margin

        return {
            "distance_m": round(dist, 2),
            "in_comm_range": in_comm_range,
            "in_conflict": in_conflict,
            "requires_deconfliction": in_conflict,
        }

    def fuse_shared_map(
        self,
        local_map: ElevationMap25D,
        received_map: ElevationMap25D,
        received_rover_pose: np.ndarray
    ) -> ElevationMap25D:
        """Merges remote rover's observed elevation points into local map, accounting for peer position."""
        merged_map = ElevationMap25D(
            size_x_m=local_map.size_x,
            size_y_m=local_map.size_y,
            resolution_m=local_map.res
        )
        # Copy local observations
        merged_map.elevation = local_map.elevation.copy()
        merged_map.variance = local_map.variance.copy()
        merged_map.hit_count = local_map.hit_count.copy()
        merged_map.obstacle_mask = local_map.obstacle_mask.copy()

        # Merge remote cells where remote rover has higher confidence
        remote_mask = received_map.hit_count > local_map.hit_count
        merged_map.elevation[remote_mask] = received_map.elevation[remote_mask]
        merged_map.variance[remote_mask] = received_map.variance[remote_mask]
        merged_map.hit_count[remote_mask] += received_map.hit_count[remote_mask]
        merged_map.obstacle_mask[remote_mask] |= received_map.obstacle_mask[remote_mask]

        # Inject remote rover's current physical position as an active obstacle in the map!
        rx, ry = received_rover_pose[0], received_rover_pose[1]
        rix, riy = merged_map.world_to_grid(rx, ry)
        # Mark safety bubble around peer rover
        bubble_radius_cells = int(round(self.safety_margin / merged_map.res))
        for dx in range(-bubble_radius_cells, bubble_radius_cells + 1):
            for dy in range(-bubble_radius_cells, bubble_radius_cells + 1):
                if dx**2 + dy**2 <= bubble_radius_cells**2:
                    cix, ciy = rix + dx, riy + dy
                    if merged_map.is_in_bounds(cix, ciy):
                        merged_map.obstacle_mask[cix, ciy] = True

        return merged_map
