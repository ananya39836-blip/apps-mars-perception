"""Extreme Mobility Dynamics, Active Articulation & Steep-Slope Wheel-Walking/Anchoring.
Level 4: Part 20 (Chapters 290 to 299).

Implements extreme planetary mobility modes:
1. Active Rocker-Bogie Articulation: Actively commands suspension joints to alter chassis attitude.
2. Dynamic CoM Shifting: Re-distributes normal load across wheels on steep slopes (up to 35 deg).
3. Wheel-Walking Crab Gait: Peristaltic crawling locomotion mode to escape severe sandy slip entrapment.
4. Steep-Slope Tethered Mobility: Computes required tether tension and anchorage safety factors.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class ActiveSuspensionArticulator:
    """Active articulation controller for rocker-bogie pitch and dynamic CoM leveling."""
    def __init__(self, rover_mass_kg: float = 185.0, wheelbase_m: float = 1.20, track_width_m: float = 0.90):
        self.mass_kg = rover_mass_kg
        self.gravity = 3.71
        self.wheelbase_m = wheelbase_m
        self.track_width_m = track_width_m
        self.max_articulation_angle_rad = math.radians(25.0)

    def compute_active_leveling(
        self, slope_pitch_rad: float, slope_roll_rad: float
    ) -> Dict:
        """Calculates active joint angles to level the chassis body against steep incline."""
        # Target chassis level attitude (pitch -> 0, roll -> 0)
        cmd_rocker_left_pitch = -np.clip(slope_pitch_rad, -self.max_articulation_angle_rad, self.max_articulation_angle_rad)
        cmd_rocker_right_pitch = -np.clip(slope_pitch_rad, -self.max_articulation_angle_rad, self.max_articulation_angle_rad)
        cmd_bogie_roll = -np.clip(slope_roll_rad, -self.max_articulation_angle_rad, self.max_articulation_angle_rad)
        
        # Residual tilt experienced by the avionics deck
        residual_pitch = slope_pitch_rad + cmd_rocker_left_pitch
        residual_roll = slope_roll_rad + cmd_bogie_roll
        
        # CoM shift vector in rover body frame (meters)
        # Shift CoM uphill along x/y to counteract gravity vector tilt
        com_shift_x_m = float(np.clip(-0.15 * math.sin(slope_pitch_rad), -0.15, 0.15))
        com_shift_y_m = float(np.clip(-0.12 * math.sin(slope_roll_rad), -0.12, 0.12))
        
        # Stability margin improvement factor
        rollover_risk_baseline = math.sin(abs(slope_pitch_rad)) + math.sin(abs(slope_roll_rad))
        rollover_risk_active = math.sin(abs(residual_pitch)) + math.sin(abs(residual_roll))
        stability_gain_pct = max(0.0, (1.0 - (rollover_risk_active / (rollover_risk_baseline + 1e-5))) * 100.0)

        return {
            'cmd_rocker_left_rad': float(cmd_rocker_left_pitch),
            'cmd_rocker_right_rad': float(cmd_rocker_right_pitch),
            'cmd_bogie_roll_rad': float(cmd_bogie_roll),
            'residual_pitch_deg': float(math.degrees(residual_pitch)),
            'residual_roll_deg': float(math.degrees(residual_roll)),
            'com_shift_m': (com_shift_x_m, com_shift_y_m),
            'stability_gain_pct': float(stability_gain_pct)
        }


class WheelWalkingGaitGenerator:
    """Generates peristaltic wheel-walking gaits for negotiating soft, entrapping sandy slopes."""
    def __init__(self, step_length_m: float = 0.08):
        self.step_length_m = step_length_m
        self.gait_phases = [
            "LOCKED_5_ADVANCE_FL",
            "LOCKED_5_ADVANCE_FR",
            "LOCKED_5_ADVANCE_ML",
            "LOCKED_5_ADVANCE_MR",
            "LOCKED_5_ADVANCE_RL",
            "LOCKED_5_ADVANCE_RR",
            "CHASSIS_PULL_FORWARD"
        ]

    def generate_gait_cycle(self, slip_ratio: float, slope_deg: float) -> Dict:
        """Computes gait parameters and net displacement under extreme slip conditions."""
        is_wheel_walking_required = (slip_ratio > 0.50 or slope_deg > 20.0)
        
        if not is_wheel_walking_required:
            return {
                'active_mode': 'STANDARD_ROLLING',
                'cycle_duration_s': 1.0,
                'advance_per_cycle_m': 0.15,
                'effective_traction_gain': 1.0
            }
            
        # Wheel-walking mode: anchors non-moving wheels while pushing single wheels forward
        # Drastically reduces bulk sinkage by avoiding continuous shear failure beneath all wheels simultaneously
        advance_per_cycle = self.step_length_m * (1.0 - 0.3 * math.sin(math.radians(slope_deg)))
        effective_traction_gain = 3.2 # 3.2x higher drawbar pull than continuous spinning in sand
        
        return {
            'active_mode': 'PERISTALTIC_WHEEL_WALKING',
            'phases': self.gait_phases,
            'cycle_duration_s': 18.0,
            'advance_per_cycle_m': float(advance_per_cycle),
            'effective_traction_gain': float(effective_traction_gain),
            'sinkage_suppression_ratio': 0.65
        }


class TetheredSlopeMobility:
    """Computes tether anchorage tension and safety factor on crater walls up to 45 degrees."""
    def __init__(self, rover_mass_kg: float = 185.0):
        self.mass_kg = rover_mass_kg
        self.gravity = 3.71
        self.rover_weight_N = self.mass_kg * self.gravity

    def evaluate_tether_tension(self, slope_deg: float, wheel_traction_limit_N: float = 150.0) -> Dict:
        """Calculates required tether line tension and anchor margin."""
        slope_rad = math.radians(slope_deg)
        grav_downslope_N = self.rover_weight_N * math.sin(slope_rad)
        grav_normal_N = self.rover_weight_N * math.cos(slope_rad)
        
        # Deficit that wheels cannot sustain without sliding downhill
        tension_required_N = max(0.0, grav_downslope_N - wheel_traction_limit_N)
        
        tether_breaking_strength_N = 8000.0 # Kevlar/Spectra tether
        safety_factor = tether_breaking_strength_N / (tension_required_N + 1e-3)
        
        return {
            'slope_deg': slope_deg,
            'grav_downslope_N': float(grav_downslope_N),
            'grav_normal_N': float(grav_normal_N),
            'tether_tension_N': float(tension_required_N),
            'tether_safety_factor': float(safety_factor),
            'anchor_holding_safe': safety_factor >= 3.0
        }
