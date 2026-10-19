"""Vehicle Physical Parameters and Kinematic Drive Constraints.
Chapter 84.1, 209.3 / Part 12 Task 101.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class RoverParams:
    """Physical dimensions, kinematic limits, and terrain interaction thresholds."""
    # Geometric dimensions (metres)
    wheelbase: float = 1.00          # Distance between front and rear axle
    track_width: float = 0.80        # Distance between left and right wheels
    ground_clearance: float = 0.25   # Belly pan clearance above ground
    wheel_radius: float = 0.15       # Radius of drive wheels
    body_length: float = 1.20        # Bounding envelope length
    body_width: float = 0.90         # Bounding envelope width
    
    # Kinematic drive limits
    v_max: float = 0.50              # Maximum forward speed (m/s)
    k_max: float = 1.50              # Maximum curvature (1/m, minimum turn radius = 0.67 m)
    a_max: float = 0.25              # Maximum linear acceleration (m/s^2)
    omega_max: float = 0.50          # Maximum yaw rate (rad/s)
    
    # Stability and traversability safety thresholds
    max_safe_slope_deg: float = 20.0 # Slope beyond which traction slips (deg)
    tip_slope_deg: float = 30.0      # Critical slope threshold triggering vehicle tip-over (deg)
    max_step_height_m: float = 0.20  # Max step ledge negotiable without high-centering

    @property
    def max_safe_slope_rad(self) -> float:
        return math.radians(self.max_safe_slope_deg)

    @property
    def tip_slope_rad(self) -> float:
        return math.radians(self.tip_slope_deg)
        
    @property
    def min_turn_radius_m(self) -> float:
        return 1.0 / self.k_max
