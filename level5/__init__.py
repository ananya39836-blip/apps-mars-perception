"""Automated Planetary Perception System (APPS) — Level 5.
Deep-Space Planetary Autonomy, Swarm Robotics, Subsurface Lava Tubes,
Ocean Worlds Cryobots, Astrobiology Biosignature Detection, and Planetary Protection Category V.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from .swarm.swarm_consensus import SwarmNode, DecentralizedSwarmCoordinator
from .subsurface.cave_navigation import SubterraneanLidarSLAM, TetheredRappelDynamics, SubsurfaceBreadcrumbDeployer
from .cryobot.ocean_worlds import CryobotThermalDrill, SubOceanPlumeTracer, ForwardLookaheadSonar
from .astrobiology.biosignature_detector import DeepUVRamanSpectrometer, BiosignatureClassifier
from .morphological.reconfigurable_robotics import WheelLegTransformer, ModularDockingInterface, ActuatorFaultRemapper
from .isru.regolith_mining import VolatileWaterExtractor, RegolithSinteringFurnace, CivilConstructionManager
from .optical_comm.laser_dtn import DSOCLinkBudget, DTNBundleRouter
from .cybersecurity.quantum_enclave import QuantumResistantEnclave
from .continual_learning.aging_model import ContinualExperienceReplay, ActuatorWearCompensator
from .qualification.planetary_protection import PlanetaryProtectionBarrier, FormalSafetyInvariantChecker
from .evaluation.label_script_l5 import KEYS_L5, level5_label, release_gate_l5

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

__version__ = "5.0.0-prototype"

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "SwarmNode",
    "DecentralizedSwarmCoordinator",
    "SubterraneanLidarSLAM",
    "TetheredRappelDynamics",
    "SubsurfaceBreadcrumbDeployer",
    "CryobotThermalDrill",
    "SubOceanPlumeTracer",
    "ForwardLookaheadSonar",
    "DeepUVRamanSpectrometer",
    "BiosignatureClassifier",
    "WheelLegTransformer",
    "ModularDockingInterface",
    "ActuatorFaultRemapper",
    "VolatileWaterExtractor",
    "RegolithSinteringFurnace",
    "CivilConstructionManager",
    "DSOCLinkBudget",
    "DTNBundleRouter",
    "QuantumResistantEnclave",
    "ContinualExperienceReplay",
    "ActuatorWearCompensator",
    "PlanetaryProtectionBarrier",
    "FormalSafetyInvariantChecker",
    "KEYS_L5",
    "level5_label",
    "release_gate_l5",
]
