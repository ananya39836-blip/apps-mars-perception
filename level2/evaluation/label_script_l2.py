"""Level 2 Milestone Designation Evaluator and Release Gate Engine.
Part 12 Chapters 189, 216 & Appendix CR/CU.
"""

KEYS_L2 = [
    "data_provenance", "licence_ok", "label_audit", "taxonomy_map",
    "split_leak_free", "domain_gap", "depth_validity", "real_calibration",
    "transfer_eval", "kinematic_model", "local_planner", "interface_schema",
    "latency_budget", "temporal_fusion", "l1_regression", "docs_traceability"
]


def level2_label(ev: dict) -> str:
    """Evaluate Level 2 milestone status mechanically across the 16 requirements.
    Weakest item decides. Never exceeds its lowest result.
    """
    if any(not ev.get(k, {}).get("exists", False) for k in KEYS_L2):
        return "L2-not-met"
    if any(not (ev[k].get("executed") is True and ev[k].get("passed") is True) for k in KEYS_L2):
        return "L2-partial"
    return "L2-met (internal)"


def release_gate_l2(checks: dict) -> tuple:
    """Determine Level 2 release readiness based on strict non-default verification checks.
    Appendix CU.
    """
    bad = [k for k, v in checks.items() if v is not True]
    status = "blocked" if bad else "ready-for-review"
    return status, bad
