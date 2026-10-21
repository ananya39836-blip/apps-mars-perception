"""Planetary Soil Mechanics and Terramechanics Model (TRL 7).

Implements classical Bekker-Wong pressure-sinkage formulation and Janosi-Hanamoto
shear displacement relationship for wheel-regolith interaction:
- Bekker pressure-sinkage: p = (k_c / b + k_phi) * z^n
- Compaction resistance: R_c
- Janosi-Hanamoto shear stress: tau = (c + sigma * tan(phi)) * (1 - exp(-j / K))
- Gross traction, motion resistance, drawbar pull, and wheel slip ratio
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from trl7_navigation import (
    ROVER_WHEEL_RADIUS_M,
    ROVER_WHEEL_WIDTH_M,
)


class SoilParameters:
    """Terramechanical geotechnical properties for planetary regolith."""
    def __init__(
        self,
        name: str = "Martian Regolith Simulant (MMS-1)",
        cohesion_c_pa: float = 1200.0,
        internal_friction_phi_deg: float = 34.0,
        sinkage_exponent_n: float = 1.0,
        kc_pa_m_n1: float = 1400.0,
        kphi_pa_m_n: float = 820000.0,
        shear_deformation_mod_k_m: float = 0.015,
    ) -> None:
        self.name = name
        self.c = float(cohesion_c_pa)
        self.phi_rad = math.radians(float(internal_friction_phi_deg))
        self.n = float(sinkage_exponent_n)
        self.kc = float(kc_pa_m_n1)
        self.kphi = float(kphi_pa_m_n)
        self.K = float(shear_deformation_mod_k_m)


class TerramechanicsModel:
    """Calculates sinkage, motion resistance, and drawbar pull for rigid rover wheels."""

    def __init__(
        self,
        wheel_radius_m: float = ROVER_WHEEL_RADIUS_M,
        wheel_width_m: float = ROVER_WHEEL_WIDTH_M,
        soil: Optional[SoilParameters] = None,
    ) -> None:
        self.r = float(wheel_radius_m)
        self.b = float(wheel_width_m)
        self.soil = soil if soil is not None else SoilParameters()

    def compute_sinkage_and_forces(
        self,
        wheel_normal_load_n: float,
        wheel_angular_rate_rad_s: float,
        chassis_linear_velocity_m_s: float,
        local_friction_mu: float = 0.85,
    ) -> Dict[str, float]:
        """Calculates wheel sinkage, compaction resistance, gross traction, and drawbar pull."""
        W = max(5.0, float(wheel_normal_load_n))
        omega_r = abs(wheel_angular_rate_rad_s * self.r)
        v = abs(chassis_linear_velocity_m_s)

        # 1. Slip ratio s = (omega*r - v) / max(omega*r, v)
        if omega_r > 1e-4:
            slip_ratio = (omega_r - v) / max(omega_r, 1e-4)
        else:
            slip_ratio = 0.0
        slip_ratio = float(np.clip(slip_ratio, 0.0, 0.95))

        # 2. Bekker sinkage z_0
        # W = b * (k_c / b + k_phi) * (z_0^(n+1) / (n+1)) * sqrt(2 * r / z_0)
        # Approximate sinkage:
        k_eq = (self.soil.kc / self.b) + self.soil.kphi
        # z0 approx = ( (n+1) * W / (b * k_eq * sqrt(2 * r)) )^(2 / (2n + 1))
        pwr = 2.0 / (2.0 * self.soil.n + 1.0)
        num = (self.soil.n + 1.0) * W
        denom = max(1.0, self.b * k_eq * math.sqrt(2.0 * self.r))
        sinkage_m = float((num / denom) ** pwr)
        sinkage_m = float(np.clip(sinkage_m, 0.001, self.r * 0.8))

        # 3. Compaction motion resistance R_c = (b * k_eq / (n + 1)) * z_0^(n + 1)
        compaction_res_n = float((self.b * k_eq / (self.soil.n + 1.0)) * (sinkage_m ** (self.soil.n + 1.0)))

        # 4. Gross tractive effort H via Janosi-Hanamoto
        # Contact area A = b * l_contact, where l_contact approx sqrt(2 * r * z0)
        l_contact = math.sqrt(max(1e-6, 2.0 * self.r * sinkage_m))
        contact_area = self.b * l_contact
        normal_stress = W / max(1e-4, contact_area)

        # Maximum shear strength tau_max = c + sigma * tan(phi)
        tau_max = self.soil.c + normal_stress * math.tan(self.soil.phi_rad)
        # Shear displacement j approx s * l_contact
        shear_disp = slip_ratio * l_contact
        tau = tau_max * (1.0 - math.exp(-shear_disp / max(1e-4, self.soil.K)))

        gross_traction_n = float(tau * contact_area * local_friction_mu)

        # 5. Net Drawbar Pull DP = H - R_c
        drawbar_pull_n = float(gross_traction_n - compaction_res_n)

        return {
            "sinkage_m": sinkage_m,
            "compaction_resistance_n": compaction_res_n,
            "gross_traction_n": gross_traction_n,
            "drawbar_pull_n": drawbar_pull_n,
            "slip_ratio": slip_ratio,
        }
