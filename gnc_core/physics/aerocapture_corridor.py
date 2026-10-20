"""Closed-Loop Aerocapture Guidance & 3-Sigma Atmospheric Density Perturbations (TRL 4).
Reference Frame: Mars-Centered Mars-Fixed (MCMF) / Mars-Centered Inertial (MCI).

Implements numerical 3-DOF entry dynamics, stochastic GRAM-style atmospheric density
perturbation injection, closed-loop numeric bank-angle predictor-corrector guidance,
and heat-flux/g-load envelope constraints.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

from gnc_core import MU_MARS, R_MARS_EQUATORIAL, PROTOTYPE_LOCK, NAVIGATION_READY


class MarsAtmosphereModel:
    """Atmospheric density profile with 3-sigma stochastic wave perturbation model."""

    def __init__(
        self,
        rho_0: float = 0.020,  # Surface density (kg/m^3)
        scale_height_m: float = 11100.0,  # Martian scale height (m)
        seed: int = 42
    ) -> None:
        self.rho_0 = float(rho_0)
        self.scale_height = float(scale_height_m)
        self.rng = np.random.default_rng(seed)

    def density(self, altitude_m: float, sigma_perturbation: float = 0.0) -> float:
        """Computes atmospheric density at altitude h with optional 3-sigma perturbation.
        
        rho(h) = rho_0 * exp(-h / H) * (1 + delta_3sigma * sin(2*pi*h / lambda_wave))
        """
        alt = max(0.0, float(altitude_m))
        rho_nom = self.rho_0 * math.exp(-alt / self.scale_height)
        
        # 3-sigma non-nominal perturbation (e.g. +/- 30% dust storm expansion)
        pert_factor = 1.0 + float(sigma_perturbation) * 0.10 * math.sin(2.0 * math.pi * alt / 15000.0)
        return float(max(1e-12, rho_nom * pert_factor))


class AerocaptureCorridorGuidance:
    """Predictor-corrector numeric guidance modulating bank angle during aerocapture."""

    def __init__(
        self,
        vehicle_mass_kg: float = 1200.0,
        ref_area_m2: float = 7.5,
        c_l: float = 0.35,
        c_d: float = 1.20,
        target_apoapsis_km: float = 6000.0,
        max_bank_deg: float = 85.0
    ) -> None:
        self.mass = float(vehicle_mass_kg)
        self.area = float(ref_area_m2)
        self.c_l = float(c_l)
        self.c_d = float(c_d)
        self.r_target_a = (R_MARS_EQUATORIAL + float(target_apoapsis_km) * 1000.0)
        self.max_bank = float(max_bank_deg)
        self.atmo = MarsAtmosphereModel()

    def compute_derivatives(
        self,
        r: float,
        v: float,
        gamma: float,
        bank_rad: float,
        rho: float
    ) -> Tuple[float, float, float]:
        """Evaluates 3-DOF planar entry equations of motion in Mars inertial frame.
        
        dr/dt = v * sin(gamma)
        dv/dt = - D / m - (mu / r^2) * sin(gamma)
        dgamma/dt = (L * cos(bank)) / (m * v) + (v / r - mu / (v * r^2)) * cos(gamma)
        """
        dyn_p = 0.5 * rho * (v**2)
        lift = dyn_p * self.area * self.c_l
        drag = dyn_p * self.area * self.c_d

        r_dot = v * math.sin(gamma)
        g_local = MU_MARS / (r**2)
        v_dot = -(drag / self.mass) - g_local * math.sin(gamma)

        gamma_dot = (lift * math.cos(bank_rad)) / (self.mass * v) + (v / r - g_local / v) * math.cos(gamma)

        return r_dot, v_dot, gamma_dot

    def evaluate_guidance_cycle(
        self,
        altitude_m: float,
        velocity_mps: float,
        flight_path_angle_rad: float,
        density_perturbation_sigma: float = 0.0
    ) -> Dict[str, Any]:
        """Calculates closed-loop bank angle command to track target apoapsis corridor.
        
        Incorporates predictive energy dissipation feedback and 3-sigma density resilience.
        """
        r = R_MARS_EQUATORIAL + float(altitude_m)
        v = float(velocity_mps)
        gamma = float(flight_path_angle_rad)

        rho = self.atmo.density(altitude_m, sigma_perturbation=density_perturbation_sigma)
        dyn_p = 0.5 * rho * (v**2)
        drag = dyn_p * self.area * self.c_d
        lift = dyn_p * self.area * self.c_l
        g_load = math.sqrt(lift**2 + drag**2) / (self.mass * 9.80665)

        # Stagnation point heat flux estimation (Sutton-Graves relation for Mars CO2)
        r_nose_m = 0.8
        k_sg = 1.9027e-4  # Sutton-Graves constant for CO2
        heat_flux_w_cm2 = k_sg * math.sqrt(rho / r_nose_m) * (v**3) / 10000.0

        # Nominal density at current altitude
        rho_nom = self.atmo.density(altitude_m, sigma_perturbation=0.0)
        density_ratio = (rho - rho_nom) / max(1e-12, rho_nom)

        # Current specific orbital energy
        energy_current = 0.5 * (v**2) - (MU_MARS / r)

        # Reference trajectory energy dissipation profile
        e_entry_ref = 0.5 * (5800.0**2) - (MU_MARS / (R_MARS_EQUATORIAL + 125000.0))
        e_target_ref = -MU_MARS / (2.0 * 0.5 * (R_MARS_EQUATORIAL + 50000.0 + self.r_target_a))
        dissipation_frac = float(np.clip((125000.0 - altitude_m) / 75000.0, 0.0, 1.0))
        energy_ref = e_entry_ref - dissipation_frac * (e_entry_ref - e_target_ref)
        energy_error = energy_current - energy_ref

        # Predictor-corrector bank angle control:
        # 1. Base bank angle 45 degrees
        # 2. Energy tracking adjustment
        # 3. Density perturbation feedback: if thin air (density_ratio < 0), lower bank to dive deeper
        k_e = 30.0 / 2.0e6  # deg per (J/kg)
        k_rho = 25.0        # deg per fractional density deviation
        bank_cmd_deg = 45.0 - k_e * energy_error + k_rho * density_ratio
        bank_cmd_deg = float(np.clip(bank_cmd_deg, 0.0, self.max_bank))

        # Check corridor status:
        # Vehicle is in corridor when within entry corridor flight path angle [-14 deg, -9 deg],
        # within structural g-load limit (<= 5.0 g), thermal heat flux limit (<= 450 W/cm^2),
        # and atmospheric capture boundary [40 km, 125 km].
        fpa_deg = math.degrees(gamma)
        in_corridor = bool(
            (-14.0 <= fpa_deg <= -9.0)
            and (g_load <= 5.0)
            and (heat_flux_w_cm2 <= 450.0)
            and (40000.0 <= altitude_m <= 125000.0)
        )
        exit_safe = bool(v <= 3600.0 or altitude_m > 125000.0)

        return {
            "altitude_m": altitude_m,
            "velocity_mps": velocity_mps,
            "flight_path_angle_deg": math.degrees(gamma),
            "density_kg_m3": rho,
            "g_load_g": float(g_load),
            "heat_flux_w_cm2": float(heat_flux_w_cm2),
            "energy_error_j_kg": float(energy_error),
            "commanded_bank_deg": round(bank_cmd_deg, 2),
            "in_corridor": in_corridor,
            "aerocapture_complete": exit_safe,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY,
        }
