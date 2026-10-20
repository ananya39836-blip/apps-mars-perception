"""Automated Planetary Perception System (APPS) — NASA TRL 5 Surface Navigation Subsystem.

Target Technology Scope:
"Autonomous planetary rover terrain perception, local mapping, traversability estimation,
and collision-aware navigation in a representative simulated planetary environment."

Under PROTOTYPE_LOCK = True, navigation_ready is held strictly False at compile-time.
"""
from __future__ import annotations

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

# Gravitational acceleration for Martian surface (m/s^2)
G_MARS: float = 3.71

# Nominal rover physical dimensions & limits (185 kg class rover)
ROVER_MASS_KG: float = 185.0
ROVER_LENGTH_M: float = 1.20
ROVER_WIDTH_M: float = 0.90
ROVER_HEIGHT_M: float = 0.80
ROVER_WHEEL_RADIUS_M: float = 0.15
ROVER_TRACK_WIDTH_M: float = 0.85
ROVER_WHEELBASE_M: float = 1.00

# Kinodynamic & traversability constraints
MAX_SPEED_MPS: float = 0.50
MAX_ACCEL_MPS2: float = 0.20
MAX_CURVATURE_INV_M: float = 1.50   # Minimum turning radius rho_min = 0.67 m
MAX_TRAVERSABLE_SLOPE_DEG: float = 25.0
MAX_STEP_HEIGHT_M: float = 0.25
SAFETY_CLEARANCE_MARGIN_M: float = 0.30

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "G_MARS",
    "ROVER_MASS_KG",
    "ROVER_LENGTH_M",
    "ROVER_WIDTH_M",
    "ROVER_HEIGHT_M",
    "ROVER_WHEEL_RADIUS_M",
    "ROVER_TRACK_WIDTH_M",
    "ROVER_WHEELBASE_M",
    "MAX_SPEED_MPS",
    "MAX_ACCEL_MPS2",
    "MAX_CURVATURE_INV_M",
    "MAX_TRAVERSABLE_SLOPE_DEG",
    "MAX_STEP_HEIGHT_M",
    "SAFETY_CLEARANCE_MARGIN_M",
]
