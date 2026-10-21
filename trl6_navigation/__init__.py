"""APPS: Automated Planetary Perception System (NASA TRL 6 Integrated Prototype).

Production-grade, modular planetary rover perception, localization, mapping,
kinodynamic path planning, closed-loop trajectory control, and FDIR executive.

Safety Invariants:
    PROTOTYPE_LOCK = True (Permanently latched; non-flight certified)
    NAVIGATION_READY = False (Explicit compile-time guard)
"""
from __future__ import annotations

# Compile-time research locks & safety invariants
PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False
SOFTWARE_VERSION: str = "2.6.0-trl6"

# Standard planetary physical constants
G_MARS: float = 3.71  # Surface gravitational acceleration [m/s^2]
G_EARTH: float = 9.80665
G_MOON: float = 1.62

# Vehicle dimensions & mechanical limits (Curiosity/Perseverance scale analog)
ROVER_MASS_KG: float = 850.0
ROVER_LENGTH_M: float = 2.80
ROVER_WIDTH_M: float = 2.20
ROVER_HEIGHT_M: float = 1.80
ROVER_WHEEL_RADIUS_M: float = 0.25
ROVER_WHEEL_WIDTH_M: float = 0.40
ROVER_TRACK_GAUGE_M: float = 2.00
ROVER_WHEELBASE_M: float = 2.20

# Kinematic and dynamic constraints
MAX_SPEED_MPS: float = 0.40
NOMINAL_SPEED_MPS: float = 0.25
MAX_STEERING_ANGLE_RAD: float = 0.785398  # +/- 45 deg
MIN_TURNING_RADIUS_M: float = 0.67
MAX_CURVATURE_INV_M: float = 1.0 / MIN_TURNING_RADIUS_M  # ~1.4925 m^-1
MAX_TRAVERSABLE_SLOPE_DEG: float = 25.0
TIP_OVER_LIMIT_SLOPE_DEG: float = 32.0
MAX_STEP_HEIGHT_M: float = 0.25  # Equal to wheel radius
SAFETY_CLEARANCE_MARGIN_M: float = 0.30

# Standardized 20 Scenario Class Identifiers (NASA TRL 6 Campaign)
SCENARIO_CLASSES: list[str] = [
    "SC-01_flat_baseline",
    "SC-02_moderate_slopes",
    "SC-03_steep_slopes",
    "SC-04_dense_obstacle_field",
    "SC-05_narrow_passages",
    "SC-06_crater_avoidance",
    "SC-07_sensor_noise",
    "SC-08_sensor_dropout",
    "SC-09_localization_drift",
    "SC-10_wheel_slip_disturbance",
    "SC-11_unexpected_obstacles",
    "SC-12_completely_blocked",
    "SC-13_low_traction_regolith",
    "SC-14_environmental_replan",
    "SC-15_critical_fault_safestop",
    "SC-16_extended_horizon_traverse",
    "SC-17_unreachable_goal_recovery",
    "SC-18_communication_latency_jitter",
    "SC-19_transient_sensor_glitch",
    "SC-20_combined_multihazard_stress",
]

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "SOFTWARE_VERSION",
    "G_MARS",
    "G_EARTH",
    "G_MOON",
    "ROVER_MASS_KG",
    "ROVER_LENGTH_M",
    "ROVER_WIDTH_M",
    "ROVER_HEIGHT_M",
    "ROVER_WHEEL_RADIUS_M",
    "ROVER_WHEEL_WIDTH_M",
    "ROVER_TRACK_GAUGE_M",
    "ROVER_WHEELBASE_M",
    "MAX_SPEED_MPS",
    "NOMINAL_SPEED_MPS",
    "MAX_STEERING_ANGLE_RAD",
    "MIN_TURNING_RADIUS_M",
    "MAX_CURVATURE_INV_M",
    "MAX_TRAVERSABLE_SLOPE_DEG",
    "TIP_OVER_LIMIT_SLOPE_DEG",
    "MAX_STEP_HEIGHT_M",
    "SAFETY_CLEARANCE_MARGIN_M",
    "SCENARIO_CLASSES",
]
