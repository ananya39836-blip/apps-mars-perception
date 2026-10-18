"""Fault injection helpers for robustness and safety verification.
Chapter 74, Appendix AE (Part 5) - Task 37.
"""
import numpy as np


def depth_dropout(depth: np.ndarray, frac: float, rng, fill=None):
    """Randomly drop fraction of depth pixels, replacing with median or fill value."""
    out = depth.copy()
    m = rng.random(depth.shape) < frac
    out[m] = np.median(depth) if fill is None else fill
    return out, m


def depth_nan(depth: np.ndarray, frac: float, rng):
    """Set fraction of depth pixels to NaN."""
    out = depth.copy()
    m = rng.random(depth.shape) < frac
    out[m] = np.nan
    return out, m


def blackout(img: np.ndarray):
    """All-zero blackout image."""
    return np.zeros_like(img)


def saturate(img: np.ndarray, gain: float = 4.0):
    """Camera saturation fault."""
    return np.clip(img * gain, 0.0, 1.0)


def add_noise(img: np.ndarray, sigma: float, rng):
    """Sensor noise burst."""
    return np.clip(img + rng.normal(0, sigma, img.shape), 0.0, 1.0).astype(img.dtype)


def stuck_frame(frames: list, k: int):
    """Frozen sensor: from index k onward, repeat frame k."""
    return [f if i < k else frames[k] for i, f in enumerate(frames)]


def corrupt_bytes(buf: bytes, frac: float, rng) -> bytes:
    """Random byte corruption in buffer."""
    b = bytearray(buf)
    idx = rng.choice(len(b), max(1, int(frac * len(b))), replace=False)
    for i in idx:
        b[i] = rng.integers(0, 256)
    return bytes(b)
