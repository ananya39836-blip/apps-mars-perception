"""Level 1 Route Audit and Path Verification.
Part 6 Appendix AL & Part 8 Chapter 129.5 (Task 67).
"""
import numpy as np


def route_audit(path: list, blocked: np.ndarray) -> list:
    """Audit planned route against the LATEST cell map. Returns list of defect reasons."""
    if not path:
        return ["empty path"]
    bad = []
    # Check that planned steps do not intersect currently blocked cells
    for c in path[1:]:
        if blocked[c[0], c[1]]:
            bad.append(f"cell {c} blocked")
            
    # Check that steps are strictly 8-connected adjacent (no teleporting)
    for a, b in zip(path, path[1:]):
        if max(abs(a[0] - b[0]), abs(a[1] - b[1])) != 1:
            bad.append(f"jump {a}->{b}")
            
    return bad


def audit_route_pixel(path: list, unsafe_px: np.ndarray, slope_px: np.ndarray,
                      unc_px: np.ndarray, c: int, footprint_px: int,
                      max_unsafe_frac: float = 0.0, max_slope: float = 0.35, unc_bound: float = 0.35) -> dict:
    """Audit planned route against image-resolution pixel tensors."""
    H, W = unsafe_px.shape
    reasons = []
    worst_u, worst_s, n_unc = 0.0, 0.0, 0
    for (r, q) in path:
        y0, y1 = max(r * c - footprint_px, 0), min((r + 1) * c + footprint_px, H)
        x0, x1 = max(q * c - footprint_px, 0), min((q + 1) * c + footprint_px, W)
        u = float(unsafe_px[y0:y1, x0:x1].mean())
        s = float(np.nanmax(slope_px[y0:y1, x0:x1])) if slope_px is not None else 0.0
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
        n_cells=len(path),
        worst_unsafe_fraction=worst_u,
        worst_slope=worst_s,
        n_uncertain_cells=n_unc,
        reasons=reasons[:20]
    )
