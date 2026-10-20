"""Level 6 Part 40: Titan Cryogenic Atmospheric & Nautical Exploration.
Chapters 490 to 499: Liquid Hydrocarbon Submersibles, Bathymetry & Dense Atmosphere VTOL.

Implements autonomous buoyancy-controlled submersibles in liquid methane/ethane seas (94 K),
cryogenic acoustic bathymetry, and thick nitrogen atmosphere rotorcraft flight.
"""
import math
from typing import Dict, Any, List, Optional
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

G_TITAN = 1.352  # m/s^2
RHO_METHANE_ETHANE = 540.0  # kg/m^3 (approx 50/50 binary mixture at 94 K)
RHO_TITAN_ATM = 5.4  # kg/m^3 (approx 4.5x Earth sea level density)


class HydrocarbonSubmersible:
    """Manages buoyancy, ballast bellows, and depth control in cryogenic liquid seas."""

    def __init__(self, dry_mass_kg: float = 320.0, max_depth_m: float = 300.0):
        self.mass_kg = dry_mass_kg
        self.max_depth_m = max_depth_m
        self.current_depth_m = 0.0
        self.bellows_volume_m3 = dry_mass_kg / RHO_METHANE_ETHANE  # Neutral displacement baseline

    def adjust_buoyancy(self, delta_volume_liters: float) -> Dict[str, Any]:
        """Adjusts bellows volume to control vertical dive/climb velocity."""
        self.bellows_volume_m3 += (delta_volume_liters / 1000.0)
        displaced_mass_kg = self.bellows_volume_m3 * RHO_METHANE_ETHANE
        net_buoyancy_N = (displaced_mass_kg - self.mass_kg) * G_TITAN

        # Vertical terminal velocity approximation: v = sqrt(2 |F_net| / (rho * C_d * A))
        c_d_area = 0.85 * 0.45
        v_vertical_mps = math.copysign(math.sqrt(2.0 * max(0.1, abs(net_buoyancy_N)) / (RHO_METHANE_ETHANE * c_d_area)), net_buoyancy_N)
        self.current_depth_m = float(np.clip(self.current_depth_m - v_vertical_mps * 10.0, 0.0, self.max_depth_m))

        return {
            "current_depth_m": round(self.current_depth_m, 2),
            "net_buoyancy_N": round(net_buoyancy_N, 2),
            "vertical_rate_mps": round(v_vertical_mps, 3),
            "safe_depth_envelope": self.current_depth_m < self.max_depth_m,
            "liquid_temp_k": 94.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class AcousticBathymetrySounder:
    """Multi-beam sonar profiling cryogenic seabed topography and bubble nucleation."""

    def __init__(self, beam_count: int = 16):
        self.beam_count = beam_count
        self.speed_of_sound = 1420.0  # m/s in 94 K liquid methane

    def ping_seabed(self, true_altitude_above_bottom_m: float) -> Dict[str, Any]:
        """Calculates acoustic time-of-flight and detects dissolved nitrogen gas effervescence."""
        tof_seconds = (2.0 * true_altitude_above_bottom_m) / self.speed_of_sound
        measured_depth = (tof_seconds * self.speed_of_sound) / 2.0
        # Cavitation / bubble threshold
        effervescence_detected = true_altitude_above_bottom_m < 8.0

        return {
            "measured_altitude_m": round(measured_depth, 2),
            "two_way_tof_ms": round(tof_seconds * 1000.0, 2),
            "effervescence_bubble_alert": effervescence_detected,
            "speed_of_sound_mps": self.speed_of_sound,
            "beams_active": self.beam_count,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class TitanDenseAeroDrone:
    """Flight mechanics and hover power modeling in Titan thick nitrogen atmosphere."""

    def __init__(self, vehicle_mass_kg: float = 45.0, rotor_diameter_m: float = 1.2):
        self.mass_kg = vehicle_mass_kg
        self.rotor_diameter_m = rotor_diameter_m
        self.disk_area = math.pi * (rotor_diameter_m / 2.0)**2

    def compute_hover_power(self) -> Dict[str, Any]:
        """Calculates aerodynamic hover power in Titan high-density, low-gravity regime."""
        weight_N = self.mass_kg * G_TITAN  # Only 60.8 N weight on Titan!
        # Induced velocity: v_i = sqrt(W / (2 * rho * A))
        v_induced = math.sqrt(weight_N / (2.0 * RHO_TITAN_ATM * self.disk_area))
        ideal_power_w = weight_N * v_induced
        actual_power_w = ideal_power_w / 0.65  # 65% figure of merit

        return {
            "weight_titan_N": round(weight_N, 2),
            "induced_velocity_mps": round(v_induced, 3),
            "hover_power_watts": round(actual_power_w, 2),
            "earth_power_ratio": round(actual_power_w / (self.mass_kg * 9.81 * math.sqrt(self.mass_kg * 9.81 / (2 * 1.225 * self.disk_area)) / 0.65), 3),
            "flight_authorized": actual_power_w < 500.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
