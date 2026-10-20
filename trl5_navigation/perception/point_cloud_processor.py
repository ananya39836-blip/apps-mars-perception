"""Point Cloud Processing & Surface Segmentation Pipeline (TRL 5).

Transforms raw 3D LiDAR and stereo depth point clouds into the common Map frame (M),
filters noise, and segments point returns into ground surface and positive/negative obstacles.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

from trl5_navigation.sensors.coordinate_transforms import transform_points


class PointCloudProcessor:
    """Processes, filters, and segments 3D point clouds for local mapping."""

    def __init__(
        self,
        voxel_size_m: float = 0.20,
        height_threshold_m: float = 0.25,
        max_valid_range_m: float = 25.0
    ) -> None:
        self.voxel_size = float(voxel_size_m)
        self.height_thresh = float(height_threshold_m)
        self.max_range = float(max_valid_range_m)

    def process_point_cloud(
        self,
        points_sensor_frame: np.ndarray,
        T_world_sensor: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Transforms points to World/Map frame and segments into ground vs obstacle points."""
        if points_sensor_frame.size == 0:
            empty = np.empty((0, 3), dtype=np.float64)
            return {"points_world": empty, "ground_points": empty, "obstacle_points": empty}

        # 1. Range clipping
        ranges = np.linalg.norm(points_sensor_frame, axis=1)
        valid_mask = (ranges >= 0.3) & (ranges <= self.max_range)
        pts_valid = points_sensor_frame[valid_mask]

        if len(pts_valid) == 0:
            empty = np.empty((0, 3), dtype=np.float64)
            return {"points_world": empty, "ground_points": empty, "obstacle_points": empty}

        # 2. Transform into World / Map frame
        pts_world = transform_points(pts_valid, T_world_sensor)

        # 3. Ground plane / obstacle segmentation via local height difference
        # Estimate local ground baseline using grid binning
        bin_x = (pts_world[:, 0] / self.voxel_size).astype(int)
        bin_y = (pts_world[:, 1] / self.voxel_size).astype(int)

        # Hash bins
        bins = {}
        for idx in range(len(pts_world)):
            key = (bin_x[idx], bin_y[idx])
            if key not in bins:
                bins[key] = []
            bins[key].append(pts_world[idx, 2])

        # Find min height (ground estimate) per bin
        ground_per_bin = {k: min(v) for k, v in bins.items()}

        is_obstacle = np.zeros(len(pts_world), dtype=bool)
        for idx in range(len(pts_world)):
            bx, by = bin_x[idx], bin_y[idx]
            min_z = ground_per_bin[(bx, by)]

            # Symmetrical cardinal neighbors for regional slope compensation
            neighbor_elevs = [
                ground_per_bin[(bx + dx, by + dy)]
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                if (bx + dx, by + dy) in ground_per_bin
            ]
            if len(neighbor_elevs) >= 2:
                local_median = float(np.median(neighbor_elevs))
                bin_lift = min_z - local_median
            else:
                bin_lift = 0.0

            # Point is an obstacle if it is higher than its bin ground or if bin itself is elevated above surrounding ground
            if (pts_world[idx, 2] - min_z) > self.height_thresh or bin_lift > self.height_thresh:
                is_obstacle[idx] = True

        return {
            "points_world": pts_world,
            "ground_points": pts_world[~is_obstacle],
            "obstacle_points": pts_world[is_obstacle],
        }
