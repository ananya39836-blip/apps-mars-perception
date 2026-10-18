"""Route audit module for independent check of planned routes against system's own maps.
Chapter 56, Appendix V (Part 4) - Task 24.
"""
import numpy as np


def audit_route(route, unsafe_px: np.ndarray, slope_px: np.ndarray, unc_px: np.ndarray,
                c: int, footprint_px: int,
                max_unsafe_frac: float = 0.0, max_slope: float = 0.35, unc_bound: float = 0.35):
    """Independent check of a planned route against the SYSTEM'S OWN pixel maps.
    route: list of (row, col) cells. Maps are HxW at image resolution.
    This catches planner or cell-reduction errors. It cannot catch hazards the
    perception layer missed; that is what ground-truth evaluation is for.
    """
    H, W = unsafe_px.shape
    reasons = []
    worst_u, worst_s, n_unc = 0.0, 0.0, 0
    for (r, q) in route:
        y0, y1 = max(r * c - footprint_px, 0), min((r + 1) * c + footprint_px, H)
        x0, x1 = max(q * c - footprint_px, 0), min((q + 1) * c + footprint_px, W)
        u = float(unsafe_px[y0:y1, x0:x1].mean())
        s = float(np.nanmax(slope_px[y0:y1, x0:x1]))
        k = float(unc_px[y0:y1, x0:x1].mean())
        worst_u, worst_s = max(worst_u, u), max(worst_s, s)
        if u > max_unsafe_frac:
            reasons.append(f"cell {(r, q)}: unsafe fraction {u:.2f}")
        if s > max_slope:
            reasons.append(f"cell {(r, q)}: slope {s:.2f}")
        if k > unc_bound:
            n_unc += 1
            reasons.append(f"cell {(r, q)}: uncertainty {k:.2f}")
    return dict(
        passed=len(reasons) == 0,
        n_cells=len(route),
        worst_unsafe_fraction=worst_u,
        worst_slope=worst_s,
        n_uncertain_cells=n_unc,
        reasons=reasons[:20]
    )
