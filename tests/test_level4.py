"""Automated Unit and Integration Test Suite for APPS Level 4.
Chapters 270 to 369 & Parts 18 to 27.

Covers:
1. Orbital-to-Tactical Hierarchical Navigation & DEM Fusion (Part 18)
2. Autonomous Opportunistic Science Detection & AEGIS Targeting (Part 19)
3. Extreme Mobility Dynamics, Active Articulation & Wheel-Walking (Part 20)
4. Heterogeneous Multi-Agent Aerial Scout & Rover Coordination (Part 21)
5. Online Adaptive Terramechanics & Bayesian Soil Identification (Part 22)
6. Neuromorphic Edge Computing & SNN Event Hazard Detection (Part 23)
7. Multi-Sol Autonomous Mission Executive & Resource Optimization (Part 24)
8. Extreme Environmental Resilience & Dust Storm Survival (Part 25)
9. Celestial Ephemeris & Horizon Silhouette Relocalization (Part 26)
10. Systems Safety, HIL Verification & Flight Qualification (Part 27)
11. Level 4 Milestone Evaluator (KEYS_L4)
"""
import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level4.navigation.hierarchical_planner import OrbitalDEMPyramid, HierarchicalPlanner
from level4.science.aegis_targeting import OpportunisticScienceDetector, ScienceTargetCandidate
from level4.mobility.extreme_mobility import (
    ActiveSuspensionArticulator, WheelWalkingGaitGenerator, TetheredSlopeMobility
)
from level4.cooperative.multi_agent import (
    AerialScoutMission, LandingSiteCertifier, MultiAgentCommunicationsLink
)
from level4.terramechanics.adaptive_bayesian import (
    OnlineBayesianTerramechanics, SlipAnticipationSentinel
)
from level4.neuromorphic.event_camera import (
    NeuromorphicEventStream, SpikingHazardFilter
)
from level4.executive.mission_executive import (
    MultiSolMissionExecutive, TemporalActivity
)
from level4.resilience.environmental_survival import (
    EnvironmentalThermalModel, DustStormSurvivalExecutive
)
from level4.relocalization.lost_in_space import (
    CelestialHeadingEstimator, HorizonSilhouetteRelocalizer
)
from level4.qualification.hil_assurance import (
    HILTimingAssurance, FaultInjectionHarness, verify_prototype_lock_level4
)
from level4.evaluation.label_script_l4 import level4_label, release_gate_l4, KEYS_L4


# ---------------- 1. Orbital-to-Tactical Hierarchical Navigation (Part 18) ----------------
def test_t40_hierarchical_planner_strategic_path():
    dem = OrbitalDEMPyramid(size_m=500.0, base_resolution_m=2.0)
    elev, slope = dem.get_elevation_and_slope(0.0, 0.0)
    assert isinstance(elev, float)
    assert 0.0 <= slope <= math.pi / 2.0

    planner = HierarchicalPlanner(dem, max_slope_deg=25.0)
    res = planner.plan_strategic_path((0.0, 0.0), (120.0, 80.0))
    assert res['status'] == 'success'
    assert res['waypoints_count'] >= 2
    assert res['total_distance_m'] > 100.0
    assert res['prototype_lock'] is True
    assert res['navigation_ready'] is False


def test_t41_hierarchical_tactical_corridors():
    dem = OrbitalDEMPyramid(size_m=500.0, base_resolution_m=2.0)
    planner = HierarchicalPlanner(dem)
    path = [(0.0, 0.0), (20.0, 15.0), (40.0, 30.0)]
    corridors = planner.generate_tactical_corridor(path, corridor_radius_m=10.0)
    assert len(corridors) == 3
    for c in corridors:
        assert 'elevation_m' in c
        assert 'slope_deg' in c
        assert c['traversability_bound_m'] == 10.0


