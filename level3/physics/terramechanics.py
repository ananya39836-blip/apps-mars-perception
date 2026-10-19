"""Bekker-Wong Soil Mechanics and Terramechanics Module for APPS Level 3.
Chapters 224, 225 & 226 (Part 13).

Calculates:
- Normal pressure-sinkage: p(z) = (k_c / b + k_phi) * z^n
- Janosi shear stress: tau(j) = (c + p * tan(phi)) * (1 - exp(-j / K_w))
- Motion compaction resistance R_c and bulldozing resistance R_b
- Net Drawbar Pull: DP = F_thrust - R_c - R_b
"""
import math
from typing import Dict, NamedTuple
import numpy as np


class SoilParameters(NamedTuple):
    name: str
    cohesion_c_kPa: float          # Cohesion c (kPa)
    friction_angle_phi_deg: float  # Internal friction angle phi (deg)
    k_c: float                     # Cohesive modulus (kN/m^(n+1))
    k_phi: float                   # Frictional modulus (kN/m^(n+2))
    exponent_n: float              # Sinkage exponent n
    shear_modulus_Kw_m: float      # Janosi shear deformation modulus K_w (m)
    density_kg_m3: float           # Bulk soil density (kg/m^3)

    @property
    def kc(self): return self.k_c

    @property
    def kphi(self): return self.k_phi

    @property
    def n(self): return self.exponent_n

    @property
    def c(self): return self.cohesion_c_kPa * 1000.0

    @property
    def phi_deg(self): return self.friction_angle_phi_deg

    @property
    def K(self): return self.shear_modulus_Kw_m


# Standard Planetary Regolith Presets from Chapter 224.2
REGOLITH_PRESETS = {
    "drift_sand": SoilParameters(
        name="drift_sand", cohesion_c_kPa=0.15, friction_angle_phi_deg=28.5,
        k_c=0.95, k_phi=1520.0, exponent_n=1.10, shear_modulus_Kw_m=0.025,
        density_kg_m3=1550.0
    ),
    "compact_regolith": SoilParameters(
        name="compact_regolith", cohesion_c_kPa=1.80, friction_angle_phi_deg=37.2,
        k_c=4.20, k_phi=2850.0, exponent_n=0.95, shear_modulus_Kw_m=0.018,
        density_kg_m3=1750.0
    ),
    "crater_ejecta": SoilParameters(
        name="crater_ejecta", cohesion_c_kPa=0.60, friction_angle_phi_deg=32.0,
        k_c=2.10, k_phi=1980.0, exponent_n=1.02, shear_modulus_Kw_m=0.022,
        density_kg_m3=1600.0
    ),
    "bedrock": SoilParameters(
        name="bedrock", cohesion_c_kPa=50.0, friction_angle_phi_deg=45.0,
        k_c=120.0, k_phi=15000.0, exponent_n=0.40, shear_modulus_Kw_m=0.005,
        density_kg_m3=2600.0
    )
}
# Backward compatibility aliases
REGOLITH_PRESETS["medium_sand"] = REGOLITH_PRESETS["compact_regolith"]
REGOLITH_PRESETS["soft_drift_sand"] = REGOLITH_PRESETS["drift_sand"]



class TerramechanicsModel:
    """Evaluates wheel-soil interaction forces, sinkage, resistances, and drawbar pull."""

    def __init__(self, wheel_radius_m: float = 0.15, wheel_width_m: float = 0.12):
        self.r = float(wheel_radius_m)
        self.b = float(wheel_width_m)

    def evaluate_wheel_soil(self, normal_load_N: float, forward_speed_m_s: float,
                            wheel_spin_rad_s: float, soil: SoilParameters) -> Dict:
        """Evaluate terramechanical contact state for a single wheel."""
        w_load = max(5.0, float(normal_load_N))
        v_fwd = max(0.001, float(forward_speed_m_s))
        r_w = self.r * max(0.0, float(wheel_spin_rad_s))

        # 1. Longitudinal Slip Ratio s = (r*w - v) / max(r*w, v)
        if r_w >= v_fwd:
            slip_s = (r_w - v_fwd) / max(r_w, 1e-4)
        else:
            slip_s = (r_w - v_fwd) / v_fwd
        slip_s = float(np.clip(slip_s, -1.0, 1.0))

        # 2. Dynamic Sinkage z_0 from Bekker equation:
        # W ~ b * (k_c/b + k_phi) * z_0^(n + 1) / (n + 1) * (geometry factor)
        modulus = (soil.k_c / self.b + soil.k_phi) * 1000.0 # to N/m^(n+2)
        n = soil.exponent_n
        
        # Iterative or closed-form approximation of sinkage z_0
        geom_factor = math.sqrt(2.0 * self.r)
        term = w_load / (self.b * modulus * geom_factor)
        z_0 = float(np.power(max(1e-7, term), 1.0 / (n + 0.5)))
        # Slip-sinkage amplification: spinning excavates soil
        if slip_s > 0.15:
            z_0 *= (1.0 + 1.2 * (slip_s - 0.15)**1.5)
        z_0 = float(min(z_0, self.r * 0.85)) # cannot sink past axle

        # 3. Motion Compaction Resistance R_c
        r_c = (self.b / (n + 1.0)) * modulus * (z_0**(n + 1.0))

        # 4. Hegedus Bulldozing Resistance R_b
        phi_rad = math.radians(soil.friction_angle_phi_deg)
        c_Pa = soil.cohesion_c_kPa * 1000.0
        # Rankine passive earth pressure coefficients
        k_p = math.tan(math.pi / 4.0 + phi_rad / 2.0)**2
        r_b = self.b * (c_Pa * z_0 * 2.0 * math.sqrt(k_p) + 0.5 * soil.density_kg_m3 * 3.71 * (z_0**2) * k_p)

        # 5. Thrust generation F_thrust via Janosi shear stress
        # Shear displacement j ~ slip_s * (r * theta_contact)
        theta_contact = math.acos(max(-1.0, min(1.0, 1.0 - z_0 / self.r)))
        j_shear = max(1e-4, abs(slip_s) * self.r * theta_contact)
        shear_strength = (c_Pa + (w_load / (self.b * 2.0 * self.r * theta_contact)) * math.tan(phi_rad))
        tau = shear_strength * (1.0 - math.exp(-j_shear / soil.shear_modulus_Kw_m))
        f_thrust = tau * self.b * self.r * theta_contact

        # 6. Net Drawbar Pull DP = F_thrust - R_c - R_b
        drawbar_pull = f_thrust - r_c - r_b

        is_entrapped = bool(slip_s > 0.70 and drawbar_pull < 0.0)

        return {
            "slip_ratio": float(slip_s),
            "sinkage_m": float(z_0),
            "compaction_resistance_N": float(r_c),
            "bulldozing_resistance_N": float(r_b),
            "thrust_force_N": float(f_thrust),
            "gross_thrust_N": float(f_thrust),
            "drawbar_pull_N": float(drawbar_pull),
            "is_entrapped": is_entrapped
        }
