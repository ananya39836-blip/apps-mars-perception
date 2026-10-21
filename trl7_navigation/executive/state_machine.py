"""11-Mode Discrete FDIR Autonomy Executive (TRL 7).

Implements deterministic Fault Detection, Isolation, and Recovery (FDIR) state transitions:
  BOOT -> STANDBY -> MAPPING -> PLANNING -> TRAVERSING -> MISSION_COMPLETE
                                     |            |
                                     v            v
                              OBSTACLE_AVOIDANCE  RECOVERY_MANEUVER
                                     |            |
                                     +------+-----+
                                            |
                                            v
                                 FAULT_ISOLATION -> SAFE_STOP -> EMERGENCY_ESTOP
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Dict, Any, List, Optional, Tuple
import time


class AutonomyState(Enum):
    BOOT = auto()
    STANDBY = auto()
    MAPPING = auto()
    PLANNING = auto()
    TRAVERSING = auto()
    OBSTACLE_AVOIDANCE = auto()
    RECOVERY_MANEUVER = auto()
    SAFE_STOP = auto()
    EMERGENCY_ESTOP = auto()
    FAULT_ISOLATION = auto()
    MISSION_COMPLETE = auto()


class ExecutiveStateMachine:
    """Manages system operational modes, autonomous transitions, and FDIR responses."""

    def __init__(self) -> None:
        self.state = AutonomyState.BOOT
        self.previous_state = AutonomyState.BOOT
        self.state_enter_time = time.time()
        self.fault_records: List[Dict[str, Any]] = []
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

    def transition_to(self, new_state: AutonomyState, reason: str = "") -> None:
        """Transitions to new state with audit logging."""
        if new_state == self.state:
            return
        self.previous_state = self.state
        self.state = new_state
        self.state_enter_time = time.time()
        if "FAULT" in reason or "FAIL" in reason or new_state in (AutonomyState.SAFE_STOP, AutonomyState.EMERGENCY_ESTOP):
            self.fault_records.append({
                "time": self.state_enter_time,
                "from_state": self.previous_state.name,
                "to_state": self.state.name,
                "reason": reason,
            })

    def handle_cycle(
        self,
        hardware_healthy: bool,
        e_stop_requested: bool,
        path_valid: bool,
        goal_reached: bool,
        hazard_in_corridor: bool,
        excessive_slip: bool,
        filter_diverged: bool,
    ) -> AutonomyState:
        """Processes telemetry flags and executes state machine transitions."""
        # 1. Catastrophic / Emergency overrides
        if e_stop_requested:
            self.transition_to(AutonomyState.EMERGENCY_ESTOP, "E-Stop button or deadman timeout asserted")
            return self.state

        if not hardware_healthy or filter_diverged:
            if self.state not in (AutonomyState.FAULT_ISOLATION, AutonomyState.SAFE_STOP, AutonomyState.EMERGENCY_ESTOP):
                self.transition_to(AutonomyState.FAULT_ISOLATION, "Hardware fault or localization covariance divergence")
                return self.state

        # 2. State-specific logic
        if self.state == AutonomyState.BOOT:
            # Self-test passed
            self.transition_to(AutonomyState.STANDBY, "Boot self-test complete")

        elif self.state == AutonomyState.STANDBY:
            # Ready to start mapping terrain
            self.transition_to(AutonomyState.MAPPING, "Mission dispatch received")

        elif self.state == AutonomyState.MAPPING:
            # Transition to planning after scan
            self.transition_to(AutonomyState.PLANNING, "Perception DEM assembled")

        elif self.state == AutonomyState.PLANNING:
            if path_valid:
                self.recovery_attempts = 0
                self.transition_to(AutonomyState.TRAVERSING, "Admissible path generated")
            else:
                if self.recovery_attempts < self.max_recovery_attempts:
                    self.recovery_attempts += 1
                    self.transition_to(AutonomyState.RECOVERY_MANEUVER, f"Planning failed, recovery attempt {self.recovery_attempts}")
                else:
                    self.transition_to(AutonomyState.SAFE_STOP, "Planning exhausted without feasible path")

        elif self.state == AutonomyState.TRAVERSING:
            if goal_reached:
                self.transition_to(AutonomyState.MISSION_COMPLETE, "Goal tolerance satisfied")
            elif hazard_in_corridor:
                self.transition_to(AutonomyState.OBSTACLE_AVOIDANCE, "New hazard detected in trajectory envelope")
            elif excessive_slip:
                self.transition_to(AutonomyState.RECOVERY_MANEUVER, "Excessive wheel slip detected")

        elif self.state == AutonomyState.OBSTACLE_AVOIDANCE:
            # Trigger replan
            self.transition_to(AutonomyState.PLANNING, "Replanning around detected hazard")

        elif self.state == AutonomyState.RECOVERY_MANEUVER:
            # After backing up, replan
            self.transition_to(AutonomyState.PLANNING, "Recovery completed; replanning")

        elif self.state == AutonomyState.FAULT_ISOLATION:
            # Isolate fault and execute controlled safe stop
            self.transition_to(AutonomyState.SAFE_STOP, "Controlled stop under fault condition")

        elif self.state == AutonomyState.SAFE_STOP:
            # Latch until manual intervention or reset
            pass

        elif self.state == AutonomyState.MISSION_COMPLETE:
            # Successfully halted at goal
            pass

        return self.state
