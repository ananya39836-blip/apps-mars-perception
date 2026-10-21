"""Multi-Criteria Traversability Estimation Engine (TRL 7).

Evaluates geometric, terramechanic, and perceptual hazard factors across the DEM:
- Gradient / Slope angle relative to rover climb limit
- Step obstacle height relative to wheel radius (0.25m)
- Surface micro-roughness (elevation variance)
- Negative obstacle drop-off hazard
- Solar shadow illumination degradation
- Regolith wheel slip penalty
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy.ndimage import binary_dilation, uniform_filter, maximum_filter, minimum_filter

from trl7_navigation import (
    MAX_TRAVERSABLE_SLOPE_DEG,
    MAX_STEP_HEIGHT_M,
    ROVER_WIDTH_M,
    SAFETY_CLEARANCE_MARGIN_M,
)
from trl7_navigation.perception.elevation_mapping import ElevationMap25D


class TraversabilityEstimator:
    """Computes continuous cost map [0.0, 1.0] and binary impassable hazard mask."""

    def __init__(
        self,
        max_slope_deg: float = MAX_TRAVERSABLE_SLOPE_DEG,
        max_step_m: float = MAX_STEP_HEIGHT_M,
        clearance_margin_m: float = SAFETY_CLEARANCE_MARGIN_M,
    ) -> None:
        self.max_slope_deg = float(max_slope_deg)
        self.max_step_m = float(max_step_m)
        self.clearance_margin_m = float(clearance_margin_m)

    def evaluate(
        self,
        elevation_map: ElevationMap25D,
        shadow_mask: Optional[np.ndarray] = None,
        friction_grid: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
        """Evaluates traversability costs across the elevation map.
        
        Returns:
            Tuple[cost_map, impassable_mask, debug_components]
        """
        elev = elevation_map.elevation
        res = elevation_map.res

        # 1. Macroscopic slope computation over vehicle-scale baseline (5x5 cells = 1.25m)
        elev_macro = uniform_filter(elev, size=5)
        dz_dx, dz_dy = np.gradient(elev_macro, res)
        slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
        slope_deg = np.degrees(slope_rad)

        c_slope = np.clip(slope_deg / self.max_slope_deg, 0.0, 1.0) ** 2

        # 2. Step obstacle height: residual height above macroscopic slope
        step_height = np.maximum(0.0, elev - elev_macro)
        c_step = np.clip(step_height / self.max_step_m, 0.0, 1.0) ** 2

        # 3. Micro-roughness (local variance in 5x5 window)
        mean_elev = uniform_filter(elev, size=5)
        mean_sq = uniform_filter(elev**2, size=5)
        roughness = np.sqrt(np.maximum(0.0, mean_sq - mean_elev**2))
        c_rough = np.clip(roughness / 0.18, 0.0, 1.0)

        # 4. Negative obstacle penalty
        c_negative = np.zeros_like(elev)
        c_negative[elevation_map.negative_obstacle_mask] = 1.0

        # 5. Shadow penalty (if supplied)
        c_shadow = np.zeros_like(elev)
        if shadow_mask is not None and shadow_mask.shape == elev.shape:
            c_shadow[shadow_mask] = 0.25  # moderate penalty for low-visibility shadowed ground

        # 6. Regolith slip penalty (if supplied)
        c_slip = np.zeros_like(elev)
        if friction_grid is not None and friction_grid.shape == elev.shape:
            c_slip = np.clip((0.85 - friction_grid) / 0.60, 0.0, 1.0)

        # Composite continuous cost map: weighted sum
        total_cost = (
            0.35 * c_slope
            + 0.35 * c_step
            + 0.15 * c_rough
            + 0.25 * c_negative
            + 0.10 * c_shadow
            + 0.15 * c_slip
        )
        total_cost = np.clip(total_cost, 0.0, 1.0)

        # Impassable condition: slope > limit OR step > wheel radius OR confirmed crater
        impassable_raw = (
            (slope_deg >= self.max_slope_deg)
            | (step_height >= self.max_step_m)
            | elevation_map.negative_obstacle_mask
        )

        # Dilate impassable hazard cells by safety clearance margin
        inflation_radius_m = self.clearance_margin_m
        inflation_cells = max(1, int(round(inflation_radius_m / res)))
        kernel = np.ones((2 * inflation_cells + 1, 2 * inflation_cells + 1), dtype=bool)

        impassable_inflated = binary_dilation(impassable_raw, structure=kernel)

        # Saturate cost in impassable zones
        total_cost[impassable_inflated] = 1.0

        components = {
            "slope_deg": slope_deg,
            "step_height_m": step_height,
            "roughness_m": roughness,
            "c_slope": c_slope,
            "c_step": c_step,
            "c_shadow": c_shadow,
            "c_slip": c_slip,
        }

        return total_cost, impassable_inflated, components
