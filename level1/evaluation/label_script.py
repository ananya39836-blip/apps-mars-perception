"""Level 1 Designation Evaluator and Release Gate Engine.
Part 10 Appendices BW & BX (Tasks 81 & 88).
"""

KEYS = [
    "audit", "modular", "partial_obs", "perception", "risk_in_nav", "mission_sim", "replan",
    "explicit_failure", "baselines", "metrics_from_trials", "tests_executed",
    "failures_recorded", "docs_match", "traceability"
]


def level1_label(evidence: dict) -> str:
    """Evaluate Level 1 milestone status mechanically across the 14 requirements.
    Weakest item decides. Never exceeds its lowest result.
    """
    if any(not evidence.get(k, {}).get("exists", False) for k in KEYS):
        return "L1-not-met"
    if any(not (evidence[k].get("executed") is True and evidence[k].get("passed") is True) for k in KEYS):
        return "L1-partial"
    return "L1-met (internal)"


def release_gate(checks: dict) -> tuple:
    """Determine release readiness based on strict non-default verification checks."""
    bad = [k for k, v in checks.items() if v is not True]
    status = "blocked" if bad else "ready-for-review"
    return status, bad
