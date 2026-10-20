"""State Monitor, Slip Entrapment Watchdog & Trajectory Error Metrics (TRL 5).

Monitors state estimation health, detects wheel slip entrapment and covariance explosion,
and evaluates Absolute Trajectory Error (ATE) and Relative Pose Error (RPE) against ground truth.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np


class StateMonitor:
    """Monitors EKF health, slip entrapment, and trajectory error metrics."""

    def __init__(
        self,
        max_slip_ratio: float = 0.60,
        slip_duration_threshold_s: float = 1.0,
        max_pos_variance_m2: float = 1.50
    ) -> None:
        self.max_slip = float(max_slip_ratio)
        self.slip_duration_thresh = float(slip_duration_threshold_s)
        self.max_var = float(max_pos_variance_m2)

        self.slip_timer_s: float = 0.0
        self.is_slip_trapped: bool = False
        self.is_localization_lost: bool = False

        # Trajectory history buffers
        self.history_estimated: List[np.ndarray] = []
        self.history_ground_truth: List[np.ndarray] = []
        self.timestamps: List[float] = []

    def record_step(
        self,
        timestamp_s: float,
        estimated_pose_xytheta: np.ndarray,
        ground_truth_pose_xytheta: np.ndarray,
        pose_covariance: np.ndarray,
        measured_slip: float,
        dt_s: float
    ) -> Dict[str, Any]:
        """Audits current time step, evaluates watchdogs, and stores trajectory history."""
        self.timestamps.append(float(timestamp_s))
        self.history_estimated.append(estimated_pose_xytheta.copy())
        self.history_ground_truth.append(ground_truth_pose_xytheta.copy())

        # 1. Slip Entrapment Watchdog
        if abs(measured_slip) > self.max_slip:
            self.slip_timer_s += float(dt_s)
            if self.slip_timer_s >= self.slip_duration_thresh:
                self.is_slip_trapped = True
        else:
            self.slip_timer_s = max(0.0, self.slip_timer_s - float(dt_s) * 0.5)

        # 2. Covariance Divergence Watchdog
        pos_var = float(pose_covariance[0, 0] + pose_covariance[1, 1])
        if pos_var > self.max_var:
            self.is_localization_lost = True

        return {
            "slip_trapped": self.is_slip_trapped,
            "localization_lost": self.is_localization_lost,
            "position_variance_m2": round(pos_var, 4),
            "slip_timer_s": round(self.slip_timer_s, 2),
        }

    def compute_trajectory_metrics(self) -> Dict[str, float]:
        """Calculates Absolute Trajectory Error (ATE RMSE) and Relative Pose Error (RPE)."""
        if len(self.history_estimated) < 2:
            return {"ate_rmse_m": 0.0, "ate_max_m": 0.0, "rpe_trans_m": 0.0, "rpe_rot_deg": 0.0}

        est_arr = np.array(self.history_estimated)
        gt_arr = np.array(self.history_ground_truth)

        # Absolute Trajectory Error (ATE) in position
        pos_errors = np.linalg.norm(est_arr[:, :2] - gt_arr[:, :2], axis=1)
        ate_rmse = float(np.sqrt(np.mean(pos_errors**2)))
        ate_max = float(np.max(pos_errors))

        # Relative Pose Error (RPE) across 1-step increments
        d_est = np.diff(est_arr, axis=0)
        d_gt = np.diff(gt_arr, axis=0)

        trans_diff = np.linalg.norm(d_est[:, :2] - d_gt[:, :2], axis=1)
        rpe_trans = float(np.mean(trans_diff))

        # Heading angular difference normalized
        rot_diff = np.abs((d_est[:, 2] - d_gt[:, 2] + math.pi) % (2.0 * math.pi) - math.pi)
        rpe_rot_deg = float(math.degrees(np.mean(rot_diff)))

        return {
            "ate_rmse_m": round(ate_rmse, 4),
            "ate_max_m": round(ate_max, 4),
            "rpe_trans_m": round(rpe_trans, 4),
            "rpe_rot_deg": round(rpe_rot_deg, 3),
        }
