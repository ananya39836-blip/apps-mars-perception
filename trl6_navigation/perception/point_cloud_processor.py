"""3D Point Cloud Processing & Ground/Obstacle Segmentation (TRL 6).

Implements:
1. Spatial voxel downsampling
2. Coordinate transformation from sensor to world frame
3. Ground surface estimation using invariant bin-lift relative elevation subtraction
4. Obstacle point segmentation with slope invariance up to 25 degrees
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

from trl6_navigation import MAX_STEP_HEIGHT_M
from trl6_navigation.sensors.coordinate_transforms import transform_points_se3


class PointCloudProcessor:
    """Processes raw point clouds into filtered 3D ground and obstacle point sets."""

    def __init__(
        self,
        voxel_size_m: float = 0.20,
        obstacle_height_thresh_m: float = MAX_STEP_HEIGHT_M
    ) -> None:
        self.voxel_size = float(voxel_size_m)
        self.obs_thresh = float(obstacle_height_thresh_m)

    def voxel_downsample(self, points: np.ndarray) -> np.ndarray:
        """Downsamples (N, 3) point cloud using a uniform spatial grid."""
        if len(points) == 0:
            return np.zeros((0, 3), dtype=np.float64)

        voxel_indices = np.floor(points / self.voxel_size).astype(np.int64)
        _, unique_indices = np.unique(voxel_indices, axis=0, return_index=True)
        return points[unique_indices]

    def process_point_cloud(
        self,
        points_lidar: np.ndarray,
        T_world_lidar: np.ndarray
    ) -> Dict[str, Any]:
        """Transforms points to world frame and segments obstacles from traversable ground."""
        if len(points_lidar) == 0:
            return {
                "points_world": np.zeros((0, 3), dtype=np.float64),
                "ground_points": np.zeros((0, 3), dtype=np.float64),
                "obstacle_points": np.zeros((0, 3), dtype=np.float64),
                "num_ground": 0,
                "num_obstacle": 0,
            }

        # 1. Downsample in sensor coordinates
        pts_down = self.voxel_downsample(points_lidar)

        # 2. Transform to world coordinates
        pts_world = transform_points_se3(pts_down, T_world_lidar)

        # 3. Spatial binning in world (X, Y) to extract local ground reference
        bin_size = self.voxel_size
        bin_coords = np.floor(pts_world[:, :2] / bin_size).astype(np.int64)

        # Map each point to its 2D horizontal bin
        bin_min_z: Dict[Tuple[int, int], float] = {}
        for idx in range(pts_world.shape[0]):
            key = (int(bin_coords[idx, 0]), int(bin_coords[idx, 1]))
            z = pts_world[idx, 2]
            if key not in bin_min_z or z < bin_min_z[key]:
                bin_min_z[key] = z

        # Segment obstacles using relative height within the local bin
        # plus symmetrical cardinal neighbor median check (bin_lift)
        obstacle_indices = []
        ground_indices = []

        for idx in range(pts_world.shape[0]):
            bx, by = int(bin_coords[idx, 0]), int(bin_coords[idx, 1])
            z = pts_world[idx, 2]
            local_min = bin_min_z[(bx, by)]

            # Symmetrical cardinal neighbor median check
            neighbor_mins = [
                bin_min_z.get((bx + dx, by + dy))
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if (bx + dx, by + dy) in bin_min_z
            ]
            bin_lift = (local_min - float(np.median(neighbor_mins))) if len(neighbor_mins) >= 2 else 0.0

            # Height above local terrain surface
            rel_h = max(z - local_min, bin_lift)

            if rel_h >= self.obs_thresh:
                obstacle_indices.append(idx)
            else:
                ground_indices.append(idx)

        ground_pts = pts_world[ground_indices] if ground_indices else np.zeros((0, 3), dtype=np.float64)
        obs_pts = pts_world[obstacle_indices] if obstacle_indices else np.zeros((0, 3), dtype=np.float64)

        return {
            "points_world": pts_world,
            "ground_points": ground_pts,
            "obstacle_points": obs_pts,
            "num_ground": len(ground_pts),
            "num_obstacle": len(obs_pts),
        }
