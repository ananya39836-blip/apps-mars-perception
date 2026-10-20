"""Venus exploration and high-temperature avionics package for Level 6."""
from .supercritical_avionics import (
    VenusSupercriticalAeroEngine, HighTempSiCAvionics, ClockworkMechanicalBackup,
    PROTOTYPE_LOCK, NAVIGATION_READY
)

__all__ = [
    "VenusSupercriticalAeroEngine", "HighTempSiCAvionics", "ClockworkMechanicalBackup",
    "PROTOTYPE_LOCK", "NAVIGATION_READY"
]
