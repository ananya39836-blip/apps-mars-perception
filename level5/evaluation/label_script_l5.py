"""Level 5 Verification Requirements, Key Registry and Milestone Label Evaluator.
Chapter 468 & Part 37.

Evaluates the 20 mandatory Level 5 verification keys (KEYS_L5) to compute the milestone designation:
- 'L5-met (internal)'
- 'L5-partial'
- 'L5-not-met'
"""
from typing import Dict, List, Tuple

KEYS_L5 = [
    "swarm_consensus",
    "swarm_potential_fields",
    "cave_zero_illumination_slam",
    "cave_tether_breadcrumb",
    "cryobot_thermal_drill",
    "cryobot_sonar_obstacle",
    "raman_spectroscopy_deconv",
    "biosignature_chirality_index",
    "reconfigurable_morphology",
    "modular_docking_actuator",
    "isru_regolith_yield",
    "isru_sintered_pad",
    "lasercom_dsoc_link",
    "lasercom_dtn_bundle",
    "quantum_enclave_crypto",
    "quantum_anti_spoofing",
    "continual_learning_replay",
    "actuator_wear_compensation",
    "planetary_protection_containment",
    "l4_regression"
]


def level5_label(evidence: Dict[str, Dict[str, bool]]) -> str:
    """Computes internal Level 5 milestone label from evidence dictionary."""
    if not isinstance(evidence, dict):
        return "L5-not-met"

    # All 20 keys must be present
    for k in KEYS_L5:
        if k not in evidence:
            return "L5-not-met"

    # Check existence
    if not all(evidence[k].get("exists", False) for k in KEYS_L5):
        return "L5-not-met"

    # Check pass status
    if not all(evidence[k].get("passed", False) for k in KEYS_L5):
        return "L5-not-met"

    # Check execution status
    if not all(evidence[k].get("executed", False) for k in KEYS_L5):
        return "L5-partial"

    return "L5-met (internal)"


def release_gate_l5(checks: Dict[str, bool]) -> Tuple[str, List[str]]:
    """Evaluates Level 5 release gate checklist."""
    unpassed = [k for k, v in checks.items() if not v]
    if not unpassed:
        return "ready-for-review", []
    return "blocked", unpassed
