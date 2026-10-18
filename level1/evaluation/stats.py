"""Statistical computation engine for Level 1 evaluation.
Part 4 Appendix S, Part 5 Appendix AD, Part 9 Chapters 150-151 & Appendix BM.
"""
import math
import numpy as np


def boot_clusters(values: list, groups: list, n_resamples: int = 2000, seed: int = 0) -> tuple:
    """Mean of per-episode values with a bootstrap over clusters (scenes)."""
    v = np.asarray(values, float)
    g = np.asarray(groups)
    ids = np.unique(g)
    by = {i: v[g == i] for i in ids}
    r = np.random.default_rng(seed)
    est = np.empty(n_resamples)
    for b in range(n_resamples):
        pick = r.choice(ids, len(ids), replace=True)
        est[b] = np.concatenate([by[i] for i in pick]).mean()
    return float(v.mean()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def boot_paired_clusters(a: list, b: list, groups: list, n_resamples: int = 2000, seed: int = 0) -> dict:
    """Paired per-episode difference a - b, bootstrapped over clusters (scenes)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    mean, lo, hi = boot_clusters(d, groups, n_resamples, seed)
    return dict(
        mean=mean,
        lo=lo,
        hi=hi,
        a_greater=float((d > 0).mean()),
        a_less=float((d < 0).mean()),
        tied=float((d == 0).mean())
    )


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    """Wilson score confidence interval for k events in n trials."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return max(c - h, 0.0), min(c + h, 1.0)


def rule_of_three(n: int) -> float:
    """Conservative 95% upper bound on a rate after zero events in n trials."""
    return 3.0 / n if n > 0 else 1.0


def clusters_needed_zero_events(upper: float, design_effect: float = 1.0) -> int:
    """Sample sizing: number of clusters needed to bound zero-event rate below upper limit."""
    return math.ceil(3.0 * design_effect / upper)
