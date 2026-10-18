"""Level 1 Watchdog, Discrepancy Estimator, Stall Detector, and Freshness Checks.
Part 6 Appendix AL, Part 8 Appendices BD & BF (Tasks 44 & 64).
"""
import numpy as np


def discrepancy(est_before: np.ndarray, seen_before: np.ndarray,
                unsafe_obs: np.ndarray, observed: np.ndarray) -> tuple:
    """Compare internal belief map held before frame with new observation on mutually seen cells.
    Returns (newly_unsafe_count, newly_clear_count).
    """
    both = seen_before & observed
    newly_unsafe = int((both & unsafe_obs & ~est_before).sum())
    newly_clear = int((both & ~unsafe_obs & est_before).sum())
    return newly_unsafe, newly_clear


def stalled(positions: list, window: int = 12, min_unique: int = 3) -> bool:
    """Detect local entrapment/oscillation: too few unique cells visited in sliding window."""
    w = positions[-window:]
    return len(w) >= window and len(set(w)) < min_unique


def map_is_fresh(last_update_step: int, now_step: int, max_age: int) -> bool:
    """Validate that internal belief map has not exceeded allowable latency threshold."""
    return (now_step - last_update_step) <= max_age


def frames_identical(a: np.ndarray, b: np.ndarray) -> bool:
    """Detect stuck sensor hardware by comparing consecutive raw frames."""
    return a.shape == b.shape and bool((a == b).all())


class Watchdog:
    """Autonomous runtime monitor enforcing progress bounds, replan budgets, and outage containment."""
    def __init__(self, k_progress: int = 12, k_outage: int = 3, max_replans: int = 60):
        self.kp = k_progress
        self.ko = k_outage
        self.mr = max_replans
        self.best = -1
        self.since = 0
        self.outage = 0
        self.replans = 0

    def update(self, col: int, sensor_ok: bool, replanned: bool) -> str:
        """Evaluate watchdog state. Returns failure reason string or None."""
        if col > self.best:
            self.since = 0
            self.best = col
        else:
            self.since += 1
            
        self.outage = 0 if sensor_ok else self.outage + 1
        self.replans += int(replanned)
        
        if self.outage >= self.ko:
            return "sensor_outage"
        if self.replans > self.mr:
            return "replan_cap"
        if self.since >= self.kp:
            return "no_progress"
            
        return None
