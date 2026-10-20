"""2.5D Local Elevation Grid & Uncertainty Mapping (TRL 5).

Maintains a 2.5D spatial grid representing local terrain elevation mean,
height variance uncertainty sigma_z^2, observed confidence, and negative obstacle drop-offs.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np


class ElevationMap25D:
    """Represents a 2.5D local elevation map with probabilistic uncertainty."""

    def __init__(
        self,
        size_x_m: float = 60.0,
        size_y_m: float = 60.0,
        resolution_m: float = 0.20,
        prior_elevation: float = 0.0
    ) -> None:
        self.size_x = float(size_x_m)
        self.size_y = float(size_y_m)
        self.res = float(resolution_m)
        self.nx = int(round(self.size_x / self.res))
        self.ny = int(round(self.size_y / self.res))

        # Grid layers
        self.elevation = np.full((self.nx, self.ny), float(prior_elevation), dtype=np.float64)
        self.variance = np.full((self.nx, self.ny), 1.0, dtype=np.float64)  # High initial uncertainty
        self.hit_count = np.zeros((self.nx, self.ny), dtype=np.int32)
        self.obstacle_mask = np.zeros((self.nx, self.ny), dtype=bool)
        self.negative_obstacle_mask = np.zeros((self.nx, self.ny), dtype=bool)

        # Coordinate arrays
        self.x_coords = np.linspace(0.0, self.size_x, self.nx)
        self.y_coords = np.linspace(0.0, self.size_y, self.ny)

    def world_to_grid(self, x_m: float, y_m: float) -> Tuple[int, int]:
        """Converts continuous world coordinates (x, y) to discrete grid indices (ix, iy)."""
        ix = int(round(x_m / self.res))
        iy = int(round(y_m / self.res))
        return ix, iy

    def grid_to_world(self, ix: int, iy: int) -> Tuple[float, float]:
        """Converts discrete grid indices (ix, iy) to continuous world coordinates (x, y)."""
        return float(ix * self.res), float(iy * self.res)

    def is_in_bounds(self, ix: int, iy: int) -> bool:
        """Checks if discrete indices are within map boundaries."""
        return 0 <= ix < self.nx and 0 <= iy < self.ny

    def update_from_point_cloud(
        self,
        points_world: np.ndarray,
        sensor_origin_world: np.ndarray,
        meas_variance: float = 0.01
    ) -> None:
        """Fuses new point returns using running Kalman-style elevation and variance updates."""
        if points_world.size == 0:
            return

        ix_arr = np.clip((points_world[:, 0] / self.res).astype(int), 0, self.nx - 1)
        iy_arr = np.clip((points_world[:, 1] / self.res).astype(int), 0, self.ny - 1)
        z_arr = points_world[:, 2]

        for i in range(len(points_world)):
            ix, iy, z = ix_arr[i], iy_arr[i], z_arr[i]

            if self.hit_count[ix, iy] == 0:
                self.elevation[ix, iy] = z
                self.variance[ix, iy] = meas_variance
                self.hit_count[ix, iy] = 1
            else:
                # Recursive Kalman update for scalar elevation
                p_prior = self.variance[ix, iy]
                k_gain = p_prior / (p_prior + meas_variance)
                self.elevation[ix, iy] += k_gain * (z - self.elevation[ix, iy])
                self.variance[ix, iy] = (1.0 - k_gain) * p_prior
                self.hit_count[ix, iy] += 1

    def mark_obstacles(self, obstacle_points_world: np.ndarray) -> None:
        """Marks grid cells containing confirmed obstacle point returns as lethal."""
        if obstacle_points_world.size == 0:
            return
        ix_arr = np.clip((obstacle_points_world[:, 0] / self.res).astype(int), 0, self.nx - 1)
        iy_arr = np.clip((obstacle_points_world[:, 1] / self.res).astype(int), 0, self.ny - 1)
        for i in range(len(obstacle_points_world)):
            self.obstacle_mask[ix_arr[i], iy_arr[i]] = True

    def detect_negative_obstacles(
        self,
        rover_pos_w: np.ndarray,
        max_lookahead_m: float = 12.0,
        drop_threshold_m: Optional[float] = None
    ) -> None:
        """Detects negative obstacles (craters, drop-offs) from steep downward slope drops."""
        rx, ry = float(rover_pos_w[0]), float(rover_pos_w[1])
        drop_thresh = float(drop_threshold_m) if drop_threshold_m is not None else max(0.08, self.res * 0.45)

        # Radial scan from rover position to detect steep downward cliffs/craters
        for angle in np.linspace(0.0, 2 * math.pi, 72, endpoint=False):
            prev_z: Optional[float] = None
            prev_dist: Optional[float] = None
            for dist in np.arange(0.5, max_lookahead_m, self.res):
                px = rx + dist * math.cos(angle)
                py = ry + dist * math.sin(angle)
                ix, iy = self.world_to_grid(px, py)
                if not self.is_in_bounds(ix, iy):
                    break

                if self.hit_count[ix, iy] > 0:
                    curr_z = self.elevation[ix, iy]
                    if prev_z is not None and prev_dist is not None:
                        delta_d = dist - prev_dist
                        delta_z = prev_z - curr_z
                        if delta_d <= 1.5 * self.res:
                            if delta_z > drop_thresh:
                                self.negative_obstacle_mask[ix, iy] = True
                        else:
                            if delta_z > drop_thresh and (delta_z / delta_d) > 0.45:
                                self.negative_obstacle_mask[ix, iy] = True
                    prev_z = curr_z
                    prev_dist = dist
