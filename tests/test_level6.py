"""Automated Unit and Integration Test Suite for APPS Level 6.
Chapters 470 to 569 & Parts 38 to 47.

Covers:
1. Interplanetary Relativistic Autonav, XNAV & Aerocapture (Part 38)
2. Lunar South Pole Infrastructure, PSR Mining & Fission Micro-Grids (Part 39)
3. Titan Cryogenic Nautical Submersibles & Dense Atmosphere Rotorcraft (Part 40)
4. Deep Core Kilometer-Depth Coiled Tubing Rig Infrastructure (Part 41)
5. Venus Supercritical 465 C Atmosphere & SiC High-Temp Avionics (Part 42)
6. Autonomous Asteroid Deflection, Kinetic Impactors & Gravity Tractors (Part 43)
7. Neuromorphic Bio-Hybrid Computing, Memristors & Synthetic Biosensors (Part 44)
8. Quantum-Entangled Interplanetary Communications & CV-QKD (Part 45)
9. Multi-Decadal Self-Replication, Metal 3D Printing & Evolution (Part 46)
10. Galactic Planetary Protection, Xenobiology & Formal Safety (Part 47)
11. Level 6 Milestone Evaluator (KEYS_L6)
"""
import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level6.interplanetary.relativistic_nav import (
    PostNewtonianPropagator, PulsarXNAVReceiver, AutonomousAerocaptureGuidance,
    PROTOTYPE_LOCK as P38_LOCK, NAVIGATION_READY as P38_NAV
)
from level6.lunar_base.megawatt_microgrid import (
    PSRIceHarvester, MegawattFissionMicrogrid, ThermalWadiReservoir,
    PROTOTYPE_LOCK as P39_LOCK, NAVIGATION_READY as P39_NAV
)
from level6.titan.cryogenic_nautical import (
    HydrocarbonSubmersible, AcousticBathymetrySounder, TitanDenseAeroDrone,
    PROTOTYPE_LOCK as P40_LOCK, NAVIGATION_READY as P40_NAV
)
from level6.drilling_rig.coiled_tubing import (
    CoiledTubingDrillRig, AcousticMudPulseTelemetry, BoreholeBlowoutPreventer,
    PROTOTYPE_LOCK as P41_LOCK, NAVIGATION_READY as P41_NAV
)
from level6.venus.supercritical_avionics import (
    VenusSupercriticalAeroEngine, HighTempSiCAvionics, ClockworkMechanicalBackup,
    PROTOTYPE_LOCK as P42_LOCK, NAVIGATION_READY as P42_NAV
)
from level6.asteroid.kinetic_deflector import (
    BinaryAsteroidTracker, KineticImpactorGuidance, GravityTractorController,
    PROTOTYPE_LOCK as P43_LOCK, NAVIGATION_READY as P43_NAV
)
from level6.bio_hybrid.synthetic_biosensors import (
    EngineeredBacterialBiosensor, MemristiveSpikingCrossbar, MicrofluidicNanoporeSequencer,
    PROTOTYPE_LOCK as P44_LOCK, NAVIGATION_READY as P44_NAV
)
from level6.quantum_network.entangled_qkd import (
    ContinuousVariableQKD, EntanglementSPDCSource, QuantumStateTomographer,
    PROTOTYPE_LOCK as P45_LOCK, NAVIGATION_READY as P45_NAV
)
from level6.self_replication.evolution_engine import (
    VonNeumannKinematicClosure, SelectiveLaserMeltingPrinter, EvolutionarySafetyGovernor,
    PROTOTYPE_LOCK as P46_LOCK, NAVIGATION_READY as P46_NAV
)
from level6.biosecurity.galactic_protection import (
    GalacticBiobarrierCanister, XenobioticSequencingAssay, FormalMultiAgentSafetyVerifier,
    PROTOTYPE_LOCK as P47_LOCK, NAVIGATION_READY as P47_NAV
)
from level6.evaluation.label_script_l6 import level6_label, release_gate_l6, KEYS_L6


