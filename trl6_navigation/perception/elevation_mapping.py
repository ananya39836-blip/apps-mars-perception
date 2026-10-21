"""2.5D Elevation Grid Mapping with Kalman Variance & Dynamic Obstacle Clearing (TRL 6).

Implements:
1. Recursive 1D Kalman elevation fusion per grid cell (elevation Z and variance sigma_z^2)
2. Distance-normalized radial negative obstacle detection (craters, drop-offs)
3. Dynamic obstacle persistence, exponential temporal decay, and ray-clearing
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np


class ElevationMap25D:
    """Manages 2.5D continuous local elevation grid with spatial uncertainty pooling."""

    def __init__(
        self,
        size_x_m: float = 60.0,
        size_y_m: float = 60.0,
        resolution_m: float = 0.20,
        default_variance: float = 1.0,
        measurement_variance: float = 0.04
    ) -> None:
        self.size_x = float(size_x_m)
        self.size_y = float(size_y_m)
        self.res = float(resolution_m)
        self.nx = int(round(self.size_x / self.res))
        self.ny = int(round(self.size_y / self.res))
        self.var_meas = float(measurement_variance)

        # Elevation (mean Z) and variance (sigma_z^2)
        self.elevation = np.zeros((self.nx, self.ny), dtype=np.float64)
        self.variance = np.ones((self.nx, self.ny), dtype=np.float64) * float(default_variance)
        self.hit_count = np.zeros((self.nx, self.ny), dtype=np.int32)

        # Hazard classification layers
        self.obstacle_mask = np.zeros((self.nx, self.ny), dtype=bool)
        self.negative_obstacle_mask = np.zeros((self.nx, self.ny), dtype=bool)
        self.obstacle_confidence = np.zeros((self.nx, self.ny), dtype=np.float64)

    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Converts continuous world coordinates (x, y) to discrete grid indices (ix, iy)."""
        ix = int(round(x / self.res))
        iy = int(round(y / self.res))
        return ix, iy

    def grid_to_world(self, ix: int, iy: int) -> Tuple[float, float]:
        """Converts discrete grid indices to world coordinates."""
        return float(ix * self.res), float(iy * self.res)

    def is_in_bounds(self, ix: int, iy: int) -> bool:
        """Audits whether grid cell (ix, iy) lies within the DEM bounds."""
        return 0 <= ix < self.nx and 0 <= iy < self.ny

    def update_from_point_cloud(self, points_world: np.ndarray, sensor_origin_w: np.ndarray) -> None:
        """Fuses 3D point observations into 2.5D cells using 1D Kalman filters."""
        if len(points_world) == 0:
            return

        for idx in range(points_world.shape[0]):
            wx = points_world[idx, 0]
            wy = points_world[idx, 1]
            wz = points_world[idx, 2]

            ix, iy = self.world_to_grid(wx, wy)
            if not self.is_in_bounds(ix, iy):
                continue

            # Kalman measurement update
            if self.hit_count[ix, iy] == 0:
                self.elevation[ix, iy] = wz
                self.variance[ix, iy] = self.var_meas
            else:
                var_prior = self.variance[ix, iy]
                K_gain = var_prior / (var_prior + self.var_meas)
                self.elevation[ix, iy] += K_gain * (wz - self.elevation[ix, iy])
                self.variance[ix, iy] = (1.0 - K_gain) * var_prior

            self.hit_count[ix, iy] += 1

    def mark_obstacles(self, obstacle_points: np.ndarray) -> None:
        """Marks grid cells containing confirmed positive obstacle points."""
        if len(obstacle_points) == 0:
            return

        for idx in range(obstacle_points.shape[0]):
            ix, iy = self.world_to_grid(obstacle_points[idx, 0], obstacle_points[idx, 1])
            if self.is_in_bounds(ix, iy):
                self.obstacle_mask[ix, iy] = True
                self.obstacle_confidence[ix, iy] = min(1.0, self.obstacle_confidence[ix, iy] + 0.35)

    def detect_negative_obstacles(
        self,
        rover_pos_w: np.ndarray,
        max_lookahead_m: float = 12.0,
        drop_threshold_m: Optional[float] = None
    ) -> None:
        """Detects negative obstacles (craters, drop-offs) from distance-normalized steep downward drops."""
        rx, ry = float(rover_pos_w[0]), float(rover_pos_w[1])
        drop_thresh = float(drop_threshold_m) if drop_threshold_m is not None else max(0.12, self.res * 0.50)

        # Radial ray scan from rover position
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
                        # Distance-normalized negative obstacle detection
                        if delta_d <= 1.5 * self.res:
                            if delta_z > drop_thresh:
                                self.negative_obstacle_mask[ix, iy] = True
                        else:
                            if delta_z > drop_thresh and (delta_z / delta_d) > 0.45:
                                self.negative_obstacle_mask[ix, iy] = True
                    prev_z = curr_z
                    prev_dist = dist

    def decay_transient_obstacles(self, decay_rate: float = 0.05) -> None:
        """Applies exponential temporal decay to transient obstacle confidence."""
        self.obstacle_confidence = np.maximum(0.0, self.obstacle_confidence - float(decay_rate))
        # Clear obstacle mask if confidence falls below threshold
        self.obstacle_mask = self.obstacle_confidence > 0.15

    def clear_dynamic_obstacles_along_rays(
        self,
        rover_pos_w: np.ndarray,
        clean_points_world: np.ndarray
    ) -> None:
        """Clears transient obstacle markings along observed line-of-sight rays to verified ground returns."""
        if len(clean_points_world) == 0:
            return

        rx, ry = float(rover_pos_w[0]), float(rover_pos_w[1])
        step_m = self.res * 1.5

        # Subsample clean points for performance
        subsample = clean_points_world[::4] if len(clean_points_world) > 100 else clean_points_world
        for pt in subsample:
            gx, gy = pt[0], pt[1]
            dist = math.hypot(gx - rx, gy - ry)
            if dist <= 0.5:
                continue

            num_steps = int(dist / step_m)
            dx = (gx - rx) / dist * step_m
            dy = (gy - ry) / dist * step_m

            for s in range(1, num_steps):
                cx = rx + s * dx
                cy = ry + s * dy
                ix, iy = self.world_to_grid(cx, cy)
                if self.is_in_bounds(ix, iy):
                    # Ray passes through clear ground: reduce obstacle confidence
                    self.obstacle_confidence[ix, iy] = max(0.0, self.obstacle_confidence[ix, iy] - 0.20)
                    if self.obstacle_confidence[ix, iy] < 0.15:
                        self.obstacle_mask[ix, iy] = False
