"""Grid planning and traversability evaluation routines.
Chapter 6 & Chapter 24.7; Appendices B & H.
"""
import numpy as np
import heapq

S = 96
HAZ = {2, 3, 4}


def classical_unsafe(img: np.ndarray, d: np.ndarray) -> np.ndarray:
    """Baseline A: hand-made rules. dark+textured -> rock, strong depth gradient -> steep."""
    from scipy import ndimage as ndi
    g = img.mean(-1)
    m = ndi.uniform_filter(g, 5)
    sd = np.sqrt(np.maximum(ndi.uniform_filter(g * g, 5) - m * m, 0))
    gy, gx = np.gradient(ndi.gaussian_filter(d, 2))
    return ((g < .28) & (sd > .03)) | (np.hypot(gx, gy) > .30)


def unsafe_map(P, ent, epi, mode, thr=.25, ut=.35, et=.05):
    """Produces boolean unsafe pixel map from model probabilities and uncertainties."""
    haz = P[..., 2] + P[..., 3]
    if mode == "B":
        return P.argmax(-1) >= 2  # standard DL: argmax hazard
    return (haz > thr) | (ent > ut) | (epi > et)  # proposed: conservative + uncertainty


def coarse(unsafe: np.ndarray, c: int = 6) -> np.ndarray:
    """Part 1 fixed coarse grid reduction."""
    n = S // c
    return unsafe[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3)) > 0.12


def coarse_v2(mask: np.ndarray, c: int = 6, bf: float = 0.12) -> np.ndarray:
    """Part 3 Appendix H parameterised coarse grid reduction."""
    n = S // c
    return mask[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3)) > bf


def astar(blocked: np.ndarray, sources, goal_col: int):
    """Multi-source Dijkstra: any free cell in column 0 -> any free cell in goal_col."""
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
                c = g[u] + (1.414 if dy and dx else 1.0)
                if c < g.get(v, 1e9):
                    g[v] = c
                    par[v] = u
                    heapq.heappush(pq, (c, v))
    return None


def nav_eval(scenes, preds, c=6):
    """Original Part 1 evaluation."""
    res = {}
    for name in preds:
        ok = coll = nopath = 0
        L = []
        for (img, d, lab), up in zip(scenes, preds[name]):
            truth = coarse(np.isin(lab, list(HAZ)), c)
            blk = coarse(up, c)
            n = blk.shape[0]
            if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                continue
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


def nav_eval_v2(scenes, preds, c=6, bf=0.12, truth_bf=None):
    """Part 3 parameterised nav evaluation with strict truth option."""
    tbf = bf if truth_bf is None else truth_bf
    res = {}
    for name in preds:
        ok = coll = nopath = skipped = 0
        lengths = []
        for (img, d, lab), up in zip(scenes, preds[name]):
            truth = coarse_v2(np.isin(lab, list(HAZ)), c, tbf)
            blk = coarse_v2(up, c, bf)
            n = blk.shape[0]
            if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                skipped += 1
                continue
            p = astar(blk, [(i, 0) for i in range(n)], n - 1)
            if p is None:
                nopath += 1
            elif any(truth[q] for q in p):
                coll += 1
            else:
                ok += 1
                lengths.append(len(p))
        N = max(ok + coll + nopath, 1)
        res[name] = dict(
            success=ok / N, collision=coll / N, no_path=nopath / N,
            mean_len=float(np.mean(lengths)) if lengths else None,
            n=N, skipped=skipped, cell=c, block_fraction=bf, truth_bf=tbf
        )
    return res
