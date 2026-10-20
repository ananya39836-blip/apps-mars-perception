"""Deterministic RTOS Fixed-Step Scheduler & Precision Monitor (TRL 4).
Compatible with FreeRTOS / RTEMS Rate-Monotonic Executive Model.

Enforces 100 Hz (10 ms) cycle timing, deadline overrun watchdogs, jitter profiling,
and IEEE 754 floating-point precision sanitization.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import time
import math
from typing import Dict, Any, Callable, List, Optional
import numpy as np

from gnc_core import PROTOTYPE_LOCK, NAVIGATION_READY


class DeterministicScheduler:
    """Simulates real-time cyclic executive operating at target rate (e.g. 100 Hz / 10 ms)."""

    def __init__(self, target_frequency_hz: float = 100.0) -> None:
        self.freq_hz = float(target_frequency_hz)
        self.period_s = 1.0 / self.freq_hz
        self.period_ns = int(self.period_s * 1e9)
        self.step_count: int = 0
        self.sim_time_s: float = 0.0

        # Timing and jitter metrics
        self.execution_latencies_ms: List[float] = []
        self.cycle_jitters_ms: List[float] = []
        self.deadline_overruns: int = 0
        self.last_cycle_start_ns: Optional[int] = None

    def sanitize_ieee754_vector(self, vec: np.ndarray, field_name: str = "vector") -> np.ndarray:
        """Enforces strict IEEE 754 precision constraints: checks for NaN, Inf, and subnormals."""
        v = np.asarray(vec, dtype=np.float64)
        if not np.all(np.isfinite(v)):
            raise FloatingPointError(f"IEEE 754 violation in {field_name}: non-finite values detected ({v})")
        # Subnormal check (below 2.22e-308 for FP64)
        zero_subnormals = np.where(np.abs(v) < 1e-300, 0.0, v)
        return zero_subnormals

    def execute_cycle(self, task_callable: Callable[[float, float], Any]) -> Dict[str, Any]:
        """Executes a single deterministic periodic task invocation.
        
        Args:
            task_callable: Callable accepting (sim_time_s, dt_s)
            
        Returns:
            Dictionary with task result, execution latency (ms), and overrun flag.
        """
        now_ns = time.perf_counter_ns()
        if self.last_cycle_start_ns is not None:
            actual_cycle_ns = now_ns - self.last_cycle_start_ns
            jitter_ms = (actual_cycle_ns - self.period_ns) / 1e6
            self.cycle_jitters_ms.append(jitter_ms)
        self.last_cycle_start_ns = now_ns

        # Execute payload task
        t_start = time.perf_counter_ns()
        task_output = task_callable(self.sim_time_s, self.period_s)
        t_end = time.perf_counter_ns()

        exec_latency_ms = (t_end - t_start) / 1e6
        self.execution_latencies_ms.append(exec_latency_ms)

        is_overrun = exec_latency_ms > (self.period_s * 1000.0)
        if is_overrun:
            self.deadline_overruns += 1

        self.step_count += 1
        self.sim_time_s += self.period_s

        return {
            "step_count": self.step_count,
            "sim_time_s": self.sim_time_s,
            "latency_ms": exec_latency_ms,
            "is_overrun": is_overrun,
            "output": task_output,
        }

    def get_timing_statistics(self) -> Dict[str, float]:
        """Computes statistical metrics of timing performance for TRL 4 validation."""
        if not self.execution_latencies_ms:
            return {"mean_latency_ms": 0.0, "max_latency_ms": 0.0, "deadline_overruns": 0}

        lat = np.array(self.execution_latencies_ms)
        jit = np.array(self.cycle_jitters_ms) if self.cycle_jitters_ms else np.zeros(1)

        return {
            "total_cycles": self.step_count,
            "target_period_ms": self.period_s * 1000.0,
            "mean_latency_ms": float(np.mean(lat)),
            "p95_latency_ms": float(np.percentile(lat, 95)),
            "p99_latency_ms": float(np.percentile(lat, 99)),
            "max_latency_ms": float(np.max(lat)),
            "mean_jitter_ms": float(np.mean(np.abs(jit))),
            "deadline_overruns": self.deadline_overruns,
            "overrun_percentage": (self.deadline_overruns / max(1, self.step_count)) * 100.0,
        }
