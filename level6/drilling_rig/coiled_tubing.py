"""Level 6 Part 41: Deep Core Subsurface Planetary Drilling Rigs.
Chapters 500 to 509: Kilometer-Scale Coiled Tubing, Acoustic Telemetry & BOP Safeguards.

Implements autonomous kilometer-depth coiled tubing drilling, weight-on-bit (WOB)
closed-loop feed control, acoustic drill string telemetry, and wellbore pressure blowout preventers.
"""
import math
from typing import Dict, Any, List, Optional
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class CoiledTubingDrillRig:
    """Manages autonomous coiled tubing injector drive and weight-on-bit (WOB) optimization."""

    def __init__(self, max_depth_m: float = 2500.0, max_pull_tension_kN: float = 120.0):
        self.max_depth_m = max_depth_m
        self.max_pull_kN = max_pull_tension_kN
        self.current_depth_m = 0.0
        self.cumulative_core_recovered_m = 0.0

    def drill_advance(self, feed_rate_m_hr: float, duration_hours: float, rock_hardness_mpa: float = 180.0) -> Dict[str, Any]:
        """Advances drill bit, tracks weight-on-bit, and tests for helical tubing buckling."""
        advance_dist = feed_rate_m_hr * duration_hours
        self.current_depth_m = min(self.max_depth_m, self.current_depth_m + advance_dist)

        # Weight on bit required proportional to compressive strength
        wob_kN = (rock_hardness_mpa / 100.0) * 8.5
        # Helical buckling threshold increases with depth and wellbore curvature
        buckling_limit_kN = 25.0 + 0.015 * self.current_depth_m
        buckling_safe = wob_kN < buckling_limit_kN

        core_yield_m = advance_dist * 0.95
        self.cumulative_core_recovered_m += core_yield_m

        return {
            "current_depth_m": round(self.current_depth_m, 2),
            "wob_applied_kN": round(wob_kN, 2),
            "buckling_threshold_kN": round(buckling_limit_kN, 2),
            "buckling_safe": buckling_safe,
            "core_recovered_m": round(core_yield_m, 2),
            "cumulative_core_m": round(self.cumulative_core_recovered_m, 2),
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class AcousticMudPulseTelemetry:
    """Acoustic compression wave telemetry transmitted along the metallic drill string."""

    def __init__(self, acoustic_speed_mps: float = 5100.0):
        self.acoustic_speed = acoustic_speed_mps

    def transmit_borehole_packet(self, depth_m: float, payload_bytes: bytes) -> Dict[str, Any]:
        """Calculates transit latency, signal attenuation, and data integrity over drill string."""
        latency_seconds = depth_m / self.acoustic_speed
        # Attenuation ~ 1.5 dB per 100 m
        attenuation_dB = 1.5 * (depth_m / 100.0)
        snr_dB = max(6.0, 28.0 - attenuation_dB)
        packet_received_intact = snr_dB >= 10.0

        return {
            "depth_m": depth_m,
            "transit_latency_ms": round(latency_seconds * 1000.0, 2),
            "attenuation_dB": round(attenuation_dB, 2),
            "snr_dB": round(snr_dB, 2),
            "packet_intact": packet_received_intact,
            "bitrate_bps": 128,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class BoreholeBlowoutPreventer:
    """Automated wellbore pressure isolation and emergency shear ram sealing."""

    def __init__(self, pressure_rating_bar: float = 500.0):
        self.rating_bar = pressure_rating_bar
        self.ram_closed = False

    def evaluate_wellbore_pressure(self, formation_pressure_bar: float, mud_hydrostatic_bar: float) -> Dict[str, Any]:
        """Detects overpressure kicks and trips emergency shear rams if influx detected."""
        overpressure_kick = formation_pressure_bar > (mud_hydrostatic_bar + 15.0)

        if overpressure_kick and not self.ram_closed:
            self.ram_closed = True
            action = "EMERGENCY_SHEAR_RAMS_TRIPPED"
        elif self.ram_closed:
            action = "WELLBORE_SEALED"
        else:
            action = "HYDROSTATIC_EQUILIBRIUM_NOMINAL"

        return {
            "formation_pressure_bar": formation_pressure_bar,
            "mud_hydrostatic_bar": mud_hydrostatic_bar,
            "overpressure_kick_detected": overpressure_kick,
            "blowout_preventer_closed": self.ram_closed,
            "action": action,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
