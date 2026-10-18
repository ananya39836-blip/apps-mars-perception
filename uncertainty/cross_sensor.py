"""Cross-sensor consistency and depth validity checks.
Chapter 58 & Appendix X (Part 4).
"""
import numpy as np
from scipy import ndimage as ndi


def _local_corr(a: np.ndarray, b: np.ndarray, win: int) -> np.ndarray:
    """Computes sliding window local Pearson correlation between two 2D fields."""
    ma, mb = ndi.uniform_filter(a, win), ndi.uniform_filter(b, win)
    va = np.maximum(ndi.uniform_filter(a * a, win) - ma * ma, 0)
    vb = np.maximum(ndi.uniform_filter(b * b, win) - mb * mb, 0)
    cov = ndi.uniform_filter(a * b, win) - ma * mb
    return cov / (np.sqrt(va * vb) + 1e-9)


def consistency_map(img: np.ndarray, depth: np.ndarray, win: int = 9, sigma: float = 1.5) -> np.ndarray:
    """Local correlation between image gradient magnitude and the magnitude of the change
    of depth slope (shading edges tend to sit where surface bends). Low/negative values
    indicate sensor disagreement or discrepancy.
    """
    g = ndi.gaussian_filter(img.mean(-1), sigma)
    gy, gx = np.gradient(g)
    dy, dx = np.gradient(ndi.gaussian_filter(depth, sigma))
    dyy, dyx = np.gradient(dy)
    dxy, dxx = np.gradient(dx)
    curv = np.sqrt(dyy ** 2 + dyx ** 2 + dxy ** 2 + dxx ** 2)
    return _local_corr(np.hypot(gx, gy), curv, win)


def depth_validity(depth: np.ndarray, win: int = 9, min_std: float = 1e-4) -> np.ndarray:
    """Flags non-finite depth values and windows whose depth is suspiciously constant."""
    bad = ~np.isfinite(depth)
    d = np.where(bad, 0.0, depth)
    m = ndi.uniform_filter(d, win)
    s = np.sqrt(np.maximum(ndi.uniform_filter(d * d, win) - m * m, 0))
    return bad | (s < min_std)
