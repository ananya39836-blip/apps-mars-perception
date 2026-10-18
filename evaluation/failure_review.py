"""Failure review helpers and object miss evaluation.
Chapter 44 & Appendix P (Part 3).
"""
import csv
import numpy as np
from scipy import ndimage as ndi

HAZ = {2, 3, 4}


def object_miss_rate(unsafe: np.ndarray, lab: np.ndarray, area_frac: float = 0.5):
    """Fraction of true hazard regions (connected components) where less than area_frac of the
    region's pixels are marked unsafe. area_frac must be fixed before use.
    """
    haz = np.isin(lab, list(HAZ))
    comp, k = ndi.label(haz)
    if k == 0:
        return None
    missed = 0
    for i in range(1, k + 1):
        reg = comp == i
        if unsafe[reg].mean() < area_frac:
            missed += 1
    return missed / k


def review_table(scenes, results, unsafe_list, path: str = "failure_review.csv", top: int = 20, seed_info: str = ""):
    """Selects top worst scenes by missed hazard area and writes CSV table skeleton."""
    rows = []
    for idx, ((img, d, lab), (P, ent, epi), un) in enumerate(zip(scenes, results, unsafe_list)):
        haz = np.isin(lab, list(HAZ))
        miss = haz & ~un
        rows.append(dict(
            index=idx,
            seed_info=seed_info,
            missed_px=int(miss.sum()),
            hazard_px=int(haz.sum()),
            miss_rate=float(miss.sum() / max(haz.sum(), 1)),
            mean_entropy_on_miss=float(ent[miss].mean()) if miss.any() else None,
            mean_disagreement_on_miss=float(epi[miss].mean()) if miss.any() else None,
            object_miss=object_miss_rate(un, lab),
            cause=""
        ))
    rows.sort(key=lambda r: -r["missed_px"])
    if rows:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows[:top]:
                w.writerow(r)
    return rows[:top]
