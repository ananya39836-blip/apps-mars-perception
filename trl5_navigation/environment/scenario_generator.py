"""Scenario Generator for Standardized Planetary Navigation Benchmarks (TRL 5).

Generates the 15 formal scenario classes with deterministic configurations,
hazard specifications, start/goal pairs, and sensor noise settings.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain


SCENARIO_CLASSES = [
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
]


class ScenarioGenerator:
    """Instantiates verified test scenarios for validation campaigns."""

    @staticmethod
    def build_scenario(scenario_id: str, seed: int = 42) -> Tuple[PlanetaryTerrain, Dict[str, Any]]:
        """Constructs the terrain and execution metadata for a given scenario ID."""
        rng = np.random.default_rng(seed)

        # Standard site dimensions: 35m x 35m
        size_m = 35.0
        start_state = np.array([4.0, 4.0, math.radians(45.0)], dtype=np.float64)  # x, y, theta
        goal_pos = np.array([25.0, 25.0], dtype=np.float64)                        # x, y
        sensor_noise_factor = 1.0
        lidar_dropout_prob = 0.05
        slip_disturbance_active = False
        pop_up_obstacle_active = False
        critical_fault_active = False
        is_blocked = False

        if "SC-01" in scenario_id or "flat_baseline" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.0, seed=seed)

        elif "SC-02" in scenario_id or "moderate_slopes" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=6.0, undulation_amplitude_m=0.20, undulation_wavelength_m=20.0, seed=seed)
            terrain.populate_rock_field(num_rocks=10, min_radius_m=0.3, max_radius_m=0.6)

        elif "SC-03" in scenario_id or "steep_slopes" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=12.0, undulation_amplitude_m=0.25, undulation_wavelength_m=20.0, seed=seed)
            terrain.populate_rock_field(num_rocks=8, min_radius_m=0.3, max_radius_m=0.6)

        elif "SC-04" in scenario_id or "dense_obstacle_field" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.15, seed=seed)
            terrain.populate_rock_field(num_rocks=18, min_radius_m=0.3, max_radius_m=0.8)

        elif "SC-05" in scenario_id or "narrow_passages" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.15, seed=seed)
            # Create a deliberate rock wall with a canyon passage at x=15
            for y_val in np.linspace(3.0, 32.0, 15):
                if 12.0 <= y_val <= 18.0:
                    continue  # Canyon passage for rover traverse
                terrain.add_boulder(center_x=15.0, center_y=y_val, radius_m=0.9, height_m=0.6)

        elif "SC-06" in scenario_id or "crater_avoidance" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.15, seed=seed)
            # Large impact crater right on direct path at (14.5, 14.5)
            terrain.add_crater(center_x=14.5, center_y=14.5, radius_m=3.5, depth_m=1.2, rim_height_m=0.3)

        elif "SC-07" in scenario_id or "sensor_noise" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=2.0, undulation_amplitude_m=0.15, seed=seed)
            terrain.populate_rock_field(num_rocks=12, min_radius_m=0.3, max_radius_m=0.7)
            sensor_noise_factor = 2.0

        elif "SC-08" in scenario_id or "sensor_dropout" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=2.0, undulation_amplitude_m=0.15, seed=seed)
            terrain.populate_rock_field(num_rocks=12, min_radius_m=0.3, max_radius_m=0.7)
            lidar_dropout_prob = 0.35

        elif "SC-09" in scenario_id or "localization_drift" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=2.0, undulation_amplitude_m=0.15, seed=seed)
            terrain.populate_rock_field(num_rocks=12, min_radius_m=0.3, max_radius_m=0.7)

        elif "SC-10" in scenario_id or "wheel_slip_disturbance" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=2.0, undulation_amplitude_m=0.15, seed=seed)
            # Inject loose sand patch along nominal path at (14.5, 14.5)
            terrain.add_loose_regolith_patch(center_x=14.5, center_y=14.5, radius_m=4.5, friction_coeff=0.25)
            slip_disturbance_active = True

        elif "SC-11" in scenario_id or "unexpected_obstacles" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.15, seed=seed)
            terrain.populate_rock_field(num_rocks=10, min_radius_m=0.3, max_radius_m=0.7)
            pop_up_obstacle_active = True

        elif "SC-12" in scenario_id or "completely_blocked" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.15, seed=seed)
            # Continuous impenetrable wall from y=0 to y=35 across x=15
            for y_val in np.linspace(0.0, 35.0, 18):
                terrain.add_boulder(center_x=15.0, center_y=y_val, radius_m=1.2, height_m=0.8)
            is_blocked = True

        elif "SC-13" in scenario_id or "low_traction_regolith" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=4.0, undulation_amplitude_m=0.3, seed=seed)
            terrain.regolith_friction[:] = 0.28
            terrain.populate_rock_field(num_rocks=15, min_radius_m=0.3, max_radius_m=0.7)

        elif "SC-14" in scenario_id or "environmental_replan" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.2, seed=seed)
            # Wall blocking direct corridor up to y=19, leaving clear detour route around y=24
            for y_val in np.linspace(2.0, 19.0, 10):
                terrain.add_boulder(center_x=15.0, center_y=y_val, radius_m=1.1, height_m=0.7)

        elif "SC-15" in scenario_id or "critical_fault_safestop" in scenario_id:
            terrain = PlanetaryTerrain(size_x_m=size_m, size_y_m=size_m, base_slope_deg=0.0, undulation_amplitude_m=0.2, seed=seed)
            terrain.populate_rock_field(num_rocks=12, min_radius_m=0.3, max_radius_m=0.7)
            critical_fault_active = True

        else:
            raise ValueError(f"Unknown scenario ID: {scenario_id}")

        metadata: Dict[str, Any] = {
            "scenario_id": scenario_id,
            "seed": seed,
            "start_state": start_state,
            "goal_pos": goal_pos,
            "sensor_noise_factor": sensor_noise_factor,
            "lidar_dropout_prob": lidar_dropout_prob,
            "slip_disturbance_active": slip_disturbance_active,
            "pop_up_obstacle_active": pop_up_obstacle_active,
            "critical_fault_active": critical_fault_active,
            "is_blocked": is_blocked,
            "num_boulders": len(terrain.boulders),
            "num_craters": len(terrain.craters),
        }

        return terrain, metadata
