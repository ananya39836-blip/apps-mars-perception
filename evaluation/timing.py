"""Stage timing helper for latency and performance profiling.
Chapter 77, Appendix AH (Part 5) - Task 32.
"""
import time
import numpy as np


def time_stage(fn, args_list, warmup: int = 3) -> dict:
    """Time fn on each element of args_list (after warmup calls).
    Returns median and 95th percentile in milliseconds, plus every sample.
    """
    for a in args_list[:warmup]:
        fn(*a)
    t = []
    for a in args_list:
        t0 = time.perf_counter()
        fn(*a)
        t.append((time.perf_counter() - t0) * 1e3)
    t = np.array(t)
    return dict(
        median_ms=float(np.median(t)),
        p95_ms=float(np.percentile(t, 95)),
        n=len(t),
        samples=t.tolist()
    )
