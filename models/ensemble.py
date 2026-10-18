"""Gradient boosting ensemble classifier for terrain segmentation & uncertainty.
Chapter 24.5 and Appendix B.
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from models.features import features

S = 96


class Ensemble:
    def __init__(self, k=5):
        self.k = k
        self.m = []

    def fit(self, scenes, per=1200, seed=0):
        rng = np.random.default_rng(seed)
        X, y = [], []
        for img, d, lab in scenes:
            f = features(img, d)
            idx = rng.choice(S * S, per, replace=False)
            X.append(f[idx])
            y.append(lab.ravel()[idx])
        X, y = np.concatenate(X), np.concatenate(y)
        keep = y < 4
        X, y = X[keep], y[keep]
        for i in range(self.k):
            b = rng.choice(len(X), len(X), replace=True)
            mdl = HistGradientBoostingClassifier(
                max_iter=60, learning_rate=.12, max_leaf_nodes=24, random_state=i
            )
            mdl.fit(X[b], y[b])
            self.m.append(mdl)
        return self

    def predict(self, img, d):
        f = features(img, d)
        P = np.stack([m.predict_proba(f) for m in self.m])  # (k, N, C)
        mp = P.mean(0)
        ent = -(mp * np.log(mp + 1e-9)).sum(1) / np.log(4)
        epi = P.std(0).mean(1)  # ensemble disagreement
        return mp.reshape(S, S, 4), ent.reshape(S, S), epi.reshape(S, S)
