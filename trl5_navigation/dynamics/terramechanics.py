"""Bekker-Wong Soil Terramechanics & Drawbar Pull Formulation (TRL 5).

Evaluates normal pressure-sinkage, Janosi-Hanamoto shear displacement,
compaction resistance, bulldozing resistance, and net Drawbar Pull (DP).
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple
import numpy as np

from trl5_navigation import ROVER_WHEEL_RADIUS_M


class BekkerWongTerramechanics:
    """Calculates soil compaction, shear thrust, and drawbar pull across regolith classes."""

    def __init__(
        self,
        wheel_radius_m: float = ROVER_WHEEL_RADIUS_M,
        wheel_width_m: float = 0.12,
        # Martian Medium Sand Baseline Soil Parameters:
        cohesion_pa: float = 800.0,
        friction_angle_deg: float = 34.0,
        k_c: float = 1400.0,       # Cohesive modulus (N/m^(n+1))
        k_phi: float = 820000.0,   # Frictional modulus (N/m^(n+2))
        sinkage_n: float = 1.0,     # Sinkage exponent
        shear_modulus_k_m: float = 0.018 # Janosi shear deformation modulus (m)
    ) -> None:
        self.r = float(wheel_radius_m)
        self.b = float(wheel_width_m)
        self.c = float(cohesion_pa)
        self.phi_rad = math.radians(float(friction_angle_deg))
        self.k_c = float(k_c)
        self.k_phi = float(k_phi)
        self.n = float(sinkage_n)
        self.K = float(shear_modulus_k_m)

    def compute_sinkage_and_resistance(
        self,
        wheel_normal_load_n: float
    ) -> Dict[str, float]:
        """Calculates Bekker wheel sinkage z_0 and compaction resistance R_c."""
        w = max(1.0, float(wheel_normal_load_n))
        # Bekker sinkage relation for rigid wheel:
        # z_0 = [ (3 * W) / ( (3 - n) * b * (k_c/b + k_phi) * sqrt(2r) ) ]^(2 / (2n + 1))
        k_eq = (self.k_c / self.b) + self.k_phi
        denom = (3.0 - self.n) * self.b * k_eq * math.sqrt(2.0 * self.r)
        z0 = ( (3.0 * w) / max(1.0, denom) ) ** (2.0 / (2.0 * self.n + 1.0))
        z0 = float(np.clip(z0, 0.001, self.r * 0.8))  # maximum sinkage clamped

        # Compaction resistance R_c = (b * k_eq / (n + 1)) * z_0^(n + 1)
        r_compaction = (self.b * k_eq / (self.n + 1.0)) * (z0 ** (self.n + 1.0))

        # Bulldozing resistance R_b (Hegedus simplified model)
        # R_b = 0.5 * b * gamma_soil * z_0^2 * N_gamma + 2 * c * z_0 * b * N_c
        gamma_soil = 1500.0 * 3.71  # soil unit weight (N/m^3)
        n_phi = math.tan(math.pi / 4.0 + self.phi_rad / 2.0)**2
        r_bulldozing = 0.5 * self.b * gamma_soil * (z0**2) * n_phi + 2.0 * self.c * z0 * self.b * math.sqrt(n_phi)

        return {
            "sinkage_m": round(z0, 4),
            "compaction_resistance_n": round(r_compaction, 2),
            "bulldozing_resistance_n": round(r_bulldozing, 2),
            "total_motion_resistance_n": round(r_compaction + r_bulldozing, 2),
        }

    def compute_thrust_and_drawbar_pull(
        self,
        wheel_normal_load_n: float,
        slip_ratio: float
    ) -> Dict[str, float]:
        """Computes wheel tractive gross thrust and net Drawbar Pull (DP = Thrust - Resistances)."""
        w = max(1.0, float(wheel_normal_load_n))
        s = float(np.clip(slip_ratio, 0.0, 0.95))

        res_info = self.compute_sinkage_and_resistance(w)
        z0 = res_info["sinkage_m"]
        r_total = res_info["total_motion_resistance_n"]

        # Contact patch length: l_c = r * arccos(1 - z_0 / r)
        l_c = self.r * math.acos(np.clip(1.0 - z0 / self.r, -1.0, 1.0))
        contact_area = self.b * l_c

        # Mean ground pressure: p_mean = W / A
        p_mean = w / max(1.0e-4, contact_area)

        # Maximum shear strength: tau_max = c + p_mean * tan(phi)
        tau_max = self.c + p_mean * math.tan(self.phi_rad)

        # Janosi-Hanamoto shear stress with slip displacement j = s * l_c
        j_shear = s * l_c
        tau_actual = tau_max * (1.0 - math.exp(-j_shear / self.K))

        # Gross tractive thrust: H = A * tau_actual
        gross_thrust_n = contact_area * tau_actual

        # Net Drawbar Pull: DP = H - R_total
        drawbar_pull_n = gross_thrust_n - r_total

        return {
            "gross_thrust_n": round(gross_thrust_n, 2),
            "drawbar_pull_n": round(drawbar_pull_n, 2),
            "sinkage_m": res_info["sinkage_m"],
            "motion_resistance_n": res_info["total_motion_resistance_n"],
            "is_stalled": bool(drawbar_pull_n <= 0.0),
        }
