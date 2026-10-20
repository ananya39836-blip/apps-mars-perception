"""Automated Unit and Integration Test Suite for APPS Level 5.
Chapters 370 to 469 & Parts 28 to 37.

Covers:
1. Swarm Consensus, Byzantine Fault Tolerance & Potential Fields (Part 28)
2. Subsurface Lava Tube Exploration, LiDAR SLAM & Tethered Rappel (Part 29)
3. Ocean Worlds Cryobot Melting Kinematics & Acoustic Sonar (Part 30)
4. Astrobiology Deep-UV Raman Deconvolution & Biosignatures (Part 31)
5. Morphologically Reconfigurable Robotics & Modular Docking (Part 32)
6. In-Situ Resource Utilization (ISRU) Mining & Microwave Sintering (Part 33)
7. Deep-Space Optical Laser Communications & DTN Bundle Protocol (Part 34)
8. Post-Quantum Cryptography & Secure Enclave Anti-Spoofing (Part 35)
9. Lifelong Continual Learning & Actuator Aging Compensation (Part 36)
10. Planetary Protection Category V & Formal Safety Invariants (Part 37)
11. Level 5 Milestone Evaluator (KEYS_L5)
"""
import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level5.swarm.swarm_consensus import (
    SwarmNode, DecentralizedSwarmCoordinator,
    PROTOTYPE_LOCK as SWARM_LOCK, NAVIGATION_READY as SWARM_NAV
)
from level5.subsurface.cave_navigation import (
    SubterraneanLidarSLAM, TetheredRappelDynamics, SubsurfaceBreadcrumbDeployer,
    PROTOTYPE_LOCK as SUB_LOCK, NAVIGATION_READY as SUB_NAV
)
from level5.cryobot.ocean_worlds import (
    CryobotThermalDrill, SubOceanPlumeTracer, ForwardLookaheadSonar,
    PROTOTYPE_LOCK as CRYO_LOCK, NAVIGATION_READY as CRYO_NAV
)
from level5.astrobiology.biosignature_detector import (
    DeepUVRamanSpectrometer, BiosignatureClassifier,
    PROTOTYPE_LOCK as ASTRO_LOCK, NAVIGATION_READY as ASTRO_NAV
)
from level5.morphological.reconfigurable_robotics import (
    WheelLegTransformer, ModularDockingInterface, ActuatorFaultRemapper,
    PROTOTYPE_LOCK as MORPH_LOCK, NAVIGATION_READY as MORPH_NAV
)
from level5.isru.regolith_mining import (
    VolatileWaterExtractor, RegolithSinteringFurnace, CivilConstructionManager,
    PROTOTYPE_LOCK as ISRU_LOCK, NAVIGATION_READY as ISRU_NAV
)
from level5.optical_comm.laser_dtn import (
    DSOCLinkBudget, DTNBundleRouter,
    PROTOTYPE_LOCK as LASER_LOCK, NAVIGATION_READY as LASER_NAV
)
from level5.cybersecurity.quantum_enclave import (
    QuantumResistantEnclave,
    PROTOTYPE_LOCK as SEC_LOCK, NAVIGATION_READY as SEC_NAV
)
from level5.continual_learning.aging_model import (
    ContinualExperienceReplay, ActuatorWearCompensator,
    PROTOTYPE_LOCK as AGE_LOCK, NAVIGATION_READY as AGE_NAV
)
from level5.qualification.planetary_protection import (
    PlanetaryProtectionBarrier, FormalSafetyInvariantChecker,
    PROTOTYPE_LOCK as QUAL_LOCK, NAVIGATION_READY as QUAL_NAV
)
from level5.evaluation.label_script_l5 import level5_label, release_gate_l5, KEYS_L5


# ---------------- 1. Swarm Consensus & Potential Fields (Part 28) ----------------
def test_t50_swarm_consensus_election_and_proposals():
    swarm = DecentralizedSwarmCoordinator(num_nodes=6)
    res = swarm.reach_consensus_on_waypoint(candidate_waypoint=(25.0, 30.0), proposed_by=0)
    assert res["affirmative_votes"] >= res["quorum_required"]
    assert res["consensus_reached"] is True
    assert res["fault_tolerance_f"] == 1


