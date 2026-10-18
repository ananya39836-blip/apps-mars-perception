"""Synthetic planted scientific target candidates generator and recall evaluator.
Chapter 62 (Part 4) - Task 30.
"""
import numpy as np


def plant_bands(img, rng, radius=9, period=3.0, contrast=0.12):
    """Plant a circular patch of regular banded albedo on an image (H x W x 3, floats in 0..1).
    Returns (new_img, mask). The mask is stored SEPARATELY from class labels, which stay unchanged.
    This is a synthetic stand-in for 'a feature worth a closer look', not geology.
    """
    H, W = img.shape[:2]
    y = rng.integers(radius + 2, H - radius - 2)
    x = rng.integers(radius + 2, W - radius - 2)
    yy, xx = np.mgrid[:H, :W]
    mask = ((yy - y) ** 2 + (xx - x) ** 2) < (radius ** 2)
    bands = 1.0 + contrast * np.sin(2.0 * np.pi * (yy + 0.4 * xx) / period)
    out = img.copy()
    out[mask] = np.clip(out[mask] * bands[mask][:, None], 0.0, 1.0)
    return out, mask


def recall_at_k(ranked_masks, planted_masks, k, min_overlap=0.3):
    """ranked_masks: candidate region masks, best first. A planted mask counts as found if
    any of the top-k candidates covers at least min_overlap of it. Returns fraction found.
    """
    if len(planted_masks) == 0:
        return 0.0
    found = 0
    for p in planted_masks:
        p_sum = max(p.sum(), 1)
        if any((c & p).sum() / p_sum >= min_overlap for c in ranked_masks[:k]):
            found += 1
    return found / len(planted_masks)
