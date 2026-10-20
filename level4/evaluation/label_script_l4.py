"""Level 4 Verification Requirements, Key Registry and Milestone Label Evaluator.
Chapter 365 & Part 27.

Evaluates the 20 mandatory Level 4 verification keys (KEYS_L4) to compute the milestone designation:
- 'L4-met (internal)'
- 'L4-partial'
- 'L4-not-met'
"""
from typing import Dict, List, Tuple

KEYS_L4 = [
    "hierarchical_planner",
    "orbital_dem_fusion",
    "aegis_targeting",
    "science_novelty_ranker",
    "active_suspension",
    "wheel_walking_crab",
    "aerial_scout_coordination",
    "landing_site_certification",
    "online_bayesian_terramech",
    "slip_anticipation_monitor",
    "neuromorphic_event_stream",
    "snn_hazard_detector",
    "temporal_pddl_executive",
    "resource_constraint_solver",
    "environmental_resilience",
    "dust_storm_hibernation",
    "celestial_ephemeris_heading",
    "horizon_silhouette_relocalization",
    "hil_flight_assurance",
    "l3_regression"
]


def level4_label(evidence: Dict[str, Dict[str, bool]]) -> str:
    """Computes internal Level 4 milestone label from evidence dictionary."""
    if not isinstance(evidence, dict):
        return "L4-not-met"

    # All 20 keys must be present
    for k in KEYS_L4:
        if k not in evidence:
            return "L4-not-met"

    # Check existence
    if not all(evidence[k].get("exists", False) for k in KEYS_L4):
        return "L4-not-met"

    # Check pass status
    if not all(evidence[k].get("passed", False) for k in KEYS_L4):
        return "L4-not-met"

    # Check execution status
    if not all(evidence[k].get("executed", False) for k in KEYS_L4):
        return "L4-partial"

    return "L4-met (internal)"


def release_gate_l4(checks: Dict[str, bool]) -> Tuple[str, List[str]]:
    """Evaluates Level 4 release gate checklist."""
    unpassed = [k for k, v in checks.items() if not v]
    if not unpassed:
        return "ready-for-review", []
    return "blocked", unpassed
