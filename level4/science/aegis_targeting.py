"""Autonomous Opportunistic Science Detection, Geomorphology & AEGIS Targeting.
Level 4: Part 19 (Chapters 280 to 289).

Implements autonomous opportunistic science targeting:
1. Rock & Outcrop Segmentation: Identifies candidate science targets from visual/spatial data.
2. Geomorphological Attribute Extraction: Roundness, angularity, albedo contrast, and size.
3. Novelty & Rarity Scoring: Evaluates target divergence from local geological background.
4. Autonomous ChemCam/SuperCam Target Selection: Ranks targets according to scientist priority profiles.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class ScienceTargetCandidate:
    """Represents a candidate scientific target identified by autonomous perception."""
    def __init__(
        self,
        target_id: int,
        pos_rel_m: Tuple[float, float, float],
        diameter_m: float,
        albedo: float,
        angularity: float,
        roundness: float,
        is_layered: bool = False
    ):
        self.target_id = target_id
        self.pos_rel_m = pos_rel_m
        self.diameter_m = diameter_m
        self.albedo = albedo
        self.angularity = angularity
        self.roundness = roundness
        self.is_layered = is_layered
        self.novelty_score = 0.0
        self.science_priority = 0.0

    def to_dict(self) -> Dict:
        return {
            'target_id': self.target_id,
            'pos_rel_m': [round(x, 3) for x in self.pos_rel_m],
            'diameter_m': round(self.diameter_m, 3),
            'albedo': round(self.albedo, 3),
            'angularity': round(self.angularity, 3),
            'roundness': round(self.roundness, 3),
            'is_layered': self.is_layered,
            'novelty_score': round(self.novelty_score, 4),
            'science_priority': round(self.science_priority, 4)
        }


class OpportunisticScienceDetector:
    """AEGIS-inspired autonomous target selection and geomorphological analysis engine."""
    def __init__(self, target_preference: str = "high_albedo_float"):
        self.target_preference = target_preference
        self.background_albedo_mean = 0.32
        self.background_albedo_std = 0.05

    def detect_targets_from_scene(
        self,
        num_candidates: int = 8,
        seed: int = 42
    ) -> List[ScienceTargetCandidate]:
        """Generates realistic candidate rock detections from local field of view."""
        rng = np.random.RandomState(seed)
        candidates = []
        for i in range(num_candidates):
            # Distance from rover (2.0m to 7.0m ChemCam laser operating range)
            r = rng.uniform(2.0, 7.0)
            theta = rng.uniform(-0.60, 0.60) # ~70 deg forward FOV
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            z = rng.uniform(-0.3, 0.2)
            
            dia = rng.uniform(0.04, 0.45)
            # Occasional unusual high albedo rock or dark basalt
            albedo = np.clip(rng.normal(0.35, 0.12), 0.10, 0.85)
            angularity = rng.uniform(0.2, 0.95)
            roundness = rng.uniform(0.1, 0.85)
            is_layered = bool(rng.uniform(0, 1) > 0.75)
            
            cand = ScienceTargetCandidate(
                target_id=100 + i,
                pos_rel_m=(x, y, z),
                diameter_m=dia,
                albedo=albedo,
                angularity=angularity,
                roundness=roundness,
                is_layered=is_layered
            )
            candidates.append(cand)
            
        return self.rank_and_prioritize(candidates)

    def rank_and_prioritize(
        self, candidates: List[ScienceTargetCandidate]
    ) -> List[ScienceTargetCandidate]:
        """Scores novelty and computes science priority score for each candidate."""
        if not candidates:
            return []
            
        for cand in candidates:
            # Novelty: deviation from typical Martian regolith background albedo
            albedo_z = abs(cand.albedo - self.background_albedo_mean) / self.background_albedo_std
            novelty = 1.0 - math.exp(-0.5 * (albedo_z**2))
            cand.novelty_score = float(novelty)
            
            # Distance factor: closer targets within optimal 3.0m - 5.0m focus range
            dist = math.hypot(cand.pos_rel_m[0], cand.pos_rel_m[1])
            dist_factor = math.exp(-0.5 * ((dist - 3.5) / 1.5)**2)
            
            # Preference profile weighting
            if self.target_preference == "high_albedo_float":
                feature_score = 0.5 * cand.albedo + 0.3 * cand.angularity + 0.2 * (1.0 if cand.is_layered else 0.0)
            elif self.target_preference == "layered_outcrop":
                feature_score = 0.6 * (1.0 if cand.is_layered else 0.0) + 0.2 * cand.roundness + 0.2 * cand.albedo
            else:
                feature_score = 0.4 * cand.novelty_score + 0.3 * cand.angularity + 0.3 * cand.albedo
                
            priority = 0.4 * cand.novelty_score + 0.4 * feature_score + 0.2 * dist_factor
            cand.science_priority = float(np.clip(priority, 0.0, 1.0))
            
        # Sort descending by priority
        candidates.sort(key=lambda c: c.science_priority, reverse=True)
        return candidates

    def get_top_targets(self, candidates: List[ScienceTargetCandidate], top_k: int = 3) -> List[Dict]:
        """Returns top K target telemetry dictionaries for autonomous science pointing."""
        return [c.to_dict() for c in candidates[:top_k]]
