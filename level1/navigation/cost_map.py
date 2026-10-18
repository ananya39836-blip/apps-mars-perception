"""Level 1 Cost Map Construction and Footprint Dilation.
Part 6 Appendix AK & Part 8 Appendix BE (Tasks 43 & 62).
"""
import numpy as np


def cell_cost(risk: np.ndarray, unc: np.ndarray, slope: np.ndarray, w: dict) -> np.ndarray:
    """Multi-criteria cell cost c = w_d + w_r*risk + w_u*unc + w_e*(1 + k_s*slope).
    All weights must be non-negative.
    """
    return (
        w["d"] +
        w["r"] * risk +
        w["u"] * unc +
        w.get("e", 0.0) * (1.0 + w.get("ks", 0.0) * slope)
    )


def blocked_map(risk: np.ndarray, unc: np.ndarray, known: np.ndarray, w: dict, allow_unknown: bool = False) -> np.ndarray:
    """Blocked if risk or uncertainty is too high; unknown cells stay blocked by default."""
    b = (risk >= w["r_block"]) | (known & (unc >= w["u_block"]))
    return b | ((~known) & (not allow_unknown))


def inflate(blocked: np.ndarray, r: int) -> np.ndarray:
    """Chebyshev square footprint dilation by radius r cells without boundary wrap."""
    if r <= 0:
        return blocked.copy()
    b = np.asarray(blocked, bool)
    out = b.copy()
    H, W = b.shape
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            sh = np.zeros_like(b)
            ys = slice(max(dy, 0), H + min(dy, 0))
            yd = slice(max(-dy, 0), H + min(-dy, 0))
            xs = slice(max(dx, 0), W + min(dx, 0))
            xd = slice(max(-dx, 0), W + min(-dx, 0))
            sh[ys, xs] = b[yd, xd]
            out |= sh
    return out