# ---------------- 2. Autonomous Opportunistic Science & AEGIS Targeting (Part 19) ----------------
def test_t42_aegis_science_candidate_detection():
    detector = OpportunisticScienceDetector(target_preference="high_albedo_float")
    candidates = detector.detect_targets_from_scene(num_candidates=6, seed=123)
    assert len(candidates) == 6
    for c in candidates:
        assert 2.0 <= math.hypot(c.pos_rel_m[0], c.pos_rel_m[1]) <= 7.5
        assert 0.0 <= c.novelty_score <= 1.0
        assert 0.0 <= c.science_priority <= 1.0

    # Ensure ranked in descending order of priority
    priorities = [c.science_priority for c in candidates]
    assert priorities == sorted(priorities, reverse=True)


def test_t43_aegis_top_targets_selection():
    detector = OpportunisticScienceDetector()
    candidates = detector.detect_targets_from_scene(num_candidates=5)
    top_3 = detector.get_top_targets(candidates, top_k=3)
    assert len(top_3) == 3
    assert top_3[0]['science_priority'] >= top_3[1]['science_priority']


# ---------------- 3. Extreme Mobility Dynamics & Articulation (Part 20) ----------------
def test_t44_active_suspension_articulation():
    articulator = ActiveSuspensionArticulator()
    # Rover on 15 deg pitch incline
    pitch_incline_rad = math.radians(15.0)
    roll_incline_rad = math.radians(5.0)
    res = articulator.compute_active_leveling(pitch_incline_rad, roll_incline_rad)

    assert res['residual_pitch_deg'] < 15.0 # Chassis leveled
    assert res['stability_gain_pct'] > 0.0
    assert res['com_shift_m'][0] < 0.0 # Shifted rearward/uphill


def test_t45_wheel_walking_crab_gait():
    gait_gen = WheelWalkingGaitGenerator(step_length_m=0.08)
    # Low slip -> Standard rolling
    res_norm = gait_gen.generate_gait_cycle(slip_ratio=0.10, slope_deg=5.0)
    assert res_norm['active_mode'] == 'STANDARD_ROLLING'

    # High slip -> Engage peristaltic wheel walking
    res_walk = gait_gen.generate_gait_cycle(slip_ratio=0.65, slope_deg=22.0)
    assert res_walk['active_mode'] == 'PERISTALTIC_WHEEL_WALKING'
    assert len(res_walk['phases']) == 7
    assert res_walk['effective_traction_gain'] > 2.0


def test_t46_tethered_slope_mobility():
    tether = TetheredSlopeMobility(rover_mass_kg=185.0)
    res = tether.evaluate_tether_tension(slope_deg=35.0, wheel_traction_limit_N=150.0)
    assert res['grav_downslope_N'] > 300.0
    assert res['tether_tension_N'] > 150.0
    assert res['tether_safety_factor'] > 3.0
    assert res['anchor_holding_safe'] is True


# ---------------- 4. Heterogeneous Multi-Agent Coordination (Part 21) ----------------
def test_t47_aerial_scout_sortie_planning():
    mission = AerialScoutMission(scout_id="Ingenuity-2", max_flight_range_m=300.0)
    sortie = mission.plan_scout_sortie(rover_pos=(10.0, 10.0), strategic_goal=(250.0, 150.0))
    assert sortie['scout_id'] == "Ingenuity-2"
    assert sortie['flight_distance_m'] <= 300.0
    assert len(sortie['waypoints']) == 5
    assert sortie['flight_duration_s'] > 30.0


def test_t48_landing_site_certification():
    certifier = LandingSiteCertifier(max_allowable_slope_deg=8.0, max_rock_height_m=0.12)
    # Safe candidate
    res_safe = certifier.certify_candidate_landing_zone(
        center_xy=(45.0, 50.0),
        local_slopes_deg=[2.1, 3.4, 4.0, 5.2],
        detected_obstacle_heights_m=[0.02, 0.05, 0.07]
    )
    assert res_safe['is_certified_for_landing'] is True
    assert res_safe['safety_score'] > 0.0

    # Unsafe candidate (slope too steep)
    res_unsafe = certifier.certify_candidate_landing_zone(
        center_xy=(100.0, 120.0),
        local_slopes_deg=[4.0, 11.5, 9.0],
        detected_obstacle_heights_m=[0.04, 0.06]
    )
    assert res_unsafe['is_certified_for_landing'] is False


