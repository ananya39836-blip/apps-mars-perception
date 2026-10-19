"""Nonlinear MPC Trajectory Optimization & Safe Stopping Arc Profile for APPS Level 3.
Chapters 253 & 256 (Part 16).

Provides:
- Emergency stopping trajectory verification (Inevitable Collision State - ICS avoidance)
- Receding horizon velocity profiling under dynamic deceleration bounds
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class SafeStoppingTrajectoryGenerator:
    """Computes certified emergency stopping profiles and ICS boundary validation."""

    def __init__(self, max_decel_m_s2: float = 0.25, max_yaw_rate_rad_s: float = 0.50,
                 r_chassis_m: float = 0.55, max_deceleration_m_s2: float = None):
        if max_deceleration_m_s2 is not None:
            max_decel_m_s2 = max_deceleration_m_s2
        self.max_decel = float(max_decel_m_s2)
        self.max_w = float(max_yaw_rate_rad_s)
        self.r_chassis = float(r_chassis_m)

    def generate_safe_stop_profile(self, current_v: float, current_pose: Tuple[float, float, float],
                                   curvature: float, esdf_dist_m: np.ndarray,
                                   cell_size_m: float = 0.25) -> Dict:
        """Compute the forward braking arc required to bring the rover to 0 velocity and verify clearance."""
        v0 = max(0.0, float(current_v))
        if v0 < 1e-3:
            return {"ics_free": True, "stopping_dist_m": 0.0, "stopping_time_s": 0.0, "stopping_pts": []}

        # Stopping distance d_stop = v^2 / (2 * a_decel)
        t_stop = v0 / self.max_decel
        d_stop = 0.5 * v0 * t_stop

        rx, ry, ryaw = current_pose
        H, W = esdf_dist_m.shape
        stop_pts = []
        is_safe = True

        n_steps = 8
        for s in np.linspace(0.0, d_stop, n_steps):
            if abs(curvature) < 1e-6:
                px = rx + s * math.cos(ryaw)
                py = ry + s * math.sin(ryaw)
            else:
                dth = curvature * s
                px = rx + (math.sin(ryaw + dth) - math.sin(ryaw)) / curvature
                py = ry + (-math.cos(ryaw + dth) + math.cos(ryaw)) / curvature

            stop_pts.append((px, py))
            gx = int(round(px / cell_size_m))
            gy = int(round(py / cell_size_m))

            if not (0 <= gx < W and 0 <= gy < H):
                is_safe = False
                break
            if esdf_dist_m[gy, gx] < self.r_chassis:
                is_safe = False
                break

        return {
            "ics_free": is_safe,
            "stopping_dist_m": float(d_stop),
            "stopping_time_s": float(t_stop),
            "stopping_pts": stop_pts
        }

    def compute_stopping_trajectory(self, initial_velocity_m_s: float = 0.15, dt_s: float = 0.1) -> Dict:
        """Compute velocity vs time deceleration stopping trajectory to full rest."""
        v0 = max(0.0, float(initial_velocity_m_s))
        a = max(0.01, self.max_decel)
        t_stop = v0 / a
        d_stop = 0.5 * v0 * t_stop
        
        times = []
        vels = []
        cur_t = 0.0
        while cur_t <= t_stop + 1e-4:
            v_curr = max(0.0, v0 - a * cur_t)
            times.append(round(cur_t, 2))
            vels.append(round(v_curr, 4))
            cur_t += dt_s

        if not times or times[-1] < t_stop:
            times.append(round(t_stop, 2))
            vels.append(0.0)

        return {
            "stopping_distance_m": float(d_stop),
            "time_to_rest_s": float(t_stop),
            "time_s": times,
            "velocity_m_s": vels
        }


# Alias for compatibility
CertifiedStoppingProfile = SafeStoppingTrajectoryGenerator
