"""Extreme Environmental Resilience: Multi-Sol Power, Thermal Cycling & Global Dust Storm Survival.
Level 4: Part 25 (Chapters 340 to 349).

Implements environmental models and survival state machines:
1. Diurnal Thermal Modeling: Excursions from -120 deg C night to +20 deg C day with survival heaters.
2. Atmospheric Optical Extinction (Tau): Dust storm degradation up to tau = 6.0.
3. Solar Array Dust Obscuration & Wind Cleaning Events: Models dust factor degradation and recovery.
4. Deep-Sleep Hibernation State Machine: Survival safing protocol under catastrophic dust storms.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class EnvironmentalThermalModel:
    """Simulates diurnal Martian thermal cycles and active survival heating."""
    def __init__(self, min_allowable_avionics_temp_c: float = -40.0):
        self.min_allowable_c = min_allowable_avionics_temp_c
        self.heater_power_w = 25.0

    def compute_diurnal_temperature(self, mars_local_solar_time_hrs: float) -> Dict:
        """Computes ambient and internal avionics temperature at given Mars solar hour."""
        # Mars day: 0 to 24 solar hours. Peak temp at 14:00, coldest at 05:00
        phase = (mars_local_solar_time_hrs - 14.0) * (2.0 * math.pi / 24.0)
        t_ambient_c = -50.0 + 70.0 * math.cos(phase) # -120 C at 02:00-05:00, +20 C at 14:00
        
        # Thermal insulation and RHU (Radioisotope Heater Unit) thermal mass damping
        is_heater_active = (t_ambient_c < -45.0)
        t_avionics_c = max(self.min_allowable_c + 5.0, t_ambient_c + (35.0 if is_heater_active else 15.0))
        
        return {
            'solar_time_hrs': round(mars_local_solar_time_hrs, 2),
            'ambient_temp_c': round(t_ambient_c, 1),
            'avionics_temp_c': round(t_avionics_c, 1),
            'survival_heater_active': is_heater_active,
            'thermal_margin_c': round(t_avionics_c - self.min_allowable_c, 1)
        }


class DustStormSurvivalExecutive:
    """Manages rover power and safe hibernation through planet-encircling dust storms."""
    def __init__(self):
        self.optical_depth_tau = 0.60 # Clear Martian sky
        self.dust_accumulation_factor = 0.88 # 88% solar panel clean
        self.hibernation_mode_active = False

    def update_atmospheric_conditions(
        self, tau_measurement: float, dust_factor_delta: float = -0.01, wind_cleaning_event: bool = False
    ) -> Dict:
        """Updates atmospheric opacity and determines survival mode transitions."""
        self.optical_depth_tau = max(0.2, tau_measurement)
        
        if wind_cleaning_event:
            self.dust_accumulation_factor = min(0.95, self.dust_accumulation_factor + 0.25)
        else:
            self.dust_accumulation_factor = max(0.15, self.dust_accumulation_factor + dust_factor_delta)
            
        # Solar irradiance attenuation: Beer-Lambert law
        # I = I_0 * exp(-tau / cos(zenith)) * dust_factor
        solar_transmittance = math.exp(-self.optical_depth_tau / 1.4) * self.dust_accumulation_factor
        solar_transmittance = float(np.clip(solar_transmittance, 0.02, 1.0))
        
        # Trigger deep-sleep hibernation if transmittance drops below 10%
        if solar_transmittance < 0.10:
            self.hibernation_mode_active = True
            system_status = "CRITICAL_DUST_STORM_DEEP_SLEEP_HIBERNATION"
            power_consumption_w = 4.5 # Ultra-low power survival beacon only
        elif solar_transmittance < 0.25:
            self.hibernation_mode_active = False
            system_status = "CONSERVATIVE_SURVIVAL_MODE_NO_DRIVE"
            power_consumption_w = 22.0
        else:
            self.hibernation_mode_active = False
            system_status = "NOMINAL_SCIENCE_OPERATIONS"
            power_consumption_w = 95.0
            
        return {
            'tau': round(self.optical_depth_tau, 2),
            'dust_factor': round(self.dust_accumulation_factor, 3),
            'solar_transmittance': round(solar_transmittance, 4),
            'hibernation_active': self.hibernation_mode_active,
            'system_status': system_status,
            'survival_power_w': power_consumption_w
        }
