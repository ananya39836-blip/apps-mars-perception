"""Footprint-aware traversability cost map and status classification.
Chapter 55, Appendix U (Part 4) - Task 23.
"""
from dataclasses import dataclass
import numpy as np
from scipy import ndimage as ndi

FREE, COSTLY, BLOCKED, UNKNOWN = 0, 1, 2, 3


@dataclass(frozen=True)
class RoverParams:
    """Hypothetical vehicle. Every value is a team decision, written down, not a fact
    about any real rover. Slope is in the units of the slope map passed in.
    """
    footprint_radius_cells: int = 1
    max_safe_slope: float = 0.35
    costly_slope_frac: float = 0.7
    block_p: float = 0.30
    costly_p: float = 0.10
    unknown_unc: float = 0.35


def to_cells(x: np.ndarray, c: int) -> np.ndarray:
    n = x.shape[0] // c
    return x[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3))


def disk(r: int) -> np.ndarray:
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    return (yy * yy + xx * xx) <= (r * r)


def build_status(p_unsafe: np.ndarray, unc: np.ndarray, slope: np.ndarray, params: RoverParams, c: int = 6) -> np.ndarray:
    """p_unsafe, unc, slope: HxW float maps. Returns per-cell status (FREE..UNKNOWN)."""
    pc, uc, sc = to_cells(p_unsafe, c), to_cells(unc, c), to_cells(slope, c)
    st = np.full(pc.shape, FREE, np.uint8)
    st[(pc >= params.costly_p) | (sc >= params.costly_slope_frac * params.max_safe_slope)] = COSTLY
    st[(pc >= params.block_p) | (sc >= params.max_safe_slope)] = BLOCKED
    st[(uc >= params.unknown_unc) & (st != BLOCKED)] = UNKNOWN
    return st


def planner_mask(status: np.ndarray, params: RoverParams, allow_unknown: bool = False) -> np.ndarray:
    """Boolean blocked mask for a grid planner. Unknown is blocked unless the explicit
    policy flag allows cautious traversal. Blocked cells are inflated by the footprint.
    """
    base = (status == BLOCKED) | ((status == UNKNOWN) & (not allow_unknown))
    r = params.footprint_radius_cells
    return ndi.binary_dilation(base, structure=disk(r)) if r > 0 else base


def step_cost(status: np.ndarray) -> np.ndarray:
    """Cost per cell for a cost-aware planner. inf means not enterable."""
    cost = np.full(status.shape, np.inf)
    cost[status == FREE] = 1.0
    cost[status == COSTLY] = 3.0
    return cost
