"""Quantitative Perception & Mapping Metrics Engine (TRL 6).

Evaluates:
1. Obstacle Detection: Precision, Recall, F1-Score, and Intersection over Union (IoU)
2. Elevation Reconstruction: Root Mean Square Error (RMSE) and Mean Absolute Error (MAE)
"""
from __future__ import annotations
import math
from typing import Dict, Any
import numpy as np

from trl6_navigation.perception.elevation_mapping import ElevationMap25D
from trl6_navigation.environment.planetary_terrain import PlanetaryTerrain


class PerceptionMetrics:
    """Computes quantitative perception and 3D mapping metrics against simulator ground truth."""

    @staticmethod
    def evaluate_obstacle_detection(
        estimated_obstacle_mask: np.ndarray,
        ground_truth_obstacle_mask: np.ndarray
    ) -> Dict[str, float]:
        """Calculates Precision, Recall, F1, and IoU between estimated and GT obstacle masks."""
        est = estimated_obstacle_mask.astype(bool)
        gt = ground_truth_obstacle_mask.astype(bool)

        tp = int(np.sum(est & gt))
        fp = int(np.sum(est & ~gt))
        fn = int(np.sum(~est & gt))
        tn = int(np.sum(~est & ~gt))

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 1.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 1.0
        f1 = float(2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 1.0

        intersection = tp
        union = tp + fp + fn
        iou = float(intersection / union) if union > 0 else 1.0

        return {
            "true_positive": float(tp),
            "false_positive": float(fp),
            "false_negative": float(fn),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "iou": round(iou, 4),
        }

    @staticmethod
    def evaluate_elevation_reconstruction(
        elev_map: ElevationMap25D,
        ground_truth_terrain: PlanetaryTerrain
    ) -> Dict[str, float]:
        """Calculates elevation reconstruction RMSE and MAE across all observed cells."""
        observed_mask = elev_map.hit_count > 0
        if not np.any(observed_mask):
            return {"rmse_m": 0.0, "mae_m": 0.0, "max_err_m": 0.0, "observed_cells": 0}

        diff = elev_map.elevation[observed_mask] - ground_truth_terrain.elevation[observed_mask]
        rmse = float(np.sqrt(np.mean(diff ** 2)))
        mae = float(np.mean(np.abs(diff)))
        max_err = float(np.max(np.abs(diff)))

        return {
            "rmse_m": round(rmse, 4),
            "mae_m": round(mae, 4),
            "max_err_m": round(max_err, 4),
            "observed_cells": int(np.sum(observed_mask)),
        }
