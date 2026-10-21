"""APPS: Automated Planetary Perception System (NASA TRL 7 Operational Prototype).

Production-grade, modular planetary rover perception, localization, mapping,
kinodynamic path planning, closed-loop trajectory control, hardware abstraction layer,
and FDIR executive for operational planetary analog environments.

Safety Invariants:
    PROTOTYPE_LOCK = True (Permanently latched; non-flight certified)
    NAVIGATION_READY = False (Explicit compile-time guard)
"""
from __future__ import annotations

# Compile-time research locks & safety invariants
PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False
SOFTWARE_VERSION: str = "2.7.0-trl7"

# Standard planetary physical constants
G_MARS: float = 3.71   # Surface gravitational acceleration [m/s^2]
G_EARTH: float = 9.80665 # Earth surface gravitational acceleration [m/s^2]
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

# Standardized 20 Scenario Class Identifiers (NASA TRL 7 Validation Campaign)
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

# Core subsystem exports
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl7_navigation.environment.scenario_generator import ScenarioConfig, ScenarioGenerator
from trl7_navigation.hardware.hardware_interface import (
    PacketHeader,
    IMUPacket,
    LiDARScanPacket,
    DepthFramePacket,
    WheelOdometryPacket,
    ActuatorCommand,
    ActuatorTelemetry,
    ISensorHAL,
    IActuatorHAL,
)
from trl7_navigation.hardware.simulated_hal import SimulatedHAL
from trl7_navigation.sensors.coordinate_transforms import TransformSE3, SensorExtrinsics
from trl7_navigation.sensors.sensor_validator import SensorValidator
from trl7_navigation.sensors.sensor_rig import IntegratedSensorRig
from trl7_navigation.perception.point_cloud_processor import PointCloudProcessor
from trl7_navigation.perception.elevation_mapping import ElevationMap25D
from trl7_navigation.perception.traversability import TraversabilityEstimator
from trl7_navigation.perception.perception_metrics import PerceptionMetrics
from trl7_navigation.localization.error_state_ekf import ErrorStateEKF
from trl7_navigation.localization.state_monitor import StateMonitor
from trl7_navigation.planning.collision_checker import CollisionChecker
from trl7_navigation.planning.kinodynamic_hybrid_astar import KinodynamicHybridAStar, PathPoint
from trl7_navigation.planning.path_tracker import PathTracker
from trl7_navigation.planning.safe_stop_controller import SafeStopController
from trl7_navigation.dynamics.rocker_bogie import RockerBogieSuspension
from trl7_navigation.dynamics.terramechanics import SoilParameters, TerramechanicsModel
from trl7_navigation.dynamics.multibody_rover import MultibodyRover
from trl7_navigation.executive.state_machine import AutonomyState, ExecutiveStateMachine
from trl7_navigation.mission.long_duration_mission import (
    MissionTelemetryRecord,
    MissionResult,
    LongDurationMissionRunner,
)
from trl7_navigation.experiments.campaign_runner import CampaignRunner, compute_wilson_ci

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
    "PlanetaryTerrain",
    "ScenarioConfig",
    "ScenarioGenerator",
    "PacketHeader",
    "IMUPacket",
    "LiDARScanPacket",
    "DepthFramePacket",
    "WheelOdometryPacket",
    "ActuatorCommand",
    "ActuatorTelemetry",
    "ISensorHAL",
    "IActuatorHAL",
    "SimulatedHAL",
    "TransformSE3",
    "SensorExtrinsics",
    "SensorValidator",
    "IntegratedSensorRig",
    "PointCloudProcessor",
    "ElevationMap25D",
    "TraversabilityEstimator",
    "PerceptionMetrics",
    "ErrorStateEKF",
    "StateMonitor",
    "CollisionChecker",
    "KinodynamicHybridAStar",
    "PathPoint",
    "PathTracker",
    "SafeStopController",
    "RockerBogieSuspension",
    "SoilParameters",
    "TerramechanicsModel",
    "MultibodyRover",
    "AutonomyState",
    "ExecutiveStateMachine",
    "MissionTelemetryRecord",
    "MissionResult",
    "LongDurationMissionRunner",
    "CampaignRunner",
    "compute_wilson_ci",
]
