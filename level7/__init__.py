"""Automated Planetary Perception System (APPS) — Level 7.
Relativistic Interstellar Flight, Solar Gravitational Lens Exoplanet Imaging,
Dyson Swarm Constellations, Sub-Kelvin Superconducting Cryo-Avionics,
and Autonomous Planetary Geoengineering & Terraforming.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""

from .interstellar.relativistic_probe import (
    LorentzBoostNavigator,
    LaserSailPropulsion,
    PulsarInterstellarXNAV,
)
from .gravitational_lens.sgl_imaging import (
    SolarGravitationalLensOptics,
    EinsteinRingDeconvolver,
    FocalStationkeepingController,
)
from .dyson_swarm.swarm_relays import (
    SolarStatiteController,
    CoherentLaserArrayBeamer,
    DecentralizedSwarmConsensus,
)
from .cryo_avionics.superconducting_core import (
    RSFQJosephsonProcessor,
    DilutionRefrigeratorThermodynamics,
    SpintronicMemoryEnclave,
)
from .geoengineering.planetary_terraforming import (
    ArtificialMagnetosphereDipole,
    OrbitalMirrorReflector,
    AtmosphericSynthesisGovernor,
)
from .evaluation.label_script_l7 import KEYS_L7, level7_label, release_gate_l7

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

__version__ = "7.0.0-prototype"

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "LorentzBoostNavigator",
    "LaserSailPropulsion",
    "PulsarInterstellarXNAV",
    "SolarGravitationalLensOptics",
    "EinsteinRingDeconvolver",
    "FocalStationkeepingController",
    "SolarStatiteController",
    "CoherentLaserArrayBeamer",
    "DecentralizedSwarmConsensus",
    "RSFQJosephsonProcessor",
    "DilutionRefrigeratorThermodynamics",
    "SpintronicMemoryEnclave",
    "ArtificialMagnetosphereDipole",
    "OrbitalMirrorReflector",
    "AtmosphericSynthesisGovernor",
    "KEYS_L7",
    "level7_label",
    "release_gate_l7",
]
