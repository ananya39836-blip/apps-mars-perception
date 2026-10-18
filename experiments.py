"""APPS-0.1 follow-up experiments: operating-point sweep (validation), then frozen test; E5 coverage-risk,
E6 ensemble size, E7 planner sensitivity. Synthetic data only.
"""
import numpy as np
import pickle
import json
import itertools
import sys
import apps01 as A
from sklearn.metrics import roc_auc_score


class APPSUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module in ("__main__", "apps01")) and name == "Ensemble":
            return A.Ensemble
        return super().find_class(module, name)


def load_model(path="apps01_model.pkl"):
    with open(path, "rb") as f:
        return APPSUnpickler(f).load()


if __name__ == "__main__":
    print("Loading model apps01_model.pkl...", flush=True)
    model = load_model("apps01_model.pkl")

    def preds(scenes, members=None):
        out = []
        old = model.m
        if members:
            model.m = old[:members]
        for i, d, l in scenes:
            out.append(model.predict(i, d))
        model.m = old
        return out

    print("Generating validation and test scenes...", flush=True)
    val = A.dataset(40, 400, False) + A.dataset(40, 401, True)
    test_n = A.dataset(60, 100, False)
    test_o = A.dataset(60, 200, True)

    print("Predicting on scenes...", flush=True)
    Rv = preds(val)
    Rn = preds(test_n)
    Ro = preds(test_o)

    def fsr(unsafe_list, scenes):
        return float(np.mean([A.false_safe(u, s[2]) for u, s in zip(unsafe_list, scenes)]))

    def boot(vals, n=1000, seed=0):
        r = np.random.default_rng(seed)
        v = np.asarray(vals, float)
        m = [r.choice(v, len(v)).mean() for _ in range(n)]
        return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))

    # ---- Operating point sweep on validation
    print("Running operating point sweep on validation...", flush=True)
    grid = []
    for thr, ut, et in itertools.product([.15, .25, .4, .6], [.35, .5, .65, .8, 9], [.05, .08, .12, 9]):
        U = [A.unsafe_map(*r, "C", thr=thr, ut=ut, et=et) for r in Rv]
        nav = A.nav_eval(val, {"x": U})["x"]
        grid.append(dict(
            thr=thr, ut=ut, et=et, fsr=fsr(U, val),
            no_path=nav["no_path"],
            collision=nav["collision"],
            success=nav["success"],
            unsafe=float(np.mean([u.mean() for u in U]))
        ))

    ok = [g for g in grid if g["fsr"] <= 0.03]
    best = min(ok, key=lambda g: (g["no_path"], g["fsr"])) if ok else min(grid, key=lambda g: g["fsr"])
    print("selected on validation:", best, flush=True)

    # ---- Frozen test, per-scene paired metrics with bootstrap CIs
    print("Running frozen test evaluation...", flush=True)
    def per_scene(scenes, R, mode, **kw):
        U = [A.unsafe_map(*r, mode, **kw) for r in R]
        fs = [A.false_safe(u, s[2]) for u, s in zip(U, scenes)]
        outs = []
        for u, s in zip(U, scenes):
            n = A.coarse(u).shape[0]
            truth = A.coarse(np.isin(s[2], list(A.HAZ)))
            blk = A.coarse(u)
            if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                outs.append(None)
                continue
            p = A.astar(blk, [(i, 0) for i in range(n)], n - 1)
            outs.append("nopath" if p is None else ("coll" if any(truth[q] for q in p) else "ok"))
        outs = [o for o in outs if o]
        return fs, outs

    test = {}
    for tag, sc, R in (("nominal", test_n, Rn), ("novel_terrain", test_o, Ro)):
        for name, mode, kw in (
            ("B_standard_ml", "B", {}),
            ("C_original", "C", {}),
            ("C_tuned", "C", dict(thr=best["thr"], ut=best["ut"], et=best["et"]))
        ):
            fs, o = per_scene(sc, R, mode, **kw)
            test[f"{tag}/{name}"] = dict(
                false_safe=boot(fs),
                success=boot([x == "ok" for x in o]),
                collision=boot([x == "coll" for x in o]),
                no_path=boot([x == "nopath" for x in o]),
                n_nav=len(o)
            )

    for k, v in test.items():
        print(k, {a: (round(b[0], 3), round(b[1], 3), round(b[2], 3)) if isinstance(b, tuple) else b for a, b in v.items()})

    # ---- E5 coverage vs risk (nominal+novel)
    print("Running E5 coverage vs risk...", flush=True)
    RR = Rn + Ro
    SC = test_n + test_o
    ent = np.concatenate([r[1].ravel() for r in RR])
    err = np.concatenate([(r[0].argmax(-1) != s[2]).ravel() for r, s in zip(RR, SC)])
    known = np.concatenate([(s[2] < 4).ravel() for s in SC])
    ent, err = ent[known], err[known]
    e5 = []
    for q in (1.0, .95, .9, .8, .7, .5):
        t = np.quantile(ent, q)
        keep = ent <= t
        e5.append(dict(coverage=float(keep.mean()), error_on_accepted=float(err[keep].mean())))
    print("E5", e5)

    # ---- E6 ensemble size
    print("Running E6 ensemble size...", flush=True)
    e6 = []
    for k in (1, 2, 3, 4, 5):
        R = preds(test_o, k)
        en = np.concatenate([r[1].ravel() for r in R])
        ep = np.concatenate([r[2].ravel() for r in R])
        nov = np.concatenate([(s[2] == 4).ravel() for s in test_o])
        sc = en + (ep * 5 if k > 1 else 0)
        e6.append(dict(
            members=k,
            auroc_entropy=float(roc_auc_score(nov, en)),
            auroc_combined=float(roc_auc_score(nov, sc)),
            ece=float(np.mean([A.ece(r[0], s[2]) for r, s in zip(R, test_o)]))
        ))
    print("E6", e6)

    # ---- E7 planner sensitivity (novel terrain)
    print("Running E7 planner sensitivity...", flush=True)
    e7 = []
    for c, bf in itertools.product((4, 6, 8, 12), (.05, .12, .25)):
        row = dict(cell=c, block_fraction=bf)
        for name, mode, kw in (("B", "B", {}), ("C_tuned", "C", dict(thr=best["thr"], ut=best["ut"], et=best["et"]))):
            res = {"ok": 0, "coll": 0, "nopath": 0}
            for s, r in zip(test_o, Ro):
                u = A.unsafe_map(*r, mode, **kw)
                n = A.S // c
                f = lambda m: m[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3)) > bf
                truth = f(np.isin(s[2], list(A.HAZ)))
                blk = f(u)
                if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                    continue
                p = A.astar(blk, [(i, 0) for i in range(n)], n - 1)
                res["nopath" if p is None else ("coll" if any(truth[q] for q in p) else "ok")] += 1
            tot = max(sum(res.values()), 1)
            row[name] = {k: round(v / tot, 3) for k, v in res.items()}
        e7.append(row)
    for r in e7:
        print(r)

    json.dump(
        dict(selected=best, grid=grid, test=test, E5=e5, E6=e6, E7=e7),
        open("experiments_results.json", "w"),
        indent=1
    )
    print("experiments_results.json successfully saved!", flush=True)