def test_t51_swarm_potential_fields_and_excavation():
    swarm = DecentralizedSwarmCoordinator(num_nodes=6)
    tasks = [(10.0, 15.0), (30.0, -10.0), (-25.0, 40.0), (5.0, -35.0)]
    alloc = swarm.allocate_tasks_cbba(tasks)
    assert alloc["tasks_allocated"] == 4
    assert len(alloc["assignments"]) == 6

    velocities = swarm.compute_swarm_potential_fields(goal_xy=(50.0, 50.0))
    assert len(velocities) == 6
    for vx, vy in velocities:
        assert -0.25 <= vx <= 0.25
        assert -0.25 <= vy <= 0.25

    # Byzantine node isolation
    iso = swarm.detect_and_quarantine_byzantine_node(suspect_node_id=1)
    assert iso["status"] == "ISOLATED"
    assert iso["remaining_active_fleet"] == 5

    excav = swarm.evaluate_fleet_excavation_throughput(duration_hours=8.0)
    assert excav["total_excavated_tons"] > 0.0
    assert excav["landing_pad_progress_pct"] > 0.0


# ---------------- 2. Subsurface Lava Tube Exploration (Part 29) ----------------
def test_t52_subterranean_lidar_slam():
    slam = SubterraneanLidarSLAM(cylinder_radius_m=6.5)
    res = slam.register_pointcloud_scan(raw_points_count=2000, forward_step_m=0.40)
    assert res["points_registered"] == 2000
    assert res["current_pose_m"][0] == 0.40
    assert res["structural_symmetry_disambiguated"] is True


def test_t53_skylight_rappel_and_breadcrumbs():
    rappel = TetheredRappelDynamics(rover_mass_kg=190.0, max_tether_length_m=75.0)
    descent = rappel.calculate_descent_state(vertical_depth_m=35.0, descent_rate_mps=0.08)
    assert descent["deployed_depth_m"] == 35.0
    assert descent["is_rappel_safe"] is True
    assert descent["tether_safety_factor"] >= 3.0

    deployer = SubsurfaceBreadcrumbDeployer(max_droppers=6, spacing_interval_m=50.0)
    d1 = deployer.evaluate_drop_trigger(current_ingress_distance_m=55.0, line_of_sight_bend_angle_deg=10.0)
    assert d1["should_deploy_now"] is True
    assert d1["total_deployed"] == 1
    assert d1["remaining_in_magazine"] == 5

    # Secondary trigger via tunnel bend
    d2 = deployer.evaluate_drop_trigger(current_ingress_distance_m=85.0, line_of_sight_bend_angle_deg=60.0)
    assert d2["should_deploy_now"] is True
    assert d2["total_deployed"] == 2


# ---------------- 3. Ocean Worlds Cryobot (Part 30) ----------------
def test_t54_cryobot_thermal_melting_kinematics():
    drill = CryobotThermalDrill(thermal_power_w=5000.0, probe_diameter_m=0.30)
    res = drill.compute_penetration_rate(ambient_ice_temp_k=115.0)
    assert res["effective_melt_rate_m_hr"] > 0.15
    assert res["penetration_speed_cm_hr"] > 15.0
    assert res["thermal_efficiency_pct"] > 40.0


def test_t55_cryobot_acoustic_sonar_and_plumes():
    tracer = SubOceanPlumeTracer(vent_origin_xy=(100.0, 100.0))
    sig = tracer.sample_chemical_signature(pos_xy=(90.0, 95.0))
    assert sig["is_plume_detected"] is True
    assert sig["concentration_ppb"] > 100.0

    sonar = ForwardLookaheadSonar(max_range_m=200.0)
    scan = sonar.scan_forward_sector(range_to_nearest_keel_m=35.0)
    assert scan["obstacle_range_m"] == 35.0
    assert scan["path_clear"] is True
    assert scan["echo_delay_ms"] > 0.0


# ---------------- 4. Astrobiology Biosignature Detection (Part 31) ----------------
def test_t56_raman_spectroscopy_analysis():
    spec = DeepUVRamanSpectrometer()
    peaks = [1602.0, 1648.0, 2928.0] # Aromatic, Amide I, Aliphatic CH
    res = spec.analyze_spectrum(detected_peaks_cm=peaks, snr_db=25.0)
    assert res["complex_organics_confirmed"] is True
    assert "amide_I" in res["matched_biomarkers"]
    assert res["organic_complexity_index"] >= 0.6


def test_t57_biosignature_biogenicity_classifier():
    classifier = BiosignatureClassifier(biogenicity_threshold=0.70)
    bio = classifier.evaluate_sample_biogenicity(
        chiral_excess_pct=34.0,
        delta_13c_permil=-32.0,
        raman_complexity_index=0.85,
        fluorescence_positive=True
    )
    assert bio["biogenicity_score"] >= 0.70
    assert bio["is_candidate_biosignature"] is True
    assert bio["priority_level"] == "CRITICAL_ALPHA"