# ---------------- 1. Interplanetary Relativistic Autonav (Part 38) ----------------
def test_t72_post_newtonian_relativistic_acceleration():
    prop = PostNewtonianPropagator()
    pos = np.array([1.496e11, 0.0, 0.0])  # 1 AU
    vel = np.array([0.0, 29780.0, 0.0])   # Earth orbital speed
    a_net = prop.compute_relativistic_acceleration(pos, vel)
    assert a_net.shape == (3,)
    assert a_net[0] < 0.0  # Attractive to Sun
    assert not np.isnan(a_net).any()


def test_t73_pulsar_xnav_and_shapiro_delay():
    prop = PostNewtonianPropagator()
    delay = prop.compute_shapiro_time_delay(1.496e11, 2.279e11, 3.5e11)
    assert delay > 0.0
    assert delay < 0.001  # Fraction of millisecond in solar system

    xnav = PulsarXNAVReceiver()
    pos = np.array([1.5e11, 0.5e11, 0.1e11])
    res = xnav.measure_time_of_arrival(pos, "PSR_B1937+21")
    assert "projected_range_m" in res
    assert 0.0 <= res["phase_fraction"] <= 1.0


def test_t74_autonomous_aerocapture_guidance():
    guidance = AutonomousAerocaptureGuidance(target_apoapsis_km=6000.0)
    cmd = guidance.compute_guidance_command(alt_km=65.0, speed_mps=5800.0, energy_depleted_pct=42.0)
    assert "commanded_bank_deg" in cmd
    assert abs(cmd["commanded_bank_deg"]) <= 75.0
    assert cmd["prototype_lock"] is True
    assert cmd["navigation_ready"] is False


# ---------------- 2. Lunar South Pole Infrastructure (Part 39) ----------------
def test_t75_lunar_psr_ice_mining():
    harvester = PSRIceHarvester(auger_diameter_m=0.45, rated_power_kw=6.5)
    res = harvester.mine_psr_sector(depth_m=1.2, duration_hours=4.0, ice_weight_pct=8.0)
    assert res["ice_extracted_kg"] > 10.0
    assert res["psr_ambient_temp_k"] == 40.0
    assert harvester.accumulated_ice_kg > 0.0


def test_t76_lunar_fission_microgrid_and_wadi():
    grid = MegawattFissionMicrogrid(reactor_thermal_mw=1.2, stirlings_count=4)
    dispatch = grid.dispatch_power({"mining_fleet": 45.0, "sintering": 60.0, "life_support": 35.0})
    assert dispatch["grid_stable"] is True
    assert dispatch["reserve_margin_pct"] > 50.0

    wadi = ThermalWadiReservoir(mass_tons=80.0, core_temp_c=650.0)
    night = wadi.compute_night_thermal_reserve(elapsed_lunar_night_hours=150.0)
    assert night["current_core_temp_c"] > 150.0
    assert night["sufficient_for_survival"] is True


# ---------------- 3. Titan Cryogenic Exploration (Part 40) ----------------
def test_t77_titan_hydrocarbon_submersible_buoyancy():
    sub = HydrocarbonSubmersible(dry_mass_kg=320.0, max_depth_m=300.0)
    dive = sub.adjust_buoyancy(delta_volume_liters=-15.0)  # Reduce displacement to sink
    assert dive["net_buoyancy_N"] < 0.0
    assert dive["vertical_rate_mps"] < 0.0
    assert dive["safe_depth_envelope"] is True


def test_t78_titan_acoustic_bathymetry_and_rotor_flight():
    sounder = AcousticBathymetrySounder(beam_count=16)
    ping = sounder.ping_seabed(true_altitude_above_bottom_m=35.0)
    assert ping["measured_altitude_m"] == 35.0
    assert ping["two_way_tof_ms"] > 0.0

    drone = TitanDenseAeroDrone(vehicle_mass_kg=45.0, rotor_diameter_m=1.2)
    hover = drone.compute_hover_power()
    assert hover["hover_power_watts"] < 500.0
    assert hover["earth_power_ratio"] < 0.25  # Much less power on Titan


# ---------------- 4. Deep Core Drilling Rig Infrastructure (Part 41) ----------------
def test_t79_coiled_tubing_deep_advance_and_buckling():
    rig = CoiledTubingDrillRig(max_depth_m=2500.0)
    adv = rig.drill_advance(feed_rate_m_hr=1.5, duration_hours=8.0, rock_hardness_mpa=160.0)
    assert adv["current_depth_m"] == 12.0
    assert adv["buckling_safe"] is True
    assert adv["core_recovered_m"] > 10.0


