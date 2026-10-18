"""Automated Markdown & LaTeX Report Table Formatter.
Part 6 Appendix AN & Part 9 Appendix BO (Task 78).
"""
import numpy as np


def md_table(rows: list, cols: list) -> str:
    """Format dictionary records into GitHub Flavored Markdown table."""
    if not rows or not cols:
        return ""
    s = "| " + " | ".join(cols) + " |\n|" + ":---:|" * len(cols) + "\n"
    for r in rows:
        s += "| " + " | ".join(str(r.get(c, "-")) for c in cols) + " |\n"
    return s


def mission_metrics(results: list) -> dict:
    """Compute aggregate mission statistics across attempted closed-loop trials."""
    N = len(results)
    if N == 0:
        return dict(n=0)
    c = lambda k: sum(r["outcome"] == k for r in results)
    withd = [r for r in results if r.get("discovered", 0) > 0]
    ok = [r for r in results if r.get("outcome") == "success"]
    return dict(
        n=N,
        success=float(c("success") / N),
        collision=float(c("collision") / N),
        no_path=float(c("no_path") / N),
        rejected=float(c("rejected") / N),
        safe_stop=float(c("safe_stop") / N),
        timeout=float(c("timeout") / N),
        any_collision=float(sum(bool(r.get("collided", False)) for r in results) / N),
        recovery=float(sum(r["outcome"] == "success" for r in withd) / len(withd)) if withd else None,
        n_with_discovery=len(withd),
        mean_steps_success=float(np.mean([r["steps"] for r in ok])) if ok else None
    )


def false_safe_map(est: np.ndarray, seen: np.ndarray, truth: np.ndarray):
    """Cell-level observed-hazard false-safe rate."""
    h = truth & seen
    if h.sum() == 0:
        return None
    return float((h & ~est).sum() / h.sum())
