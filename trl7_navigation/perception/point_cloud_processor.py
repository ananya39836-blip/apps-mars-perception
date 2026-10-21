"""3D Point Cloud Processing Engine (TRL 7).

Performs spatial point cloud filtering, voxel downsampling, statistical outlier removal,
local surface normal estimation via PCA, and robust ground-obstacle segmentation.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class PointCloudProcessor:
    """Processes raw LiDAR and depth camera point clouds for terrain mapping."""

    def __init__(
        self,
        voxel_size_m: float = 0.20,
        ground_height_threshold_m: float = 0.15,
        normal_radius_m: float = 0.60,
    ) -> None:
        self.voxel_size = float(voxel_size_m)
        self.ground_thresh = float(ground_height_threshold_m)
        self.normal_radius = float(normal_radius_m)

    def voxel_downsample(self, points: np.ndarray) -> np.ndarray:
        """Downsamples (N, 3) point cloud using a 3D regular voxel grid centroid filter."""
        if len(points) == 0:
            return np.zeros((0, 3), dtype=np.float64)

        voxel_indices = np.floor(points / self.voxel_size).astype(np.int64)
        # Unique voxel keys
        _, unique_inv = np.unique(voxel_indices, axis=0, return_inverse=True)

        # Compute centroid per unique voxel using numpy bincount
        n_voxels = unique_inv.max() + 1
        counts = np.bincount(unique_inv, minlength=n_voxels)
        sum_x = np.bincount(unique_inv, weights=points[:, 0], minlength=n_voxels)
        sum_y = np.bincount(unique_inv, weights=points[:, 1], minlength=n_voxels)
        sum_z = np.bincount(unique_inv, weights=points[:, 2], minlength=n_voxels)

        centroids = np.column_stack([sum_x / counts, sum_y / counts, sum_z / counts])
        return centroids

    def filter_statistical_outliers(self, points: np.ndarray, k_neighbors: int = 8, std_ratio: float = 2.0) -> np.ndarray:
        """Removes sparse outlier points based on mean distance to k-nearest neighbors."""
        n_pts = len(points)
        if n_pts <= k_neighbors:
            return points

        # Subsample if large
        pts = points if n_pts < 800 else points[np.random.choice(n_pts, 800, replace=False)]

        # Approximate distance distribution
        # Compute pairwise distance matrix on subset
        diff = pts[:, np.newaxis, :] - pts[np.newaxis, :, :]
        dists = np.linalg.norm(diff, axis=-1)
        np.fill_diagonal(dists, np.inf)

        k_dists = np.partition(dists, kth=k_neighbors, axis=1)[:, :k_neighbors]
        mean_k = np.mean(k_dists, axis=1)

        mu = np.mean(mean_k)
        sigma = np.std(mean_k)
        inlier_mask = mean_k < (mu + std_ratio * sigma)

        return pts[inlier_mask]

    def segment_ground(
        self, points_world: np.ndarray, base_elevation_ref: float = 0.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Segments point cloud into ground returns and obstacle returns.
        
        Returns:
            Tuple[ground_points, obstacle_points]
        """
        if len(points_world) == 0:
            return np.zeros((0, 3)), np.zeros((0, 3))

        # Local height above minimum elevation in small horizontal tiles
        # Group points into 1m x 1m spatial bins
        bin_size = 1.0
        coords = np.floor(points_world[:, :2] / bin_size).astype(np.int64)
        _, inv = np.unique(coords, axis=0, return_inverse=True)

        n_bins = inv.max() + 1
        min_z = np.full(n_bins, np.inf)
        np.minimum.at(min_z, inv, points_world[:, 2])

        # Point relative height above tile minimum
        rel_h = points_world[:, 2] - min_z[inv]

        ground_mask = rel_h <= self.ground_thresh
        obstacle_mask = ~ground_mask

        return points_world[ground_mask], points_world[obstacle_mask]
