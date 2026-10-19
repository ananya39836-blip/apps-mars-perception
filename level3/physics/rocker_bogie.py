"""Rocker-Bogie Passive Suspension Kinematics for APPS Level 3.
Chapter 223 (Part 13).

Computes forward kinematic suspension equilibrium across 6 wheels:
- Differential averaging bar: theta_chassis = 0.5 * (theta_rocker_L + theta_rocker_R)
- Left and Right Rockers and rear Bogie pivots.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class RockerBogieSuspension:
    """Rocker-bogie kinematic equalizer maintaining 6-wheel ground contact."""

    def __init__(self, wheelbase_m: float = 1.20, track_width_m: float = 0.90,
                 wheel_radius_m: float = 0.15, max_rocker_deg: float = 25.0,
                 max_bogie_deg: float = 35.0):
        self.wheelbase = float(wheelbase_m)
        self.track_width = float(track_width_m)
        self.r_wheel = float(wheel_radius_m)
        self.max_rocker_rad = math.radians(max_rocker_deg)
        self.max_bogie_rad = math.radians(max_bogie_deg)

        # Nominal relative wheel positions in rover body frame: (x, y)
        half_w = self.track_width / 2.0
        self.wheel_offsets = {
            "FL": (0.60, half_w),    # Front Left
            "FR": (0.60, -half_w),   # Front Right
            "ML": (0.00, half_w),    # Middle Left (bogie forward)
            "MR": (0.00, -half_w),   # Middle Right
            "RL": (-0.60, half_w),   # Rear Left (bogie aft)
            "RR": (-0.60, -half_w),  # Rear Right
        }

    def compute_wheel_world_positions(self, rover_x: float, rover_y: float,
                                      rover_yaw: float) -> Dict[str, Tuple[float, float]]:
        """Project nominal wheel positions into world (X, Y) coordinates."""
        cos_th = math.cos(rover_yaw)
        sin_th = math.sin(rover_yaw)
        w_pos = {}
        for name, (lx, ly) in self.wheel_offsets.items():
            wx = rover_x + lx * cos_th - ly * sin_th
            wy = rover_y + lx * sin_th + ly * cos_th
            w_pos[name] = (float(wx), float(wy))
        return w_pos

    def resolve_suspension_equilibrium(self, wheel_contact_z: Dict[str, float]) -> Dict:
        """From 6 wheel terrain contact elevations z_i, compute suspension articulation and chassis attitude."""
        z_fl = wheel_contact_z.get("FL", 0.0)
        z_fr = wheel_contact_z.get("FR", 0.0)
        z_ml = wheel_contact_z.get("ML", 0.0)
        z_mr = wheel_contact_z.get("MR", 0.0)
        z_rl = wheel_contact_z.get("RL", 0.0)
        z_rr = wheel_contact_z.get("RR", 0.0)

        # Left bogie pitch: between ML and RL
        dz_bogie_l = z_ml - z_rl
        bogie_l_rad = math.atan2(dz_bogie_l, 0.60)
        bogie_l_rad = float(np.clip(bogie_l_rad, -self.max_bogie_rad, self.max_bogie_rad))
        bogie_l_center_z = (z_ml + z_rl) / 2.0

        # Right bogie pitch: between MR and RR
        dz_bogie_r = z_mr - z_rr
        bogie_r_rad = math.atan2(dz_bogie_r, 0.60)
        bogie_r_rad = float(np.clip(bogie_r_rad, -self.max_bogie_rad, self.max_bogie_rad))
        bogie_r_center_z = (z_mr + z_rr) / 2.0

        # Left rocker pitch: between FL and Left Bogie center
        dz_rocker_l = z_fl - bogie_l_center_z
        rocker_l_rad = math.atan2(dz_rocker_l, 0.60)
        rocker_l_rad = float(np.clip(rocker_l_rad, -self.max_rocker_rad, self.max_rocker_rad))

        # Right rocker pitch: between FR and Right Bogie center
        dz_rocker_r = z_fr - bogie_r_center_z
        rocker_r_rad = math.atan2(dz_rocker_r, 0.60)
        rocker_r_rad = float(np.clip(rocker_r_rad, -self.max_rocker_rad, self.max_rocker_rad))

        # Chassis pitch is averaged by the differential bar
        chassis_pitch = 0.5 * (rocker_l_rad + rocker_r_rad)

        # Chassis roll from left-right rocker difference
        chassis_roll = math.atan2(
            (z_fl + bogie_l_center_z) / 2.0 - (z_fr + bogie_r_center_z) / 2.0,
            self.track_width
        )

        chassis_z = (z_fl + z_fr + z_ml + z_mr + z_rl + z_rr) / 6.0 + self.r_wheel + 0.20

        # Equalized normal forces across 6 wheels (185 kg * 3.71 m/s^2 / 6 = ~114.4 N baseline)
        nominal_load = (185.0 * 3.71) / 6.0
        pitch_bias = math.sin(chassis_pitch) * 30.0
        roll_bias = math.sin(chassis_roll) * 30.0

        wheel_loads = {
            "FL": float(max(10.0, nominal_load - pitch_bias + roll_bias)),
            "FR": float(max(10.0, nominal_load - pitch_bias - roll_bias)),
            "ML": float(max(10.0, nominal_load + roll_bias)),
            "MR": float(max(10.0, nominal_load - roll_bias)),
            "RL": float(max(10.0, nominal_load + pitch_bias + roll_bias)),
            "RR": float(max(10.0, nominal_load + pitch_bias - roll_bias)),
        }

        return {
            "chassis_pitch_rad": float(chassis_pitch),
            "chassis_roll_rad": float(chassis_roll),
            "chassis_z_m": float(chassis_z),
            "rocker_left_deg": float(math.degrees(rocker_l_rad)),
            "rocker_right_deg": float(math.degrees(rocker_r_rad)),
            "bogie_left_deg": float(math.degrees(bogie_l_rad)),
            "bogie_right_deg": float(math.degrees(bogie_r_rad)),
            "wheel_normal_loads_N": wheel_loads
        }

    def forward_kinematics(self, rocker_pitch_left: float, rocker_pitch_right: float) -> Dict:
        """Forward kinematic decoupling of differential pitch averaging bar."""
        diff_pitch = 0.5 * (rocker_pitch_left - rocker_pitch_right)
        avg_pitch = 0.5 * (rocker_pitch_left + rocker_pitch_right)
        return {
            "diff_pitch_rad": float(diff_pitch),
            "avg_pitch_rad": float(avg_pitch),
            "rocker_left_rad": float(rocker_pitch_left),
            "rocker_right_rad": float(rocker_pitch_right)
        }

    def compute_wheel_normal_loads(self, total_normal_load_N: float = 686.35,
                                   pitch_rad: float = 0.0,
                                   roll_rad: float = 0.0) -> Dict[str, float]:
        """Compute normal ground contact forces equalized across 6 wheels under terrain inclination."""
        nom = float(total_normal_load_N) / 6.0
        pitch_bias = math.sin(pitch_rad) * (total_normal_load_N * 0.08)
        roll_bias = math.sin(roll_rad) * (total_normal_load_N * 0.08)

        loads = {
            "fl": float(max(5.0, nom - pitch_bias + roll_bias)),
            "fr": float(max(5.0, nom - pitch_bias - roll_bias)),
            "ml": float(max(5.0, nom + roll_bias)),
            "mr": float(max(5.0, nom - roll_bias)),
            "rl": float(max(5.0, nom + pitch_bias + roll_bias)),
            "rr": float(max(5.0, nom + pitch_bias - roll_bias)),
            "FL": float(max(5.0, nom - pitch_bias + roll_bias)),
            "FR": float(max(5.0, nom - pitch_bias - roll_bias)),
            "ML": float(max(5.0, nom + roll_bias)),
            "MR": float(max(5.0, nom - roll_bias)),
            "RL": float(max(5.0, nom + pitch_bias + roll_bias)),
            "RR": float(max(5.0, nom + pitch_bias - roll_bias)),
        }
        return loads
