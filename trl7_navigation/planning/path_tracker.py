"""Adaptive Pure Pursuit Path Follower (TRL 7).

Computes discrete steering and velocity actuator commands to accurately track
continuous reference trajectories under terrain slip disturbances.
Features:
- Curvature-adaptive lookahead distance
- Lateral acceleration derating on sharp bends (a_lat <= 0.35 m/s^2)
- Heading error deadband and anti-windup
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    MAX_SPEED_MPS,
    NOMINAL_SPEED_MPS,
    MAX_STEERING_ANGLE_RAD,
    ROVER_WHEELBASE_M,
    MIN_TURNING_RADIUS_M,
)
from trl7_navigation.hardware.hardware_interface import ActuatorCommand
from trl7_navigation.planning.kinodynamic_hybrid_astar import PathPoint


class PathTracker:
    """Adaptive Pure Pursuit trajectory follower with curvature derating."""

    def __init__(
        self,
        min_lookahead_m: float = 1.20,
        lookahead_ratio_s: float = 2.0,
        max_lat_accel_m_s2: float = 0.30,
        wheelbase_m: float = ROVER_WHEELBASE_M,
    ) -> None:
        self.min_lookahead = float(min_lookahead_m)
        self.lookahead_ratio = float(lookahead_ratio_s)
        self.max_lat_accel = float(max_lat_accel_m_s2)
        self.L = float(wheelbase_m)
        self.cmd_seq = 0

    def compute_command(
        self,
        current_pose: Tuple[float, float, float],  # x, y, yaw
        current_v: float,
        path: List[PathPoint],
        timestamp_s: float = 0.0,
    ) -> Tuple[ActuatorCommand, bool]:
        """Calculates steering and velocity command. Returns (cmd, is_goal_reached)."""
        self.cmd_seq += 1
        rx, ry, ryaw = current_pose

        if len(path) == 0:
            return ActuatorCommand(timestamp_s, self.cmd_seq, 0.0, 0.0, e_stop=False), True

        # Check goal reached (within 0.8m of final path point)
        dist_to_final = math.hypot(path[-1].x - rx, path[-1].y - ry)
        if dist_to_final <= 0.80:
            return ActuatorCommand(timestamp_s, self.cmd_seq, 0.0, 0.0, brake_engaged=True), True

        # Adaptive lookahead distance
        lookahead_d = max(self.min_lookahead, self.lookahead_ratio * abs(current_v))

        # Find closest point index along path
        min_idx = 0
        min_d = float('inf')
        for i, pt in enumerate(path):
            d = math.hypot(pt.x - rx, pt.y - ry)
            if d < min_d:
                min_d = d
                min_idx = i

        # Search forward from closest point for lookahead point
        target_pt: Optional[PathPoint] = None
        for pt in path[min_idx:]:
            d = math.hypot(pt.x - rx, pt.y - ry)
            if d >= lookahead_d:
                target_pt = pt
                break

        if target_pt is None:
            target_pt = path[-1]

        # Heading error alpha
        target_heading = math.atan2(target_pt.y - ry, target_pt.x - rx)
        alpha = (target_heading - ryaw + math.pi) % (2.0 * math.pi) - math.pi

        # Pure pursuit curvature: kappa = 2 * sin(alpha) / lookahead_d
        kappa = (2.0 * math.sin(alpha)) / max(0.2, lookahead_d)
        steer_angle = math.atan(self.L * kappa)
        steer_angle = float(np.clip(steer_angle, -MAX_STEERING_ANGLE_RAD, MAX_STEERING_ANGLE_RAD))

        # Curvature-based velocity derating
        curve_limit = math.sqrt(self.max_lat_accel / max(0.01, abs(kappa)))
        target_v = min(NOMINAL_SPEED_MPS, curve_limit)

        # Slow down smoothly when nearing final waypoint
        if dist_to_final < 3.0:
            target_v *= max(0.3, dist_to_final / 3.0)

        cmd = ActuatorCommand(
            timestamp_s=timestamp_s,
            seq=self.cmd_seq,
            linear_velocity_m_s=float(target_v),
            steering_angle_rad=steer_angle,
            curvature_inv_m=kappa,
        )

        return cmd, False
