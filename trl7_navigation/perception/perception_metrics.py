"""Perception Verification and Validation Metrics (TRL 7).

Computes standardized quantitative metrics comparing online perception maps
against ground-truth planetary terrain models:
- Intersection-over-Union (IoU) of obstacle hazard masks
- Classification Precision, Recall, and F1-Score
- Elevation Root Mean Squared Error (RMSE) [meters]
- Negative Obstacle False Negative Rate (safety critical)
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class PerceptionMetrics:
    """Quantitative evaluation suite for terrain perception performance."""

    @staticmethod
    def compute_elevation_rmse(
        est_elevation: np.ndarray, gt_elevation: np.ndarray, observed_mask: Optional[np.ndarray] = None
    ) -> float:
        """Computes RMSE between estimated elevation map and ground-truth DEM."""
        if observed_mask is None:
            observed_mask = np.ones_like(est_elevation, dtype=bool)

        if not np.any(observed_mask):
            return 0.0

        diff = est_elevation[observed_mask] - gt_elevation[observed_mask]
        mse = np.mean(diff ** 2)
        return float(np.sqrt(mse))

    @staticmethod
    def compute_obstacle_metrics(
        est_mask: np.ndarray, gt_mask: np.ndarray
    ) -> Dict[str, float]:
        """Computes IoU, Precision, Recall, and F1 between estimated hazard mask and ground-truth."""
        tp = int(np.sum(est_mask & gt_mask))
        fp = int(np.sum(est_mask & ~gt_mask))
        fn = int(np.sum(~est_mask & gt_mask))
        tn = int(np.sum(~est_mask & ~gt_mask))

        union = tp + fp + fn
        iou = float(tp / union) if union > 0 else 1.0
        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "iou": iou,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    @staticmethod
    def compute_crater_hazard_metrics(
        est_crater_mask: np.ndarray, gt_crater_mask: np.ndarray
    ) -> Dict[str, float]:
        """Evaluates detection of negative obstacles (craters). False negatives are critical."""
        metrics = PerceptionMetrics.compute_obstacle_metrics(est_crater_mask, gt_crater_mask)
        # False negative rate = FN / (TP + FN)
        tp = metrics["tp"]
        fn = metrics["fn"]
        fnr = float(fn / (tp + fn)) if (tp + fn) > 0 else 0.0
        metrics["false_negative_rate"] = fnr
        return metrics
