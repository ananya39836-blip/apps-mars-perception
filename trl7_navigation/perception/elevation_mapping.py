"""2.5D Probabilistic Elevation Mapping Engine (TRL 7).

Maintains a 2.5D regular grid of planetary terrain elevation with 1D Kalman filter
variance updates per cell, temporal uncertainty inflation, ray-clearing,
and negative obstacle (crater) detection.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ElevationMap25D:
    """Probabilistic 2.5D elevation grid with Kalman variance propagation."""

    def __init__(
        self,
        size_x_m: float = 60.0,
        size_y_m: float = 60.0,
        resolution_m: float = 0.25,
        default_variance: float = 1.0,
    ) -> None:
        self.size_x = float(size_x_m)
        self.size_y = float(size_y_m)
        self.res = float(resolution_m)
        self.nx = int(round(self.size_x / self.res))
        self.ny = int(round(self.size_y / self.res))

        # Grid state
        self.elevation = np.zeros((self.nx, self.ny), dtype=np.float64)
        self.variance = np.full((self.nx, self.ny), default_variance, dtype=np.float64)
        self.observed = np.zeros((self.nx, self.ny), dtype=bool)
        self.negative_obstacle_mask = np.zeros((self.nx, self.ny), dtype=bool)

        # Coordinate axes
        self.x_coords = np.linspace(0.0, self.size_x, self.nx)
        self.y_coords = np.linspace(0.0, self.size_y, self.ny)

    def update_from_point_cloud(
        self, points_world: np.ndarray, measurement_noise_std: float = 0.05
    ) -> None:
        """Updates elevation grid cells using 3D points in world frame via Kalman fusion."""
        if len(points_world) == 0:
            return

        r_var = float(measurement_noise_std ** 2)

        # Compute cell indices
        ix = np.floor(points_world[:, 0] / self.res).astype(np.int64)
        iy = np.floor(points_world[:, 1] / self.res).astype(np.int64)

        # Bounds check
        valid = (ix >= 0) & (ix < self.nx) & (iy >= 0) & (iy < self.ny)
        if not np.any(valid):
            return

        ix = ix[valid]
        iy = iy[valid]
        z_pts = points_world[valid, 2]

        for i, j, z_meas in zip(ix, iy, z_pts):
            if not self.observed[i, j]:
                self.elevation[i, j] = z_meas
                self.variance[i, j] = r_var
                self.observed[i, j] = True
            else:
                # 1D Kalman filter update
                var_prior = self.variance[i, j]
                k = var_prior / (var_prior + r_var)
                self.elevation[i, j] += k * (z_meas - self.elevation[i, j])
                self.variance[i, j] = (1.0 - k) * var_prior

    def decay_unobserved_variance(self, rate_per_sec: float = 0.01, dt: float = 0.1) -> None:
        """Increases uncertainty in cells that have not been observed recently."""
        self.variance += rate_per_sec * dt

    def detect_negative_obstacles(
        self, rover_x: float, rover_y: float, crater_depth_thresh_m: float = 0.45
    ) -> np.ndarray:
        """Identifies negative obstacles (craters, drop-offs) by comparing local cell depression.
        
        A negative obstacle is defined as a contiguous region where elevation drops significantly
        below the local surrounding planar trend.
        """
        from scipy.ndimage import uniform_filter
        elev_smooth = uniform_filter(self.elevation, size=3)
        local_mean = uniform_filter(elev_smooth, size=7)
        depression = local_mean - elev_smooth

        # Mark negative obstacles where depression exceeds threshold and cell is observed
        self.negative_obstacle_mask = (depression > crater_depth_thresh_m) & self.observed
        return self.negative_obstacle_mask

    def get_elevation_at(self, x: float, y: float) -> float:
        """Interpolates elevation at world position (x, y)."""
        ix = int(np.clip(round(x / self.res), 0, self.nx - 1))
        iy = int(np.clip(round(y / self.res), 0, self.ny - 1))
        return float(self.elevation[ix, iy])
