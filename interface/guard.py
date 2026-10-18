"""navigation_ready Guard module.
Chapter 70, Appendix AB (Part 5) - Task 34.
"""
import math

PROTOTYPE_LOCK = True  # first version: the flag can never be true. Unlocking is a separate, reviewed change.


def _ok_fraction(x, bound):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0.0 <= x <= bound


def evaluate_readiness(evidence: dict, bounds: dict) -> dict:
    """Checks the five conditions of Chapter 8.3 of Part 1. Missing, malformed or
    non-finite evidence counts as failing. Returns the flag and plain-language reasons.
    """
    r = []
    if evidence.get("traversability_map") is not True:
        r.append("no traversability map")
    if evidence.get("geometry_validated_for_frame") is not True:
        r.append("geometry not validated for this frame")
    if not _ok_fraction(evidence.get("unsafe_fraction"), bounds.get("unsafe_max", 1.0)):
        r.append("unsafe fraction missing or out of bounds")
    if not _ok_fraction(evidence.get("uncertain_fraction"), bounds.get("uncertain_max", 1.0)):
        r.append("uncertain fraction missing or out of bounds")
    if evidence.get("sensor_consistency_passed") is not True:
        r.append("sensor consistency checks not passed")
    if evidence.get("model_version") not in bounds.get("approved_models", ()):
        r.append("model version not approved for current conditions")
        
    by_checks = len(r) == 0
    if PROTOTYPE_LOCK and by_checks:
        r.append("prototype lock: flag held false pending reviewed unlock")
        
    return dict(
        navigation_ready=bool(by_checks and not PROTOTYPE_LOCK),
        reasons=r,
        checks_passed=by_checks
    )
