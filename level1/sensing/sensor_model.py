"""Level 1 Sensor Model, Field of View, Pose Error, and Registration.
Part 6 Appendix AJ, Part 7 Appendix AV & Task 42/54.
"""
import math
import numpy as np
from scipy import ndimage as ndi


def range_miss_prob(dist: float, near: float = 0.02, far: float = 0.35, d_half: float = 8.0) -> float:
    """Fitted monotone miss probability growing with sensor-to-target distance."""
    return near + (far - near) * (1.0 - math.exp(-math.log(2.0) * dist / d_half))


def fov_mask(n: int, pos: tuple, heading: float, fov_deg: float, range_cells: float):
    """Cells inside a range-limited sector. heading in radians (0 = +col direction).
    Rover position itself is always included.
    """
    yy, xx = np.mgrid[:n, :n]
    dy, dx = yy - pos[0], xx - pos[1]
    d = np.hypot(dy, dx)
    ang = np.arctan2(dy, dx)
    diff = np.abs((ang - heading + np.pi) % (2 * np.pi) - np.pi)
    m = (d <= range_cells) & (diff <= np.radians(fov_deg) / 2.0)
    m[pos[0], pos[1]] = True
    return m, d


def observe(truth: np.ndarray, pos: tuple, heading: float, cfg: dict, rng, sensor_ok: bool = True):
    """Returns (unsafe_estimate, observed_mask, uncertainty).
    Error grows with distance. A failed sensor observes nothing.
    """
    n = truth.shape[0]
    z = np.zeros((n, n), bool)
    if not sensor_ok:
        return z, z.copy(), np.ones((n, n), dtype=float)
        
    m, d = fov_mask(n, pos, heading, cfg["fov_deg"], cfg["range"])
    frac = np.clip(d / max(cfg["range"], 1e-3), 0.0, 1.0)
    
    # Distance-dependent miss probability
    miss_p = cfg.get("miss0", 0.02) + cfg.get("miss_slope", 0.30) * frac
    miss = rng.random((n, n)) < miss_p
    fa = rng.random((n, n)) < cfg.get("false_alarm", 0.01)
    
    est = ((truth & ~miss) | fa) & m
    unc = np.where(m, 0.10 + 0.80 * frac, 1.0)
    return est, m, unc


def believed_pose(true_pos: tuple, sigma_cells: float, rng, n: int) -> tuple:
    """Believed pose = true pose + Gaussian noise (independent per step)."""
    if sigma_cells <= 0.0:
        return (int(true_pos[0]), int(true_pos[1]))
    e = np.rint(rng.normal(0, sigma_cells, 2)).astype(int)
    return (
        int(np.clip(true_pos[0] + e[0], 0, n - 1)),
        int(np.clip(true_pos[1] + e[1], 0, n - 1))
    )


def register(arr: np.ndarray, shift: tuple) -> np.ndarray:
    """Shift observation grid by (dy, dx) cells into the believed frame."""
    return ndi.shift(arr.astype(float), shift, order=0, mode="constant", cval=0.0) > 0.5