# ---------------- 5. Morphologically Reconfigurable Robotics (Part 32) ----------------
def test_t58_morphological_kinematics_transformation():
    robot = WheelLegTransformer()
    assert robot.current_morphology == "WHEEL_MODE"

    # Smooth terrain stays in wheel mode
    t1 = robot.trigger_transformation(terrain_roughness_index=0.2, slope_deg=10.0)
    assert t1["active_morphology"] == "WHEEL_MODE"
    assert t1["mode_changed"] is False

    # Extreme terrain triggers metamorphosis
    t2 = robot.trigger_transformation(terrain_roughness_index=0.85, slope_deg=30.0)
    assert t2["active_morphology"] == "LEGGED_CLIMBER_MODE"
    assert t2["mode_changed"] is True
    assert t2["obstacle_clearance_m"] == 0.55


def test_t59_modular_docking_and_remapping():
    dock = ModularDockingInterface(latch_holding_force_N=1500.0)
    res = dock.engage_docking_latch(alignment_error_mm=5.0)
    assert res["capture_successful"] is True
    assert res["power_bus_continuity"] is True

    remapper = ActuatorFaultRemapper(num_dof=6)
    remap = remapper.handle_joint_freeze(frozen_joint_index=2)
    assert remap["remaining_active_dof"] == 5
    assert remap["retains_positioning"] is True


# ---------------- 6. In-Situ Resource Utilization Mining (Part 33) ----------------
def test_t60_regolith_water_extraction():
    extractor = VolatileWaterExtractor(water_content_wt_pct=7.0)
    res = extractor.process_regolith_batch(batch_mass_kg=60.0)
    assert res["recovered_water_kg"] > 3.0
    assert res["extraction_efficiency_pct"] == 88.0
    assert res["energy_consumed_kwh"] > 0.0


def test_t61_microwave_sintering_and_pad_construction():
    furnace = RegolithSinteringFurnace(microwave_power_kw=4.0)
    brick = furnace.sinter_brick(brick_volume_cm3=1500.0)
    assert brick["is_landing_pad_grade"] is True
    assert brick["compressive_strength_mpa"] >= 30.0

    mgr = CivilConstructionManager(target_pad_radius_m=15.0, target_berm_height_m=3.0)
    eval_res = mgr.evaluate_construction_metrics(current_elevation_std_cm=1.4, berm_volume_fraction=0.98)
    assert eval_res["grade_tolerance_satisfied"] is True
    assert eval_res["overall_pad_certified"] is True


# ---------------- 7. Deep-Space Optical Comm & DTN (Part 34) ----------------
def test_t62_dsoc_laser_link_budget():
    dsoc = DSOCLinkBudget(laser_power_w=30.0, aperture_diameter_m=0.25)
    link = dsoc.compute_optical_link(distance_au=1.2, pointing_jitter_urad=0.18)
    assert link["link_viable"] is True
    assert link["data_rate_mbps"] >= 15.0
    assert link["link_margin_db"] > 3.0


def test_t63_dtn_bundle_routing():
    router = DTNBundleRouter(storage_buffer_gb=200.0)
    # Contact closed -> stored
    s1 = router.process_bundle_transmission(bundle_size_mb=500.0, is_contact_window_open=False)
    assert s1["action"] == "STORED_IN_NONVOLATILE_DTN_BUFFER"
    assert s1["custody_accepted"] is True

    # Contact open -> transmitted
    s2 = router.process_bundle_transmission(bundle_size_mb=500.0, is_contact_window_open=True)
    assert s2["action"] == "CUSTODY_TRANSFERRED_DOWNLINK_SUCCESS"
    assert s2["custody_accepted"] is True


# ---------------- 8. Post-Quantum Cryptography & Enclave (Part 35) ----------------
def test_t64_quantum_enclave_ml_dsa_signatures():
    enclave = QuantumResistantEnclave()
    pub, priv = enclave.generate_ml_dsa_keypair()
    assert pub.startswith("ML-DSA-87-")
    assert priv.startswith("ML-DSA-87-SEC-")

    payload = b"EXECUTE-DRILL-CORE-SAMPLE-32"
    sig = enclave.sign_command_bundle("CMD-101", payload, priv)
    assert sig.startswith("SIG_ML_DSA_")

    ver = enclave.verify_command_signature("CMD-101", payload, sig, counter=enclave.monotonic_counter, public_key=pub)
    assert ver["valid"] is True
    assert ver["anti_spoofing_clearance"] is True