def test_t80_acoustic_mud_pulse_and_bop_shear_rams():
    telemetry = AcousticMudPulseTelemetry()
    pkt = telemetry.transmit_borehole_packet(depth_m=850.0, payload_bytes=b"LOG_GAMMA_STRATA_42")
    assert pkt["packet_intact"] is True
    assert pkt["transit_latency_ms"] > 100.0

    bop = BoreholeBlowoutPreventer(pressure_rating_bar=500.0)
    kick = bop.evaluate_wellbore_pressure(formation_pressure_bar=120.0, mud_hydrostatic_bar=95.0)
    assert kick["overpressure_kick_detected"] is True
    assert kick["blowout_preventer_closed"] is True


# ---------------- 5. Venus Supercritical 465 C Avionics (Part 42) ----------------
def test_t81_venus_supercritical_dense_atmosphere_lift():
    balloon = VenusSupercriticalAeroEngine(envelope_volume_m3=85.0, structural_mass_kg=140.0)
    lift = balloon.calculate_buoyant_lift(altitude_km=5.0)
    assert lift["ambient_density_kg_m3"] > 40.0
    assert lift["buoyancy_positive"] is True
    assert lift["supercritical_regime"] is True


def test_t82_venus_high_temp_sic_avionics_and_clockwork():
    sic = HighTempSiCAvionics(gate_count=15000)
    cycle = sic.execute_logic_cycle(ambient_temp_c=480.0, clock_mhz=10.0)
    assert cycle["logic_operational"] is True
    assert cycle["leakage_current_na"] < 50.0

    mech = ClockworkMechanicalBackup()
    out = mech.step_mechanical_cycle(input_torque_nm=12.0)
    assert out["output_torque_nm"] > 40.0
    assert out["clockwork_jammed"] is False


# ---------------- 6. Asteroid Deflection & Kinetic Impactors (Part 43) ----------------
def test_t83_binary_asteroid_orbit_and_hill_sphere():
    tracker = BinaryAsteroidTracker()
    params = tracker.compute_mutual_orbital_parameters()
    assert params["mutual_period_hours"] > 5.0
    assert params["hill_sphere_radius_km"] > 10.0


def test_t84_hypervelocity_kinetic_impactor_and_tractor():
    impactor = KineticImpactorGuidance(impactor_mass_kg=570.0, impact_speed_mps=6500.0)
    homing = impactor.compute_terminal_guidance(range_to_target_m=12000.0, los_rate_rad_s=0.0008, beta_estimate=2.4)
    assert homing["time_to_go_s"] < 2.0
    assert homing["delta_momentum_Ns"] > 8e6
    assert homing["target_locked"] is True

    tractor = GravityTractorController()
    tow = tractor.compute_towing_force(standoff_distance_m=150.0, cant_angle_deg=20.0)
    assert tow["gravitational_tow_force_N"] > 0.0
    assert tow["station_keeping_stable"] is True


# ---------------- 7. Neuromorphic Bio-Hybrid Computing (Part 44) ----------------
def test_t85_engineered_bacterial_biosensor_luciferase():
    sensor = EngineeredBacterialBiosensor()
    res = sensor.assay_sample_metabolites(target_amino_acid_conc_pM=25.0)
    assert res["bioluminescent_signal_cps"] > 500.0
    assert res["detection_confirmed"] is True
    assert res["containment_intact"] is True


def test_t86_memristive_spiking_crossbar_and_nanopore():
    crossbar = MemristiveSpikingCrossbar(rows=64, cols=64)
    spikes = np.ones(64)
    inf = crossbar.execute_synaptic_inference(spikes)
    assert inf["active_power_watts"] < 0.50
    assert inf["max_activation"] > 0.0

    nanopore = MicrofluidicNanoporeSequencer(channels_count=512)
    seq = nanopore.sequence_nucleic_fragment(sequence_length_bp=3000)
    assert seq["base_call_accuracy_pct"] >= 99.0
    assert seq["sequencing_time_s"] > 0.0


