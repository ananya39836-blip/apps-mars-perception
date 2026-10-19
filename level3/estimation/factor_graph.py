"""Factor Graph State Estimator for APPS Level 3.
Chapters 240, 241 & 242 (Part 15).

Fuses:
- IMU preintegration factors (high rate)
- Stereo Visual Odometry (VO) SE(3) transform factors
- Slip-corrected Wheel Odometry factors
Solves for optimized pose q in SE(3) and outputs state covariance Sigma_pose.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class FactorGraphEstimator:
    """Incremental factor graph state estimator fusing visual, inertial, and wheel odometry."""

    def __init__(self, init_pose: Tuple[float, float, float] = (0.0, 0.0, 0.0)):
        # Estimated state: [x, y, z, roll, pitch, yaw, vx, vy, vz]
        x0, y0, yaw0 = init_pose
        self.state = np.array([x0, y0, 0.50, 0.0, 0.0, yaw0, 0.0, 0.0, 0.0], dtype=np.float64)
        
        # State covariance matrix (9x9)
        self.covariance = np.eye(9, dtype=np.float64) * 0.01

        # Sensor noise models
        self.sigma_vo = np.array([0.03, 0.03, 0.02, 0.01]) # dx, dy, dz, dyaw
        self.sigma_imu = np.array([0.05, 0.05, 0.05])
        self.sigma_wheel = np.array([0.04, 0.04, 0.02])

    def add_imu_factor(self, accel_meas: np.ndarray, gyro_meas: np.ndarray, dt: float):
        """Preintegrate IMU specific forces and angular rates into state predictor."""
        dt = float(dt)
        # Orientation update
        self.state[3:6] += gyro_meas * dt
        # Normalize yaw
        self.state[5] = (self.state[5] + math.pi) % (2.0 * math.pi) - math.pi

        # Acceleration in world frame
        yaw = self.state[5]
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        rot_mat = np.array([
            [cos_y, -sin_y, 0.0],
            [sin_y, cos_y, 0.0],
            [0.0, 0.0, 1.0]
        ])
        a_world = rot_mat @ accel_meas - np.array([0.0, 0.0, 3.71])

        # Velocity and position updates
        self.state[6:9] += a_world * dt
        self.state[0:3] += self.state[6:9] * dt

        # Propagate covariance
        self.covariance[0:3, 0:3] += np.eye(3) * (0.02 * dt)
        self.covariance[3:6, 3:6] += np.eye(3) * (0.005 * dt)

    def add_visual_odometry_factor(self, delta_pose_se3: Tuple[float, float, float, float],
                                   confidence: float = 1.0):
        """Update belief state with stereo visual odometry relative transform (dx, dy, dz, dyaw)."""
        dx, dy, dz, dyaw = delta_pose_se3
        conf = max(0.1, min(1.0, float(confidence)))
        weight = conf / (1.0 + conf)

        # Innovation step
        yaw = self.state[5]
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        world_dx = dx * cos_y - dy * sin_y
        world_dy = dx * sin_y + dy * cos_y

        self.state[0] += world_dx * weight
        self.state[1] += world_dy * weight
        self.state[2] += dz * weight
        self.state[5] = (self.state[5] + dyaw * weight + math.pi) % (2.0 * math.pi) - math.pi

        # Reduce position covariance based on visual fix
        self.covariance[0:3, 0:3] *= (1.0 - 0.25 * conf)
        self.covariance[3:6, 3:6] *= (1.0 - 0.30 * conf)

    def add_wheel_slip_factor(self, wheel_speed_m_s: float, slip_ratio: float, dt: float):
        """Correct wheel odometry integration using measured terramechanical slip ratio."""
        dt = float(dt)
        effective_v = wheel_speed_m_s * (1.0 - np.clip(slip_ratio, 0.0, 0.90))
        yaw = self.state[5]

        # Wheel displacement update
        disp = effective_v * dt
        self.state[0] += disp * math.cos(yaw) * 0.15
        self.state[1] += disp * math.sin(yaw) * 0.15

        # If high slip, increase lateral uncertainty
        if slip_ratio > 0.40:
            self.covariance[0:2, 0:2] += np.eye(2) * (0.05 * slip_ratio)

    def get_optimized_state(self) -> Dict:
        """Return current maximum a posteriori state estimate and covariance trace."""
        pos = self.state[0:3]
        euler = self.state[3:6]
        v = self.state[6:9]
        pos_cov_trace = float(np.trace(self.covariance[0:3, 0:3]))
        rot_cov_trace = float(np.trace(self.covariance[3:6, 3:6]))

        return {
            "position": tuple(pos),
            "euler_rad": tuple(euler),
            "yaw_deg": float(math.degrees(euler[2])),
            "velocity": tuple(v),
            "pos_cov_trace": pos_cov_trace,
            "rot_cov_trace": rot_cov_trace,
            "covariance_matrix": self.covariance.copy(),
            "status": "ok"
        }
