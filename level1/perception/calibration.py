"""Level 1 Perception Calibration under Distribution Shift.
Part 7 Chapter 119 & Appendix AW.
"""
import numpy as np


def softmax(z: np.ndarray) -> np.ndarray:
    z_shift = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z_shift)
    return e / e.sum(axis=-1, keepdims=True)


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected Calibration Error across confidence bins."""
    conf = p.max(axis=-1)
    cor = (p.argmax(axis=-1) == y)
    e = 0.0
    for lo in np.linspace(0.0, 1.0, bins, endpoint=False):
        m = (conf > lo) & (conf <= lo + 1.0 / bins)
        if m.any():
            e += m.mean() * abs(cor[m].mean() - conf[m].mean())
    return float(e)


def fit_temperature(logits: np.ndarray, y: np.ndarray, grid=np.linspace(0.25, 5.0, 96)) -> float:
    """Fit optimal temperature scalar T minimizing negative log likelihood on validation data."""
    best_t, best_nll = 1.0, float("inf")
    for t in grid:
        probs = softmax(logits / t)
        nll = -np.log(probs[np.arange(len(y)), y] + 1e-12).mean()
        if nll < best_nll:
            best_t, best_nll = float(t), float(nll)
    return best_t
