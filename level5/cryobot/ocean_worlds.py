"""Ocean Worlds & Cryogenic Cryobot Sub-Ice Exploration (Europa/Enceladus Penetration).
Level 5: Part 30 (Chapters 390 to 399).

Implements deep-ice penetration and sub-surface ocean autonomy:
1. Thermal Melt-Head Phase Change Drilling Kinematics.
2. Hydrothermal Vent Chemical Gradient Plume Tracing.
3. Forward Lookahead Sonar for Sub-Ice Keels.
4. Buoyant Trim & Hydrodynamic Attitude Control.
"""
import math
from typing import Dict, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class CryobotThermalDrill:
    """Models thermal melt-head kinematics through cryogenic vacuum ice shells (Europa/Enceladus)."""
    def __init__(self, thermal_power_w: float = 4500.0, probe_diameter_m: float = 0.28, probe_mass_kg: float = 120.0):
        self.power_w = thermal_power_w
        self.diameter_m = probe_diameter_m
        self.area_m2 = math.pi * (probe_diameter_m / 2.0)**2
        self.mass_kg = probe_mass_kg
        self.density_ice = 920.0 # kg/m3
        self.latent_heat_fusion = 334000.0 # J/kg
        self.specific_heat_ice = 2050.0 # J/kg*K

    def compute_penetration_rate(self, ambient_ice_temp_k: float = 110.0) -> Dict:
        """Calculates vertical melting velocity (m/hr) through cryogenic ice."""
        delta_t_k = max(10.0, 273.15 - ambient_ice_temp_k)
        # Energy required to warm ice to 273K and melt it: Q = L_f + c_p * Delta_T
        energy_per_kg = self.latent_heat_fusion + self.specific_heat_ice * delta_t_k
        
        # Melting rate: v = P / (rho_ice * Area * energy_per_kg)
        v_mps = self.power_w / (self.density_ice * self.area_m2 * energy_per_kg)
        v_m_per_hour = v_mps * 3600.0
        
        # Thermal efficiency factor (accounting for lateral conductive loss into cold ice wall)
        efficiency_pct = max(45.0, 85.0 - 0.25 * delta_t_k)
        effective_v_m_per_hour = v_m_per_hour * (efficiency_pct / 100.0)
        
        return {
            'ambient_ice_temp_k': ambient_ice_temp_k,
            'theoretical_melt_rate_m_hr': round(v_m_per_hour, 3),
            'effective_melt_rate_m_hr': round(effective_v_m_per_hour, 3),
            'thermal_efficiency_pct': round(efficiency_pct, 1),
            'penetration_speed_cm_hr': round(effective_v_m_per_hour * 100.0, 1)
        }


class SubOceanPlumeTracer:
    """Autonomous chemical gradient ascent to locate sub-ocean hydrothermal vent plumes."""
    def __init__(self, vent_origin_xy: Tuple[float, float] = (150.0, 80.0)):
        self.vent_pos = vent_origin_xy

    def sample_chemical_signature(self, pos_xy: Tuple[float, float]) -> Dict:
        """Measures dissolved volatile concentration (e.g. silica, methane, hydrogen)."""
        dist = math.hypot(pos_xy[0] - self.vent_pos[0], pos_xy[1] - self.vent_pos[1])
        # Gaussian plume dispersion model
        concentration_ppb = 850.0 * math.exp(-0.5 * (dist / 45.0)**2) + np.random.uniform(0.0, 5.0)
        
        # Gradient vector pointing towards vent
        grad_x = - (pos_xy[0] - self.vent_pos[0]) / (dist + 1e-4)
        grad_y = - (pos_xy[1] - self.vent_pos[1]) / (dist + 1e-4)
        
        return {
            'pos': pos_xy,
            'concentration_ppb': round(concentration_ppb, 2),
            'gradient_bearing_deg': round(math.degrees(math.atan2(grad_y, grad_x)), 1),
            'is_plume_detected': concentration_ppb > 25.0
        }


class ForwardLookaheadSonar:
    """Acoustic obstacle avoidance sonar detecting submerged ice keels and rocky inclusions."""
    def __init__(self, max_range_m: float = 250.0):
        self.max_range_m = max_range_m

    def scan_forward_sector(self, range_to_nearest_keel_m: float = 45.0) -> Dict:
        """Returns acoustic return parameters and clearance margin."""
        is_clear = range_to_nearest_keel_m > 15.0
        acoustic_delay_ms = (2.0 * range_to_nearest_keel_m / 1450.0) * 1000.0 # Speed of sound in brine: 1450 m/s
        
        return {
            'obstacle_range_m': round(range_to_nearest_keel_m, 1),
            'echo_delay_ms': round(acoustic_delay_ms, 2),
            'path_clear': is_clear,
            'recommended_steering_bias': "DIVE_DOWN" if not is_clear else "MAINTAIN_HEADING"
        }
