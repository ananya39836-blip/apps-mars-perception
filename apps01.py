"""APPS-0.1 - Automated Planetary Perception System (prototype, synthetic Mars-like terrain).
Pipeline: image(+noisy depth) -> pixel features -> ensemble segmentation -> uncertainty
-> traversability -> A* navigation test -> structured JSON. Pure numpy/scipy/sklearn.
"""
import numpy as np
import json
import heapq
import time
import pickle
import sys
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

S = 96
CLASSES = ["bedrock", "sand", "rock", "steep_slope"]  # trained classes; label 4 = novel terrain (never trained)
HAZ = {2, 3, 4}


def noise(rng, sigma, amp=1.0):
    n = ndi.gaussian_filter(rng.standard_normal((S, S)), sigma, mode="wrap")
    return amp * n / (n.std() + 1e-9)


def shadow_mask(H, az, el):
    dy, dx = np.sin(az), np.cos(az)
    t = np.tan(el)
    sh = np.zeros_like(H, bool)
    for k in range(1, 14):
        Hs = ndi.shift(H, (k * dy, k * dx), order=1, mode="nearest")
        sh |= (Hs - k * t) > H + 0.02
    return sh


def make_scene(rng, ood=False):
    H = noise(rng, 14, 3.0) + noise(rng, 5, 0.9)
    for _ in range(rng.integers(0, 3)):  # ridges -> steep terrain
        y, x = rng.integers(10, S - 10, 2)
        a = rng.uniform(0, np.pi)
        yy, xx = np.mgrid[:S, :S]
        d = (yy - y) * np.cos(a) - (xx - x) * np.sin(a)
        H += rng.uniform(2, 4) * np.exp(-(d / rng.uniform(4, 8)) ** 2)
    lab = np.zeros((S, S), int)
    lowland = ndi.gaussian_filter(H, 3) < np.percentile(H, rng.uniform(30, 50))
    lab[lowland] = 1
    Hr = H.copy()
    rocks = np.zeros((S, S), bool)
    yy, xx = np.mgrid[:S, :S]
    for _ in range(rng.integers(5, 14)):
        y, x = rng.integers(4, S - 4, 2)
        ry, rx = rng.uniform(2, 5, 2)
        th = rng.uniform(0, np.pi)
        u = (xx - x) * np.cos(th) + (yy - y) * np.sin(th)
        v = -(xx - x) * np.sin(th) + (yy - y) * np.cos(th)
        m = (u / rx) ** 2 + (v / ry) ** 2 < 1
        rocks |= m
        Hr += m * rng.uniform(0.6, 1.4) * np.clip(1 - ((u / rx) ** 2 + (v / ry) ** 2), 0, 1) ** .5
    gy, gx = np.gradient(ndi.gaussian_filter(H, 1.0))
    steep = np.hypot(gx, gy) > 0.42
    lab[steep & ~lowland] = 3
    lab[rocks] = 2
    if ood:  # novel terrain never seen in training
        for _ in range(rng.integers(1, 3)):
            y, x = rng.integers(15, S - 15, 2)
            r = rng.uniform(8, 14)
            m = ((yy - y) ** 2 + (xx - x) ** 2 < r ** 2) & ~rocks
            m = ndi.binary_dilation(m, iterations=1) & ~rocks
            lab[m] = 4
    alb = np.zeros((S, S, 3))
    base = {0: (.55, .34, .24), 1: (.74, .55, .36), 2: (.38, .29, .26), 3: (.52, .33, .24), 4: (.30, .33, .40)}
    for k, c in base.items():
        alb[lab == k] = c
    tex = {0: .10, 1: .02, 2: .12, 3: .10, 4: .05}
    for k, a in tex.items():
        alb[lab == k] *= 1 + a * noise(rng, 0.8)[lab == k][:, None]
    az, el = rng.uniform(0, 2 * np.pi), np.radians(rng.uniform(25, 60))
    gy, gx = np.gradient(Hr)
    nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    sun = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)])
    shade = np.clip(nrm @ sun, 0, 1) * 0.85 + 0.15
    shade = np.where(shadow_mask(Hr, az, el), shade * 0.35, shade)
    img = alb * shade[..., None] * rng.uniform(.8, 1.2)
    img += rng.normal(0, 0.02, img.shape)
    img = np.clip(img, 0, 1)
    depth = Hr + rng.normal(0, 0.15, Hr.shape)  # noisy stereo-like depth
    return img.astype(np.float32), depth.astype(np.float32), lab


