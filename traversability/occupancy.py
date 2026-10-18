"""Occupancy grid fusion and sequence cropping for temporal perception.
Chapter 60, Appendix W (Part 4) - Tasks 28 & 29.
"""
import numpy as np


class OccupancyFusion:
    """Log-odds fusion of per-frame unsafe probabilities on a cell grid, already warped
    into a common map frame. Asymmetric on purpose: evidence of hazard moves the cell
    further than evidence of safety. A never-observed cell stays UNKNOWN.
    """
    def __init__(self, shape, l_haz=0.9, l_safe=0.3, l_lim=4.0, decay=0.0):
        self.L = np.zeros(shape, dtype=float)
        self.n_obs = np.zeros(shape, dtype=int)
        self.l_haz, self.l_safe, self.l_lim, self.decay = l_haz, l_safe, l_lim, decay

    def update(self, p_unsafe, observed):
        """p_unsafe in [0,1]; observed is a bool mask of cells this frame actually saw."""
        p = np.clip(p_unsafe, 1e-3, 1.0 - 1e-3)
        step = np.where(p > 0.5, self.l_haz * (2.0 * p - 1.0), -self.l_safe * (1.0 - 2.0 * p))
        if self.decay:
            self.L *= (1.0 - self.decay)
        self.L = np.where(observed, np.clip(self.L + step, -self.l_lim, self.l_lim), self.L)
        self.n_obs += observed.astype(int)

    def p_unsafe(self):
        return 1.0 / (1.0 + np.exp(-self.L))

    def unknown(self, min_obs=1):
        return self.n_obs < min_obs


def warp_integer(grid: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """Shift a grid by whole cells; vacated cells get fill.
    A stand-in for a pose-based warp, used to inject localisation error by perturbing dy, dx.
    """
    out = np.full_like(grid, fill)
    H, W = grid.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    out[yd, xd] = grid[ys, xs]
    return out


def crop_sequence(world: np.ndarray, stride: int, size: int, noise_fn=None, rng=None):
    """Cut size-by-size windows from a wide array (H x Wtot [x C]) at a fixed stride.
    Returns (frames, offsets) where offsets[i] is column of frame i in map frame.
    """
    Wtot = world.shape[1]
    frames, offs = [], []
    for x in range(0, Wtot - size + 1, stride):
        f = world[:, x:x + size].copy()
        frames.append(noise_fn(f, rng) if noise_fn else f)
        offs.append(x)
    return frames, offs
