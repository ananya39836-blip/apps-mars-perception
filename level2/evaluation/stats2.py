"""Statistical Engine for Level 2 3D Benchmark Evaluation.
Cluster bootstrap resampling, Wilson score rare-event bounds, and Rule of Three.
Chapter 151 / Part 12 Chapter 219.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


def wilson_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score confidence interval for binomial proportion."""
    if total <= 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = float(successes) / float(total)
    denom = 1.0 + (z**2) / total
    center = (p + (z**2) / (2.0 * total)) / denom
    half = (z / denom) * math.sqrt((p * (1.0 - p) / total) + (z**2) / (4.0 * total**2))
    return float(max(0.0, center - half)), float(min(1.0, center + half))


def rule_of_three(total: int) -> float:
    """Rule of Three upper bound for zero observed events."""
    if total <= 0:
        return 1.0
    return float(3.0 / total)


def boot_clusters_3d(scenes_data: List[dict], metric_key: str, n_boot: int = 2000,
                     seed: int = 42) -> Tuple[float, float, float]:
    """Cluster bootstrap resamples grouped strictly by 3D terrain scene."""
    rng = np.random.default_rng(seed)
    n_scenes = len(scenes_data)
    if n_scenes == 0:
        return 0.0, 0.0, 0.0
        
    rates = [s[metric_key] for s in scenes_data]
    mean_val = float(np.mean(rates))
    
    boot_means = []
    for _ in range(n_boot):
        idx = rng.choice(n_scenes, size=n_scenes, replace=True)
        boot_means.append(np.mean([rates[i] for i in idx]))
        
    lo = float(np.percentile(boot_means, 2.5))
    hi = float(np.percentile(boot_means, 97.5))
    return mean_val, lo, hi


def boot_paired_diff_3d(episodes_b: List[dict], episodes_c: List[dict],
                        metric_key: str, n_boot: int = 2000,
                        seed: int = 42) -> dict:
    """Paired difference (B minus C) resampled at scene level."""
    rng = np.random.default_rng(seed)
    
    # Group by scene_id
    scenes_b = {}
    for ep in episodes_b:
        scenes_b.setdefault(ep["scene_id"], []).append(ep[metric_key])
    scenes_c = {}
    for ep in episodes_c:
        scenes_c.setdefault(ep["scene_id"], []).append(ep[metric_key])
        
    scene_ids = sorted(list(set(scenes_b.keys()) & set(scenes_c.keys())))
    n_scenes = len(scene_ids)
    
    diffs = [np.mean(scenes_b[s]) - np.mean(scenes_c[s]) for s in scene_ids]
    mean_diff = float(np.mean(diffs))
    
    boot_diffs = []
    for _ in range(n_boot):
        idx = rng.choice(n_scenes, size=n_scenes, replace=True)
        boot_diffs.append(np.mean([diffs[i] for i in idx]))
        
    lo = float(np.percentile(boot_diffs, 2.5))
    hi = float(np.percentile(boot_diffs, 97.5))
    return {
        "mean_diff": round(mean_diff, 4),
        "ci_95": [round(lo, 4), round(hi, 4)],
        "b_greater": int(sum(1 for d in diffs if d > 0)),
        "c_greater": int(sum(1 for d in diffs if d < 0)),
        "tied": int(sum(1 for d in diffs if d == 0))
    }
