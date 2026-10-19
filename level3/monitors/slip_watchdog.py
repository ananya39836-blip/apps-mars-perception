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
                 sustained_steps_limit: int = 4):
        self.slip_warning_thresh = float(slip_warning_thresh)
        self.entrapment_thresh = float(entrapment_thresh)
        self.sinkage_limit_m = float(sinkage_limit_m)
        self.sustained_steps_limit = int(sustained_steps_limit)

        self.consecutive_high_slip = 0
        self.consecutive_warning_slip = 0
        self.history = []

    def update(self, wheel_slip_dict: Dict[str, float],
               sinkage_dict: Dict[str, float],
               net_dp_N: float) -> Optional[str]:
        """Update monitor state with current wheel slip, sinkages, and net drawbar pull.
        
        Returns:
            None if normal, or trigger string: 'throttle_50' | 'cost_inflate' | 'emergency_safe_stop'
        """
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
