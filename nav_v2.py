"""Appendix H. nav_eval_v2
Parameterised coarse, nav_eval and a strict truth option.
"""
import numpy as np
import apps01 as A


def coarse_v2(mask, c=6, bf=0.12):
    """Reduce a pixel mask to cells; a cell is True when the fraction of True pixels exceeds bf."""
    n = A.S // c
    return mask[:n * c, :n * c].reshape(n, c, n, c).mean((1, 3)) > bf


def nav_eval_v2(scenes, preds, c=6, bf=0.12, truth_bf=None):
    """truth_bf=None reproduces the Part 1 rule (truth uses the same bf).
    truth_bf=0.0 means any true hazard pixel makes a cell hazardous (strict truth).
    """
    tbf = bf if truth_bf is None else truth_bf
    res = {}
    for name in preds:
        ok = coll = nopath = skipped = 0
        lengths = []
        for (img, d, lab), up in zip(scenes, preds[name]):
            truth = coarse_v2(np.isin(lab, list(A.HAZ)), c, tbf)
            blk = coarse_v2(up, c, bf)
            n = blk.shape[0]
            if (~truth[:, 0]).sum() == 0 or (~truth[:, -1]).sum() == 0:
                skipped += 1
                continue
            p = A.astar(blk, [(i, 0) for i in range(n)], n - 1)
            if p is None:
                nopath += 1
            elif any(truth[q] for q in p):
                coll += 1
            else:
                ok += 1
                lengths.append(len(p))
        N = max(ok + coll + nopath, 1)
        res[name] = dict(
            success=ok / N,
            collision=coll / N,
            no_path=nopath / N,
            mean_len=float(np.mean(lengths)) if lengths else None,
            n=N,
            skipped=skipped,
            cell=c,
            block_fraction=bf,
            truth_bf=tbf
        )
    return res
