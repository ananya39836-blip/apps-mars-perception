"""Automated Unit & Integration Tests for Level 7 Systems.
Verifies:
- Relativistic Interstellar Probe Avionics (Part 53)
- Solar Gravitational Lens (SGL) Exoplanet Imaging (Part 54)
- Dyson Swarm Constellations & Optical Relays (Part 55)
- Sub-Kelvin Superconducting Cryo-Avionics (Part 56)
- Autonomous Planetary Geoengineering & Terraforming (Part 57)
- Level 7 Milestone Key Assessment Engine & Safety Locks
"""
import math
import numpy as np
import pytest

from level7 import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    LorentzBoostNavigator,
    LaserSailPropulsion,
    PulsarInterstellarXNAV,
    SolarGravitationalLensOptics,
    EinsteinRingDeconvolver,
    FocalStationkeepingController,
    SolarStatiteController,
    CoherentLaserArrayBeamer,
    DecentralizedSwarmConsensus,
    RSFQJosephsonProcessor,
    DilutionRefrigeratorThermodynamics,
    SpintronicMemoryEnclave,
    ArtificialMagnetosphereDipole,
    OrbitalMirrorReflector,
    AtmosphericSynthesisGovernor,
    KEYS_L7,
    level7_label,
    release_gate_l7,
)


def test_t115_level7_prototype_lock_invariants():
    """Verify safety lock invariants in Level 7 modules."""
    assert PROTOTYPE_LOCK is True
    assert NAVIGATION_READY is False


def test_t116_lorentz_factor_and_aberration():
    """Verify relativistic Lorentz gamma and forward stellar aberration angle."""
    nav = LorentzBoostNavigator(cruise_beta=0.20)
    assert 1.020 < nav.gamma < 1.022

    # Forward aberration decreases apparent angle for incoming rays
    theta_orig = math.radians(60.0)
    theta_boosted = nav.transform_stellar_aberration(theta_orig, beta=0.20)
    assert theta_boosted < theta_orig
    assert math.degrees(theta_boosted) < 60.0


def test_t117_relativistic_doppler_and_proper_time():
    """Verify relativistic blueshift/redshift and spacetime time dilation."""
    nav = LorentzBoostNavigator(cruise_beta=0.20)
    # Head-on blueshift (theta = 0)
    nu_blue = nav.compute_relativistic_doppler(1e14, beta=0.20, theta_rad=0.0)
    assert nu_blue > 1e14

    # Proper time dilation over 1 year (31,557,600 s)
    t_coord = 31557600.0
    res = nav.compute_proper_time_dilation(t_coord, beta=0.20)
    assert res["proper_time_s"] < t_coord
    assert 0.979 < res["dilation_ratio"] < 0.981
    assert res["time_deficit_s"] > 0.0


def test_t118_laser_sail_thrust_and_thermal_balance():
    """Verify photon momentum thrust and equilibrium radiative temperature."""
    prop = LaserSailPropulsion(sail_area_m2=100.0, sail_mass_kg=0.05)
    # 10 GW laser beam
    thrust = prop.compute_photon_thrust(laser_power_w=1e10, reflectivity=0.99995)
    assert thrust["thrust_n"] > 60.0  # ~66.7 N
    assert thrust["acceleration_mps2"] > 1000.0

    # Thermal balance: absorbed heat must radiate away keeping sail < 500 K
    thermal = prop.compute_sail_equilibrium_temp(laser_power_w=1e10, reflectivity=0.99995)
    assert thermal["equilibrium_temp_k"] < 500.0
    assert thermal["is_sublimation_safe"] is True


def test_t119_interstellar_dust_impact_energetics():
    """Verify relativistic dust impact kinetic energy dissipation at 0.2c."""
    prop = LaserSailPropulsion()
    # 1 microgram dust grain
    impact = prop.compute_dust_impact_energy(dust_mass_kg=1e-9, beta=0.20)
    assert impact["kinetic_energy_joules"] > 1.0e6  # Mega-joules per microgram
    assert impact["tnt_equivalent_grams"] > 100.0


def test_t120_pulsar_xnav_triangulation_and_shapiro_delay():
    """Verify millisecond pulsar phase fixes and general relativistic Shapiro delay."""
    xnav = PulsarInterstellarXNAV()
    shapiro = xnav.compute_shapiro_gravitational_delay(1.496e11, 100.0 * 1.496e11)
    assert shapiro > 0.0

    pos_m = np.array([10.0 * 1.496e11, 0.0, 0.0])
    fix = xnav.triangulate_position_fix(pos_m, timestamp_s=1000.0)
    assert fix["status"] == "TRIANGULATION_LOCKED"
    assert "PSR_B1937+21" in fix["pulsar_fixes"]


