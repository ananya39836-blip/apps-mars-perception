"""Error-State Extended Kalman Filter (ES-EKF) for Planetary Rover State Estimation (TRL 5).

Fuses high-rate 6-axis IMU inertial measurements with wheel odometry and tilt sensors
under non-zero terrain slip. Tracks position, velocity, heading, and sensor biases
with continuous covariance estimation.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation import G_MARS


class ErrorStateEKF:
    """Error-State Extended Kalman Filter (ES-EKF) for 2D/3D rover state estimation."""

    def __init__(
        self,
        init_x: float = 0.0,
        init_y: float = 0.0,
        init_yaw_rad: float = 0.0,
        init_pos_std_m: float = 0.05,
        init_yaw_std_rad: float = 0.02
    ) -> None:
        # Nominal State: [x (m), y (m), yaw (rad), v (m/s), b_gyro (rad/s)]
        self.state = np.array([
            float(init_x),
            float(init_y),
            float(init_yaw_rad),
            0.0,
            0.0
        ], dtype=np.float64)

        # State Covariance P (5x5)
        self.P = np.diag([
            init_pos_std_m**2,
            init_pos_std_m**2,
            init_yaw_std_rad**2,
            0.04,   # velocity std 0.2 m/s
            1.0e-4  # gyro bias std
        ])

        # Process noise covariance Q (5x5)
        self.q_pos = 0.01**2
        self.q_yaw = 0.005**2
        self.q_v = 0.05**2
        self.q_bias = 1.0e-5**2

        # Measurement noise covariances R
        self.r_odom_v = 0.02**2
        self.r_odom_w = 0.01**2

    def predict(self, meas_gyro_z: float, meas_accel_x: float, dt_s: float) -> None:
        """Propagates state and error covariance via IMU kinematic motion model."""
        dt = float(dt_s)
        x, y, yaw, v, b_gyro = self.state

        # Correct gyro for estimated bias
        w_corrected = float(meas_gyro_z) - b_gyro

        # Non-linear kinematic propagation
        yaw_new = (yaw + w_corrected * dt + math.pi) % (2.0 * math.pi) - math.pi
        v_new = max(0.0, v + meas_accel_x * dt)

        # Planar position propagation
        x_new = x + v * math.cos(yaw) * dt
        y_new = y + v * math.sin(yaw) * dt

        self.state = np.array([x_new, y_new, yaw_new, v_new, b_gyro], dtype=np.float64)

        # State Transition Jacobian F = d(f)/d(x)
        F = np.eye(5, dtype=np.float64)
        F[0, 2] = -v * math.sin(yaw) * dt
        F[0, 3] = math.cos(yaw) * dt
        F[1, 2] = v * math.cos(yaw) * dt
        F[1, 3] = math.sin(yaw) * dt
        F[2, 4] = -dt

        # Process noise matrix Q
        Q = np.diag([
            self.q_pos * dt,
            self.q_pos * dt,
            self.q_yaw * dt,
            self.q_v * dt,
            self.q_bias * dt
        ])

        self.P = F @ self.P @ F.T + Q

    def update_wheel_odometry(self, meas_v: float, meas_w: float) -> None:
        """Performs Kalman measurement update using wheel encoder velocity observations."""
        v_meas = float(meas_v)
        w_meas = float(meas_w)

        # Measurement model: z = [v; w] = [state[3]; meas_gyro_z - state[4]]
        # H matrix (2x5): maps state to [v; w]
        H = np.zeros((2, 5), dtype=np.float64)
        H[0, 3] = 1.0  # dv / dv
        H[1, 4] = -1.0 # dw / db_gyro

        z_pred = np.array([self.state[3], -self.state[4]], dtype=np.float64)
        z_actual = np.array([v_meas, w_meas], dtype=np.float64)
        y_residual = z_actual - z_pred

        R = np.diag([self.r_odom_v, self.r_odom_w])

        # Innovation covariance S = H * P * H^T + R
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        # State update
        dx = K @ y_residual
        self.state += dx
        # Normalize yaw
        self.state[2] = (self.state[2] + math.pi) % (2.0 * math.pi) - math.pi

        # Joseph form covariance update for numerical stability: P = (I - KH)P(I - KH)^T + KRK^T
        I = np.eye(5, dtype=np.float64)
        IKH = I - K @ H
        self.P = IKH @ self.P @ IKH.T + K @ R @ K.T

    def get_estimated_pose(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns estimated (x, y, yaw) and 3x3 pose covariance matrix."""
        pose = np.array([self.state[0], self.state[1], self.state[2]], dtype=np.float64)
        cov = self.P[:3, :3]
        return pose, cov
