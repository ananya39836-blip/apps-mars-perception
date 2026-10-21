"""APPS TRL 8 Navigation & Autonomy Research Package.

Technology Readiness Level 8 (TRL 8):
System prototype demonstration and qualification baseline for an integrated
autonomous planetary rover perception, localization, mapping, traversability
assessment, motion planning, closed-loop control, fault management, and telemetry system.

Safety Invariants:
    PROTOTYPE_LOCK: Must remain True to prevent unverified flight execution.
    NAVIGATION_READY: Must remain False in research and synthetic validation environments.
"""
from __future__ import annotations
from typing import Final, List, Dict, Any
from enum import Enum

# Permanent Research Safety Locks
PROTOTYPE_LOCK: Final[bool] = True
NAVIGATION_READY: Final[bool] = False

# Physical & Environmental Constants (Mars Nominal)
G_MARS: Final[float] = 3.72076  # Surface gravitational acceleration (m/s^2)
ROVER_MASS_KG: Final[float] = 850.0  # Flight-representative rover mass (kg)
ROVER_LENGTH_M: Final[float] = 2.80  # Overall structural length (m)
ROVER_WIDTH_M: Final[float] = 2.20  # Overall structural width (m)
ROVER_HEIGHT_M: Final[float] = 1.80  # Mast zenith height (m)
WHEEL_RADIUS_M: Final[float] = 0.25  # Nominal wheel radius (m)
WHEEL_BASE_M: Final[float] = 2.20  # Front to rear wheel base (m)
TRACK_WIDTH_M: Final[float] = 2.00  # Lateral track width (m)

# Kinematic & Motion Constraints
MAX_FORWARD_VELOCITY_MPS: Final[float] = 0.40  # Max nominal cruising speed (m/s)
MAX_REVERSE_VELOCITY_MPS: Final[float] = 0.15  # Max recovery speed (m/s)
MAX_CURVATURE_INV_M: Final[float] = 1.50  # Max turning curvature (m^-1), R_min = 0.67m
MAX_STEERING_ANGLE_RAD: Final[float] = 0.65  # Max wheel turn angle (~37.2 deg)
MAX_ACCELERATION_MPS2: Final[float] = 0.20  # Max longitudinal acceleration (m/s^2)
MAX_LATERAL_ACCEL_MPS2: Final[float] = 0.30  # Max lateral tip-over acceleration (m/s^2)
SAFE_STOP_DECEL_MPS2: Final[float] = -0.20  # Certified constant-jerk deceleration (m/s^2)
SAFE_STOP_JERK_MPS3: Final[float] = -0.50  # Constant jerk rate (m/s^3)

# Terrain & Hazard Thresholds
MAX_TRAVERSABLE_SLOPE_DEG: Final[float] = 25.0  # Soft cost threshold (deg)
TIP_OVER_LIMIT_SLOPE_DEG: Final[float] = 30.0  # Hard impassable geometric wall (deg)
MAX_STEP_OBSTACLE_M: Final[float] = 0.20  # Maximum clearable rock step height (m)
MIN_OBSTACLE_CLEARANCE_M: Final[float] = 0.35  # Footprint safety inflation margin (m)

# 13 Formal Operating States
class OperatingState(str, Enum):
    INITIALIZATION = "INITIALIZATION"
    SELF_TEST = "SELF_TEST"
    IDLE = "IDLE"
    PERCEPTION = "PERCEPTION"
    LOCALIZATION = "LOCALIZATION"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    REPLANNING = "REPLANNING"
    SAFE_STOP = "SAFE_STOP"
    RECOVERY = "RECOVERY"
    MISSION_COMPLETE = "MISSION_COMPLETE"
    MISSION_ABORT = "MISSION_ABORT"
    FAULT = "FAULT"

# 20 Standardized Operational Scenarios
SCENARIO_IDS: Final[List[str]] = [
    f"SC-{i:02d}" for i in range(1, 21)
]

__version__: Final[str] = "3.8.0-trl8"
__author__: Final[str] = "APPS Autonomy & Systems Qualification Team"
