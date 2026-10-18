"""Seed management and near-duplicate audit utilities.
Part 7 Appendix AU & Part 9 Task 71.
"""
import numpy as np


def split_seeds(base: int, n_train: int, n_val: int, n_test: int, stride: int = 1000) -> dict:
    """Generate disjoint seed ranges separated by large strides."""
    r = {}
    s = base
    for name, n in (("train", n_train), ("val", n_val), ("test", n_test)):
        r[name] = list(range(s, s + n))
        s += n + stride
    return r


def check_disjoint(reg: dict) -> bool:
    """Verify that no seed appears in more than one split."""
    allv = [x for v in reg.values() for x in v]
    return len(allv) == len(set(allv))


def sig(grid: np.ndarray, k: int = 8) -> np.ndarray:
    """Compute coarse 8x8 binary spatial hash signature for a terrain grid."""
    g = np.asarray(grid, float)
    n = g.shape[0] // k
    p = g[:n * k, :n * k].reshape(k, n, k, n).mean((1, 3)).ravel()
    return (p > np.median(p)).astype(np.uint8)


def near_duplicates(grids_a: list, grids_b: list, max_hamming: int = 4) -> int:
    """Count near-duplicate pairs across two splits using Hamming distance on spatial signatures."""
    A = [sig(g) for g in grids_a]
    B = [sig(g) for g in grids_b]
    return sum(int((a != b).sum() <= max_hamming) for a in A for b in B)
