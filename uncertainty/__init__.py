"""Uncertainty and calibration subpackage for APPS."""
from uncertainty.calibration import scale_probs, fit_temperature, entropy_norm, ece
from uncertainty.cross_sensor import consistency_map, depth_validity
from uncertainty.novelty import MahalanobisOOD, RankGate

__all__ = [
    "scale_probs", "fit_temperature", "entropy_norm", "ece",
    "consistency_map", "depth_validity", "MahalanobisOOD", "RankGate"
]
