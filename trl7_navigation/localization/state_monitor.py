"""Localization State Monitor & Trajectory Error Analysis (TRL 7).

Computes Absolute Trajectory Error (ATE), Relative Pose Error (RPE),
cumulative dead-reckoning drift percentages, and covariance health watchdogs.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class StateMonitor:
    """Monitors trajectory estimation accuracy and filter consistency."""

    def __init__(self, max_pos_variance_m2: float = 2.50) -> None:
        self.max_pos_var = float(max_pos_variance_m2)
        self.gt_trajectory: List[Tuple[float, float, float]] = []
        self.est_trajectory: List[Tuple[float, float, float]] = []
        self.timestamps: List[float] = []

    def record_step(
        self,
        t: float,
        gt_pose: Tuple[float, float, float],   # x, y, z
        est_pose: Tuple[float, float, float],  # x, y, z
    ) -> None:
        """Records ground truth and estimated pose at time t."""
        self.timestamps.append(float(t))
        self.gt_trajectory.append(gt_pose)
        self.est_trajectory.append(est_pose)

    def compute_trajectory_metrics(self) -> Dict[str, float]:
        """Computes ATE, cumulative distance, final error, and drift percentage."""
        if len(self.gt_trajectory) < 2:
            return {"ate_rmse_m": 0.0, "total_dist_m": 0.0, "final_error_m": 0.0, "drift_percent": 0.0}

        gt_arr = np.array(self.gt_trajectory)
        est_arr = np.array(self.est_trajectory)

        # 2D/3D errors
        errors_xyz = est_arr - gt_arr
        dist_errors = np.linalg.norm(errors_xyz[:, :2], axis=1)

        ate_rmse = float(np.sqrt(np.mean(dist_errors ** 2)))
        final_err = float(dist_errors[-1])

        # Compute total ground-truth distance traversed
        seg_dists = np.linalg.norm(np.diff(gt_arr[:, :2], axis=0), axis=1)
        total_dist = float(np.sum(seg_dists))

        drift_percent = float((final_err / total_dist) * 100.0) if total_dist > 0.1 else 0.0

        return {
            "ate_rmse_m": ate_rmse,
            "max_error_m": float(np.max(dist_errors)),
            "final_error_m": final_err,
            "total_dist_m": total_dist,
            "drift_percent": drift_percent,
        }

    def check_covariance_divergence(self, P_cov: np.ndarray) -> Tuple[bool, float]:
        """Checks if position variance trace exceeds watchdog threshold."""
        pos_var_trace = float(np.trace(P_cov[0:3, 0:3]))
        diverged = pos_var_trace > self.max_pos_var
        return diverged, pos_var_trace
