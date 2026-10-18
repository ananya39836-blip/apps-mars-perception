"""Calibration and temperature scaling utilities.
Chapter 5.4, Appendix I (Part 3).
"""
import numpy as np


def scale_probs(P: np.ndarray, T: float) -> np.ndarray:
    """P: (..., C) averaged probabilities. Returns renormalised probabilities after temperature T."""
    logp = np.log(np.clip(P, 1e-9, 1.0)) / T
    logp -= logp.max(-1, keepdims=True)
    q = np.exp(logp)
    return q / q.sum(-1, keepdims=True)


def fit_temperature(P_list, lab_list, grid=np.linspace(0.5, 3.0, 51)):
    """Fit T on known-class pixels only (labels 0..3). Novel pixels (label 4) are excluded."""
    Ps, ys = [], []
    for P, lab in zip(P_list, lab_list):
        m = lab < 4
        Ps.append(P[m])
        ys.append(lab[m])
    P_all, y_all = np.concatenate(Ps), np.concatenate(ys)
    best_T, best_nll = 1.0, np.inf
    for T in grid:
        q = scale_probs(P_all, T)
        nll = -np.log(q[np.arange(len(y_all)), y_all] + 1e-9).mean()
        if nll < best_nll:
            best_T, best_nll = float(T), float(nll)
    return best_T, best_nll


def entropy_norm(P: np.ndarray) -> np.ndarray:
    """Normalised entropy scaled to [0, 1] by dividing by log(num_classes)."""
    return -(P * np.log(P + 1e-9)).sum(-1) / np.log(P.shape[-1])


def ece(P: np.ndarray, lab: np.ndarray, bins: int = 10) -> float:
    """Expected Calibration Error over known classes (labels < 4)."""
    m = lab < 4
    conf = P.max(-1)[m]
    cor = (P.argmax(-1)[m] == lab[m])
    e = 0.0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        s = (conf > lo) & (conf <= lo + 1.0 / bins)
        if s.any():
            e += s.mean() * abs(cor[s].mean() - conf[s].mean())
    return float(e)