def features(img, depth):
    g = img.mean(-1)
    F = [img[..., 0], img[..., 1], img[..., 2], img[..., 0] / (img[..., 2] + .05)]
    for s in (1, 2, 4):
        F.append(ndi.gaussian_filter(g, s))
    for w in (3, 7):
        m = ndi.uniform_filter(g, w)
        F.append(np.sqrt(np.maximum(ndi.uniform_filter(g * g, w) - m * m, 0)))
    gy, gx = np.gradient(ndi.gaussian_filter(g, 1))
    F.append(np.hypot(gx, gy))
    F.append(ndi.gaussian_laplace(g, 2))
    F.append(g - ndi.gaussian_filter(g, 8))
    for s in (2, 3):
        dy, dx = np.gradient(ndi.gaussian_filter(depth, s))
        F.append(np.hypot(dx, dy))
    F.append(ndi.gaussian_laplace(depth, 2))
    F.append(depth - ndi.gaussian_filter(depth, 6))
    return np.stack(F, -1).reshape(-1, len(F)).astype(np.float32)


def dataset(n, seed, ood=False):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        img, d, lab = make_scene(rng, ood)
        out.append((img, d, lab))
    return out


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
            mdl = HistGradientBoostingClassifier(max_iter=60, learning_rate=.12, max_leaf_nodes=24, random_state=i)
            mdl.fit(X[b], y[b])
            self.m.append(mdl)
        return self

    def predict(self, img, d):
        f = features(img, d)
        P = np.stack([m.predict_proba(f) for m in self.m])  # k, N, C
        mp = P.mean(0)
        ent = -(mp * np.log(mp + 1e-9)).sum(1) / np.log(4)
        epi = P.std(0).mean(1)  # ensemble disagreement
        return mp.reshape(S, S, 4), ent.reshape(S, S), epi.reshape(S, S)


# ---------- baselines & traversability ----------
def classical_unsafe(img, d):
    """Baseline A: hand-made rules. dark+textured -> rock, strong depth gradient -> steep."""
    g = img.mean(-1)
    m = ndi.uniform_filter(g, 5)
    sd = np.sqrt(np.maximum(ndi.uniform_filter(g * g, 5) - m * m, 0))
    gy, gx = np.gradient(ndi.gaussian_filter(d, 2))
    return ((g < .28) & (sd > .03)) | (np.hypot(gx, gy) > .30)


def unsafe_map(P, ent, epi, mode, thr=.25, ut=.35, et=.05):
    haz = P[..., 2] + P[..., 3]
    if mode == "B":
        return P.argmax(-1) >= 2  # standard DL: argmax hazard
    return (haz > thr) | (ent > ut) | (epi > et)  # proposed: conservative + uncertainty


def coarse(unsafe, c=6):
    n = S // c
    return unsafe[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3)) > 0.12


def astar(blocked, sources, goal_col):
    """Multi-source Dijkstra: any free cell in column 0 -> any free cell in the last column."""
    n = blocked.shape[0]
    pq = [(0, u) for u in sources if not blocked[u]]
    g = {u: 0 for _, u in pq}
    par = {}
    heapq.heapify(pq)
    while pq:
        c0, u = heapq.heappop(pq)
        if c0 > g.get(u, 1e9):
            continue
        if u[1] == goal_col:
            p = [u]
            while u in par:
                u = par[u]
                p.append(u)
            return p[::-1]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            v = (u[0] + dy, u[1] + dx)
            if 0 <= v[0] < n and 0 <= v[1] < n and not blocked[v]:
                c = g[u] + (1.414 if dy and dx else 1)
                if c < g.get(v, 1e9):
                    g[v] = c
                    par[v] = u
                    heapq.heappush(pq, (c, v))
    return None


def nav_eval(scenes, preds, c=6):
    res = {}
    for name in preds:
        ok = coll = nopath = 0
        L = []
        for (img, d, lab), up in zip(scenes, preds[name]):
            truth = coarse(np.isin(lab, list(HAZ)), c)
            blk = coarse(up, c)
            n = blk.shape[0]
            if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                continue  # skip scenes with no feasible truth route
            p = astar(blk, [(i, 0) for i in range(n)], n - 1)
            if p is None:
                nopath += 1
            elif any(truth[q] for q in p):
                coll += 1
            else:
                ok += 1
                L.append(len(p))
        N = max(ok + coll + nopath, 1)
        res[name] = dict(success=ok / N, collision=coll / N, no_path=nopath / N,
                         mean_len=float(np.mean(L)) if L else None, n=N)
    return res


def seg_metrics(P, lab):
    pred = P.argmax(-1)
    m = lab < 4
    r = {}
    r["pixel_acc"] = float((pred[m] == lab[m]).mean())
    r["mIoU"] = float(np.mean([
        ((pred == k) & (lab == k)).sum() / max(((pred == k) | (lab == k))[m | (pred == k)].sum(), 1)
        for k in range(4)
    ]))
    return r


def ece(P, lab, bins=10):
    m = lab < 4
    conf = P.max(-1)[m]
    cor = (P.argmax(-1)[m] == lab[m])
    e = 0
    for lo in np.linspace(0, 1, bins, endpoint=False):
        s = (conf > lo) & (conf <= lo + 1 / bins)
        if s.any():
            e += s.mean() * abs(cor[s].mean() - conf[s].mean())
    return float(e)


