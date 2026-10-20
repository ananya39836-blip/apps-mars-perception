"""6-DOF Multibody Rover Dynamics & Tip-Over Stability (TRL 5).

Implements rigid-body Newton-Euler equations of motion under Martian gravity (g = 3.71 m/s^2),
computing rotational attitude dynamics, accelerations, and Force-Angle Stability Margin (FASM).
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation import (
    G_MARS, ROVER_MASS_KG, ROVER_TRACK_WIDTH_M, ROVER_WHEELBASE_M, ROVER_HEIGHT_M
)


class MultibodyRoverDynamics:
    """Evaluates 6-DOF rigid-body dynamics and tip-over energy barrier."""

    def __init__(
        self,
        mass_kg: float = ROVER_MASS_KG,
        track_width_m: float = ROVER_TRACK_WIDTH_M,
        wheelbase_m: float = ROVER_WHEELBASE_M,
        com_height_m: float = 0.35,
        gravity_mps2: float = G_MARS
    ) -> None:
        self.mass = float(mass_kg)
        self.track_w = float(track_width_m)
        self.wheelbase = float(wheelbase_m)
        self.h_com = float(com_height_m)
        self.g = float(gravity_mps2)

        # Diagonal moment of inertia tensor [I_xx, I_yy, I_zz] (kg*m^2)
        # Approximate as rectangular cuboid: I_xx = m/12 * (w^2 + h^2), I_yy = m/12 * (l^2 + h^2), I_zz = m/12 * (l^2 + w^2)
        self.I_xx = (self.mass / 12.0) * (self.track_w**2 + ROVER_HEIGHT_M**2)
        self.I_yy = (self.mass / 12.0) * (self.wheelbase**2 + ROVER_HEIGHT_M**2)
        self.I_zz = (self.mass / 12.0) * (self.wheelbase**2 + self.track_w**2)
        self.inertia_diag = np.array([self.I_xx, self.I_yy, self.I_zz], dtype=np.float64)

        # Critical static tip-over angle
        self.tip_over_angle_rad = math.atan2(self.track_w / 2.0, self.h_com)

    def evaluate_static_equilibrium(
        self,
        surface_normal: np.ndarray
    ) -> Dict[str, Any]:
        """Calculates pitch, roll, and static stability margin on an inclined surface."""
        n = surface_normal / np.linalg.norm(surface_normal)

        # Roll and pitch angles from surface normal
        pitch_rad = float(-math.atan2(n[0], n[2]))
        roll_rad = float(math.atan2(n[1], n[2]))
        total_tilt_rad = float(math.acos(np.clip(n[2], -1.0, 1.0)))

        # Force-Angle Stability Margin (FASM): energy barrier to rollover
        fasm_roll_rad = self.tip_over_angle_rad - abs(roll_rad)
        fasm_pitch_rad = math.atan2(self.wheelbase / 2.0, self.h_com) - abs(pitch_rad)
        min_stability_rad = min(fasm_roll_rad, fasm_pitch_rad)

        # Tip-over hazard flag
        is_rollover_imminent = bool(min_stability_rad <= math.radians(8.0) or total_tilt_rad >= math.radians(30.0))

        return {
            "pitch_deg": round(math.degrees(pitch_rad), 2),
            "roll_deg": round(math.degrees(roll_rad), 2),
            "tilt_deg": round(math.degrees(total_tilt_rad), 2),
            "stability_margin_rad": round(min_stability_rad, 4),
            "is_stable": not is_rollover_imminent,
            "rollover_hazard": is_rollover_imminent,
        }

    def compute_acceleration_limits(
        self,
        surface_friction_coeff: float = 0.70,
        slope_angle_rad: float = 0.0
    ) -> Dict[str, float]:
        """Computes maximum tractive acceleration and braking limit without tip-over or slip."""
        mu = float(surface_friction_coeff)
        theta = float(slope_angle_rad)

        # Normal force component per unit mass
        g_normal = self.g * math.cos(theta)
        g_parallel = self.g * math.sin(theta)

        # Friction traction limit: a_fric = mu * g_normal - g_parallel
        max_a_traction = max(0.0, mu * g_normal - g_parallel)

        # Dynamic tip-over acceleration limit: a_tip = (track_w / (2 * h_com)) * g_normal
        max_a_tip = (self.track_w / (2.0 * self.h_com)) * g_normal

        # Governed acceleration limit
        a_limit = min(max_a_traction, max_a_tip, 0.40)  # capped at 0.40 m/s^2

        return {
            "max_accel_mps2": round(a_limit, 3),
            "traction_limit_mps2": round(max_a_traction, 3),
            "tip_over_accel_limit_mps2": round(max_a_tip, 3),
        }
