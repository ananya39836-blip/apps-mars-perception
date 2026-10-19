"""Latency Budget and Timing Harness for Level 2 Pipeline.
Task 105 / Chapter 213 & Appendix CQ (Part 12).
"""
import time
from typing import Dict, List
import numpy as np


def latency_report(samples_ms: Dict[str, List[float]],
                   budget_ms: Dict[str, float] = None, q: float = 95.0) -> dict:
    """Computes median and 95th percentile execution latency per stage against budget.
    Appendix CQ.
    """
    if budget_ms is None:
        budget_ms = {
            "sensor_model": 5.0,
            "perception": 80.0,
            "traversability_mapper": 10.0,
            "primitive_planner": 15.0,
            "kinematic_step": 2.0,
            "monitors_and_interface": 5.0,
            "total_loop_step": 120.0
        }
        
    out = {}
    for stage, xs in samples_ms.items():
        if len(xs) == 0:
            raise ValueError("no samples: " + stage)
        p = float(np.percentile(xs, q))
        median = float(np.median(xs))
        budget = float(budget_ms.get(stage, float("inf")))
        out[stage] = {
            "median_ms": round(median, 2),
            "p95_ms": round(p, 2),
            "budget_ms": budget,
            "within_budget": bool(p <= budget),
            "calls": len(xs)
        }
    return out


class StageTimer:
    """Context manager for collecting stage timing benchmarks in milliseconds."""
    def __init__(self, stage_name: str, accumulator: Dict[str, List[float]]):
        self.stage_name = stage_name
        self.acc = accumulator
        self.t0 = 0.0

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        dt_ms = (time.perf_counter() - self.t0) * 1000.0
        self.acc.setdefault(self.stage_name, []).append(dt_ms)