def test_t49_multiagent_rf_communications():
    comm = MultiAgentCommunicationsLink(tx_power_dbm=20.0, frequency_mhz=900.0)
    res = comm.evaluate_rf_link(distance_m=150.0, line_of_sight_occluded=False)
    assert res['is_link_established'] is True
    assert res['link_margin_db'] > 6.0
    assert res['throughput_kbps'] >= 50.0


# ---------------- 5. Online Adaptive Terramechanics (Part 22) ----------------
def test_t50_online_bayesian_terramechanics():
    filter_bt = OnlineBayesianTerramechanics()
    # Feed drift sand telemetry: high sinkage (4.2cm) and slip (0.35)
    for _ in range(5):
        res = filter_bt.update_with_measurement(
            measured_sinkage_cm=4.2, measured_slip_ratio=0.35, wheel_torque_Nm=35.0
        )
    assert res['update_count'] == 5
    assert res['dominant_soil_class'] == 'drift_sand'
    assert res['dominant_probability'] > 0.50
    assert res['estimated_cohesion_kPa'] < 2.0


def test_t51_slip_anticipation_sentinel():
    sentinel = SlipAnticipationSentinel(critical_slip_threshold=0.45)
    mock_soil = {'posteriors': {'drift_sand': 0.85, 'loose_dust': 0.10}}
    res = sentinel.evaluate_predictive_risk(
        current_slip=0.25, bayesian_soil=mock_soil, upcoming_slope_deg=18.0
    )
    assert res['predicted_slip'] > 0.35
    assert res['is_anticipation_warning'] is True
    assert res['recommended_action'] in ("ENGAGE_WHEEL_WALKING", "EMERGENCY_HALT")


# ---------------- 6. Neuromorphic Edge Computing (Part 23) ----------------
def test_t52_neuromorphic_event_stream():
    stream = NeuromorphicEventStream(sensor_width=346, sensor_height=260)
    events = stream.generate_event_burst(motion_speed_mps=0.10, num_events=200)
    assert len(events) == 200
    for ev in events:
        assert 0 <= ev['x'] < 346
        assert 0 <= ev['y'] < 260
        assert ev['p'] in (-1, 1)


def test_t53_snn_spiking_hazard_filter():
    snn = SpikingHazardFilter()
    events = [{'x': 10, 'y': 20, 't_us': 1000 + i * 10, 'p': 1} for i in range(120)]
    res = snn.process_events(events)
    assert res['total_events_processed'] == 120
    assert res['spikes_fired'] > 0
    assert res['estimated_power_watts'] < 2.5 # Low-SWaP

    # Radiation single-event upset and scrubbing
    snn.inject_radiation_upset()
    assert snn.radiation_bitflip_detected is True
    snn.scrub_radiation_memory()
    assert snn.radiation_bitflip_detected is False


# ---------------- 7. Multi-Sol Autonomous Mission Executive (Part 24) ----------------
def test_t54_multi_sol_mission_executive():
    exec_sol = MultiSolMissionExecutive(battery_capacity_wh=1200.0, initial_soc_pct=80.0)
    plan = exec_sol.plan_sol_timeline(sol_id=101, traverse_distance_m=75.0)
    assert plan['sol_id'] == 101
    assert len(plan['planned_activities']) >= 5
    assert plan['is_resource_safe'] is True
    assert 20.0 <= plan['final_soc_pct'] <= 100.0


def test_t55_contingency_handling():
    exec_sol = MultiSolMissionExecutive()
    res = exec_sol.handle_contingency("DRIVE_SLIP_HALT")
    assert res['executive_status'] == 'RESOLVED'
    assert 'AEGIS_SCIENCE' in res['autonomous_resolution']