def test_t65_enclave_anti_spoofing_challenge():
    enclave = QuantumResistantEnclave()
    seed = b"ORBITAL_EPHEMERIS_CHALLENGE_2026"
    resp = enclave.ephemeris_challenge_response(seed, mission_time_sec=1254300.0)
    assert isinstance(resp, str)
    assert len(resp) == 64


# ---------------- 9. Continual Learning & Actuator Wear (Part 36) ----------------
def test_t66_continual_learning_experience_replay():
    replay = ContinualExperienceReplay(capacity=10)
    for i in range(12):
        replay.store_experience(
            state=np.zeros(4),
            action=np.zeros(2),
            reward=float(i),
            next_state=np.ones(4),
            surprise=float(i + 1)
        )
    assert len(replay.buffer) == 10  # Cap preserved
    batch = replay.sample_batch(batch_size=5)
    assert len(batch["states"]) == 5
    assert batch["mean_novelty"] > 0.0


def test_t67_actuator_wear_and_adaptive_torque():
    compensator = ActuatorWearCompensator(num_actuators=6)
    compensator.advance_mission_wear(elapsed_hours=5000.0)
    assert np.all(compensator.backlash_rad > 0.001)
    assert np.all(compensator.friction_coeff > 0.15)

    desired_torque = np.array([10.0, 15.0, 8.0, 12.0, 20.0, 14.0])
    velocity = np.array([1.2, -0.8, 1.5, 0.5, -1.0, 0.2])
    comp = compensator.compute_adapted_torque(desired_torque, velocity)
    assert len(comp["compensated_torque"]) == 6
    assert comp["max_backlash_mrad"] > 1.0


# ---------------- 10. Planetary Protection Category V & Invariants (Part 37) ----------------
def test_t68_planetary_protection_break_the_chain():
    barrier = PlanetaryProtectionBarrier(surface_area_m2=10.0)
    assert barrier.containment_sealed is False

    res = barrier.execute_break_the_chain_seal(induction_temperature_c=540.0, duration_seconds=18.0)
    assert res["containment_sealed"] is True
    assert res["sterilization_met"] is True
    assert res["residual_spore_burden_total"] < 1.0
    assert res["integrity_score"] > 0.8


def test_t69_formal_safety_invariants_checker():
    checker = FormalSafetyInvariantChecker()
    good_state = checker.verify_state(
        speed_mps=0.45,
        pitch_deg=12.0,
        roll_deg=-8.0,
        battery_soc=0.68,
        thermal_c=-40.0,
        prototype_lock=True,
        navigation_ready=False
    )
    assert good_state["safe"] is True
    assert good_state["invariants_passed"] is True

    # Bad state: prototype unlocked or overspeed
    bad_state = checker.verify_state(
        speed_mps=1.5,
        pitch_deg=45.0,
        roll_deg=0.0,
        battery_soc=0.05,
        thermal_c=-140.0,
        prototype_lock=False,
        navigation_ready=True
    )
    assert bad_state["safe"] is False
    assert bad_state["failed_count"] >= 4


# ---------------- 11. Level 5 Milestone Evaluator & Prototype Locks ----------------
def test_t70_level5_label_evaluator():
    evidence = {k: {"exists": True, "passed": True, "executed": True} for k in KEYS_L5}
    assert level5_label(evidence) == "L5-met (internal)"

    # Partial execution
    partial_evidence = {k: {"exists": True, "passed": True, "executed": False} for k in KEYS_L5}
    assert level5_label(partial_evidence) == "L5-partial"

    # Missing one key
    incomplete_evidence = dict(evidence)
    del incomplete_evidence[KEYS_L5[0]]
    assert level5_label(incomplete_evidence) == "L5-not-met"

    gate_status, unpassed = release_gate_l5({k: True for k in KEYS_L5})
    assert gate_status == "ready-for-review"
    assert len(unpassed) == 0


def test_t71_prototype_lock_and_nav_ready_invariants():
    assert SWARM_LOCK is True
    assert SWARM_NAV is False
    assert SUB_LOCK is True
    assert SUB_NAV is False
    assert CRYO_LOCK is True
    assert CRYO_NAV is False
    assert ASTRO_LOCK is True
    assert ASTRO_NAV is False
    assert MORPH_LOCK is True
    assert MORPH_NAV is False
    assert ISRU_LOCK is True
    assert ISRU_NAV is False
    assert LASER_LOCK is True
    assert LASER_NAV is False
    assert SEC_LOCK is True
    assert SEC_NAV is False
    assert AGE_LOCK is True
    assert AGE_NAV is False
    assert QUAL_LOCK is True
    assert QUAL_NAV is False
