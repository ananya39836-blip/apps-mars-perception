"""Bootstrap statistical estimation utilities.
Chapter 43, Appendix N (Part 3).
"""
import numpy as np


def boot_mean(vals, n=2000, seed=0):
    r = np.random.default_rng(seed)
    v = np.asarray(vals, float)
    m = np.array([r.choice(v, len(v)).mean() for _ in range(n)])
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def boot_paired(a, b, n=2000, seed=0):
    """Per-scene difference a - b with bootstrap interval, plus win/loss/tie fractions."""
    d = np.asarray(a, float) - np.asarray(b, float)
    mean, lo, hi = boot_mean(d, n, seed)
    return dict(
        mean=mean, lo=lo, hi=hi,
        a_greater=float((d > 0).mean()),
        a_less=float((d < 0).mean()),
        tied=float((d == 0).mean())
    )


def boot_pooled_false_safe(missed, hazard, n=2000, seed=0):
    """missed[i], hazard[i]: per-scene counts of missed hazard pixels and total hazard pixels.
    Resamples scenes and recomputes sum(missed) / sum(hazard).
    """
    r = np.random.default_rng(seed)
    m = np.asarray(missed, float)
    h = np.asarray(hazard, float)
    k = len(m)
    est = []
    for _ in range(n):
        idx = r.integers(0, k, k)
        est.append(m[idx].sum() / max(h[idx].sum(), 1.0))
    return float(m.sum() / max(h.sum(), 1.0)), float(np.percentile(est, 2.5)), float(np.percentile(est, 97.5))


def upper_bound_zero_events(n_trials: int) -> float:
    """Approximate 95 percent upper bound when no events are seen ('rule of three')."""
    return 3.0 / n_trials
