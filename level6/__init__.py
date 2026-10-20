"""Automated Planetary Perception System (APPS) — Level 6.
Interplanetary Relativistic Autonav, Lunar Megawatt Grids, Titan Submersibles,
Deep Core Drilling Rigs, Venus Supercritical SiC Avionics, Asteroid Kinetic Impactors,
Neuromorphic Bio-Hybrids, Quantum-Entangled Interplanetary QKD,
Von Neumann Self-Replication, and Galactic Planetary Protection.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from .interplanetary.relativistic_nav import PostNewtonianPropagator, PulsarXNAVReceiver, AutonomousAerocaptureGuidance
from .lunar_base.megawatt_microgrid import PSRIceHarvester, MegawattFissionMicrogrid, ThermalWadiReservoir
from .titan.cryogenic_nautical import HydrocarbonSubmersible, AcousticBathymetrySounder, TitanDenseAeroDrone
from .drilling_rig.coiled_tubing import CoiledTubingDrillRig, AcousticMudPulseTelemetry, BoreholeBlowoutPreventer
from .venus.supercritical_avionics import VenusSupercriticalAeroEngine, HighTempSiCAvionics, ClockworkMechanicalBackup
from .asteroid.kinetic_deflector import BinaryAsteroidTracker, KineticImpactorGuidance, GravityTractorController
from .bio_hybrid.synthetic_biosensors import EngineeredBacterialBiosensor, MemristiveSpikingCrossbar, MicrofluidicNanoporeSequencer
from .quantum_network.entangled_qkd import ContinuousVariableQKD, EntanglementSPDCSource, QuantumStateTomographer
from .self_replication.evolution_engine import VonNeumannKinematicClosure, SelectiveLaserMeltingPrinter, EvolutionarySafetyGovernor
from .biosecurity.galactic_protection import GalacticBiobarrierCanister, XenobioticSequencingAssay, FormalMultiAgentSafetyVerifier
from .evaluation.label_script_l6 import KEYS_L6, level6_label, release_gate_l6

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

__version__ = "6.0.0-prototype"

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "PostNewtonianPropagator",
    "PulsarXNAVReceiver",
    "AutonomousAerocaptureGuidance",
    "PSRIceHarvester",
    "MegawattFissionMicrogrid",
    "ThermalWadiReservoir",
    "HydrocarbonSubmersible",
    "AcousticBathymetrySounder",
    "TitanDenseAeroDrone",
    "CoiledTubingDrillRig",
    "AcousticMudPulseTelemetry",
    "BoreholeBlowoutPreventer",
    "VenusSupercriticalAeroEngine",
    "HighTempSiCAvionics",
    "ClockworkMechanicalBackup",
    "BinaryAsteroidTracker",
    "KineticImpactorGuidance",
    "GravityTractorController",
    "EngineeredBacterialBiosensor",
    "MemristiveSpikingCrossbar",
    "MicrofluidicNanoporeSequencer",
    "ContinuousVariableQKD",
    "EntanglementSPDCSource",
    "QuantumStateTomographer",
    "VonNeumannKinematicClosure",
    "SelectiveLaserMeltingPrinter",
    "EvolutionarySafetyGovernor",
    "GalacticBiobarrierCanister",
    "XenobioticSequencingAssay",
    "FormalMultiAgentSafetyVerifier",
    "KEYS_L6",
    "level6_label",
    "release_gate_l6",
]
