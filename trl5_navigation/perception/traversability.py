"""Multi-Criteria Traversability Estimation Engine (TRL 5).

Evaluates terrain slope, surface roughness, step height, obstacle clearance,
and regolith traction to generate a continuous traversability cost map in [0, 1].
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np
from scipy.ndimage import distance_transform_edt

from trl5_navigation import MAX_TRAVERSABLE_SLOPE_DEG, MAX_STEP_HEIGHT_M, SAFETY_CLEARANCE_MARGIN_M
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


class TraversabilityEstimator:
    """Computes calibrated traversability cost maps from 2.5D elevation models."""

    def __init__(
        self,
        max_slope_deg: float = MAX_TRAVERSABLE_SLOPE_DEG,
        max_step_m: float = MAX_STEP_HEIGHT_M,
        clearance_margin_m: float = SAFETY_CLEARANCE_MARGIN_M,
        roughness_threshold_m: float = 0.15,
        w_slope: float = 0.35,
        w_rough: float = 0.15,
        w_step: float = 0.25,
        w_clearance: float = 0.25
    ) -> None:
        self.max_slope_deg = float(max_slope_deg)
        self.max_step_m = float(max_step_m)
        self.clearance_m = float(clearance_margin_m)
        self.rough_thresh = float(roughness_threshold_m)

        # Cost weighting factors (sum = 1.0)
        self.w_slope = float(w_slope)
        self.w_rough = float(w_rough)
        self.w_step = float(w_step)
        self.w_clearance = float(w_clearance)

    def evaluate_traversability(
        self,
        elevation_map: ElevationMap25D,
        regolith_friction_map: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """Calculates multi-criteria traversability layers and combined cost map in [0, 1]."""
        elev = elevation_map.elevation.copy()
        res = elevation_map.res
        nx, ny = elev.shape

        # Infill unobserved cells with nearest observed elevation to avoid false boundary cliff artifacts
        unobs = elevation_map.hit_count == 0
        if np.any(unobs) and np.any(~unobs):
            indices = distance_transform_edt(unobs, return_distances=False, return_indices=True)
            elev[unobs] = elev[tuple(indices[:, unobs])]

        # Smooth elevation grid slightly to prevent numerical gradient noise from voxel discretization
        from scipy.ndimage import gaussian_filter
        elev_smooth = gaussian_filter(elev, sigma=0.8)

        # 1. Slope Layer: evaluate numerical gradient magnitude on smoothed DEM
        gy, gx = np.gradient(elev_smooth, res, res)
        grad_mag = np.sqrt(gx**2 + gy**2)
        slope_rad = np.arctan(grad_mag)
        slope_deg = np.degrees(slope_rad)

        # Normalized slope cost in [0, 1]
        c_slope = np.clip(slope_deg / self.max_slope_deg, 0.0, 1.0)
        # Lethal slope mask: consider observed cells (or all cells if prior DEM fixture without hit_count)
        if np.all(elevation_map.hit_count == 0):
            observed_mask = np.ones((nx, ny), dtype=bool)
        else:
            observed_mask = elevation_map.hit_count > 0
        lethal_slope = (slope_deg > self.max_slope_deg) & observed_mask

        # 2. Step Height Layer: max neighbor elevation jump
        step_map = np.zeros((nx, ny), dtype=np.float64)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                shifted = np.roll(np.roll(elev_smooth, dx, axis=0), dy, axis=1)
                diff = np.abs(elev_smooth - shifted)
                step_map = np.maximum(step_map, diff)

        c_step = np.clip(step_map / self.max_step_m, 0.0, 1.0)
        lethal_step = (step_map > self.max_step_m) & observed_mask

        # 3. Roughness Layer: local elevation standard deviation
        # Use variance layer from elevation map where available
        c_roughness = np.clip(np.sqrt(elevation_map.variance) / self.rough_thresh, 0.0, 1.0)

        # 4. Obstacle Clearance Layer: Euclidean distance transform from obstacle boundaries
        combined_lethal = (
            elevation_map.obstacle_mask
            | elevation_map.negative_obstacle_mask
            | lethal_slope
            | lethal_step
        )

        # Distance transform (in meters)
        clearance_cells = distance_transform_edt(~combined_lethal)
        clearance_dist_m = clearance_cells * res

        # Clearance cost decays smoothly from 1.0 at obstacle boundary to 0.0 at clearance_m
        c_clearance = np.clip(1.0 - (clearance_dist_m / (self.clearance_m * 2.0)), 0.0, 1.0)

        # 5. Regolith Traction Layer (optional)
        c_traction = np.zeros((nx, ny), dtype=np.float64)
        if regolith_friction_map is not None:
            if regolith_friction_map.shape == (nx, ny):
                f_map = regolith_friction_map
            else:
                from scipy.ndimage import zoom
                zoom_factors = (nx / regolith_friction_map.shape[0], ny / regolith_friction_map.shape[1])
                f_map = zoom(regolith_friction_map, zoom_factors, order=0)
            mu_nom = 0.85
            c_traction = np.clip((mu_nom - f_map) / mu_nom, 0.0, 1.0)

        # Composite Traversability Cost Map
        cost_map = (
            self.w_slope * c_slope
            + self.w_step * c_step
            + self.w_rough * c_roughness
            + self.w_clearance * c_clearance
            + 0.15 * c_traction
        )
        cost_map = np.clip(cost_map, 0.0, 1.0)

        # Enforce lethal obstacles strictly at cost 1.0
        cost_map[combined_lethal] = 1.0

        return {
            "cost_map": cost_map,
            "slope_deg": slope_deg,
            "step_map": step_map,
            "clearance_dist_m": clearance_dist_m,
            "lethal_mask": combined_lethal,
            "c_slope": c_slope,
            "c_step": c_step,
            "c_clearance": c_clearance,
        }
