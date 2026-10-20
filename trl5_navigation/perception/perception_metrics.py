"""Quantitative Perception Metrics and Benchmark Scoring (TRL 5).

Evaluates obstacle detection precision, recall, F1, Intersection-over-Union (IoU),
and continuous elevation reconstruction Root-Mean-Square Error (RMSE).
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


class PerceptionMetrics:
    """Computes rigorous perception accuracy metrics against ground truth."""

    @staticmethod
    def evaluate_obstacle_detection(
        detected_obstacle_mask: np.ndarray,
        ground_truth_obstacle_mask: np.ndarray
    ) -> Dict[str, float]:
        """Calculates Precision, Recall, F1-score, and IoU against ground-truth hazard mask."""
        pred = detected_obstacle_mask.astype(bool)
        gt = ground_truth_obstacle_mask.astype(bool)

        tp = int(np.sum(pred & gt))
        fp = int(np.sum(pred & ~gt))
        fn = int(np.sum(~pred & gt))
        tn = int(np.sum(~pred & ~gt))

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1 = float(2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        intersection = tp
        union = tp + fp + fn
        iou = float(intersection / union) if union > 0 else 1.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "iou": round(iou, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }

    @staticmethod
    def evaluate_elevation_reconstruction(
        estimated_elevation_map: ElevationMap25D,
        ground_truth_terrain: PlanetaryTerrain
    ) -> Dict[str, float]:
        """Calculates elevation reconstruction RMSE, MAE, and max error over observed cells."""
        observed = estimated_elevation_map.hit_count > 0
        if not np.any(observed):
            return {"rmse_m": 0.0, "mae_m": 0.0, "max_error_m": 0.0, "coverage_pct": 0.0}

        est_z = estimated_elevation_map.elevation[observed]
        gt_z = ground_truth_terrain.elevation[observed]

        error = est_z - gt_z
        rmse = float(np.sqrt(np.mean(error**2)))
        mae = float(np.mean(np.abs(error)))
        max_err = float(np.max(np.abs(error)))
        coverage_pct = float(100.0 * np.sum(observed) / observed.size)

        return {
            "rmse_m": round(rmse, 4),
            "mae_m": round(mae, 4),
            "max_error_m": round(max_err, 4),
            "coverage_pct": round(coverage_pct, 2),
        }