def false_safe(unsafe, lab):
    h = np.isin(lab, list(HAZ))
    return float((~unsafe & h).sum() / max(h.sum(), 1))


def observation_record(scene_id, P, ent, epi, unsafe):
    objs = []
    rock = ndi.label(P.argmax(-1) == 2)[0]
    for i, sl in enumerate(ndi.find_objects(rock), 1):
        area = int((rock[sl] == i).sum())
        if area < 12:
            continue
        cy, cx = ndi.center_of_mass(rock == i)
        objs.append(dict(type="rock", location_px=[int(cx), int(cy)], area_px=area,
                         obstacle_candidate=True, mean_uncertainty=float(ent[rock == i].mean())))
    unc = ent > .35
    return dict(
        scene_id=scene_id,
        image_size=[S, S],
        objects=objs,
        terrain_fraction={c: float((P.argmax(-1) == k).mean()) for k, c in enumerate(CLASSES)},
        uncertain_fraction=float(unc.mean()),
        unsafe_fraction=float(unsafe.mean()),
        terrain_assessment=dict(status="image_and_noisy_depth_only", map_available=True, calibrated_on="synthetic_data_only"),
        scientific_targets=[],
        navigation_ready=False,
        limitations=["trained on synthetic terrain only; no Mars performance claimed",
                     "cannot determine mineral composition",
                     "depth is simulated noisy stereo"]
    )


if __name__ == "__main__":
    t0 = time.time()
    ntr = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    print(f"Starting APPS-0.1 training with {ntr} scenes...", flush=True)
    train = dataset(ntr, 1)
    model = Ensemble(5).fit(train)
    print("trained", time.time() - t0, flush=True)
    pickle.dump(model, open("apps01_model.pkl", "wb"))

    rep = {}
    for tag, ood, seed in (("in_distribution", False, 100), ("novel_terrain_OOD", True, 200)):
        test = dataset(60, seed, ood)
        R = [model.predict(i, d) for i, d, _ in test]
        U = {
            "A_classical": [classical_unsafe(i, d) for i, d, _ in test],
            "B_standard_ml": [unsafe_map(*r, "B") for r in R],
            "C_APPS_uncertainty": [unsafe_map(*r, "C") for r in R]
        }
        r = dict(
            false_safe_rate={k: float(np.mean([false_safe(u, t[2]) for u, t in zip(v, test)])) for k, v in U.items()},
            unsafe_area={k: float(np.mean([u.mean() for u in v])) for k, v in U.items()},
            navigation=nav_eval(test, U)
        )
        seg = [seg_metrics(p[0], t[2]) for p, t in zip(R, test)]
        r["segmentation"] = {k: float(np.mean([s[k] for s in seg])) for k in seg[0]}
        r["ECE"] = float(np.mean([ece(p[0], t[2]) for p, t in zip(R, test)]))
        mm = np.concatenate([(t[2] < 4).ravel() for t in test])
        ent = np.concatenate([p[1].ravel() for p in R])
        err = np.concatenate([(p[0].argmax(-1) != t[2]).ravel() for p, t in zip(R, test)])
        r["uncertainty_AUROC_for_errors"] = float(roc_auc_score(err[mm], ent[mm]))
        if ood:
            nov = np.concatenate([(t[2] == 4).ravel() for t in test])
            epi = np.concatenate([p[2].ravel() for p in R])
            r["uncertainty_AUROC_novel_terrain_entropy"] = float(roc_auc_score(nov, ent))
            r["uncertainty_AUROC_novel_terrain_disagreement"] = float(roc_auc_score(nov, epi))
        rep[tag] = r
        print(tag, json.dumps(r, indent=1), flush=True)

    json.dump(rep, open("evaluation_results.json", "w"), indent=1)

    # demo outputs
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    demo = dataset(3, 300, True)
    fig, ax = plt.subplots(3, 5, figsize=(15, 9))
    recs = []
    cm = np.array([[.55, .34, .24], [.9, .8, .4], [.2, .2, .2], [.8, .2, .2], [.2, .4, .9]])
    for r_, (img, d, lab) in enumerate(demo):
        P, ent, epi = model.predict(img, d)
        un = unsafe_map(P, ent, epi, "C")
        recs.append(observation_record(f"synthetic_{r_:03d}", P, ent, epi, un))
        for a, im, t in zip(ax[r_], (img, cm[lab], cm[P.argmax(-1)], ent, un),
                            ("image", "truth (blue=novel)", "prediction", "uncertainty", "unsafe map")):
            a.imshow(im, cmap="magma" if t == "uncertainty" else "gray" if t == "unsafe map" else None)
            a.set_title(t)
            a.axis("off")
    plt.tight_layout()
    plt.savefig("apps01_demo.png", dpi=80)
    json.dump(recs, open("sample_observations.json", "w"), indent=1)
    print("done", time.time() - t0)
