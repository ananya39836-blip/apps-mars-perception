"""GNC Core — Spacecraft Guidance, Navigation & Control Engine (NASA/ESA TRL 4).

Architecture & Verification Standards:
- Reference Frames: International Celestial Reference Frame (ICRF / J2000), Mars-Centered Inertial (MCI), Mars-Centered Mars-Fixed (MCMF).
- Timing Standards: 100 Hz (10 ms) fixed-step deterministic scheduling compatible with RTOS (FreeRTOS / RTEMS).
- Telemetry Standards: CCSDS 133.0-B-1 Space Packet Protocol & ECSS-E-ST-70-41C Packet Utilization Standard (PUS).
- Mathematical Engine: 1PN Einstein-Infeld-Hoffmann relativistic orbit propagation, Shapiro light-time delay, 3-sigma stochastic aerocapture corridor predictor-corrector.
- Sensor Error Models: Navigation-grade IMU (Allan variance, 1st-order Gauss-Markov bias instability), Poisson photon XNAV pulsar timing, range-squared LiDAR with latency ring-buffering.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

# Physical and Astrodynamical Constants (CODATA 2022 / IAU 2015)
C_LIGHT: float = 299792458.0  # Speed of light in vacuum (m/s)
MU_SUN: float = 1.32712440018e20  # Heliocentric gravitational parameter (m^3/s^2)
MU_MARS: float = 4.282837e13  # Mars gravitational parameter (m^3/s^2)
R_MARS_EQUATORIAL: float = 3396.2e3  # Mars equatorial radius (m)
R_MARS_POLAR: float = 3376.2e3  # Mars polar radius (m)
AU_METERS: float = 1.495978707e11  # Astronomical Unit in meters

# Telemetry Protocol IDs
CCSDS_APID_GNC_TELEMETRY: int = 0x01A0
CCSDS_APID_IMU_TELEMETRY: int = 0x01A1
CCSDS_APID_XNAV_TELEMETRY: int = 0x01A2
CCSDS_APID_CORRIDOR_CMD: int = 0x01A3

__version__ = "4.0.0-trl4-breadboard"

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "C_LIGHT",
    "MU_SUN",
    "MU_MARS",
    "R_MARS_EQUATORIAL",
    "R_MARS_POLAR",
    "AU_METERS",
    "CCSDS_APID_GNC_TELEMETRY",
    "CCSDS_APID_IMU_TELEMETRY",
    "CCSDS_APID_XNAV_TELEMETRY",
    "CCSDS_APID_CORRIDOR_CMD",
]
