"""6-Wheel Rocker-Bogie Kinematic Suspension Model (TRL 7).

Resolves ground contact, rocker articulation, bogie pitch, and differential cross-bar
coupling for planetary exploration rovers traversing 3D non-planar terrain.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    ROVER_MASS_KG,
    ROVER_TRACK_GAUGE_M,
    ROVER_WHEELBASE_M,
    ROVER_WHEEL_RADIUS_M,
    G_MARS,
)
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain


class RockerBogieSuspension:
    """Kinematic model of the 6-wheel articulated rocker-bogie suspension."""

    def __init__(
        self,
        wheelbase_m: float = ROVER_WHEELBASE_M,
        track_gauge_m: float = ROVER_TRACK_GAUGE_M,
        wheel_radius_m: float = ROVER_WHEEL_RADIUS_M,
        rover_mass_kg: float = ROVER_MASS_KG,
        gravity_mps2: float = G_MARS,
    ) -> None:
        self.L = float(wheelbase_m)
        self.W = float(track_gauge_m)
        self.r_wheel = float(wheel_radius_m)
        self.mass = float(rover_mass_kg)
        self.g = float(gravity_mps2)

        # Nominal wheel offsets in body frame [x, y]
        # 0: Front-Left, 1: Middle-Left, 2: Rear-Left
        # 3: Front-Right, 4: Middle-Right, 5: Rear-Right
        half_w = self.W * 0.5
        half_l = self.L * 0.5
        self.nominal_wheel_offsets = np.array([
            [ half_l,  half_w],  # FL
            [    0.0,  half_w],  # ML
            [-half_l,  half_w],  # RL
            [ half_l, -half_w],  # FR
            [    0.0, -half_w],  # MR
            [-half_l, -half_w],  # RR
        ], dtype=np.float64)

    def resolve_ground_contact(
        self,
        rover_x: float,
        rover_y: float,
        rover_yaw: float,
        terrain: PlanetaryTerrain,
    ) -> Dict[str, Any]:
        """Calculates 3D coordinates, rocker angles, and normal forces for all 6 wheels."""
        cy = math.cos(rover_yaw)
        sy = math.sin(rover_yaw)

        wheel_positions = np.zeros((6, 3), dtype=np.float64)

        for i in range(6):
            bx, by = self.nominal_wheel_offsets[i]
            wx = rover_x + (cy * bx - sy * by)
            wy = rover_y + (sy * bx + cy * by)
            wz = terrain.get_elevation_at(wx, wy) + self.r_wheel
            wheel_positions[i] = [wx, wy, wz]

        # Articulation angles
        # Left side: bogie pitch between ML (index 1) and RL (index 2)
        dz_bogie_l = wheel_positions[1, 2] - wheel_positions[2, 2]
        dx_bogie_l = np.linalg.norm(wheel_positions[1, :2] - wheel_positions[2, :2])
        bogie_angle_left = math.atan2(dz_bogie_l, max(0.1, dx_bogie_l))

        # Right side: bogie pitch between MR (index 4) and RR (index 5)
        dz_bogie_r = wheel_positions[4, 2] - wheel_positions[5, 2]
        dx_bogie_r = np.linalg.norm(wheel_positions[4, :2] - wheel_positions[5, :2])
        bogie_angle_right = math.atan2(dz_bogie_r, max(0.1, dx_bogie_r))

        # Differential bar tilt couples left and right rockers
        z_left_mean = np.mean(wheel_positions[0:3, 2])
        z_right_mean = np.mean(wheel_positions[3:6, 2])
        differential_tilt = math.atan2(z_left_mean - z_right_mean, self.W)

        # Normal load distribution (quasi-static equilibrium under gravity)
        # Total vehicle weight W = m * g
        total_weight = self.mass * self.g
        # Equalized distribution via rocker-bogie differential (approx 1/6 per wheel on flat ground)
        # Adjust for lateral load transfer based on differential tilt
        lat_ratio = np.clip(differential_tilt / math.radians(25.0), -0.5, 0.5)
        normal_forces = np.ones(6) * (total_weight / 6.0)
        normal_forces[0:3] *= (1.0 - lat_ratio)
        normal_forces[3:6] *= (1.0 + lat_ratio)

        return {
            "wheel_positions_world": wheel_positions,
            "bogie_angle_left_rad": bogie_angle_left,
            "bogie_angle_right_rad": bogie_angle_right,
            "differential_tilt_rad": differential_tilt,
            "wheel_normal_forces_n": normal_forces,
        }
