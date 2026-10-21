"""Multi-Criteria Traversability Cost Map Generator (TRL 6).

Combines:
1. Local surface gradient (slope in degrees)
2. Maximum step height discontinuity
3. High-frequency surface roughness (local elevation variance)
4. Obstacle clearance buffer (Euclidean distance field)
5. Regolith slip friction penalty
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from trl6_navigation import (
    MAX_TRAVERSABLE_SLOPE_DEG,
    MAX_STEP_HEIGHT_M,
    SAFETY_CLEARANCE_MARGIN_M,
)
from trl6_navigation.perception.elevation_mapping import ElevationMap25D


class TraversabilityEstimator:
    """Evaluates multi-criteria traversability cost maps from 2.5D elevation grids."""

    def __init__(
        self,
        max_slope_deg: float = MAX_TRAVERSABLE_SLOPE_DEG,
        max_step_m: float = MAX_STEP_HEIGHT_M,
        clearance_margin_m: float = SAFETY_CLEARANCE_MARGIN_M,
        w_slope: float = 0.35,
        w_step: float = 0.25,
        w_rough: float = 0.15,
        w_clear: float = 0.15,
        w_friction: float = 0.10
    ) -> None:
        self.max_slope = float(max_slope_deg)
        self.max_step = float(max_step_m)
        self.margin = float(clearance_margin_m)

        # Cost weights (sum to 1.0)
        self.w_slope = float(w_slope)
        self.w_step = float(w_step)
        self.w_rough = float(w_rough)
        self.w_clear = float(w_clear)
        self.w_friction = float(w_friction)

    def evaluate_traversability(
        self,
        elev_map: ElevationMap25D,
        regolith_friction: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Calculates multi-criteria traversability cost grid [0.0, 1.0]."""
        nx, ny = elev_map.nx, elev_map.ny
        res = elev_map.res

        # 1. Slope Gradient Computation
        # Infill unobserved cells using nearest neighbor extrapolation to prevent boundary cliffs
        raw_z = elev_map.elevation.copy()
        unobs_mask = (elev_map.hit_count == 0)
        if np.any(unobs_mask) and np.any(~unobs_mask):
            _, nearest_indices = distance_transform_edt(unobs_mask, return_indices=True)
            infilled_z = raw_z[nearest_indices[0], nearest_indices[1]]
            # Smooth infilled Voronoi boundaries to prevent step artifacts
            infilled_z = gaussian_filter(infilled_z, sigma=0.8)
            infilled_z[~unobs_mask] = raw_z[~unobs_mask]
        else:
            infilled_z = raw_z

        gz, gx = np.gradient(infilled_z, res)
        slope_rad = np.arctan(np.sqrt(gx**2 + gz**2))
        slope_deg = np.degrees(slope_rad)
        cost_slope = np.clip(slope_deg / self.max_slope, 0.0, 1.0)

        # 2. Maximum Step Discontinuity (3x3 kernel)
        z_padded = np.pad(infilled_z, 1, mode="edge")
        z_min = np.zeros((nx, ny), dtype=np.float64)
        z_max = np.zeros((nx, ny), dtype=np.float64)
        for di in range(3):
            for dj in range(3):
                sub = z_padded[di : di + nx, dj : dj + ny]
                if di == 0 and dj == 0:
                    z_min = sub.copy()
                    z_max = sub.copy()
                else:
                    z_min = np.minimum(z_min, sub)
                    z_max = np.maximum(z_max, sub)
        step_height = z_max - z_min
        cost_step = np.clip(step_height / self.max_step, 0.0, 1.0)

        # 3. Surface Roughness (Local Height Variance)
        cost_roughness = np.clip(np.sqrt(elev_map.variance) / 0.15, 0.0, 1.0)

        # 4. Obstacle Clearance Field
        lethal_combined = elev_map.obstacle_mask | elev_map.negative_obstacle_mask
        if np.any(lethal_combined):
            dist_pixels = distance_transform_edt(~lethal_combined)
            dist_m = dist_pixels * res
        else:
            dist_m = np.ones((nx, ny), dtype=np.float64) * 10.0

        # Clearance cost decays exponentially outside vehicle safety buffer
        cost_clearance = np.exp(-np.maximum(0.0, dist_m - self.margin) / 0.50)

        # 5. Terramechanical Friction Penalty
        if regolith_friction is not None:
            cost_friction = np.clip((1.0 - regolith_friction) / 0.65, 0.0, 1.0)
        else:
            cost_friction = np.zeros((nx, ny), dtype=np.float64)

        # Weighted Traversal Cost Combination
        cost_map = (
            self.w_slope * cost_slope
            + self.w_step * cost_step
            + self.w_rough * cost_roughness
            + self.w_clear * cost_clearance
            + self.w_friction * cost_friction
        )

        # Hard Lethal Obstacle Clamping (Cost = 1.0)
        # Apply lethal flags strictly to observed cells or unobserved boundaries
        has_hits = np.any(elev_map.hit_count > 0)
        observed_mask = (elev_map.hit_count > 0) if has_hits else np.ones((nx, ny), dtype=bool)

        lethal_slope = (slope_deg > self.max_slope) & observed_mask
        lethal_step = (step_height > self.max_step) & observed_mask

        lethal_mask = lethal_combined | lethal_slope | lethal_step
        cost_map[lethal_mask] = 1.0

        return {
            "cost_map": cost_map,
            "slope_deg": slope_deg,
            "step_height_m": step_height,
            "clearance_dist_m": dist_m,
            "lethal_mask": lethal_mask,
            "cost_slope": cost_slope,
            "cost_clearance": cost_clearance,
        }
