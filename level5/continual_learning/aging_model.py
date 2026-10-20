"""Level 5 Part 36: Lifelong Continual Learning & Actuator Aging Model.
Chapter 450-459: Multi-Mission Adaptation & Mechanical Degradation Compensation.

Provides Bayesian experience replay, catastrophic forgetting suppression,
actuator gear wear/backlash tracking, and online control gain adaptation for
decade-long planetary exploration missions.
"""
import math
from typing import Dict, Any, List, Optional
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class ContinualExperienceReplay:
    """Episodic memory replay with importance sampling to prevent catastrophic forgetting."""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer: List[Dict[str, Any]] = []
        self.surprise_scores: List[float] = []

    def store_experience(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray, surprise: float = 1.0):
        """Stores experience tuple with Bayesian surprise weight."""
        if len(self.buffer) >= self.capacity:
            # Drop lowest surprise entry
            min_idx = int(np.argmin(self.surprise_scores))
            self.buffer.pop(min_idx)
            self.surprise_scores.pop(min_idx)

        self.buffer.append({
            "state": np.asarray(state, dtype=np.float32),
            "action": np.asarray(action, dtype=np.float32),
            "reward": float(reward),
            "next_state": np.asarray(next_state, dtype=np.float32)
        })
        self.surprise_scores.append(float(surprise))

    def sample_batch(self, batch_size: int = 32) -> Dict[str, np.ndarray]:
        """Samples experiences proportional to surprise / novelty weight."""
        n = len(self.buffer)
        if n == 0:
            return {}
        probs = np.array(self.surprise_scores)
        probs = probs / np.sum(probs)
        k = min(batch_size, n)
        indices = np.random.choice(n, size=k, p=probs, replace=False if n >= k else True)

        states = np.array([self.buffer[i]["state"] for i in indices])
        actions = np.array([self.buffer[i]["action"] for i in indices])
        rewards = np.array([self.buffer[i]["reward"] for i in indices])
        next_states = np.array([self.buffer[i]["next_state"] for i in indices])

        return {
            "states": states,
            "actions": actions,
            "rewards": rewards,
            "next_states": next_states,
            "mean_novelty": float(np.mean([self.surprise_scores[i] for i in indices]))
        }


class ActuatorWearCompensator:
    """Predicts mechanical degradation and adapts control gains."""

    def __init__(self, num_actuators: int = 6):
        self.num_actuators = num_actuators
        self.operating_hours = np.zeros(num_actuators, dtype=np.float32)
        self.backlash_rad = np.full(num_actuators, 0.001, dtype=np.float32)  # Initial 1 mrad backlash
        self.friction_coeff = np.full(num_actuators, 0.15, dtype=np.float32)  # Initial viscous friction
        self.nominal_gains = np.full(num_actuators, 100.0, dtype=np.float32)  # Nominal torque gain

    def advance_mission_wear(self, elapsed_hours: float, load_factors: Optional[np.ndarray] = None):
        """Simulates wear progression over operational lifetime."""
        if load_factors is None:
            load_factors = np.ones(self.num_actuators, dtype=np.float32)

        self.operating_hours += elapsed_hours
        # Wear model: backlash increases logarithmically, friction increases with thermal cycling
        wear_rate = 1.0e-5 * load_factors
        self.backlash_rad += (wear_rate * elapsed_hours).astype(np.float32)
        self.friction_coeff += (0.00005 * load_factors * elapsed_hours).astype(np.float32)

    def compute_adapted_torque(self, desired_torque: np.ndarray, angular_velocity: np.ndarray) -> Dict[str, Any]:
        """Calculates compensated torque accounting for backlash deadband and friction drift."""
        raw_cmd = np.asarray(desired_torque, dtype=np.float32)
        vel = np.asarray(angular_velocity, dtype=np.float32)

        # Backlash deadband compensation
        deadband_comp = np.sign(vel) * (self.backlash_rad * 10.0)
        # Viscous friction compensation
        friction_comp = self.friction_coeff * vel

        compensated_torque = raw_cmd + friction_comp + deadband_comp
        # Adaptive gain correction factor
        gain_scale = 1.0 + (self.backlash_rad / 0.05)

        return {
            "raw_torque": raw_cmd.tolist(),
            "compensated_torque": compensated_torque.tolist(),
            "gain_scale_factors": gain_scale.tolist(),
            "max_backlash_mrad": float(np.max(self.backlash_rad) * 1000.0),
            "mean_friction": float(np.mean(self.friction_coeff))
        }
