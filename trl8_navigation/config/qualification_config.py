"""Qualification and System Configuration Package."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
import numpy as np

@dataclass(frozen=True)
class QualificationConfig:
    """Immutable system configuration parameters with sanity bounds checking."""
    # Timing budgets (ms)
    imu_rate_hz: float = 100.0
    navigation_rate_hz: float = 10.0
    max_cycle_latency_ms: float = 100.0
    planner_timeout_ms: float = 80.0
    
    # Kinematics
    rover_length_m: float = 2.80
    rover_width_m: float = 2.20
    rover_mass_kg: float = 850.0
    wheel_radius_m: float = 0.25
    max_velocity_mps: float = 0.40
    max_curvature_inv_m: float = 1.50
    
    # Hazard limits
    max_slope_deg: float = 25.0
    tip_over_slope_deg: float = 30.0
    step_obstacle_limit_m: float = 0.20
    inflation_margin_m: float = 0.35
    
    # Grid map
    grid_resolution_m: float = 0.20
    local_map_size_m: float = 30.0
    
    def validate(self) -> bool:
        """Validates all physical bounds."""
        assert self.imu_rate_hz >= 50.0, "IMU rate must be at least 50 Hz"
        assert self.navigation_rate_hz >= 5.0, "Navigation rate must be at least 5 Hz"
        assert self.rover_mass_kg > 0.0, "Mass must be positive"
        assert self.max_velocity_mps <= 1.0, "Speed exceeds planetary rover limit"
        assert self.max_slope_deg < self.tip_over_slope_deg, "Slope limit mismatch"
        return True
