"""Formal 11-Mode Operating State Machine & FDIR Executive (TRL 6).

Implements discrete operating modes, deterministic transition guards,
fault detection, isolation, and recovery (FDIR), and certified safe-stop latching.
"""
from __future__ import annotations
import time
from enum import Enum
from typing import Dict, Any, List, Optional
import numpy as np

from trl6_navigation import PROTOTYPE_LOCK, NAVIGATION_READY


class RoverOperatingMode(str, Enum):
    """Discrete rover operational states."""
    INITIALIZATION = "INITIALIZATION"
    SELF_TEST = "SELF_TEST"
    IDLE = "IDLE"
    PERCEPTION = "PERCEPTION"
    LOCALIZATION = "LOCALIZATION"
    PLANNING = "PLANNING"
    EXECUTION = "EXECUTION"
    REPLANNING = "REPLANNING"
    SAFE_STOP = "SAFE_STOP"
    RECOVERY = "RECOVERY"
    MISSION_COMPLETE = "MISSION_COMPLETE"
    FAULT = "FAULT"


class RoverFDIRStateMachine:
    """Manages rover operating states, transition validation, and safety invariants."""

    def __init__(self, experiment_id: str = "EXP_TRL6_001") -> None:
        self.experiment_id = str(experiment_id)
        self.current_mode = RoverOperatingMode.INITIALIZATION
        self.previous_mode: Optional[RoverOperatingMode] = None
        self.transition_history: List[Dict[str, Any]] = []
        self.fault_reasons: List[str] = []
        self.is_safe_stopped: bool = False

        self._record_transition(RoverOperatingMode.INITIALIZATION, "System boot & subsystem initialization")

    def _record_transition(self, new_mode: RoverOperatingMode, reason: str) -> None:
        """Appends validated state transition to execution ledger."""
        timestamp = time.time()
        record = {
            "timestamp": timestamp,
            "from_mode": self.previous_mode.value if self.previous_mode else None,
            "to_mode": new_mode.value,
            "reason": reason,
        }
        self.transition_history.append(record)
        self.previous_mode = self.current_mode
        self.current_mode = new_mode

    def transition_to(self, target_mode: RoverOperatingMode, reason: str = "") -> bool:
        """Executes state transition subject to formal transition guards."""
        curr = self.current_mode

        # Terminal state locks
        if curr == RoverOperatingMode.FAULT and target_mode != RoverOperatingMode.INITIALIZATION:
            return False  # FAULT can only be cleared by reboot

        # Valid transition rules
        valid_transitions = {
            RoverOperatingMode.INITIALIZATION: [RoverOperatingMode.SELF_TEST, RoverOperatingMode.FAULT],
            RoverOperatingMode.SELF_TEST: [RoverOperatingMode.IDLE, RoverOperatingMode.FAULT],
            RoverOperatingMode.IDLE: [RoverOperatingMode.PERCEPTION, RoverOperatingMode.LOCALIZATION, RoverOperatingMode.PLANNING, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT],
            RoverOperatingMode.PERCEPTION: [RoverOperatingMode.LOCALIZATION, RoverOperatingMode.PLANNING, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT],
            RoverOperatingMode.LOCALIZATION: [RoverOperatingMode.PLANNING, RoverOperatingMode.EXECUTION, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT],
            RoverOperatingMode.PLANNING: [RoverOperatingMode.EXECUTION, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.REPLANNING, RoverOperatingMode.FAULT],
            RoverOperatingMode.EXECUTION: [RoverOperatingMode.REPLANNING, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.MISSION_COMPLETE, RoverOperatingMode.FAULT],
            RoverOperatingMode.REPLANNING: [RoverOperatingMode.EXECUTION, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.RECOVERY, RoverOperatingMode.FAULT],
            RoverOperatingMode.RECOVERY: [RoverOperatingMode.PLANNING, RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT],
            RoverOperatingMode.SAFE_STOP: [RoverOperatingMode.RECOVERY, RoverOperatingMode.IDLE, RoverOperatingMode.FAULT],
            RoverOperatingMode.MISSION_COMPLETE: [RoverOperatingMode.IDLE, RoverOperatingMode.INITIALIZATION],
            RoverOperatingMode.FAULT: [RoverOperatingMode.INITIALIZATION],
        }

        allowed_targets = valid_transitions.get(curr, [])
        if target_mode in allowed_targets:
            if target_mode in (RoverOperatingMode.SAFE_STOP, RoverOperatingMode.FAULT):
                self.is_safe_stopped = True
            self._record_transition(target_mode, reason)
            return True
        else:
            # Illegal transition attempt triggers FAULT
            err_msg = f"Illegal transition attempted: {curr.value} -> {target_mode.value} (Reason: {reason})"
            self.fault_reasons.append(err_msg)
            self.is_safe_stopped = True
            self._record_transition(RoverOperatingMode.FAULT, err_msg)
            return False

    def trigger_emergency_safe_stop(self, trigger_reason: str) -> None:
        """Immediately latches rover into SAFE_STOP state."""
        self.is_safe_stopped = True
        self.transition_to(RoverOperatingMode.SAFE_STOP, trigger_reason)

    def trigger_critical_fault(self, fault_message: str) -> None:
        """Latches rover into permanent FAULT state and latches safe stop."""
        self.is_safe_stopped = True
        self.fault_reasons.append(fault_message)
        self.transition_to(RoverOperatingMode.FAULT, fault_message)

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns machine-readable summary of state machine status."""
        return {
            "current_mode": self.current_mode.value,
            "is_safe_stopped": self.is_safe_stopped,
            "has_fault": bool(len(self.fault_reasons) > 0),
            "fault_reasons": self.fault_reasons,
            "total_transitions": len(self.transition_history),
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY,
        }
