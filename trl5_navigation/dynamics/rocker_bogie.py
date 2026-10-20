"""Rocker-Bogie Passive Suspension Kinematics & Wheel Load Equalization (TRL 5).

Models the 6-wheel rocker-bogie passive articulated suspension, differential averaging bar,
and normal ground contact force distribution under uneven planetary terrain.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

from trl5_navigation import G_MARS, ROVER_MASS_KG


class RockerBogieSuspension:
    """Calculates forward kinematics and normal load distribution across 6 wheels."""

    def __init__(
        self,
        rover_mass_kg: float = ROVER_MASS_KG,
        gravity_mps2: float = G_MARS,
        rocker_length_m: float = 0.55,
        bogie_length_m: float = 0.45
    ) -> None:
        self.mass = float(rover_mass_kg)
        self.g = float(gravity_mps2)
        self.total_weight_n = self.mass * self.g
        self.rocker_len = float(rocker_length_m)
        self.bogie_len = float(bogie_length_m)

    def compute_differential_bar_pitch(
        self,
        rocker_angle_left_rad: float,
        rocker_angle_right_rad: float
    ) -> float:
        """Computes main chassis differential pitch angle: theta_diff = (theta_L - theta_R) / 2."""
        return float((rocker_angle_left_rad - rocker_angle_right_rad) / 2.0)

    def distribute_wheel_normal_forces(
        self,
        wheel_contact_elevations_m: np.ndarray,
        terrain_slope_rad: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates normal ground reaction forces N_1 .. N_6 across all 6 wheels.
        
        Wheel layout:
        0: Front-Left, 1: Middle-Left, 2: Rear-Left
        3: Front-Right, 4: Middle-Right, 5: Rear-Right
        """
        z_wheels = np.asarray(wheel_contact_elevations_m, dtype=np.float64)
        if len(z_wheels) != 6:
            raise ValueError(f"Expected 6 wheel elevations, got {len(z_wheels)}")

        # Effective normal load considering terrain slope
        w_eff = self.total_weight_n * math.cos(terrain_slope_rad)
        nom_load_per_wheel = w_eff / 6.0

        # Elevation deviation relative to mean ground plane
        mean_z = np.mean(z_wheels)
        dz = z_wheels - mean_z

        # Bogie lever stiffness k_eff (N/m) distributes load
        k_eff = 2500.0  # N/m
        load_perturbation = k_eff * dz

        # Rocker-bogie mechanism equalization: bogie balances rear two wheels on each side
        # Left side:
        load_perturbation[1] = 0.5 * (load_perturbation[1] + load_perturbation[2])
        load_perturbation[2] = load_perturbation[1]
        # Right side:
        load_perturbation[4] = 0.5 * (load_perturbation[4] + load_perturbation[5])
        load_perturbation[5] = load_perturbation[4]

        # Raw normal forces
        normal_forces = nom_load_per_wheel + load_perturbation
        # Clamp to strictly non-negative (wheel can lift off, cannot pull on ground)
        normal_forces = np.maximum(0.0, normal_forces)

        # Normalize sum to match total effective weight
        if np.sum(normal_forces) > 0:
            normal_forces = normal_forces * (w_eff / np.sum(normal_forces))

        min_wheel_load = float(np.min(normal_forces))
        wheel_lift_off = bool(min_wheel_load <= 5.0)  # less than 5 N is considered wheel lift

        return {
            "wheel_forces_n": np.round(normal_forces, 2),
            "total_normal_load_n": round(float(np.sum(normal_forces)), 2),
            "min_wheel_load_n": round(min_wheel_load, 2),
            "wheel_lift_off": wheel_lift_off,
            "nominal_wheel_load_n": round(nom_load_per_wheel, 2),
        }
