"""Level 7 Verification Requirements, Key Registry and Milestone Label Evaluator.
Chapter 668 & Part 57.

Evaluates the 20 mandatory Level 7 verification keys (KEYS_L7) to compute the milestone designation:
- 'L7-met (internal)'
- 'L7-partial'
- 'L7-not-met'

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from typing import Dict, List, Tuple

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

KEYS_L7 = [
    "interstellar_lorentz_aberration",
    "interstellar_relativistic_doppler",
    "interstellar_spacetime_dilation",
    "interstellar_laser_sail_thrust",
    "interstellar_sail_thermal_equilibrium",
    "interstellar_dust_impact_dissipation",
    "interstellar_pulsar_xnav",
    "sgl_schwarzschild_optics",
    "sgl_optical_gain_amplification",
    "sgl_einstein_ring_deconvolution",
    "sgl_focal_stationkeeping",
    "dyson_statite_radiation_levitation",
    "dyson_coherent_phased_array",
    "dyson_interplanetary_power_beaming",
    "dyson_decentralized_consensus",
    "cryo_rsfq_100ghz_processor",
    "cryo_dilution_refrigerator_50mk",
    "cryo_spintronic_radiation_tolerance",
    "geoengineering_magnetosphere_shield",
    "geoengineering_ecological_governor",
]


def level7_label(evidence: Dict[str, Dict[str, bool]]) -> str:
    """Computes internal Level 7 milestone label from evidence dictionary."""
    if not isinstance(evidence, dict):
        return "L7-not-met"

    # All 20 keys must be present
    for k in KEYS_L7:
        if k not in evidence:
            return "L7-not-met"

    # Check existence
    if not all(evidence[k].get("exists", False) for k in KEYS_L7):
        return "L7-not-met"

    # Check pass status
    if not all(evidence[k].get("passed", False) for k in KEYS_L7):
        return "L7-not-met"

    # Check execution status
    if not all(evidence[k].get("executed", False) for k in KEYS_L7):
        return "L7-partial"

    return "L7-met (internal)"


def release_gate_l7(checks: Dict[str, bool]) -> Tuple[str, List[str]]:
    """Evaluates Level 7 release gate readiness."""
    mandatory = [
        "tests_passing",
        "prototype_locked",
        "nav_ready_false",
        "manifest_valid",
        "keys_complete",
    ]
    missing = [c for c in mandatory if not checks.get(c, False)]
    if not missing:
        return "READY-FOR-REVIEW", []
    return "BLOCKED", missing
