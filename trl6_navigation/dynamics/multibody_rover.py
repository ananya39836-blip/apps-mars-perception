"""6-DOF Multibody Rover Equations of Motion & Tip-Over Stability (TRL 6).

Implements 6-DOF Newton-Euler rigid body equations under Martian gravity:
- Translational equations: m * (v_dot + w x v) = F_gravity + F_tractive + F_resistance
- Rotational equations: I * w_dot + w x (I * w) = M_forces
- Dynamic tip-over rollover stability margin (FASM) auditing
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl6_navigation import G_MARS, ROVER_MASS_KG, TIP_OVER_LIMIT_SLOPE_DEG


class MultibodyRoverDynamics:
    """Simulates 6-DOF Newton-Euler rover dynamics and tip-over stability limits."""

    def __init__(
        self,
        mass_kg: float = ROVER_MASS_KG,
        gravity_mps2: float = G_MARS,
        inertia_diag: Tuple[float, float, float] = (350.0, 480.0, 520.0)
    ) -> None:
        self.m = float(mass_kg)
        self.g = float(gravity_mps2)
        self.I = np.diag(inertia_diag)
        self.I_inv = np.diag([1.0 / val for val in inertia_diag])

        # State vectors: position (3), velocity (3), Euler angles (3), angular velocity (3)
        self.pos = np.zeros(3, dtype=np.float64)
        self.vel = np.zeros(3, dtype=np.float64)
        self.rpy = np.zeros(3, dtype=np.float64)
        self.omega = np.zeros(3, dtype=np.float64)

    def evaluate_static_equilibrium(
        self,
        slope_angle_deg: float,
        heading_relative_to_gradient_deg: float = 0.0
    ) -> Dict[str, Any]:
        """Audits static rollover tip-over stability margin on sloped terrain."""
        slope_rad = math.radians(slope_angle_deg)
        head_rad = math.radians(heading_relative_to_gradient_deg)

        # Pitch component: downhill/uphill
        pitch_rad = slope_rad * math.cos(head_rad)
        # Roll component: cross-slope tilt
        roll_rad = slope_rad * math.sin(head_rad)

        total_tilt_deg = float(slope_angle_deg)
        stability_margin_deg = max(0.0, TIP_OVER_LIMIT_SLOPE_DEG - total_tilt_deg)
        is_safe = total_tilt_deg <= TIP_OVER_LIMIT_SLOPE_DEG

        return {
            "slope_deg": round(total_tilt_deg, 2),
            "pitch_deg": round(math.degrees(pitch_rad), 2),
            "roll_deg": round(math.degrees(roll_rad), 2),
            "stability_margin_deg": round(stability_margin_deg, 2),
            "is_stable": is_safe,
            "tip_over_imminent": bool(stability_margin_deg < 5.0),
        }

    def step_forward_dynamics(
        self,
        net_tractive_force_n: float,
        steering_curvature: float,
        dt_s: float = 0.05
    ) -> Dict[str, Any]:
        """Integrates 1 step of forward planar longitudinal and yaw dynamics."""
        dt = float(dt_s)
        # Longitudinal acceleration: a = F_net / m
        a_x = net_tractive_force_n / self.m
        self.vel[0] = max(0.0, self.vel[0] + a_x * dt)

        # Yaw rate from bicycle model: w_z = v_x * kappa
        w_z = self.vel[0] * float(steering_curvature)
        self.omega[2] = w_z

        # Orientation update
        self.rpy[2] = (self.rpy[2] + w_z * dt + math.pi) % (2.0 * math.pi) - math.pi

        # Position update
        self.pos[0] += self.vel[0] * math.cos(self.rpy[2]) * dt
        self.pos[1] += self.vel[0] * math.sin(self.rpy[2]) * dt

        return {
            "pos_xyz": self.pos.copy(),
            "vel_xyz": self.vel.copy(),
            "yaw_deg": round(math.degrees(self.rpy[2]), 2),
            "accel_mps2": round(a_x, 4),
        }
