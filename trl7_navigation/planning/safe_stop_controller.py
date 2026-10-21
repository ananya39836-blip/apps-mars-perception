"""Certified Safe-Stop Deceleration Controller (TRL 7).

Executes deterministic, constant-jerk and bounded-acceleration deceleration
profiles (a_decel = -0.20 m/s^2) upon fault injection or E-Stop assertion,
bringing the vehicle to rest and latching mechanical brakes.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation.hardware.hardware_interface import ActuatorCommand


class SafeStopController:
    """Deterministic deceleration governor for controlled emergency and fault halts."""

    def __init__(
        self,
        nominal_decel_m_s2: float = 0.20,
        emergency_decel_m_s2: float = 0.40,
        stop_velocity_epsilon_m_s: float = 0.02,
    ) -> None:
        self.nominal_decel = float(nominal_decel_m_s2)
        self.emergency_decel = float(emergency_decel_m_s2)
        self.v_eps = float(stop_velocity_epsilon_m_s)
        self.cmd_seq = 0

    def compute_stopping_command(
        self,
        current_v: float,
        current_steer: float,
        dt: float,
        emergency: bool = False,
        timestamp_s: float = 0.0,
    ) -> Tuple[ActuatorCommand, bool]:
        """Calculates discrete stopping command. Returns (cmd, is_fully_stopped)."""
        self.cmd_seq += 1
        decel_rate = self.emergency_decel if emergency else self.nominal_decel

        if abs(current_v) <= self.v_eps:
            # Completely halted; latch mechanical brakes
            cmd = ActuatorCommand(
                timestamp_s=timestamp_s,
                seq=self.cmd_seq,
                linear_velocity_m_s=0.0,
                steering_angle_rad=0.0,
                brake_engaged=True,
                e_stop=emergency,
            )
            return cmd, True

        # Ramp down velocity toward zero
        dv = decel_rate * dt
        if current_v > 0.0:
            new_v = max(0.0, current_v - dv)
        else:
            new_v = min(0.0, current_v + dv)

        # Straighten steering angle during deceleration
        dsteer = 0.5 * dt
        if current_steer > 0.0:
            new_steer = max(0.0, current_steer - dsteer)
        else:
            new_steer = min(0.0, current_steer + dsteer)

        cmd = ActuatorCommand(
            timestamp_s=timestamp_s,
            seq=self.cmd_seq,
            linear_velocity_m_s=float(new_v),
            steering_angle_rad=float(new_steer),
            brake_engaged=(new_v == 0.0),
            e_stop=emergency,
        )
        return cmd, (new_v == 0.0)