# ---------------- 8. Quantum Interplanetary Communications (Part 45) ----------------
def test_t87_continuous_variable_qkd_secret_rate():
    qkd = ContinuousVariableQKD()
    rate = qkd.compute_secret_key_rate(distance_au=1.2)
    assert rate["qber"] < 0.11
    assert rate["channel_secure"] is True


def test_t88_entanglement_spdc_chsh_and_tomography():
    source = EntanglementSPDCSource()
    chsh = source.evaluate_bell_inequality(phase_jitter_rad=0.05)
    assert chsh["s_chsh_correlation"] > 2.0  # Violation of classical limit!
    assert chsh["bell_inequality_violated"] is True
    assert chsh["entanglement_fidelity"] > 0.95

    tomo = QuantumStateTomographer()
    rec = tomo.reconstruct_density_matrix(fidelity=0.96)
    assert rec["quantum_state_certified"] is True
    assert rec["purity"] > 0.90


# ---------------- 9. Self-Replication & Manufacturing (Part 46) ----------------
def test_t89_von_neumann_kinematic_closure():
    closure = VonNeumannKinematicClosure(total_bill_of_materials=150)
    res = closure.evaluate_closure_ratio()
    assert res["closure_ratio"] >= 0.95
    assert res["kinematic_closure_achieved"] is True


def test_t90_selective_laser_melting_and_safety_governor():
    slm = SelectiveLaserMeltingPrinter()
    print_res = slm.sinter_structural_component(part_mass_kg=12.5)
    assert print_res["yield_strength_mpa"] >= 850.0
    assert print_res["tensile_qualified"] is True

    gov = EvolutionarySafetyGovernor(max_population_quota=32)
    auth = gov.authorize_reproduction(child_firmware_invariants_checked=True)
    assert auth["reproduction_authorized"] is True
    assert auth["current_population"] == 7


# ---------------- 10. Galactic Planetary Protection & Invariants (Part 47) ----------------
def test_t91_galactic_biobarrier_vacuum_braze_seal():
    canister = GalacticBiobarrierCanister(volume_liters=4.5)
    assert canister.sealed is False
    braze = canister.execute_vacuum_braze_seal(braze_temp_c=650.0, hold_seconds=45.0)
    assert braze["containment_sealed"] is True
    assert braze["helium_leak_rate_mbar_l_s"] < 1e-11


def test_t92_xenobiotic_sequencing_and_formal_invariants():
    assay = XenobioticSequencingAssay()
    res = assay.evaluate_genetic_divergence(unaligned_bases_fraction=0.88, non_canonical_backbone=True)
    assert res["terrestrial_origin_disproven"] is True
    assert res["biosecurity_alert_level"] == "LEVEL_4_HOT_ZONE"

    verifier = FormalMultiAgentSafetyVerifier()
    check = verifier.verify_level6_invariants(
        prototype_lock=True,
        navigation_ready=False,
        biobarrier_sealed=True,
        population_under_quota=True,
        qber_within_bounds=True
    )
    assert check["all_invariants_satisfied"] is True
    assert check["level6_certified"] is True


# ---------------- 11. Level 6 Milestone Evaluator & Prototype Locks ----------------
def test_t93_level6_milestone_label_and_locks():
    evidence = {k: {"exists": True, "passed": True, "executed": True} for k in KEYS_L6}
    assert level6_label(evidence) == "L6-met (internal)"

    gate_status, unpassed = release_gate_l6({k: True for k in KEYS_L6})
    assert gate_status == "ready-for-review"
    assert len(unpassed) == 0

    # Invariants on compile-time guards
    assert P38_LOCK is True and P38_NAV is False
    assert P39_LOCK is True and P39_NAV is False
    assert P40_LOCK is True and P40_NAV is False
    assert P41_LOCK is True and P41_NAV is False
    assert P42_LOCK is True and P42_NAV is False
    assert P43_LOCK is True and P43_NAV is False
    assert P44_LOCK is True and P44_NAV is False
    assert P45_LOCK is True and P45_NAV is False
    assert P46_LOCK is True and P46_NAV is False
    assert P47_LOCK is True and P47_NAV is False
