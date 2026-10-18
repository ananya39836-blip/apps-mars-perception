"""Cluster bootstrap estimation utilities for multi-episode scene runs.
Chapter 76, Appendix AD (Part 5).
"""
import numpy as np


def boot_clusters(values, groups, n=2000, seed=0):
    """Mean of per-episode values with a bootstrap over clusters (scenes).
    values: per-episode numbers; groups: cluster id per episode.
    """
    v = np.asarray(values, float)
    g = np.asarray(groups)
    ids = np.unique(g)
    by = {i: v[g == i] for i in ids}
    r = np.random.default_rng(seed)
    est = np.empty(n)
    for b in range(n):
        pick = r.choice(ids, len(ids))
        est[b] = np.concatenate([by[i] for i in pick]).mean()
    return float(v.mean()), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def boot_paired_clusters(a, b, groups, n=2000, seed=0):
    """Paired per-episode difference a - b, bootstrapped over clusters."""
    d = np.asarray(a, float) - np.asarray(b, float)
    mean, lo, hi = boot_clusters(d, groups, n, seed)
    return dict(
        mean=mean, lo=lo, hi=hi,
        a_greater=float((d > 0).mean()),
        a_less=float((d < 0).mean()),
        tied=float((d == 0).mean())
    )
