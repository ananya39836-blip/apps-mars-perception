"""Level 6 Verification Requirements, Key Registry and Milestone Label Evaluator.
Chapter 568 & Part 47.

Evaluates the 20 mandatory Level 6 verification keys (KEYS_L6) to compute the milestone designation:
- 'L6-met (internal)'
- 'L6-partial'
- 'L6-not-met'
"""
from typing import Dict, List, Tuple

KEYS_L6 = [
    "interplanetary_relativistic_nav",
    "interplanetary_aerocapture",
    "lunar_psr_cryo_mining",
    "lunar_megawatt_microgrid",
    "titan_submersible_buoyancy",
    "titan_dense_atmosphere_flight",
    "deep_drilling_coiled_tubing",
    "deep_drilling_mud_telemetry",
    "venus_supercritical_aerodynamics",
    "venus_sic_high_temp_logic",
    "asteroid_binary_tracking",
    "asteroid_kinetic_impactor",
    "biohybrid_bacterial_biosensor",
    "biohybrid_memristive_crossbar",
    "quantum_cv_qkd_sifting",
    "quantum_entanglement_chsh",
    "self_replication_closure",
    "self_replication_slm_printer",
    "galactic_biosecurity_containment",
    "l5_regression"
]


def level6_label(evidence: Dict[str, Dict[str, bool]]) -> str:
    """Computes internal Level 6 milestone label from evidence dictionary."""
    if not isinstance(evidence, dict):
        return "L6-not-met"

    # All 20 keys must be present
    for k in KEYS_L6:
        if k not in evidence:
            return "L6-not-met"

    # Check existence
    if not all(evidence[k].get("exists", False) for k in KEYS_L6):
        return "L6-not-met"

    # Check pass status
    if not all(evidence[k].get("passed", False) for k in KEYS_L6):
        return "L6-not-met"

    # Check execution status
    if not all(evidence[k].get("executed", False) for k in KEYS_L6):
        return "L6-partial"

    return "L6-met (internal)"


def release_gate_l6(checks: Dict[str, bool]) -> Tuple[str, List[str]]:
    """Evaluates Level 6 release gate checklist."""
    unpassed = [k for k, v in checks.items() if not v]
    if not unpassed:
        return "ready-for-review", []
    return "blocked", unpassed
