"""Kinodynamic Primitive Local Planner and Swept Footprint Auditor.
Chapter 211 & Appendix CO/CP (Part 12 Task 103).
"""
import math
from typing import List, Tuple, Dict
import numpy as np


def arc_pose(k: float, length: float) -> Tuple[float, float, float]:
    """End pose (dx, dy, dtheta) in start frame for curvature k and arc length.
    Formula from Appendix CO.
    """
    if abs(k) < 1e-9:
        return (float(length), 0.0, 0.0)
    th = k * length
    dx = math.sin(th) / k
    dy = (1.0 - math.cos(th)) / k
    return (float(dx), float(dy), float(th))


def generate_primitives(k_max: float = 1.0, length_m: float = 1.50,
                        n_primitives: int = 7) -> List[Dict]:
    """Generate fixed candidate motion primitive library across curvature span [-k_max, k_max]."""
    curvatures = np.linspace(-k_max, k_max, n_primitives)
    prims = []
    for idx, k in enumerate(curvatures):
        dx, dy, dth = arc_pose(k, length_m)
        prims.append({
            "index": idx,
            "curvature": float(k),
            "length_m": float(length_m),
            "dx": float(dx),
            "dy": float(dy),
            "dtheta": float(dth)
        })
    return prims


def rasterize_swept_footprint(x0_m: float, y0_m: float, th0_rad: float,
                              k: float, length_m: float, body_length: float = 1.20,
                              body_width: float = 0.90, cell_size_m: float = 0.25,
                              n_samples: int = 8) -> List[Tuple[int, int]]:
    """Rasterizes the continuous vehicle footprint swept along an arc primitive into grid cell indices."""
    swept_cells = set()
    s_steps = np.linspace(0.0, length_m, n_samples)
    
    half_l = body_length / 2.0
    half_w = body_width / 2.0
    corners_local = [
        (half_l, half_w), (half_l, -half_w),
        (-half_l, half_w), (-half_l, -half_w),
        (0.0, 0.0)
    ]
    
    for s in s_steps:
        # Arc pose relative to start
        dx_rel, dy_rel, dth_rel = arc_pose(k, s)
        # Transform to world frame
        cos_th = math.cos(th0_rad)
        sin_th = math.sin(th0_rad)
        cx = x0_m + dx_rel * cos_th - dy_rel * sin_th
        cy = y0_m + dx_rel * sin_th + dy_rel * cos_th
        cth = th0_rad + dth_rel
        
        # Transform vehicle corners
        cos_c = math.cos(cth)
        sin_c = math.sin(cth)
        for lx, ly in corners_local:
            wx = cx + lx * cos_c - ly * sin_c
            wy = cy + lx * sin_c + ly * cos_c
            gx = int(round(wx / cell_size_m))
            gy = int(round(wy / cell_size_m))
            swept_cells.add((gy, gx))
            
    return list(swept_cells)


def plan_primitive(pose: Tuple[float, float, float], goal_x_m: float, goal_y_m: float,
                   cost_map: np.ndarray, blocked_map: np.ndarray,
                   hazard_risk: np.ndarray = None, p_budget: float = 0.50,
                   cell_size_m: float = 0.25, k_max: float = 1.00,
                   prim_length_m: float = 1.50, body_length: float = 1.20,
                   body_width: float = 0.90, w_progress: float = 2.0,
                   w_heading: float = 0.50) -> dict:
    """Evaluate candidate kinodynamic primitives and select the optimal collision-free arc.
    
    Returns:
        dict(status, selected_primitive, score, swept_cells, p_proxy)
        status vocabulary: 'ok' | 'no_primitive' | 'rejected_budget' | 'invalid_input'
    """
    x, y, th = pose
    if not (math.isfinite(x) and math.isfinite(y) and math.isfinite(th)):
        return dict(status="invalid_input", primitive=None, score=None, swept_cells=[], p_proxy=None)
        
    H, W = cost_map.shape
    primitives = generate_primitives(k_max=k_max, length_m=prim_length_m, n_primitives=7)
    
    current_dist_to_goal = math.hypot(goal_x_m - x, goal_y_m - y)
    
    candidates = []
    for prim in primitives:
        k = prim["curvature"]
        dx_loc, dy_loc, dth_loc = prim["dx"], prim["dy"], prim["dtheta"]
        
        # End pose in world coordinates
        end_x = x + dx_loc * math.cos(th) - dy_loc * math.sin(th)
        end_y = y + dx_loc * math.sin(th) + dy_loc * math.cos(th)
        end_th = th + dth_loc
        
        # Swept footprint rasterization
        swept = rasterize_swept_footprint(
            x, y, th, k, prim_length_m,
            body_length=body_length, body_width=body_width,
            cell_size_m=cell_size_m
        )
        
        # Check collision against blocked map and bounds
        is_blocked = False
        summed_cost = 0.0
        risk_vals = []
        for gy, gx in swept:
            if not (0 <= gy < H and 0 <= gx < W):
                is_blocked = True
                break
            if blocked_map[gy, gx]:
                is_blocked = True
                break
            summed_cost += cost_map[gy, gx]
            if hazard_risk is not None:
                risk_vals.append(float(hazard_risk[gy, gx]))
                
        if is_blocked:
            continue
            
        # Route risk budget check
        p_proxy = 0.0
        if risk_vals:
            p_proxy = float(1.0 - np.prod([1.0 - r for r in risk_vals]))
            if p_proxy > p_budget:
                continue
                
        # Metric progress towards goal
        new_dist_to_goal = math.hypot(goal_x_m - end_x, goal_y_m - end_y)
        progress = current_dist_to_goal - new_dist_to_goal
        
        # Heading alignment towards goal
        desired_heading = math.atan2(goal_y_m - end_y, goal_x_m - end_x)
        heading_error = abs((end_th - desired_heading + math.pi) % (2 * math.pi) - math.pi)
        
        # Composite score: lower is better
        score = float(summed_cost - w_progress * progress + w_heading * heading_error)
        candidates.append({
            "primitive": prim,
            "score": score,
            "swept": swept,
            "p_proxy": p_proxy,
            "end_pose": (end_x, end_y, end_th)
        })
        
    if not candidates:
        return dict(status="no_primitive", primitive=None, score=None, swept_cells=[], p_proxy=None)
        
    # Pick lowest score primitive (tie-break by index)
    best = min(candidates, key=lambda c: (c["score"], c["primitive"]["index"]))
    return dict(
        status="ok",
        primitive=best["primitive"],
        score=best["score"],
        swept_cells=best["swept"],
        p_proxy=best["p_proxy"],
        end_pose=best["end_pose"]
    )
