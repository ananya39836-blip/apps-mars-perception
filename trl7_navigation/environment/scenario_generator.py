"""TRL 7 Standardized Scenario Generator.

Generates 20 standardized, reproducible operational scenario classes (SC-01 to SC-20)
for validation in representative planetary analog environments.
Each scenario configures terrain topography, rock fields, craters, regolith friction,
lighting/shadows, sensor disturbance levels, and mission waypoints.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from trl7_navigation import (
    SCENARIO_CLASSES,
    ROVER_LENGTH_M,
    ROVER_WIDTH_M,
)
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain


@dataclass
class ScenarioConfig:
    """Configuration parameter set defining an operational test scenario."""
    scenario_id: str
    description: str
    terrain_size_x: float = 50.0
    terrain_size_y: float = 50.0
    resolution_m: float = 0.25
    base_slope_deg: float = 0.0
    undulation_amplitude_m: float = 0.3
    undulation_wavelength_m: float = 12.0
    start_pose: Tuple[float, float, float] = (5.0, 5.0, 0.0)  # x, y, yaw_rad
    goal_pose: Tuple[float, float] = (40.0, 40.0)             # x, y
    waypoints: List[Tuple[float, float]] = field(default_factory=list)
    boulders: List[Tuple[float, float, float, float]] = field(default_factory=list)  # x, y, radius, height
    craters: List[Tuple[float, float, float, float]] = field(default_factory=list)    # x, y, radius, depth
    friction_patches: List[Tuple[float, float, float, float, float]] = field(default_factory=list) # xmin, xmax, ymin, ymax, mu
    sun_elev_deg: float = 40.0
    sun_azim_deg: float = 45.0
    # Sensor & fault disturbance injections
    imu_noise_multiplier: float = 1.0
    lidar_noise_m: float = 0.02
    lidar_dropout_prob: float = 0.0
    dropout_duration_s: float = 0.0
    slip_bias: float = 0.05
    inject_fault: Optional[str] = None
    inject_fault_time_s: float = 0.0
    goal_is_unreachable: bool = False


class ScenarioGenerator:
    """Factory for standard operational test scenarios."""

    @staticmethod
    def get_supported_scenarios() -> List[str]:
        return list(SCENARIO_CLASSES)

    @classmethod
    def create_scenario(cls, scenario_id: str, seed: int = 42) -> Tuple[PlanetaryTerrain, ScenarioConfig]:
        """Constructs and populates terrain and configuration for scenario_id."""
        if scenario_id not in SCENARIO_CLASSES:
            raise ValueError(f"Unknown scenario_id: {scenario_id}. Supported: {SCENARIO_CLASSES}")

        rng = np.random.default_rng(seed)

        # Baseline defaults
        cfg = ScenarioConfig(
            scenario_id=scenario_id,
            description="Operational analog scenario",
            terrain_size_x=50.0,
            terrain_size_y=50.0,
            resolution_m=0.25,
            start_pose=(5.0, 5.0, 0.0),
            goal_pose=(40.0, 40.0),
        )

        if scenario_id == "SC-01_flat_baseline":
            cfg.description = "Flat baseline traverse over nominal bedrock with minimal hazards."
            cfg.undulation_amplitude_m = 0.1
            cfg.boulders = [(20.0, 20.0, 0.5, 0.2), (25.0, 30.0, 0.6, 0.25)]

        elif scenario_id == "SC-02_moderate_slopes":
            cfg.description = "Rolling hills and moderate slopes up to 12 degrees."
            cfg.undulation_amplitude_m = 0.40
            cfg.undulation_wavelength_m = 16.0
            cfg.base_slope_deg = 5.0

        elif scenario_id == "SC-03_steep_slopes":
            cfg.description = "Steep terrain near rover traversability limits (up to 22 deg)."
            cfg.base_slope_deg = 12.0
            cfg.undulation_amplitude_m = 0.50
            cfg.undulation_wavelength_m = 16.0

        elif scenario_id == "SC-04_dense_obstacle_field":
            cfg.description = "Dense boulder field requiring tortuous obstacle avoidance (>25% rock coverage)."
            cfg.undulation_amplitude_m = 0.2
            boulders = []
            for _ in range(35):
                bx = float(rng.uniform(10.0, 42.0))
                by = float(rng.uniform(10.0, 42.0))
                # Keep start and goal clear
                if np.hypot(bx - 5.0, by - 5.0) > 4.0 and np.hypot(bx - 40.0, by - 40.0) > 4.0:
                    r = float(rng.uniform(0.4, 1.2))
                    h = float(rng.uniform(0.2, 0.6))
                    boulders.append((bx, by, r, h))
            cfg.boulders = boulders

        elif scenario_id == "SC-05_narrow_passages":
            cfg.description = "Constrained chokepoints and boulder gates with widths near vehicle track gauge."
            cfg.undulation_amplitude_m = 0.2
            # Chokepoint 1 at x=20
            cfg.boulders = [
                (20.0, 10.0, 3.0, 0.8),
                (20.0, 17.5, 2.5, 0.8),
                (20.0, 25.0, 2.5, 0.8), # gate between 19.5 and 22.5 y
                (20.0, 35.0, 3.5, 0.8),
                # Chokepoint 2 at x=32
                (32.0, 22.0, 3.0, 0.8),
                (32.0, 32.0, 3.0, 0.8),
                (32.0, 42.0, 3.0, 0.8),
            ]

        elif scenario_id == "SC-06_crater_avoidance":
            cfg.description = "Multiple negative obstacle impact craters on nominal surface."
            cfg.undulation_amplitude_m = 0.15
            cfg.craters = [
                (18.0, 18.0, 3.5, 0.9),
                (28.0, 30.0, 4.0, 1.2),
                (35.0, 20.0, 2.8, 0.7),
            ]

        elif scenario_id == "SC-07_sensor_noise":
            cfg.description = "Nominal terrain with 3.5x elevated IMU noise and LiDAR ranging jitter."
            cfg.undulation_amplitude_m = 0.3
            cfg.imu_noise_multiplier = 3.5
            cfg.lidar_noise_m = 0.08
            cfg.boulders = [(15.0, 18.0, 0.8, 0.4), (28.0, 25.0, 0.9, 0.45)]

        elif scenario_id == "SC-08_sensor_dropout":
            cfg.description = "Intermittent sensor dropouts (LiDAR link drop for 1.8s mid-traverse)."
            cfg.undulation_amplitude_m = 0.3
            cfg.lidar_dropout_prob = 0.25
            cfg.dropout_duration_s = 2.0
            cfg.boulders = [(20.0, 22.0, 0.9, 0.4), (30.0, 28.0, 1.0, 0.5)]

        elif scenario_id == "SC-09_localization_drift":
            cfg.description = "High wheel slip inducing cumulative dead-reckoning drift."
            cfg.undulation_amplitude_m = 0.4
            cfg.slip_bias = 0.28
            cfg.friction_patches = [(10.0, 40.0, 10.0, 40.0, 0.40)]

        elif scenario_id == "SC-10_wheel_slip_disturbance":
            cfg.description = "Sudden low-traction regolith patch inducing severe wheel spin."
            cfg.undulation_amplitude_m = 0.3
            cfg.friction_patches = [
                (18.0, 30.0, 18.0, 30.0, 0.22),  # severe slip patch
            ]
            cfg.boulders = [(24.0, 24.0, 0.7, 0.35)]

        elif scenario_id == "SC-11_unexpected_obstacles":
            cfg.description = "Dynamic or unmapped obstacle directly obstructing planned nominal corridor."
            cfg.undulation_amplitude_m = 0.2
            cfg.boulders = [
                (22.0, 22.0, 1.4, 0.6), # directly along direct line
                (24.0, 23.5, 1.2, 0.5),
            ]

        elif scenario_id == "SC-12_completely_blocked":
            cfg.description = "Cul-de-sac canyon wall forcing autonomous dead-end detection and recovery."
            cfg.undulation_amplitude_m = 0.2
            # Barrier of boulders across diagonal
            cfg.boulders = [
                (20.0 + i * 1.5, 30.0 - i * 1.5, 1.5, 0.7) for i in range(-5, 8)
            ]

        elif scenario_id == "SC-13_low_traction_regolith":
            cfg.description = "Full regolith dune field with low friction and slope slip coupling."
            cfg.undulation_amplitude_m = 0.7
            cfg.undulation_wavelength_m = 10.0
            cfg.friction_patches = [(0.0, 50.0, 0.0, 50.0, 0.35)]

        elif scenario_id == "SC-14_environmental_replan":
            cfg.description = "Low sun angle causing extreme shadow occlusion requiring replanning."
            cfg.undulation_amplitude_m = 0.4
            cfg.sun_elev_deg = 12.0  # Very low sun, long shadows
            cfg.sun_azim_deg = 70.0
            cfg.boulders = [(20.0, 20.0, 1.5, 0.8), (30.0, 28.0, 1.6, 0.9)]

        elif scenario_id == "SC-15_critical_fault_safestop":
            cfg.description = "Critical actuator fault injected mid-traverse requiring certified safe stop."
            cfg.undulation_amplitude_m = 0.2
            cfg.inject_fault = "MOTOR_CONTROLLER_STALL"
            cfg.inject_fault_time_s = 15.0
            cfg.boulders = [(20.0, 20.0, 0.8, 0.4)]

        elif scenario_id == "SC-16_extended_horizon_traverse":
            cfg.description = "Long multi-waypoint traverse (>100 m) across extended terrain domain."
            cfg.terrain_size_x = 80.0
            cfg.terrain_size_y = 80.0
            cfg.start_pose = (5.0, 5.0, 0.0)
            cfg.goal_pose = (70.0, 70.0)
            cfg.waypoints = [(25.0, 15.0), (45.0, 40.0), (30.0, 65.0), (70.0, 70.0)]
            cfg.undulation_amplitude_m = 0.5
            cfg.boulders = [
                (20.0, 12.0, 1.0, 0.5), (40.0, 35.0, 1.2, 0.6),
                (35.0, 55.0, 1.0, 0.5), (60.0, 65.0, 1.1, 0.55)
            ]

        elif scenario_id == "SC-17_unreachable_goal_recovery":
            cfg.description = "Goal requested inside an impassable deep crater, testing goal standoff recovery."
            cfg.craters = [(35.0, 35.0, 5.0, 1.8)]
            cfg.goal_pose = (35.0, 35.0)  # dead center of crater
            cfg.goal_is_unreachable = True

        elif scenario_id == "SC-18_communication_latency_jitter":
            cfg.description = "High uplink/downlink telemetry latency and jitter between autonomy core and ground."
            cfg.undulation_amplitude_m = 0.3
            cfg.boulders = [(22.0, 22.0, 1.0, 0.5), (32.0, 30.0, 1.0, 0.5)]

        elif scenario_id == "SC-19_transient_sensor_glitch":
            cfg.description = "Telemetry packet corruption, NaN/Inf spikes, and transient IMU anomalies."
            cfg.undulation_amplitude_m = 0.3
            cfg.boulders = [(18.0, 18.0, 0.9, 0.45), (28.0, 26.0, 1.0, 0.5)]

        elif scenario_id == "SC-20_combined_multihazard_stress":
            cfg.description = "Combined stress: steep slopes, boulder field, low friction, low sun, and high noise."
            cfg.base_slope_deg = 14.0
            cfg.undulation_amplitude_m = 0.8
            cfg.sun_elev_deg = 15.0
            cfg.imu_noise_multiplier = 2.5
            cfg.lidar_noise_m = 0.06
            cfg.friction_patches = [(15.0, 35.0, 15.0, 35.0, 0.40)]
            boulders = []
            for _ in range(20):
                bx = float(rng.uniform(10.0, 38.0))
                by = float(rng.uniform(10.0, 38.0))
                if np.hypot(bx - 5.0, by - 5.0) > 4.0 and np.hypot(bx - 40.0, by - 40.0) > 4.0:
                    boulders.append((bx, by, float(rng.uniform(0.5, 1.2)), float(rng.uniform(0.3, 0.6))))
            cfg.boulders = boulders
            cfg.craters = [(26.0, 26.0, 3.0, 0.8)]

        # Construct PlanetaryTerrain from config
        terrain = PlanetaryTerrain(
            size_x_m=cfg.terrain_size_x,
            size_y_m=cfg.terrain_size_y,
            resolution_m=cfg.resolution_m,
            base_slope_deg=cfg.base_slope_deg,
            undulation_amplitude_m=cfg.undulation_amplitude_m,
            undulation_wavelength_m=cfg.undulation_wavelength_m,
            seed=seed,
        )

        for bx, by, br, bh in cfg.boulders:
            terrain.add_boulder(bx, by, br, bh)

        for cx, cy, cr, cd in cfg.craters:
            terrain.add_crater(cx, cy, cr, cd)

        for xmin, xmax, ymin, ymax, mu in cfg.friction_patches:
            terrain.set_regolith_friction_patch(xmin, xmax, ymin, ymax, mu)

        return terrain, cfg
