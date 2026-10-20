"""Level 6 Part 43: Autonomous Asteroid Deflection & Kinetic Impactors.
Chapters 520 to 529: Binary Asteroid Proximity Operations, Hypervelocity Homing & Gravity Tractors.

Implements autonomous binary asteroid proximity operations, line-of-sight proportional
navigation for hypervelocity kinetic impactors (DART-heritage), and ion gravity tractor towing.
"""
import math
from typing import Dict, Any, List, Optional
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

G_UNIV = 6.67430e-11  # m^3 / (kg s^2)


class BinaryAsteroidTracker:
    """Tracks binary asteroid mutual orbit (Didymos-Dimorphos class) and Hill sphere bounds."""

    def __init__(self, m_primary_kg: float = 5.2e11, m_secondary_kg: float = 4.8e9, semi_major_axis_m: float = 1180.0):
        self.m1 = m_primary_kg
        self.m2 = m_secondary_kg
        self.a = semi_major_axis_m

    def compute_mutual_orbital_parameters(self) -> Dict[str, Any]:
        """Calculates orbital period, mutual mean motion, and Hill sphere radius."""
        mu_total = G_UNIV * (self.m1 + self.m2)
        mean_motion_rad_s = math.sqrt(mu_total / (self.a**3))
        period_hours = (2.0 * math.pi / mean_motion_rad_s) / 3600.0

        # Hill sphere relative to Sun at 1.05 AU
        r_sun = 1.05 * 1.496e11
        r_hill_m = r_sun * ((self.m1 + self.m2) / (3.0 * 1.989e30))**(1.0 / 3.0)

        return {
            "primary_mass_kg": self.m1,
            "secondary_mass_kg": self.m2,
            "mutual_period_hours": round(period_hours, 2),
            "mean_motion_rad_s": mean_motion_rad_s,
            "hill_sphere_radius_km": round(r_hill_m / 1000.0, 2),
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class KineticImpactorGuidance:
    """Proportional navigation guidance for hypervelocity kinetic impactor (6.5 km/s)."""

    def __init__(self, impactor_mass_kg: float = 570.0, impact_speed_mps: float = 6500.0, nav_gain_N: float = 3.5):
        self.mass_kg = impactor_mass_kg
        self.v_impact = impact_speed_mps
        self.nav_gain = nav_gain_N

    def compute_terminal_guidance(self, range_to_target_m: float, los_rate_rad_s: float, beta_estimate: float = 2.4) -> Dict[str, Any]:
        """Calculates commanded lateral acceleration and predicted momentum deflection."""
        # Proportional navigation command: a_cmd = N * v_c * omega_los
        a_cmd_mps2 = float(np.clip(self.nav_gain * self.v_impact * los_rate_rad_s, -45.0, 45.0))
        time_to_go_s = range_to_target_m / self.v_impact

        # Momentum transfer: Delta_P = beta * m * v
        delta_p_Ns = beta_estimate * self.mass_kg * self.v_impact
        kinetic_energy_gj = 0.5 * self.mass_kg * (self.v_impact**2) / 1e9

        return {
            "time_to_go_s": round(time_to_go_s, 3),
            "commanded_accel_mps2": round(a_cmd_mps2, 2),
            "delta_momentum_Ns": round(delta_p_Ns, 2),
            "kinetic_energy_gj": round(kinetic_energy_gj, 2),
            "target_locked": range_to_target_m < 50000.0,
            "impact_imminent": time_to_go_s < 1.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class GravityTractorController:
    """Models ion engine stand-off station-keeping for gravitational deflection towing."""

    def __init__(self, spacecraft_mass_kg: float = 1200.0, target_asteroid_mass_kg: float = 4.8e9):
        self.m_craft = spacecraft_mass_kg
        self.m_ast = target_asteroid_mass_kg

    def compute_towing_force(self, standoff_distance_m: float, cant_angle_deg: float = 20.0) -> Dict[str, Any]:
        """Calculates mutual gravitational attraction and required canted ion thrust."""
        f_grav_N = G_UNIV * (self.m_craft * self.m_ast) / (standoff_distance_m**2)
        # Thrusters must be canted to prevent plume impingement on asteroid
        cant_rad = math.radians(cant_angle_deg)
        required_thrust_N = f_grav_N / math.cos(cant_rad)

        return {
            "standoff_distance_m": standoff_distance_m,
            "gravitational_tow_force_N": round(f_grav_N, 4),
            "required_ion_thrust_N": round(required_thrust_N, 4),
            "cant_angle_deg": cant_angle_deg,
            "station_keeping_stable": standoff_distance_m >= 100.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