def test_t121_schwarzschild_radius_and_sgl_focal_distance():
    """Verify solar lens geometry: r_s ~ 2953 m and minimum focal line z_min ~ 547.5 AU."""
    sgl = SolarGravitationalLensOptics()
    focal = sgl.compute_minimum_focal_distance()
    assert 2950.0 < focal["schwarzschild_radius_m"] < 2960.0
    assert 545.0 < focal["z_min_au"] < 550.0

    # Deflection angle at solar grazing limb
    defl = sgl.compute_deflection_angle(impact_parameter_m=6.9634e8)
    assert 1.5e-6 < defl < 1.0e-5  # ~1.75 arcseconds ~ 8.48e-6 rad


def test_t122_sgl_monochromatic_optical_gain():
    """Verify optical amplification exceeds 10^11 at 1 micron wavelength."""
    sgl = SolarGravitationalLensOptics()
    gain = sgl.compute_optical_gain(wavelength_m=1.0e-6, radial_offset_m=0.0, focal_z_au=600.0)
    assert gain["peak_axial_gain"] > 1.0e11
    assert gain["actual_gain"] > 1.0e11


def test_t123_einstein_ring_richardson_lucy_deconvolution():
    """Verify Richardson-Lucy deconvolution of blurred Einstein ring."""
    deconv = EinsteinRingDeconvolver(grid_size=12)
    synthetic_ring = np.random.uniform(0.1, 0.9, (12, 12))
    res = deconv.deconvolve_surface_patch(synthetic_ring, iterations=15)
    assert res["convergence_status"] == "CONVERGED_STABLE"
    assert len(res["reconstructed_map"]) == 12
    assert res["psnr_db"] > 0.0


def test_t124_sgl_focal_stationkeeping_controller():
    """Verify sub-centimeter transverse corridor containment under radiation pressure."""
    ctrl = FocalStationkeepingController(max_transverse_error_m=0.05)
    pos_err = np.array([0.02, -0.01])
    vel_err = np.array([0.001, -0.002])
    f_srp = np.array([1e-5, 0.0])
    cmd = ctrl.compute_control_thrust(pos_err, vel_err, f_srp)
    assert cmd["is_within_corridor"] is True
    assert cmd["thrust_magnitude_uN"] > 0.0


def test_t125_solar_statite_lightness_number_and_equilibrium():
    """Verify non-Keplerian radiation levitation lightness beta ~ 1.0."""
    statite = SolarStatiteController()
    beta = statite.compute_lightness_number(areal_density_g_m2=0.768, reflectivity=1.0)
    assert 1.9 < beta < 2.1  # For 0.768 g/m2, beta ~ 2.0; at 1.536 g/m2, beta ~ 1.0

    sigma_reflect = statite.sigma_crit_g_m2 * 2.0  # ~1.532 g/m2 for perfect reflection
    beta_crit = statite.compute_lightness_number(areal_density_g_m2=sigma_reflect, reflectivity=1.0)
    assert abs(beta_crit - 1.0) < 0.02

    eval_res = statite.evaluate_levitation_equilibrium(heliocentric_dist_au=0.1, areal_density_g_m2=sigma_reflect)
    assert eval_res["is_levitating_stable"] is True


def test_t126_coherent_laser_array_strehl_and_spot_profile():
    """Verify phased-array Strehl ratio >= 0.92 and focal spot calculation."""
    array = CoherentLaserArrayBeamer(wavelength_m=1.064e-6)
    strehl = array.compute_strehl_ratio(phase_variance_rad2=0.05)
    assert strehl >= 0.92

    profile = array.compute_beam_spot_profile(distance_m=1.496e11, array_diameter_m=2000.0)
    assert profile["spot_diameter_m"] > 0.0
    assert profile["beam_divergence_urad"] < 2.0


def test_t127_dyson_interplanetary_power_beaming_reception():
    """Verify beamed gigawatt energy capture at receiver rectenna."""
    array = CoherentLaserArrayBeamer(wavelength_m=1.064e-6)
    res = array.compute_received_power(
        beam_power_w=1.0e9,
        distance_m=1.0e9,
        array_diameter_m=1000.0,
        collector_diameter_m=500.0,
        phase_jitter_rad=0.10,
    )
    assert res["transmitted_power_mw"] == 1000.0
    assert res["received_power_mw"] > 0.0
    assert res["strehl_ratio"] > 0.98