# ---------------- 8. Extreme Environmental Resilience (Part 25) ----------------
def test_t56_environmental_thermal_model():
    thermal = EnvironmentalThermalModel()
    # Nighttime at 03:00 Mars local time
    res_night = thermal.compute_diurnal_temperature(mars_local_solar_time_hrs=3.0)
    assert res_night['ambient_temp_c'] < -80.0
    assert res_night['survival_heater_active'] is True
    assert res_night['thermal_margin_c'] >= 0.0

    # Daytime at 14:00 Mars local time
    res_day = thermal.compute_diurnal_temperature(mars_local_solar_time_hrs=14.0)
    assert res_day['ambient_temp_c'] > -10.0
    assert res_day['survival_heater_active'] is False


def test_t57_dust_storm_deep_sleep_hibernation():
    exec_dust = DustStormSurvivalExecutive()
    # Nominal conditions
    res_nom = exec_dust.update_atmospheric_conditions(tau_measurement=0.60)
    assert res_nom['hibernation_active'] is False

    # Severe global dust storm (tau = 6.5)
    res_storm = exec_dust.update_atmospheric_conditions(tau_measurement=6.5)
    assert res_storm['hibernation_active'] is True
    assert res_storm['survival_power_w'] < 10.0


# ---------------- 9. Celestial & Horizon Relocalization (Part 26) ----------------
def test_t58_celestial_heading_sun_ephemeris():
    celestial = CelestialHeadingEstimator(rover_lat_deg=-18.5, rover_lon_deg=77.5)
    az_rad, elev_rad = celestial.calculate_ephemeris_sun_vector(mars_local_solar_time_hrs=12.0)
    assert 0.0 <= az_rad <= 2.0 * math.pi
    assert elev_rad > 0.0 # Above horizon at local noon

    res = celestial.determine_true_heading(
        mars_local_solar_time_hrs=12.0, measured_sun_azimuth_body_rad=0.15
    )
    assert 'estimated_true_heading_deg' in res
    assert res['heading_uncertainty_deg'] < 1.0


def test_t59_horizon_silhouette_relocalization():
    reloc = HorizonSilhouetteRelocalizer()
    skyline = reloc.generate_panoramic_skyline(num_bins=72)
    assert len(skyline) == 72

    candidates = [(10.0, 10.0), (50.0, -30.0), (120.0, 80.0)]
    res = reloc.match_skyline_to_orbital_dem(skyline, candidates)
    assert res['best_estimated_position_m'] == (50.0, -30.0)
    assert res['relocalization_successful'] is True
    assert res['position_uncertainty_m'] < 10.0


# ---------------- 10. Systems Safety, HIL Verification & Label (Part 27) ----------------
def test_t60_hil_timing_and_fault_injection():
    timing = HILTimingAssurance(cycle_deadline_ms=100.0)
    r1 = timing.record_cycle_execution(0.045) # 45 ms
    assert r1['timing_deadline_met'] is True

    summary = timing.compute_jitter_and_wcet()
    assert summary['meets_hard_realtime'] is True

    harness = FaultInjectionHarness()
    inj = harness.inject_fault("MOTOR_ENCODER_FREEZE")
    assert inj['safety_critical'] is True
    assert inj['fdir_safing_engaged'] is True


def test_t61_level4_label_and_prototype_lock():
    lock_status = verify_prototype_lock_level4()
    assert lock_status['qualification_guard_satisfied'] is True

    # Validate 20 keys
    assert len(KEYS_L4) == 20
    mock_evidence = {k: {'exists': True, 'executed': True, 'passed': True} for k in KEYS_L4}
    assert level4_label(mock_evidence) == "L4-met (internal)"

    # If one key fails
    mock_evidence["hierarchical_planner"]["passed"] = False
    assert level4_label(mock_evidence) == "L4-not-met"

    gate_status, blocked = release_gate_l4({k: True for k in KEYS_L4})
    assert gate_status == "ready-for-review"
    assert len(blocked) == 0
