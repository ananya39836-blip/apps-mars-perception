"""Integrated 6-DOF Multibody Rover Dynamics Engine (TRL 7).

Couples planetary gravity, chassis Newton-Euler equations of motion, 6-wheel
rocker-bogie kinematic articulation, and terramechanic soil resistance.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    ROVER_MASS_KG,
    ROVER_WHEEL_RADIUS_M,
    G_MARS,
    G_EARTH,
)
from trl7_navigation.dynamics.rocker_bogie import RockerBogieSuspension
from trl7_navigation.dynamics.terramechanics import TerramechanicsModel
from trl7_navigation.environment.planetary_terrain import PlanetaryTerrain


class MultibodyRover:
    """Full 6-DOF dynamic simulator for autonomous planetary rover locomotion."""

    def __init__(
        self,
        terrain: PlanetaryTerrain,
        start_pose: Tuple[float, float, float] = (5.0, 5.0, 0.0),
        mass_kg: float = ROVER_MASS_KG,
        gravity_mps2: float = G_MARS,
    ) -> None:
        self.terrain = terrain
        self.mass = float(mass_kg)
        self.g = float(gravity_mps2)

        # Pose & Velocities
        self.x = float(start_pose[0])
        self.y = float(start_pose[1])
        self.z = float(self.terrain.get_elevation_at(self.x, self.y))
        self.yaw = float(start_pose[2])
        self.pitch = 0.0
        self.roll = 0.0

        self.v_forward = 0.0
        self.omega_yaw = 0.0

        # Subsystems
        self.suspension = RockerBogieSuspension(gravity_mps2=self.g, rover_mass_kg=self.mass)
        self.terramechanics = TerramechanicsModel()

    def step(self, cmd_v: float, cmd_steer: float, dt: float) -> Dict[str, Any]:
        """Integrates vehicle state forward by dt seconds under terramechanic constraints."""
        # 1. Kinematic suspension ground contact
        susp_data = self.suspension.resolve_ground_contact(self.x, self.y, self.yaw, self.terrain)
        normal_forces = susp_data["wheel_normal_forces_n"]

        # 2. Terramechanic forces across 6 wheels
        local_fric = 0.85
        if 0 <= self.x < self.terrain.size_x and 0 <= self.y < self.terrain.size_y:
            ix = int(np.clip(self.x / self.terrain.res, 0, self.terrain.nx - 1))
            iy = int(np.clip(self.y / self.terrain.res, 0, self.terrain.ny - 1))
            local_fric = self.terrain.regolith_friction[ix, iy]

        total_dp = 0.0
        mean_slip = 0.0
        for i in range(6):
            w_load = normal_forces[i]
            # Commanded wheel rate
            omega_w = cmd_v / ROVER_WHEEL_RADIUS_M
            terra = self.terramechanics.compute_sinkage_and_forces(
                wheel_normal_load_n=w_load,
                wheel_angular_rate_rad_s=omega_w,
                chassis_linear_velocity_m_s=self.v_forward,
                local_friction_mu=local_fric,
            )
            total_dp += terra["drawbar_pull_n"]
            mean_slip += terra["slip_ratio"] / 6.0

        # 3. Acceleration from net drawbar pull: a = F_net / m
        # Slope resistance: F_slope = m * g * sin(pitch)
        slope_res = self.mass * self.g * math.sin(self.pitch)
        f_net = total_dp - slope_res
        accel = f_net / self.mass

        # Numerical integration of velocity
        self.v_forward += accel * dt
        # Clamp velocity to command direction
        if cmd_v >= 0.0:
            self.v_forward = float(np.clip(self.v_forward, 0.0, max(cmd_v, 0.05)))
        else:
            self.v_forward = float(np.clip(self.v_forward, min(cmd_v, -0.05), 0.0))

        # Steering yaw rate
        self.omega_yaw = (self.v_forward / self.suspension.L) * math.tan(cmd_steer)

        # Update pose
        self.yaw += self.omega_yaw * dt
        self.yaw = (self.yaw + math.pi) % (2.0 * math.pi) - math.pi

        self.x += self.v_forward * math.cos(self.yaw) * dt
        self.y += self.v_forward * math.sin(self.yaw) * dt

        self.x = float(np.clip(self.x, 0.5, self.terrain.size_x - 0.5))
        self.y = float(np.clip(self.y, 0.5, self.terrain.size_y - 0.5))
        self.z = float(self.terrain.get_elevation_at(self.x, self.y))

        self.pitch = susp_data["bogie_angle_left_rad"] * 0.5 + susp_data["bogie_angle_right_rad"] * 0.5
        self.roll = susp_data["differential_tilt_rad"]

        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "yaw": self.yaw,
            "pitch": self.pitch,
            "roll": self.roll,
            "v_forward": self.v_forward,
            "mean_slip": mean_slip,
            "total_drawbar_pull_n": total_dp,
            "suspension": susp_data,
        }
