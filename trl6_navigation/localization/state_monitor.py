"""State Monitor, Trajectory Metrics & Autonomous Watchdogs (TRL 6).

Implements:
1. Trajectory accuracy auditing: Absolute Trajectory Error (ATE) & Relative Pose Error (RPE)
2. Covariance divergence watchdog (localization failure detection)
3. Slip entrapment watchdog (excessive wheel slip in loose regolith)
"""
from __future__ import annotations
import math
from typing import Dict, Any, List
import numpy as np


class StateMonitor:
    """Monitors state estimation health, watchdog conditions, and computes trajectory metrics."""

    def __init__(
        self,
        max_position_variance_m2: float = 4.0,
        slip_entrapment_thresh: float = 0.60,
        slip_duration_limit_s: float = 1.5
    ) -> None:
        self.max_pos_var = float(max_position_variance_m2)
        self.slip_thresh = float(slip_entrapment_thresh)
        self.slip_dur_limit = float(slip_duration_limit_s)

        # Execution logs
        self.timestamps: List[float] = []
        self.est_poses: List[np.ndarray] = []
        self.gt_poses: List[np.ndarray] = []
        self.covariances: List[np.ndarray] = []
        self.slip_ratios: List[float] = []

        # Internal watchdog states
        self.slip_timer_s: float = 0.0
        self.is_slip_trapped: bool = False
        self.is_localization_diverged: bool = False

    def record_step(
        self,
        timestamp_s: float,
        estimated_pose_xytheta: np.ndarray,
        ground_truth_pose_xytheta: np.ndarray,
        pose_covariance: np.ndarray,
        measured_slip: float,
        dt_s: float = 0.05
    ) -> Dict[str, Any]:
        """Records a simulation step and evaluates autonomous watchdog conditions."""
        self.timestamps.append(float(timestamp_s))
        self.est_poses.append(estimated_pose_xytheta.copy())
        self.gt_poses.append(ground_truth_pose_xytheta.copy())
        self.covariances.append(pose_covariance.copy())
        self.slip_ratios.append(float(measured_slip))

        # 1. Slip Entrapment Watchdog
        if measured_slip >= self.slip_thresh:
            self.slip_timer_s += float(dt_s)
            if self.slip_timer_s >= self.slip_dur_limit:
                self.is_slip_trapped = True
        else:
            self.slip_timer_s = max(0.0, self.slip_timer_s - float(dt_s) * 0.5)

        # 2. Covariance Divergence Watchdog
        pos_var_trace = float(pose_covariance[0, 0] + pose_covariance[1, 1])
        if pos_var_trace > self.max_pos_var:
            self.is_localization_diverged = True

        return {
            "slip_trapped": self.is_slip_trapped,
            "localization_lost": self.is_localization_diverged,
            "pos_variance_trace": round(pos_var_trace, 4),
            "slip_timer_s": round(self.slip_timer_s, 2),
        }

    def compute_trajectory_metrics(self) -> Dict[str, float]:
        """Calculates formal ATE (RMSE & Max) and RPE (translation & rotation)."""
        if len(self.est_poses) < 2:
            return {
                "ate_rmse_m": 0.0,
                "ate_max_m": 0.0,
                "rpe_trans_m": 0.0,
                "rpe_rot_deg": 0.0,
            }

        est = np.array(self.est_poses)
        gt = np.array(self.gt_poses)

        # 1. Absolute Trajectory Error (ATE)
        pos_errors = np.hypot(est[:, 0] - gt[:, 0], est[:, 1] - gt[:, 1])
        ate_rmse = float(np.sqrt(np.mean(pos_errors ** 2)))
        ate_max = float(np.max(pos_errors))

        # 2. Relative Pose Error (RPE) across adjacent 1-step increments
        d_est = np.diff(est[:, :2], axis=0)
        d_gt = np.diff(gt[:, :2], axis=0)
        step_errors = np.linalg.norm(d_est - d_gt, axis=1)
        rpe_trans = float(np.mean(step_errors))

        # Heading angular delta error
        d_yaw_est = np.diff(est[:, 2])
        d_yaw_gt = np.diff(gt[:, 2])
        yaw_err = (d_yaw_est - d_yaw_gt + math.pi) % (2.0 * math.pi) - math.pi
        rpe_rot_deg = float(np.mean(np.degrees(np.abs(yaw_err))))

        return {
            "ate_rmse_m": round(ate_rmse, 4),
            "ate_max_m": round(ate_max, 4),
            "rpe_trans_m": round(rpe_trans, 4),
            "rpe_rot_deg": round(rpe_rot_deg, 4),
        }
