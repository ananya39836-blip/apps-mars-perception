"""Seed sequence generation and statistical sample sizing utilities.
Chapter 54, Appendix S (Part 4) - Task 21.
"""
import hashlib
import json
import math
import numpy as np


def scene_seeds(root: int, purpose: str, n: int) -> list:
    """Derive n independent per-scene seeds from a root seed and a purpose label.
    Same (root, purpose, n) always gives the same list; different purposes give
    statistically independent streams.
    """
    h = hashlib.sha256(purpose.encode()).digest()
    words = [int(root)] + [int.from_bytes(h[i:i + 4], "little") for i in (0, 4, 8, 12)]
    ss = np.random.SeedSequence(words)
    return [int(c.generate_state(1, dtype=np.uint64)[0]) for c in ss.spawn(n)]


def check_disjoint(registry: dict) -> bool:
    """registry: {purpose: [seeds]}. Raise if one seed is listed under two purposes."""
    seen = {}
    for purpose, seeds in registry.items():
        for s in seeds:
            if s in seen and seen[s] != purpose:
                raise ValueError(f"seed {s} used for {seen[s]} and {purpose}")
            seen[s] = purpose
    return True


def write_registry(path: str, root: int, purposes: dict) -> dict:
    """purposes: {name: n_scenes}. Writes derived seeds so the file is the record."""
    reg = {p: scene_seeds(root, p, n) for p, n in purposes.items()}
    check_disjoint(reg)
    with open(path, "w") as f:
        json.dump(dict(root=root, purposes=purposes, seeds=reg), f, indent=1)
    return reg


def wilson(k: int, n: int, z: float = 1.96) -> tuple:
    """Wilson score interval for k events in n trials."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2.0 * n)) / d
    h = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return max(c - h, 0.0), min(c + h, 1.0)


def n_for_halfwidth(w: float, p: float = 0.5, z: float = 1.96) -> int:
    """Scenes needed for a binary rate near p to get a 95 percent half-width w."""
    return math.ceil(z * z * p * (1.0 - p) / (w * w))


def n_for_paired_halfwidth(sd_diff: float, w: float, z: float = 1.96) -> int:
    """Scenes needed for a paired mean difference whose per-scene sd is sd_diff."""
    return math.ceil((z * sd_diff / w) ** 2)


def rule_of_three(n: int) -> float:
    """Approximate 95 percent upper bound on a rate after zero events in n trials."""
    return 3.0 / n if n > 0 else 1.0
