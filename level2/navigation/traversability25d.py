"""2.5D Terrain and Traversability Cost Map Builder.
Chapter 210 / Part 12 Task 102.
Combines elevation, slope, roughness, step height, perception risk, and depth validity.
"""
import numpy as np
from scipy import ndimage as ndi


def build_traversability_25d(elevation: np.ndarray, hazard_risk: np.ndarray,
                             uncertainty: np.ndarray, seen: np.ndarray,
                             cell_size_m: float = 0.25,
                             w: dict = None, allow_unknown: bool = False,
                             max_slope_deg: float = 20.0,
                             max_step_m: float = 0.20) -> dict:
    """Constructs 2.5D traversability cost grid and hard blocked mask.
    
    Formula (Chapter 210.3):
        c(x) = w_d + w_r*r(x) + w_u*u(x) + w_e*(1 + k_s*s(x)) + w_g*g(x)
    """
    if w is None:
        w = dict(d=1.0, r=3.0, u=2.0, e=1.0, ks=0.5, g=1.5, r_block=0.30, u_block=0.35, p_budget=0.50)
        
    H, W = elevation.shape
    
    # 1. Slope estimation
    gy, gx = np.gradient(elevation, cell_size_m)
    slope_rad = np.arctan(np.hypot(gx, gy))
    slope_deg = np.degrees(slope_rad)
    
    # 2. Roughness estimation (local std in 3x3 window)
    mean_e = ndi.uniform_filter(elevation, size=3)
    sq_e = ndi.uniform_filter(elevation**2, size=3)
    roughness = np.sqrt(np.maximum(0.0, sq_e - mean_e**2)) / cell_size_m
    
    # 3. Step height calculation (max elevation difference across 4-neighbors)
    step_h = np.zeros((H, W), dtype=np.float32)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        shifted = ndi.shift(elevation, (dy, dx), order=1, mode="nearest")
        step_h = np.maximum(step_h, np.abs(shifted - elevation))
        
    # 4. Multi-criteria cell cost c(x)
    base_cost = (
        w["d"] +
        w["r"] * hazard_risk +
        w["u"] * uncertainty +
        w.get("e", 1.0) * (1.0 + w.get("ks", 0.5) * slope_rad) +
        w.get("g", 1.5) * roughness
    )
    
    # 5. Hard blocking rule
    # Blocked if: class risk > r_block, slope > max_slope, step > max_step, unc > u_block, or unobserved
    is_blocked = (
        (hazard_risk >= w["r_block"]) |
        (slope_deg > max_slope_deg) |
        (step_h > max_step_m) |
        (seen & (uncertainty >= w["u_block"]))
    )
    if not allow_unknown:
        is_blocked |= (~seen)
        
    return {
        "cost_map": base_cost.astype(np.float32),
        "blocked_map": is_blocked.astype(bool),
        "slope_deg": slope_deg.astype(np.float32),
        "roughness": roughness.astype(np.float32),
        "step_height_m": step_h.astype(np.float32)
    }
