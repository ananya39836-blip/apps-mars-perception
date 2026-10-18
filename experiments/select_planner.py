"""Operating point and block fraction selection drivers for Tasks 2 and 22.
Supports Part 3 Appendix J and Part 4 Appendix R.
"""
import json
import itertools
import datetime
import os
import sys
import pickle
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import apps01 as A
from nav_v2 import nav_eval_v2, coarse_v2

# Pickle compatibility
sys.modules['__main__'].Ensemble = A.Ensemble

RULE_V1 = (
    "Choose the block fraction with the lowest no-path rate such that validation collision "
    "rate is 0 under the strict truth setting. Ties: lower false-safe, then larger bf."
)

RULE_V2 = (
    "Per condition, strict truth. Constraint: zero collisions in BOTH conditions and cell-level "
    "false-safe not above the most conservative candidate. Objective: minimise the larger no-path "
    "rate. Tie: smaller block fraction, then smaller cell. Fallback: select nothing."
)

PERC = dict(thr=0.15, ut=0.35, et=0.05)


def cell_false_safe(scenes, unsafe_list, c, bf):
    """Share of truly hazardous cells (strict truth) that the planner mask leaves free."""
    miss = tot = 0
    for (img, d, lab), up in zip(scenes, unsafe_list):
        t = coarse_v2(np.isin(lab, list(A.HAZ)), c, 0.0)
        b = coarse_v2(up, c, bf)
        miss += int((t & ~b).sum())
        tot += int(t.sum())
    return miss / max(tot, 1)


def select_v1(model, val_nominal_seed=500, val_novel_seed=501, n=40):
    val = A.dataset(n, val_nominal_seed, False) + A.dataset(n, val_novel_seed, True)
    R = [model.predict(i, d) for i, d, _ in val]
    U = [A.unsafe_map(*r, "C", **PERC) for r in R]
    grid = []
    for c, bf in itertools.product((4, 6, 8), (0.05, 0.12, 0.18, 0.25, 0.35, 0.50)):
        r = nav_eval_v2(val, {"C": U}, c=c, bf=bf, truth_bf=0.0)["C"]
        grid.append(dict(cell=c, bf=bf, **{k: r[k] for k in ("success", "collision", "no_path", "n", "skipped")}))
    ok = [g for g in grid if g["collision"] == 0.0]
    best = min(ok, key=lambda g: (g["no_path"], -g["bf"])) if ok else None
    out = dict(date=str(datetime.date.today()), rule=RULE_V1, seeds=dict(val_nominal=val_nominal_seed, val_novel=val_novel_seed),
               perception=PERC, grid=grid, selected=best)
    with open("planner_selection.json", "w") as f:
        json.dump(out, f, indent=1)
    return out


def select_v2(model, val_nom, val_nov, cells=(4, 6, 8), bfs=(0.05, 0.12, 0.18, 0.25, 0.35, 0.50)):
    U = {}
    for name, val in (("nominal", val_nom), ("novel", val_nov)):
        R = [model.predict(i, d) for i, d, _ in val]
        U[name] = (val, [A.unsafe_map(*r, "C", **PERC) for r in R])
    grid = []
    for c, bf in itertools.product(cells, bfs):
        row = dict(cell=c, bf=bf)
        for name, (val, un) in U.items():
            r = nav_eval_v2(val, {"C": un}, c=c, bf=bf, truth_bf=0.0)["C"]
            row[name] = {k: r[k] for k in ("success", "collision", "no_path", "n", "skipped")}
            row[name]["cell_false_safe"] = cell_false_safe(val, un, c, bf)
        grid.append(row)
    ref = max(g[k]["cell_false_safe"] for g in grid if g["bf"] == min(bfs) for k in U)
    ok = [g for g in grid if all(g[k]["collision"] == 0.0 and g[k]["cell_false_safe"] <= ref for k in U)]
    best = min(ok, key=lambda g: (max(g[k]["no_path"] for k in U), g["bf"], g["cell"])) if ok else None
    out = dict(date=str(datetime.date.today()), rule=RULE_V2, perception=PERC, grid=grid, selected=best)
    with open("planner_selection_v2.json", "w") as f:
        json.dump(out, f, indent=1)
    return out


class APPSUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module in ("__main__", "apps01")) and name == "Ensemble":
            return A.Ensemble
        return super().find_class(module, name)


if __name__ == "__main__":
    with open("apps01_model.pkl", "rb") as f:
        model = APPSUnpickler(f).load()
    print("Running planner selection v1...")
    out1 = select_v1(model)
    print("Selected v1:", out1["selected"])
    print("Running planner selection v2...")
    val_nom = A.dataset(40, 500, False)
    val_nov = A.dataset(40, 501, True)
    out2 = select_v2(model, val_nom, val_nov)
    print("Selected v2:", out2["selected"])
