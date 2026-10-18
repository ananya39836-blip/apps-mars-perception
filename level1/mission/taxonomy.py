"""Outcome Taxonomy and accounting standards for Level 1 Missions.
Chapter 95.2 & Chapter 137 (Part 6 & Part 8).
"""

OUTCOMES = (
    "success",          # Reached goal column without collision
    "collision",        # Entered true hazard cell
    "no_path",          # Planner returned no route
    "rejected",         # Path exceeded risk budget
    "safe_stop",        # Watchdog, audit, or sensor outage controlled halt
    "timeout",          # Exceeded step limit
    "invalid_input"     # Input validation failure
)


def is_valid_outcome(status: str) -> bool:
    return status in OUTCOMES
