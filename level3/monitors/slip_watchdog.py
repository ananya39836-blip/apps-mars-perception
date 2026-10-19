"""Terramechanical Slip & Entrapment Watchdog Monitor for APPS Level 3.
Chapters 226 & 227 (Part 13).

Tracks wheel slip ratios, sinkage divergence, and commands safing triggers.
"""
from typing import Dict, List, Optional


class SlipEntrapmentWatchdog:
    """Watchdog monitor protecting against runaway soil sinkage and wheel entrapment."""

    def __init__(self, slip_warning_thresh: float = 0.45,
                 entrapment_thresh: float = 0.75,
                 sinkage_limit_m: float = 0.08,
                 sustained_steps_limit: int = 4,
                 slip_warning_threshold: float = None,
                 slip_emergency_threshold: float = None):
        if slip_warning_threshold is not None:
            slip_warning_thresh = slip_warning_threshold
        if slip_emergency_threshold is not None:
            entrapment_thresh = slip_emergency_threshold
        self.slip_warning_thresh = float(slip_warning_thresh)
        self.entrapment_thresh = float(entrapment_thresh)
        self.sinkage_limit_m = float(sinkage_limit_m)
        self.sustained_steps_limit = int(sustained_steps_limit)

        self.consecutive_high_slip = 0
        self.consecutive_warning_slip = 0
        self.history = []

    def update(self, wheel_slip_dict: Dict[str, float] = None,
               sinkage_dict: Dict[str, float] = None,
               net_dp_N: float = 0.0,
               forward_velocity_m_s: float = None,
               wheel_angular_velocity_rad_s: float = None,
               wheel_radius_m: float = 0.15) -> Optional[Any]:
        """Update monitor state with current wheel slip, sinkages, and net drawbar pull."""
        if forward_velocity_m_s is not None and wheel_angular_velocity_rad_s is not None:
            vx = max(1e-4, float(forward_velocity_m_s))
            rw = float(wheel_radius_m * wheel_angular_velocity_rad_s)
            slip = float((rw - vx) / max(rw, vx))
            is_warn = bool(slip >= self.slip_warning_thresh)
            is_emerg = bool(slip >= self.entrapment_thresh)
            return {
                "slip_ratio": slip,
                "trip_warning": is_warn,
                "trip_emergency_stop": is_emerg,
                "status": "emergency_safe_stop" if is_emerg else ("throttle_50" if is_warn else "nominal")
            }

        if wheel_slip_dict is None:
            wheel_slip_dict = {}
        if sinkage_dict is None:
            sinkage_dict = {}
        max_slip = max(wheel_slip_dict.values()) if wheel_slip_dict else 0.0
        max_sinkage = max(sinkage_dict.values()) if sinkage_dict else 0.0
        
        self.history.append({
            "max_slip": max_slip,
            "max_sinkage": max_sinkage,
            "net_dp_N": net_dp_N
        })

        # 1. Critical Entrapment Check
        if max_slip >= self.entrapment_thresh or (max_slip > 0.60 and net_dp_N <= 0.0):
            self.consecutive_high_slip += 1
            if self.consecutive_high_slip >= self.sustained_steps_limit:
                return "emergency_safe_stop"
        else:
            self.consecutive_high_slip = max(0, self.consecutive_high_slip - 1)

        # 2. Sinkage Limit Check
        if max_sinkage >= self.sinkage_limit_m:
            return "cost_inflate"

        # 3. Slip Warning Check
        if max_slip >= self.slip_warning_thresh:
            self.consecutive_warning_slip += 1
            if self.consecutive_warning_slip >= 2:
                return "throttle_50"
        else:
            self.consecutive_warning_slip = 0

        return None

    def reset(self):
        self.consecutive_high_slip = 0
        self.consecutive_warning_slip = 0
        self.history.clear()
