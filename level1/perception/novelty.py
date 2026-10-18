"""Level 1 Feature-Space Novelty Detection & RankGate.
Part 7 Chapter 120, Part 4 Chapters 58-59.
"""
import numpy as np


class MahalanobisOOD:
    """Distance of a pixel feature vector to nearest training cluster with shrunk covariance."""
    def __init__(self):
        self.mu = []
        self.P = []

    def fit(self, X: np.ndarray, y: np.ndarray, shrink: float = 0.1):
        self.mu, self.P = [], []
        d = X.shape[1]
        for k in np.unique(y):
            Xk = X[y == k]
            mu = Xk.mean(0)
            S = np.cov(Xk, rowvar=False)
            S = (1.0 - shrink) * S + shrink * (np.trace(S) / d) * np.eye(d)
            self.mu.append(mu)
            self.P.append(np.linalg.inv(S))
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        d = X.shape[1]
        out = [np.einsum("ij,jk,ik->i", X - m, P, X - m) / d for m, P in zip(self.mu, self.P)]
        return np.min(np.stack(out), 0)


class RankGate:
    """Percentile-based multi-cue uncertainty and novelty gate."""
    def __init__(self):
        self.ref = {}

    def fit(self, clean_scores: dict):
        self.ref = {k: np.sort(np.asarray(v, float)) for k, v in clean_scores.items()}
        return self

    def percentile(self, name: str, x: np.ndarray) -> np.ndarray:
        r = self.ref[name]
        return np.searchsorted(r, x, side="right") / len(r)

    def unsafe(self, scores: dict, q: dict) -> np.ndarray:
        out = None
        for k, x in scores.items():
            f = self.percentile(k, x) > q[k]
            out = f if out is None else (out | f)
        return out