def test_t128_decentralized_swarm_consensus_dispatch():
    """Verify distributed consensus power dispatch across multiple planetary targets."""
    swarm = DecentralizedSwarmConsensus(node_count=10000)
    demands = {"Mars_Colony": 4.0, "Titan_Base": 2.0, "Lunar_Base": 1.5}
    dispatch = swarm.dispatch_power_grid(demands, capacity_per_node_mw=1.0)
    assert dispatch["total_capacity_gw"] == 10.0
    assert dispatch["dispatch_fulfillment_ratio"] == 1.0
    assert dispatch["allocation"]["Mars_Colony"]["allocated_gw"] == 4.0


def test_t129_rsfq_superconducting_switching_and_power():
    """Verify RSFQ magnetic flux quantum switching energy and 100 GHz micro-power."""
    rsfq = RSFQJosephsonProcessor(critical_current_uA=100.0, target_freq_ghz=100.0)
    e_switch = rsfq.compute_switching_energy()
    assert 2.0e-19 < e_switch < 2.1e-19  # ~2.068e-19 J

    power = rsfq.evaluate_core_power_dissipation(active_gate_count=50000)
    assert power["clock_frequency_ghz"] == 100.0
    assert power["total_power_uw"] < 2000.0  # Ultra-low microwatt level


def test_t130_dilution_refrigerator_50mk_thermodynamics():
    """Verify 3He-4He dilution refrigerator continuous cooling at 50 mK."""
    fridge = DilutionRefrigeratorThermodynamics(flow_rate_umol_s=50.0)
    cooling_50mk = fridge.compute_mixing_cooling_power(mixing_temp_k=0.050)
    assert cooling_50mk > 0.0

    eq = fridge.evaluate_thermal_equilibrium(internal_heat_load_uw=5.0, target_base_temp_k=0.050)
    assert eq["is_cryo_stable"] is True
    assert eq["thermal_margin_uw"] > 0.0


def test_t131_spintronic_radiation_tolerance_and_seu():
    """Verify STT-MRAM zero-SEU radiation hardness under cosmic rays."""
    mem = SpintronicMemoryEnclave(memory_capacity_gb=64)
    res = mem.evaluate_radiation_tolerance(incident_let_mev=85.0)
    assert res["single_event_latchup_immune"] is True
    assert res["status"] == "RADIATION_HARDENED_CERTIFIED"


def test_t132_artificial_magnetosphere_standoff_distance():
    """Verify L1 artificial magnetic dipole standoff shields Mars (downstream >= 2.0 R_Mars)."""
    dipole = ArtificialMagnetosphereDipole(dipole_moment_Am2=1.5e16)
    standoff = dipole.compute_standoff_distance(solar_wind_density_cm3=4.0, solar_wind_velocity_kms=450.0)
    assert standoff["downstream_planetary_radii"] >= 2.0
    assert standoff["is_shielding_sufficient"] is True


def test_t133_orbital_solar_mirror_sublimation_yield():
    """Verify orbital solar mirror flux redirection and annual CO2 gas yield."""
    mirrors = OrbitalMirrorReflector(total_mirror_area_km2=2500.0)
    sub = mirrors.compute_sublimation_yield(target_cap_area_km2=10000.0)
    assert sub["total_reflected_power_gw"] > 1000.0
    assert sub["annual_co2_release_metric_tons"] > 1e11


def test_t134_atmospheric_synthesis_climate_forcing_and_governor():
    """Verify greenhouse radiative forcing and ecological safety throttle."""
    gov = AtmosphericSynthesisGovernor(max_allowed_warming_k_per_yr=0.50)
    # Safe moderate synthesis
    safe_run = gov.evaluate_climate_forcing(current_surface_pressure_mbar=15.0, pfc_concentration_ppm=5.0, annual_synthesis_rate_tons=1e6)
    assert safe_run["is_within_ecological_safety_cap"] is True
    assert safe_run["governor_action"] == "NOMINAL_SYNTHESIS"

    # Excessive synthesis triggering governor throttle
    excess_run = gov.evaluate_climate_forcing(current_surface_pressure_mbar=50.0, pfc_concentration_ppm=25.0, annual_synthesis_rate_tons=5e7)
    assert excess_run["is_within_ecological_safety_cap"] is False
    assert excess_run["governor_action"] == "THROTTLE_50_PERCENT"


def test_t135_level7_milestone_label_and_release_gate():
    """Verify 20 Level 7 requirement keys and release gate evaluation."""
    assert len(KEYS_L7) == 20

    evidence = {k: {"exists": True, "passed": True, "executed": True} for k in KEYS_L7}
    label = level7_label(evidence)
    assert label == "L7-met (internal)"

    gate, blockers = release_gate_l7({
        "tests_passing": True,
        "prototype_locked": True,
        "nav_ready_false": True,
        "manifest_valid": True,
        "keys_complete": True,
    })
    assert gate == "READY-FOR-REVIEW"
    assert len(blockers) == 0
