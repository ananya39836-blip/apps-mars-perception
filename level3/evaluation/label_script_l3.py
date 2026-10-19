"""Level 3 Verification Requirements, Key Registry and Milestone Label Evaluator.
Chapter 265 & Appendix CT (Part 17).

Evaluates the 20 mandatory Level 3 verification keys (KEYS_L3) to compute the milestone designation:
- 'L3-met (internal)'
- 'L3-partial'
- 'L3-not-met'
"""
from typing import Dict, List, Tuple

KEYS_L3 = [
    "multibody_dynamics",
    "rocker_bogie",
    "terramechanics_model",
    "drawbar_pull",
    "slip_watchdog",
    "tactical_imu",
    "flash_lidar_3d",
    "dust_extinction",
    "negative_obstacles",
    "factor_graph_estimator",
    "voxel_map_3d",
    "state_lattice_planner",
    "safe_stopping_profile",
    "information_boundary_l3",
    "interface_lock_l3",
    "hpsc_timing_budget",
    "fdir_watchdog_hierarchy",
    "l2_regression",
    "l1_regression",
    "docs_traceability_l3"
]


def level3_label(evidence: Dict[str, Dict[str, bool]]) -> str:
    """Computes internal milestone label from evidence dictionary."""
    if not isinstance(evidence, dict):
        return "L3-not-met"

    # All 20 keys must be present
    for k in KEYS_L3:
        if k not in evidence:
            return "L3-not-met"

    # Check existence
    if not all(evidence[k].get("exists", False) for k in KEYS_L3):
        return "L3-not-met"

    # Check pass status
    if not all(evidence[k].get("passed", False) for k in KEYS_L3):
        return "L3-not-met"

    # Check execution status
    if not all(evidence[k].get("executed", False) for k in KEYS_L3):
        return "L3-partial"

    return "L3-met (internal)"


def release_gate_l3(checks: Dict[str, bool]) -> Tuple[str, List[str]]:
    """Evaluates Level 3 release gate checklist."""
    unpassed = [k for k, v in checks.items() if not v]
    if not unpassed:
        return "ready-for-review", []
    return "blocked", unpassed
