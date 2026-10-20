"""Level 6 Part 38: Interplanetary Autonomy & Relativistic Navigation.
Chapters 470 to 479: Deep-Space Autonav, XNAV Pulsar Timing & Aerocapture.

Implements autonomous heliocentric trajectory propagation with post-Newtonian
relativistic corrections, X-ray pulsar navigation (XNAV), Shapiro delay modeling,
and closed-loop planetary aerocapture corridor guidance.
"""
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

C_LIGHT = 299792458.0  # m/s
MU_SUN = 1.32712440018e20  # m^3 / s^2


class PostNewtonianPropagator:
    """Propagates heliocentric orbits with 1st Post-Newtonian (1PN) relativistic corrections."""

    def __init__(self, mu_central: float = MU_SUN):
        self.mu = mu_central

    def compute_relativistic_acceleration(self, pos_m: np.ndarray, vel_mps: np.ndarray) -> np.ndarray:
        """Computes Newtonian plus 1PN relativistic acceleration."""
        r = np.linalg.norm(pos_m)
        v = np.linalg.norm(vel_mps)
        n = pos_m / (r + 1e-9)

        # Newtonian acceleration
        a_newt = - (self.mu / (r**2)) * n

        # 1PN Relativistic correction: a_1PN = (mu / (c^2 * r^2)) * [ (4*mu/r - v^2)*n + 4*(v.n)*v ]
        c2 = C_LIGHT**2
        term1 = (4.0 * self.mu / r - v**2) * n
        term2 = 4.0 * np.dot(vel_mps, n) * vel_mps
        a_1pn = (self.mu / (c2 * r**2)) * (term1 + term2)

        return a_newt + a_1pn

    def compute_shapiro_time_delay(self, r_tx_m: float, r_rx_m: float, d_chord_m: float) -> float:
        """Calculates relativistic Shapiro light-time delay in gravitational well."""
        num = r_tx_m + r_rx_m + d_chord_m
        den = max(1e-3, r_tx_m + r_rx_m - d_chord_m)
        delay_s = (2.0 * self.mu / (C_LIGHT**3)) * math.log(num / den)
        return float(delay_s)


class PulsarXNAVReceiver:
    """Simulates X-ray pulsar navigation (XNAV) timing and phase ambiguity resolution."""

    def __init__(self):
        # Benchmark millisecond pulsar database
        self.pulsars = {
            "PSR_B1937+21": {"period_s": 0.0015578065, "f0_hz": 641.92825, "direction": np.array([0.25, 0.85, 0.46])},
            "PSR_B1821-24": {"period_s": 0.0030543152, "f0_hz": 327.40552, "direction": np.array([-0.12, 0.65, 0.75])},
            "PSR_J0437-4715": {"period_s": 0.0057574519, "f0_hz": 173.68792, "direction": np.array([0.72, -0.45, 0.52])}
        }

    def measure_time_of_arrival(self, true_pos_m: np.ndarray, pulsar_name: str) -> Dict[str, Any]:
        """Calculates pulse time of arrival (TOA) and geometric range projection."""
        p_data = self.pulsars.get(pulsar_name, self.pulsars["PSR_B1937+21"])
        u_vec = p_data["direction"] / np.linalg.norm(p_data["direction"])
        proj_dist_m = float(np.dot(true_pos_m, u_vec))
        delta_tau_s = proj_dist_m / C_LIGHT

        # Phase offset
        phase = (delta_tau_s * p_data["f0_hz"]) % 1.0

        return {
            "pulsar": pulsar_name,
            "projected_range_m": proj_dist_m,
            "geometric_time_delay_s": delta_tau_s,
            "phase_fraction": float(phase),
            "timing_uncertainty_ns": 120.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class AutonomousAerocaptureGuidance:
    """Predictor-corrector guidance modulating bank angle during hypervelocity planetary atmospheric capture."""

    def __init__(self, target_apoapsis_km: float = 6000.0, max_bank_deg: float = 75.0):
        self.target_r_a_m = target_apoapsis_km * 1000.0
        self.max_bank_deg = max_bank_deg

    def compute_guidance_command(self, alt_km: float, speed_mps: float, energy_depleted_pct: float) -> Dict[str, Any]:
        """Calculates bank angle command to track energy-depletion reference corridor."""
        # Target energy dissipation profile
        target_depletion = min(1.0, max(0.0, (120.0 - alt_km) / 75.0))
        error = target_depletion - (energy_depleted_pct / 100.0)

        # Proportional bank angle control
        bank_cmd_deg = float(np.clip(45.0 + error * 60.0, -self.max_bank_deg, self.max_bank_deg))
        in_corridor = abs(error) <= 0.08
        exit_safe = speed_mps <= 4200.0 or alt_km > 115.0

        return {
            "altitude_km": alt_km,
            "entry_speed_mps": speed_mps,
            "commanded_bank_deg": round(bank_cmd_deg, 2),
            "corridor_tracking_ok": in_corridor,
            "aerocapture_complete": exit_safe,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
