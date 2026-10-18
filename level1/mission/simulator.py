"""Level 1 Simulator Environment with Strict Information Boundary.
Chapter 91 & Chapter 130 (Part 6 & Part 8).
"""
import numpy as np
from level1.sensing.sensor_model import observe


class Simulator:
    """Isolated environment holding the ground-truth hazard layer.
    The rover side receives no direct handle to truth.
    """
    def __init__(self, truth_grid: np.ndarray, goal_col: int = None):
        self._truth = np.asarray(truth_grid, bool)
        self.n = self._truth.shape[0]
        self.goal_col = self.n - 1 if goal_col is None else goal_col

    def get_observation(self, true_pos: tuple, heading: float, sensor_cfg: dict, rng, sensor_ok: bool = True) -> tuple:
        """Produce restricted sensor observation strictly within the field of view."""
        return observe(self._truth, true_pos, heading, sensor_cfg, rng, sensor_ok)

    def is_hazard(self, pos: tuple) -> bool:
        """Strict truth evaluation: returns True if pos is a hazard cell."""
        if 0 <= pos[0] < self.n and 0 <= pos[1] < self.n:
            return bool(self._truth[pos[0], pos[1]])
        return False

    def is_goal(self, pos: tuple) -> bool:
        """Arrival condition: rover position has reached the goal column."""
        return pos[1] == self.goal_col

    def in_bounds(self, pos: tuple) -> bool:
        return 0 <= pos[0] < self.n and 0 <= pos[1] < self.n
