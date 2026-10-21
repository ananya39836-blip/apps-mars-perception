"""Rocker-Bogie Passive Articulation Kinematics & Wheel Load Balancing (TRL 6).

Implements 6-wheel rocker-bogie passive suspension kinematics:
- Differential cross-bar pitch averaging
- 6-wheel ground contact normal force distribution under Martian surface gravity
- Chassis roll/pitch attitude equilibrium across uneven terrain
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

from trl6_navigation import G_MARS, ROVER_MASS_KG


class RockerBogieKinematics:
    """Computes rocker-bogie articulated kinematics and wheel normal load distributions."""

    def __init__(self, rover_mass_kg: float = ROVER_MASS_KG, gravity_mps2: float = G_MARS) -> None:
        self.mass = float(rover_mass_kg)
        self.g = float(gravity_mps2)
        self.weight_n = self.mass * self.g

        # Wheel contact coordinates relative to chassis center (+X fwd, +Y left, +Z down)
        # 6 wheels: LF, LM, LR, RF, RM, RR
        self.wheel_offsets = {
            "LF": np.array([1.10, 1.00, 0.0]),
            "LM": np.array([0.00, 1.05, 0.0]),
            "LR": np.array([-1.10, 1.00, 0.0]),
            "RF": np.array([1.10, -1.00, 0.0]),
            "RM": np.array([0.00, -1.05, 0.0]),
            "RR": np.array([-1.10, -1.00, 0.0]),
        }

    def compute_differential_pitch(
        self,
        rocker_angle_left_rad: float,
        rocker_angle_right_rad: float
    ) -> Dict[str, float]:
        """Calculates chassis pitch attitude and differential cross-bar rotation."""
        th_l = float(rocker_angle_left_rad)
        th_r = float(rocker_angle_right_rad)

        # Differential link averages left and right rocker rotations
        chassis_pitch = 0.5 * (th_l + th_r)
        diff_angle = 0.5 * (th_l - th_r)

        return {
            "chassis_pitch_rad": round(chassis_pitch, 4),
            "chassis_pitch_deg": round(math.degrees(chassis_pitch), 2),
            "differential_angle_rad": round(diff_angle, 4),
            "differential_angle_deg": round(math.degrees(diff_angle), 2),
        }

    def compute_wheel_normal_loads(
        self,
        surface_pitch_rad: float = 0.0,
        surface_roll_rad: float = 0.0
    ) -> Dict[str, float]:
        """Calculates normal ground contact forces (N) across all 6 wheels on sloped terrain."""
        # Gravity vector in rover chassis frame
        cp = math.cos(surface_pitch_rad)
        sp = math.sin(surface_pitch_rad)
        cr = math.cos(surface_roll_rad)
        sr = math.sin(surface_roll_rad)

        # Normal component of gravity perpendicular to terrain surface
        f_normal_total = self.weight_n * cp * cr

        # Base nominal static load per wheel (1/6th of total normal force)
        f_base = f_normal_total / 6.0

        # Pitch load transfer: forward wheels lose/gain load on slopes
        delta_pitch = (self.weight_n * sp * 0.8) / 4.0

        # Roll load transfer: uphill wheels lose load, downhill gain
        delta_roll = (self.weight_n * sr * 0.8) / 3.0

        loads = {
            "LF": max(50.0, f_base - delta_pitch + delta_roll),
            "LM": max(50.0, f_base + delta_roll),
            "LR": max(50.0, f_base + delta_pitch + delta_roll),
            "RF": max(50.0, f_base - delta_pitch - delta_roll),
            "RM": max(50.0, f_base - delta_roll),
            "RR": max(50.0, f_base + delta_pitch - delta_roll),
        }

        # Normalize to maintain exact total normal equilibrium
        tot = sum(loads.values())
        if tot > 0:
            scale = f_normal_total / tot
            loads = {k: round(v * scale, 2) for k, v in loads.items()}

        return loads
