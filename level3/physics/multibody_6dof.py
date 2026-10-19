"""6-DOF Multibody Rigid-Body Dynamics for APPS Level 3 Simulation.
Chapters 222 & 229 (Part 13).

Models translational and rotational dynamics:
m * d(v)/dt + omega x (m * v) = F_ext
I * d(omega)/dt + omega x (I * omega) = M_ext
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class RigidBody6DOF:
    """6-DOF Rigid-Body Dynamics simulator with Newton-Euler equations and Force-Angle Stability Margin."""
    
    def __init__(self, mass_kg: float = 185.0,
                 inertia_diag: Tuple[float, float, float] = (24.5, 32.8, 41.2),
                 gravity_m_s2: float = 3.71):
        self.mass = float(mass_kg)
        self.inertia = np.diag(inertia_diag)
        self.inertia_inv = np.linalg.inv(self.inertia)
        self.g = float(gravity_m_s2)
        
        # State vector: [x, y, z, roll, pitch, yaw, vx, vy, vz, wx, wy, wz]
        self.state = np.zeros(12, dtype=np.float64)
        self.state[2] = 0.50 # initial nominal height

    def set_pose(self, x: float, y: float, z: float, roll: float, pitch: float, yaw: float):
        self.state[0:3] = [x, y, z]
        self.state[3:6] = [roll, pitch, yaw]
        self.state[6:12] = 0.0

    def step(self, f_ext: np.ndarray, m_ext: np.ndarray, dt: float) -> Dict:
        """Advance dynamics by time step dt under external forces f_ext (3D) and moments m_ext (3D)."""
        if not (np.all(np.isfinite(f_ext)) and np.all(np.isfinite(m_ext)) and math.isfinite(dt) and dt > 0):
            return {"status": "invalid_input", "state": self.state.copy(), "fasm": 0.0}

        # Current state unpacking
        pos = self.state[0:3]
        euler = self.state[3:6] # roll, pitch, yaw
        v = self.state[6:9]
        w = self.state[9:12]

        # Gravitational force in world frame
        f_grav = np.array([0.0, 0.0, -self.mass * self.g], dtype=np.float64)
        total_force = f_ext + f_grav
        
        # Translational acceleration: a = F_total / m
        a_lin = total_force / self.mass
        
        # Rotational acceleration: I * dw/dt = M_ext - w x (I * w)
        gyroscopic_torque = np.cross(w, self.inertia @ w)
        total_moment = m_ext - gyroscopic_torque
        a_rot = self.inertia_inv @ total_moment

        # Symplectic Euler update
        v_next = v + a_lin * dt
        w_next = w + a_rot * dt

        # Damping to stabilize ground contact
        v_next[0:2] *= 0.98
        w_next *= 0.95

        pos_next = pos + v_next * dt
        euler_next = euler + w_next * dt
        # Normalize yaw to [-pi, pi]
        euler_next[2] = (euler_next[2] + math.pi) % (2.0 * math.pi) - math.pi

        self.state[0:3] = pos_next
        self.state[3:6] = euler_next
        self.state[6:9] = v_next
        self.state[9:12] = w_next

        # Compute Force-Angle Stability Margin (FASM)
        fasm = self.compute_fasm(contact_points=[
            (0.60, 0.45, 0.0),   # Front Left
            (0.00, 0.45, 0.0),   # Mid Left
            (-0.60, 0.45, 0.0),  # Rear Left
            (-0.60, -0.45, 0.0), # Rear Right
            (0.00, -0.45, 0.0),  # Mid Right
            (0.60, -0.45, 0.0)   # Front Right
        ], f_net=total_force)

        is_tipover = bool(fasm < 5.0 or abs(euler_next[0]) > math.radians(35.0) or abs(euler_next[1]) > math.radians(35.0))

        return {
            "status": "ok",
            "state": self.state.copy(),
            "position": tuple(pos_next),
            "euler_angles": tuple(euler_next),
            "linear_velocity": tuple(v_next),
            "angular_velocity": tuple(w_next),
            "fasm": float(fasm),
            "is_tipover": is_tipover
        }

    def compute_fasm(self, contact_points: List[Tuple[float, float, float]], f_net: np.ndarray) -> float:
        """Force-Angle Stability Margin (FASM) from Chapter 229.2.
        FASM = min_i ( theta_tip_i * ||F_net|| ).
        """
        f_norm = float(np.linalg.norm(f_net))
        if f_norm < 1e-3:
            return 50.0

        # Downward force vector
        h_cm = max(0.10, self.state[2])
        # Center of pressure on ground plane: x_cop = -F_x / |F_z| * h_cm
        fz = abs(f_net[2]) if abs(f_net[2]) > 1e-2 else 185.0 * self.g
        cop_x = (f_net[0] / fz) * h_cm
        cop_y = (f_net[1] / fz) * h_cm

        # Distance from COP to support polygon edges
        min_d = float("inf")
        n_pts = len(contact_points)
        for i in range(n_pts):
            p1 = contact_points[i]
            p2 = contact_points[(i + 1) % n_pts]
            x1, y1 = p1[0], p1[1]
            x2, y2 = p2[0], p2[1]

            # Edge vector
            dx = x2 - x1
            dy = y2 - y1
            edge_len = math.hypot(dx, dy)
            if edge_len < 1e-4:
                continue

            # Perpendicular distance from COP to line segment
            dist = abs(dy * cop_x - dx * cop_y + x2 * y1 - y2 * x1) / edge_len
            if dist < min_d:
                min_d = dist

        # Tip angle theta ~ arctan(dist / h_cm)
        theta_tip = math.atan2(min_d, h_cm)
        margin = theta_tip * f_norm
        return float(max(0.0, margin))
