"""15-State Error-State Extended Kalman Filter (ES-EKF) for TRL 7 Planetary Rover.

Fuses high-frequency IMU strapdown mechanization with wheel odometry and visual/LiDAR
pose corrections.
State vector (16 nominal, 15 error states):
  Nominal: [p (3), v (3), q (4), b_a (3), b_g (3)]
  Error:   [delta_p (3), delta_v (3), delta_theta (3), delta_b_a (3), delta_b_g (3)]

Features:
- Closed-form error-state transition matrix F_k
- Joseph-form measurement update for positive semi-definite covariance preservation
- Quaternion error injection and renormalization
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import G_MARS
from trl7_navigation.sensors.coordinate_transforms import (
    euler_to_quaternion,
    quaternion_to_euler,
    quaternion_to_rotation_matrix,
)


def skew_symmetric(v: np.ndarray) -> np.ndarray:
    """Computes 3x3 skew-symmetric matrix for cross product [v x]."""
    return np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ], dtype=np.float64)


class ErrorStateEKF:
    """15-State Error-State Extended Kalman Filter with Joseph-form updates."""

    def __init__(
        self,
        init_pos: Tuple[float, float, float] = (5.0, 5.0, 0.0),
        init_yaw: float = 0.0,
        gravity_mps2: float = G_MARS,
    ) -> None:
        self.g = float(gravity_mps2)

        # Nominal states
        self.p = np.array(init_pos, dtype=np.float64)
        self.v = np.zeros(3, dtype=np.float64)
        self.q = euler_to_quaternion(0.0, 0.0, init_yaw)
        self.b_a = np.zeros(3, dtype=np.float64)
        self.b_g = np.zeros(3, dtype=np.float64)

        # 15x15 Error Covariance P
        self.P = np.eye(15, dtype=np.float64)
        self.P[0:3, 0:3] *= 0.05 ** 2   # Pos variance
        self.P[3:6, 3:6] *= 0.02 ** 2   # Vel variance
        self.P[6:9, 6:9] *= (math.radians(1.0)) ** 2  # Att variance
        self.P[9:12, 9:12] *= 0.05 ** 2 # Accel bias
        self.P[12:15, 12:15] *= (math.radians(0.5)) ** 2 # Gyro bias

        # Process noise spectral densities Q
        self.var_acc = 0.04 ** 2
        self.var_gyr = (math.radians(0.2)) ** 2
        self.var_b_a = 0.001 ** 2
        self.var_b_g = (math.radians(0.01)) ** 2

        self.last_predict_time: float = -1.0

    def predict_imu(
        self,
        accel_body: np.ndarray,
        gyro_body: np.ndarray,
        dt: float,
    ) -> None:
        """Propagates nominal state and error covariance using IMU measurement."""
        if dt <= 0.0:
            return

        # 1. Nominal state integration
        R_b_w = quaternion_to_rotation_matrix(self.q)
        unbiased_accel = accel_body - self.b_a
        unbiased_gyro = gyro_body - self.b_g

        # Specific force in world frame + gravity
        g_w = np.array([0.0, 0.0, -self.g], dtype=np.float64)
        a_w = R_b_w @ unbiased_accel + g_w

        # Position & Velocity update
        self.p += self.v * dt + 0.5 * a_w * (dt ** 2)
        self.v += a_w * dt

        # Attitude quaternion update via matrix exponential
        angle = np.linalg.norm(unbiased_gyro) * dt
        if angle > 1e-9:
            axis = unbiased_gyro / np.linalg.norm(unbiased_gyro)
            dq = np.array([
                math.cos(angle * 0.5),
                axis[0] * math.sin(angle * 0.5),
                axis[1] * math.sin(angle * 0.5),
                axis[2] * math.sin(angle * 0.5),
            ], dtype=np.float64)
            # Quaternion multiply: q_new = q * dq
            qw, qx, qy, qz = self.q
            dq_w, dq_x, dq_y, dq_z = dq
            self.q = np.array([
                qw*dq_w - qx*dq_x - qy*dq_y - qz*dq_z,
                qw*dq_x + qx*dq_w + qy*dq_z - qz*dq_y,
                qw*dq_y - qx*dq_z + qy*dq_w + qz*dq_x,
                qw*dq_z + qx*dq_y - qy*dq_x + qz*dq_w,
            ], dtype=np.float64)
            self.q /= np.linalg.norm(self.q)

        # 2. Error-state transition matrix F (15x15)
        F = np.eye(15, dtype=np.float64)
        F[0:3, 3:6] = np.eye(3) * dt
        F[3:6, 6:9] = -R_b_w @ skew_symmetric(unbiased_accel) * dt
        F[3:6, 9:12] = -R_b_w * dt
        F[6:9, 6:9] = np.eye(3) - skew_symmetric(unbiased_gyro) * dt
        F[6:9, 12:15] = -np.eye(3) * dt

        # Process noise covariance Q
        Q = np.zeros((15, 15), dtype=np.float64)
        Q[3:6, 3:6] = np.eye(3) * self.var_acc * dt
        Q[6:9, 6:9] = np.eye(3) * self.var_gyr * dt
        Q[9:12, 9:12] = np.eye(3) * self.var_b_a * dt
        Q[12:15, 12:15] = np.eye(3) * self.var_b_g * dt

        # Covariance propagation
        self.P = F @ self.P @ F.T + Q

    def update_wheel_odometry(
        self,
        meas_linear_v: float,
        meas_angular_w: float,
        r_cov: float = 0.05 ** 2,
    ) -> None:
        """Corrects state using wheel odometry forward speed and non-holonomic zero lateral/vertical slip."""
        R_b_w = quaternion_to_rotation_matrix(self.q)
        v_body = R_b_w.T @ self.v

        # Non-holonomic measurement: [vx, vy, vz]_body = [meas_linear_v, 0.0, 0.0]
        z_meas = np.array([meas_linear_v, 0.0, 0.0], dtype=np.float64)
        res = z_meas - v_body

        # Jacobian H (3x15): d(v_body)/dv = R_b_w^T
        H = np.zeros((3, 15), dtype=np.float64)
        H[0:3, 3:6] = R_b_w.T

        # Covariance R (3x3): tighter on lateral and vertical non-holonomic constraints
        R = np.diag([r_cov, 0.02**2, 0.02**2])
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        dx = (K @ res).flatten()
        self._inject_error_state(dx)

        I_KH = np.eye(15) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T

    def update_position(
        self,
        meas_pos: np.ndarray,
        r_cov: float = 0.10 ** 2,
    ) -> None:
        """Corrects state using visual/LiDAR absolute position measurement."""
        res = meas_pos - self.p
        H = np.zeros((3, 15), dtype=np.float64)
        H[0:3, 0:3] = np.eye(3)

        R = np.eye(3, dtype=np.float64) * r_cov
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        dx = (K @ res).flatten()
        self._inject_error_state(dx)

        I_KH = np.eye(15) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T

    def _inject_error_state(self, dx: np.ndarray) -> None:
        """Injects estimated error vector into nominal state and resets error to zero."""
        self.p += dx[0:3]
        self.v += dx[3:6]

        # Attitude error delta_theta into quaternion
        d_theta = dx[6:9]
        angle = np.linalg.norm(d_theta)
        if angle > 1e-9:
            axis = d_theta / angle
            dq = np.array([
                math.cos(angle * 0.5),
                axis[0] * math.sin(angle * 0.5),
                axis[1] * math.sin(angle * 0.5),
                axis[2] * math.sin(angle * 0.5),
            ], dtype=np.float64)
            qw, qx, qy, qz = self.q
            dq_w, dq_x, dq_y, dq_z = dq
            self.q = np.array([
                qw*dq_w - qx*dq_x - qy*dq_y - qz*dq_z,
                qw*dq_x + qx*dq_w + qy*dq_z - qz*dq_y,
                qw*dq_y - qx*dq_z + qy*dq_w + qz*dq_x,
                qw*dq_z + qx*dq_y - qy*dq_x + qz*dq_w,
            ], dtype=np.float64)
            self.q /= np.linalg.norm(self.q)

        self.b_a += dx[9:12]
        self.b_g += dx[12:15]

    def get_estimated_pose(self) -> Tuple[float, float, float, float, float, float]:
        """Returns (x, y, z, roll, pitch, yaw) in world frame."""
        roll, pitch, yaw = quaternion_to_euler(self.q)
        return float(self.p[0]), float(self.p[1]), float(self.p[2]), roll, pitch, yaw
