"""Technical Data and Chapter Specifications for APPS Level 6 Volumes (Parts 38 to 42).
Provides exactly 37 structured pages per volume covering full Level 6 planetary & deep-space autonomy:
- Volume 1 (Part 38): Interplanetary Autonomy, Relativistic Deep-Space Celestial Navigation & Aerocapture
- Volume 2 (Part 39): Permanent Lunar South Pole Infrastructure, Cryogenic Micro-Grids & PSR Excavation
- Volume 3 (Part 40): Titan Cryogenic Atmospheric & Nautical Exploration (Liquid Hydrocarbon Submersibles)
- Volume 4 (Part 41): Deep Core Planetary Subsurface Drilling Rig Infrastructure (Kilometer-Depth Coiled Tubing)
- Volume 5 (Part 42): Venus Supercritical Atmosphere, Corrosive Mechanics & High-Temperature SiC Electronics
"""

def create_page(title, lead, ch_num=None, equations=None, items=None, table=None, col_widths=None, callout=None, callout_bg="#FFF5F5", callout_border="#FEB2B2"):
    p = {
        'title': title,
        'lead': lead,
    }
    if ch_num is not None:
        p['ch_num'] = ch_num
    if equations is not None:
        p['equations'] = equations
    if items is not None:
        p['items'] = items
    if table is not None:
        p['table'] = table
    if col_widths is not None:
        p['col_widths'] = col_widths
    if callout is not None:
        p['callout'] = callout
        p['callout_bg'] = callout_bg
        p['callout_border'] = callout_border
    return p


# =============================================================================
# VOLUME 1 (PART 38): INTERPLANETARY AUTONOMY & RELATIVISTIC NAVIGATION
# =============================================================================
def get_volume_38_data():
    pages = []
    # Page 1: Cover
    pages.append({'summary': 'Specifies deep-space autonomous interplanetary cruise, general relativistic optical navigation, X-ray pulsar timing (XNAV), and autonomous planetary aerocapture corridor guidance.'})
    # Page 2: Exec Summary
    pages.append(create_page(
        title="Executive Summary & Interplanetary Information Boundary Rung 6",
        lead="Establishes Level 6 autonomous interplanetary navigation without continuous Deep Space Network (DSN) ground tracking loops.",
        ch_num=470,
        items=[
            {'heading': 'Milestone Scope', 'text': 'Level 6 encompasses long-duration autonomous cruise across the solar system with real-time relativistic corrections and closed-loop orbit insertion.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready must evaluate strictly to False in all output records.'},
            {'heading': 'Autonomous Ephemeris', 'text': 'Onboard numerical integration of multi-body gravitational potential including relativistic post-Newtonian expansions.'}
        ],
        table=[
            ["Navigation Mode", "Primary Observable", "Accuracy Baseline", "Update Frequency"],
            ["XNAV Pulsar", "Millisecond X-Ray Pulses", "0.5 km position error", "Continuous 1 Hz"],
            ["Optical Triangulation", "Planetary Limb & Asteroid Sight", "2.0 arcsec angular fix", "Every 15 min"],
            ["Autonomous Aerocapture", "Entry Interface Deceleration", "< 0.05 deg corridor margin", "100 Hz IMU Loop"]
        ]
    ))
    # Page 3: TOC
    pages.append({'title': 'Table of Contents'})

    # Pages 4-33: 30 Technical Chapters (Ch 470.1 to 479.3)
    p_defs = [
        # Ch 470
        ("Post-Newtonian Gravitational Trajectory Propagation", "N-body equations of motion with first post-Newtonian relativistic corrections.", 470.1, ["a_PN = (G M / r^2) * [(4 G M / c^2 r - v^2 / c^2) n + 4 (v . n) v / c^2]", "Delta_r_PN <= 1.2 m / AU"]),
        ("Relativistic Light-Time Delay & Aberration Compensation", "Lorentz frame transformations for optical line-of-sight tracking across heliocentric space.", 470.2, ["Delta_t_Shapiro = (2 G M_sun / c^3) * ln((r_1 + r_2 + d) / (r_1 + r_2 - d))", "Theta_aberration = v_rel / c * sin(alpha)"]),
        ("Solar Radiation Pressure (SRP) Dynamic Modeling", "Surface optical reflectivity, specular bounce, and thermal re-radiation thrust estimation.", 470.3, ["F_SRP = (Phi_solar / c) * A_proj * (1 + C_r)", "C_r_degradation = 0.02 / yr"]),
        # Ch 471
        ("X-Ray Pulsar Navigation (XNAV) Pulse Profile Matching", "Phase fold alignment against millisecond pulsar timing models (PSR B1937+21, B1821-24).", 471.1, ["Delta_tau_pulse = (r_sc . n_pulsar) / c + Delta_Doppler", "sigma_TOA <= 150 ns"]),
        ("Pulsar Phase Ambiguity Resolution Algorithms", "Iterative integer cycle ambiguity fixing across non-orthogonal pulsar triads.", 471.2, ["Phi_meas = mod(t_TOA * f_0, 1.0)", "Confidence_ambiguity_fix >= 0.9998"]),
        ("Autonomous Clock Drift & Relativistic Dilation Tracking", "Kalman estimation of spaceborne rubidium/cesium atomic clock time-dilation offsets.", 471.3, ["dt_proper / dt_coordinate = 1 - U / c^2 - v^2 / (2 c^2)", "Clock_stability_sigma_y <= 1e-14"]),
        # Ch 472
        ("Optical Planetary Limb & Feature Triangulation", "Sub-pixel horizon limb extraction and planetary crescent center-of-mass fitting.", 472.1, ["Limb_edge_error <= 0.08 pixel", "Position_triangulation_sigma <= 4.2 km"]),
        ("Beacon Asteroid Asteroseismology & Optical Fixes", "Autonomous optical centroiding of designated main-belt navigation asteroids.", 472.2, ["Bearing_vector = K^-1 * [u, v, 1]^T", "Residual_angular_error <= 1.5 urad"]),
        ("Stellar Occultation Autonomous Timing", "Micro-photometer detection of stellar flux extinction behind planetary atmospheres.", 472.3, ["Scale_height_H = k_B * T / (m * g)", "Radius_precision <= 15 m"]),
        # Ch 473
        ("Autonomous Trajectory Correction Maneuver (TCM) Targeting", "B-plane coordinate targeting and impulsive velocity increment optimization.", 473.1, ["B . T = target_val_1", "B . R = target_val_2", "Delta_V_budget <= 45.0 m/s"]),
        ("Continuous Low-Thrust Ion Propulsion Guidance", "Collocation and pontryagin maximum principle for multi-year low-thrust Hall thrusters.", 473.2, ["H = lambda_r . v + lambda_v . (T_thrust / m + g)", "Thrust_efficiency >= 0.68"]),
        ("Gravity Assist Flyby Corridor Safety Envelopes", "Hyperbolic trajectory periapsis altitude locks and planetary impact probability bounds.", 473.3, ["r_periapsis >= r_planet + h_safe", "P_impact <= 1e-7"]),
        # Ch 474
        ("Autonomous Planetary Aerocapture Corridor Entry", "Closed-loop entry corridor capture converting hyperbolic excess velocity to bound orbit.", 474.1, ["gamma_entry = -5.85 deg", "Tolerance_gamma <= 0.08 deg"]),
        ("Entry Deceleration Load & Thermal Flux Bounds", "Real-time bank angle modulation governing peak stagnation heat flux and g-load limits.", 474.2, ["q_stag = k_heat * sqrt(rho / R_nose) * v^3", "Bank_angle_rate <= 15 deg/s"]),
        ("Hypersonic Aerodynamic Coefficients Adaptation", "Online recursive estimation of drag and lift coefficients in rarefied upper atmospheres.", 474.3, ["C_L_est = 2 L / (rho v^2 S)", "C_D_est = 2 D / (rho v^2 S)"]),
        # Ch 475
        ("Autonomous Orbit Insertion Burn Sequencing", "Apoapsis raise burn triggering upon atmospheric exit to establish stable science orbit.", 475.1, ["Delta_V_raise = sqrt(mu / r_a) * (sqrt(2 r_p / (r_a + r_p)) - 1)", "Burn_timing_error <= 0.1 s"]),
        ("Aerobraking Phase Duration & Periapsis Trimming", "Multi-week automated aerobraking managing periapsis density variations.", 475.2, ["Delta_h_periapsis = 0.5 * H_atm * Delta_rho / rho", "Margin_thermal <= 22 %"]),
        ("Attitude Control During Rarefied Gas Immersion", "Reaction wheel desaturation using aerodynamic torque trimming during atmospheric passage.", 475.3, ["tau_aero = 0.5 * rho * v^2 * S * c_p_offset", "Momentum_dump_efficiency >= 85 %"]),
        # Ch 476
        ("Deep Space Communication Disruption Prediction", "Orbital ephemeris computation of solar conjunction blackout geometry and occultation.", 476.1, ["SEP_angle = acos((r_sun . r_earth) / (|r_sun| |r_earth|))", "Blackout_SEP_limit = 2.5 deg"]),
        ("Autonomous Hibernation & Wakeup Sequencing", "Multi-month micro-power dormancy during quiet cruise with autonomous fault triggers.", 476.2, ["P_hibernation <= 14.5 W", "Reboot_sequence_time <= 180 s"]),
        ("Thermal Gradient Transient Protection Near Perihelion", "Active louvers and heat pipe management under solar irradiance swings ($> 2600 W/m^2$).", 476.3, ["T_bus_max <= 45.0 C", "Heat_rejection_capacity >= 800 W"]),
        # Ch 477
        ("Autonomous Optical Navigation (AutoNav) Image Pipeline", "Feature-based optical tracking of target planet satellites (Phobos/Deimos, Io/Europa).", 477.1, ["Residual_pixel_rms <= 0.05", "Outlier_rejection_method = RANSAC_3D"]),
        ("Ephemeris Uncertainty Covariance Propagation", "Extended Kalman Filter with state error transition matrix Phi(t, t_0) over long baselines.", 477.2, ["P(t) = Phi * P_0 * Phi^T + Q", "Covariance_trace_bound <= 100 km^2"]),
        ("Autonomous Rendezvous Orbit Phasing Dynamics", "Clohessy-Wiltshire relative motion control for secondary probe interception.", 477.3, ["x_ddot - 2 n y_dot - 3 n^2 x = f_x", "y_ddot + 2 n x_dot = f_y"]),
        # Ch 478
        ("Hardware Fault Isolation During High-g Burn Phases", "Sensor voting and thruster quad failover in under 20 ms during critical burns.", 478.1, ["T_switchover <= 18 ms", "Overpressure_valve_trip = 35.0 bar"]),
        ("Radiation Belt Penetration Hardening Verification", "Total Ionizing Dose (TID) mitigation and single-event latchup (SEL) current clamps.", 478.2, ["TID_tolerance >= 300 krad", "SEL_clamp_speed <= 1.5 us"]),
        ("Autonomous Solar Array Articulation Under High Dynamic Pressure", "Array feathering and feather-lock engagements prior to atmospheric contact.", 478.3, ["Lock_engagement_force >= 450 N", "Feather_angle_tolerance <= 0.5 deg"]),
        # Ch 479
        ("Autonomous Science Data Prioritization for Downlink", "Onboard deep-learning novelty classification filtering high-value flyby imagery.", 479.1, ["Priority_metric = Novelty_score * Compression_ratio", "Buffer_management = PRIORITY_QUEUE"]),
        ("Cross-Mission Relativistic Reference Standards", "Standardization against Barycentric Dynamical Time (TDB) and ICRF3 celestial frame.", 479.2, ["ICRF3_alignment_error <= 10 nrad", "Time_standard = TDB_CLOCK"]),
        ("Level 6 Interplanetary Verification Invariants", "Formal mathematical invariants certifying complete autonomous interplanetary injection.", 479.3, ["INV_PERIAPSIS_SAFE = r_p > r_crit", "INV_FUEL_RESERVE = m_prop >= m_margin"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Relativistic & Interplanetary Invariance', 'latex': eq[0], 'vars': eq[1]}]))

    # Pages 34-37
    pages.append(create_page(
        title="Verification & Validation Matrix — Part 38",
        lead="Comprehensive compliance matrix for Part 38 Interplanetary Autonomy and Relativistic Navigation.",
        table=[
            ["Req ID", "Specification Element", "Compliance Method", "Margin / Status"],
            ["REQ-38-01", "Post-Newtonian Gravitational Propagator", "Numerical Symplectic Integration", "Pass (< 1.2 m/AU)"],
            ["REQ-38-02", "X-Ray Pulsar Timing (XNAV)", "Phase Matching & TOA Fold", "Pass (< 0.5 km 3D)"],
            ["REQ-38-03", "Autonomous Aerocapture Guidance", "Bank-Angle Predictor-Corrector", "Pass (0.05 deg corridor)"],
            ["REQ-38-04", "Shapiro Light Delay Correction", "Relativistic Frame Transform", "Pass (< 15 ns residual)"],
            ["REQ-38-05", "B-Plane Trajectory Targeting", "Differential Corrector TCM", "Pass (< 2.0 km miss)"],
            ["REQ-38-06", "High-TID Avionics Resilience", "Hardware Radiation Clamps", "Pass (> 300 krad)"]
        ],
        col_widths=[75, 175, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 38",
        lead="Exact analytical proofs governing relativistic light deflection and trajectory stability.",
        equations=[
            {'id': '38.INV.1', 'label': 'Relativistic Light Bending Metric', 'latex': 'Delta_theta = 4 G M / (c^2 b) * (1 + cos(chi)) / 2', 'vars': 'Gravitational deflection angle around massive solar/planetary body.'},
            {'id': '38.INV.2', 'label': 'Lyapunov Aerocapture Energy Depletion', 'latex': 'V_energy(t) = 0.5 * (E(t) - E_target)^2 -> dV/dt = -k_gain * (E - E_target) * rho v^3', 'vars': 'Asymptotic convergence to target capture orbit without exit skip-out.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 38",
        lead="Fail-safe mechanisms enforcing prototype safeguards and uncrewed autonomous integrity.",
        items=[
            {'heading': 'Trajectory Lock', 'text': 'Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False in all telemetry records.'},
            {'heading': 'Hyperbolic Skip Safeguard', 'text': 'Autonomous aerocapture guidance automatically commands max lift-down if drag depletion profile lags target by > 4.5%.'},
            {'heading': 'Solar Pointing Attitude Lock', 'text': 'In any anomalous FDIR safing event, vehicle reverts immediately to Sun-pointing safe mode preserving power and thermal stability.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 38",
        lead="Formal documentation standard conformance and cryptographic integrity record.",
        table=[
            ["Standard", "Description", "Conformance Status"],
            ["NASA-STD-7009A", "Standard for Models and Simulations", "Fully Compliant"],
            ["CCSDS 502.0-B-2", "Orbit Data Messages (OEM / OMM)", "Fully Compliant"],
            ["AIAA G-043A", "Guide to the Practice of Space Flight Safety", "Fully Compliant"]
        ],
        col_widths=[110, 240, 154]
    ))
    return {'vol_num': 38, 'doc_id': 'APPS-L6-VOL-38-RELATIVISTIC-NAV', 'title': 'Interplanetary Autonomy & Relativistic Navigation', 'subtitle': 'Relativistic Trajectory Propagation, X-Ray Pulsar Timing (XNAV) & Closed-Loop Aerocapture', 'pages': pages}


# =============================================================================
# VOLUME 2 (PART 39): PERMANENT LUNAR SOUTH POLE INFRASTRUCTURE
# =============================================================================
def get_volume_39_data():
    pages = []
    pages.append({'summary': 'Specifies autonomous civil engineering, permanently shadowed region (PSR) cryogenic ice mining, megawatt fission micro-grids, and thermal wadi energy storage at Shackleton Crater.'})
    pages.append(create_page(
        title="Executive Summary & Lunar Infrastructure Architecture Rung 6",
        lead="Establishes Level 6 autonomous infrastructure deployment at Lunar South Pole permanently shadowed craters (40 K).",
        ch_num=480,
        items=[
            {'heading': 'Extreme Cold Mining', 'text': 'Continuous autonomous excavation of water ice regolith inside 40 K permanently shadowed regions without direct solar illumination.'},
            {'heading': 'Fission Micro-Grid', 'text': 'Autonomous dispatch of 1.2 MW thermal Stirling fission surface power with high-voltage DC distribution.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False.'}
        ],
        table=[
            ["Subsystem", "Operational Technology", "Design Capacity", "Environment"],
            ["PSR Ice Harvester", "Pneumatic Fluidized Auger", "450 kg ice/sol", "Permanently Shadowed (40 K)"],
            ["Power Transmission", "10 kV SiC Solid-State HVDC", "1.2 MW continuous", "Lunar Vacuum & Dust"],
            ["Thermal Wadi", "Regolith Sintered Heat Well", "25 kWh thermal storage", "14-Day Lunar Night"]
        ]
    ))
    pages.append({'title': 'Table of Contents'})

    p_defs = [
        ("Permanently Shadowed Region (PSR) Ice Cryo-Mining", "Pneumatic and auger harvesting in 40 K cryogenic ultra-hard water ice regolith.", 480.1, ["Yield_ice = m_regolith * f_ice * eta_harvest", "tau_shear_40K = 4.2 MPa"]),
        ("Pneumatic Fluidized Regolith Extraction Dynamics", "Gas-assisted particle suspension conveying ice grains without mechanical jamming.", 480.2, ["v_fluidize = sqrt(d_p * g_luna * (rho_p - rho_gas) / rho_gas)", "Gas_recycle_ratio >= 0.96"]),
        ("Cryogenic Lubricant-Free Magnetic Bearings", "Active magnetic levitation bearings operating reliably in vacuum at 40 K without grease.", 480.3, ["F_mag = B^2 * A_pole / (2 mu_0)", "Power_levitation <= 25 W"]),
        ("Megawatt Fission Surface Power Autonomous Dispatch", "Stirling cycle closed-loop power generation balancing mining, sintering, and life-support.", 481.1, ["P_elec = eta_stirling * Q_reactor", "eta_stirling >= 0.32 @ 1100 K"]),
        ("Solid-State 10 kV HVDC Grid Intertie & Switching", "High-voltage direct current power beaming and transmission lines across crater rims.", 481.2, ["P_loss = I^2 * R_cable", "V_distribution = 10000 V", "Switching_efficiency >= 0.992"]),
        ("Thermal Wadi Phase Change Energy Reservoirs", "Concentrated solar sintered basalt thermal capacitors buffering lunar night survival heat.", 481.3, ["Q_stored = m_basalt * c_p * Delta_T", "T_wadi_core >= 650 C"]),
        ("Autonomous Landing Pad Civil Blast Protection Walls", "Robotic sintering and interlocking brick construction for rocket launch plume deflection.", 482.1, ["H_berm >= 4.5 m", "Compressive_strength >= 45 MPa"]),
        ("Microwave Sintering Horn Resonator Multi-Kilowatt Array", "2.45 GHz multi-magnetron phased array heating regolith to solid-state necking.", 482.2, ["P_dep = 2 * pi * f * epsilon_0 * epsilon_r'' * |E|^2", "Depth_penetration_cm = 12.5"]),
        ("Sulfur Concrete & In-Situ Basalt Extrusion 3D Printing", "Waterless concrete binder synthesis utilizing volatile sulfur extracted from regolith.", 482.3, ["Sigma_compressive = 38.0 MPa", "Setting_time_min <= 20 min"]),
        ("Crater Rim Tower Optical Power & Comm Relays", "200-meter telescopic masts positioned on peaks of eternal light (PEL) catching continuous sun.", 483.1, ["Illumination_fraction >= 0.92", "Laser_beaming_power = 25 kW"]),
        ("Direct-to-Earth High-Bandwidth Lunar Lasercom Link", "Multi-gigabit optical transceivers providing continuous broadband backhaul to Earth.", 483.2, ["Data_rate_gbps = 10.0", "Wavelength = 1550 nm"]),
        ("Crater Rim Tether Cable Car Material Transport", "Automated gravity-assist funicular hauling ice payloads from crater floor to rim.", 483.3, ["Payload_capacity = 2500 kg", "Cable_tension_safety >= 3.5"]),
        ("Cryogenic Volatile Distillation & Hydrogen Liquefaction", "Multi-stage fractionation separating H2O, CO2, NH3, and CH4 from PSR volatiles.", 484.1, ["Purity_H2O >= 0.999", "T_condense_CO2 = 145 K"]),
        ("Electrolysis Plant Oxygen & Hydrogen Cryo-Storage", "Proton Exchange Membrane (PEM) water electrolysis producing LOX/LH2 propellant.", 484.2, ["m_O2_rate = 1.2 kg/hr", "Electrolysis_efficiency >= 0.82"]),
        ("High-Pressure Propellant Depot Zero-Boil-Off (ZBO)", "Pulse-tube active cryo-coolers maintaining liquid hydrogen below 20 K with zero vent.", 484.3, ["Q_lift_20K >= 15 W", "Boiloff_rate = 0.0 %/day"]),
        ("Autonomous Excavator Fleet Fleet-Wide Battery Swapping", "Hermetic automated battery hot-swap stations deployed across mining haul routes.", 485.1, ["Swap_time_s <= 90 s", "Latching_cycles >= 10000"]),
        ("Lunar Dust Mitigation Active Electrostatic Curtains", "Dynamic multiphase traveling electrostatic fields repelling fine charged abrasive dust.", 485.2, ["Dust_removal_efficiency >= 0.98", "V_phase = 2.5 kV"]),
        ("Ultrasonic Dust Vibration Cleaning for Solar Arrays", "High-frequency piezoceramic transducers dislodging sub-micron regolith particles.", 485.3, ["f_ultrasonic = 28 kHz", "Cleanliness_recovery >= 0.95"]),
        ("Autonomous Soil Compaction Dynamic Cone Penetrometry", "Real-time geotechnical bearing capacity mapping along heavy haul roads.", 486.1, ["CBR_rating >= 85", "Bearing_capacity >= 350 kPa"]),
        ("Crater Wall Geotechnical Stability & Rockfall Sentinels", "Distributed seismic and tilt sensors detecting slope failures and crater wall slumps.", 486.2, ["sigma_seismic = 1e-9 m/s^2", "Alert_latency <= 250 ms"]),
        ("Sub-Surface Cavity Mapping with Ground Penetrating Radar", "Multi-frequency GPR scanning for buried lava tubes and voids beneath landing pads.", 486.3, ["Depth_resolution_cm = 5.0", "Max_penetration_depth_m = 45.0"]),
        ("Lunar Gateway High-Rate Rendezvous Telemetry", "Autonomous UHF and Ka-band orbital tracking of arriving crew and cargo landers.", 487.1, ["Acquisition_range_km = 1200", "Tracking_jitter_deg <= 0.02"]),
        ("Autonomous Beacon Transponders for Precision Touchdown", "Surface pseudo-satellite (Pseudolite) constellation delivering sub-meter landing fixes.", 487.2, ["Positioning_accuracy_m <= 0.35", "Constellation_nodes = 4"]),
        ("Emergency Propellant Dump & Flare-Off Automation", "High-speed pyrotechnic venting system safely isolating cryogenic tanks upon breach.", 487.3, ["Vent_dump_time_s <= 45 s", "Ignition_suppression_verified = True"]),
        ("Autonomous Life Support Closed-Loop Water Recovery", "Vapor compression distillation recycling 98% of human and industrial graywater.", 488.1, ["Recovery_fraction >= 0.98", "TDS_effluent_ppm <= 10"]),
        ("Algae Photobioreactor Oxygen Generation Integration", "Automated cultivation of Chlorella algae utilizing waste CO2 and LED lighting.", 488.2, ["O2_yield_L_day = 550", "Biomass_production_rate_g = 120"]),
        ("Radiation Storm Shelter Regolith Shielding Deployment", "Robotic earthmoving stacking 3.5 meters of regolith over habitat pressure vessels.", 488.3, ["Shielding_depth_m = 3.5", "GCR_dose_reduction >= 0.88"]),
        ("Civil Infrastructure Long-Sol Degradation Tracking", "Acoustic emission and fiber-optic strain monitoring across sintered launch pads.", 489.1, ["Strain_precision_microstrain = 1.0", "Microcrack_detection_mm <= 0.5"]),
        ("Human Habitat Autonomous Life-Support Handover", "Seamless transfer of environmental controls between autonomous and crewed modes.", 489.2, ["Handover_time_s <= 5.0", "Zero_interruption_verified = True"]),
        ("Level 6 Lunar Infrastructure Verification Invariants", "Formal mathematical invariants ensuring permanent base civil stability.", 489.3, ["INV_GRID_STABILITY = P_gen >= P_demand * 1.25", "INV_ICE_STOCK = M_ice >= M_survival"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Lunar Infrastructure Invariance', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 39",
        lead="Compliance matrix for Part 39 Lunar South Pole Infrastructure.",
        table=[
            ["Req ID", "Element", "Method", "Margin"],
            ["REQ-39-01", "PSR Ice Extraction Yield", "Auger Thermal Batch Run", "Pass (> 450 kg/sol)"],
            ["REQ-39-02", "10 kV HVDC Grid Transmission", "Solid-State Switched Test", "Pass (1.2 MW continuous)"],
            ["REQ-39-03", "Microwave Sintered Pad Strength", "Compressive Core Crush", "Pass (> 45 MPa)"],
            ["REQ-39-04", "Active Electrostatic Dust Removal", "Dust Exposure Test", "Pass (> 98% removal)"],
            ["REQ-39-05", "ZBO Propellant Storage", "Pulse-Tube Cryo-Chamber", "Pass (0.0% vent/day)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 39",
        lead="Analytical models for cryogenic regolith mechanics and thermal wadi heat capacity.",
        equations=[
            {'id': '39.INV.1', 'label': 'Thermal Wadi Storage Equation', 'latex': 'E_th = rho * V * c_p * (T_hot - T_cold) * exp(-k_loss * t)', 'vars': 'Heat retention in sintered regolith core over 354-hour lunar night.'},
            {'id': '39.INV.2', 'label': 'Cryogenic Regolith Shear Strength', 'latex': 'tau_failure = c_0(T) + sigma_normal * tan(phi_friction) * (1 + beta_ice * w_ice)', 'vars': 'Cohesion enhancement at 40 K as a function of interstitial ice fraction.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 39",
        lead="Safety locks protecting multi-rover civil infrastructure and power grids.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Grid Overload Trip', 'text': 'Solid-state HVDC breakers isolate faulty mining sectors in < 25 microseconds upon overcurrent.'},
            {'heading': 'Cryo-Auger Thermal Guard', 'text': 'Melt-head heaters automatically disable if temperature exceeds 220 K to avoid steam geyser eruptions.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 39",
        lead="Standards conformance for permanent space civil construction.",
        table=[
            ["Standard", "Description", "Status"],
            ["AIAA S-102.2.4", "Space Systems - Power Systems Safety", "Compliant"],
            ["NASA-STD-3001", "Space Flight Human-System Standard", "Compliant"],
            ["IEEE 1547", "Interconnecting Distributed Energy Resources", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 39, 'doc_id': 'APPS-L6-VOL-39-LUNAR-BASE', 'title': 'Lunar South Pole Infrastructure & Cryo-Grids', 'subtitle': 'Permanently Shadowed Region Ice Harvesting, Fission Megawatt Micro-Grids & Thermal Wadis', 'pages': pages}


# =============================================================================
# VOLUME 3 (PART 40): TITAN CRYOGENIC NAUTICAL & ATMOSPHERIC EXPLORATION
# =============================================================================
def get_volume_40_data():
    pages = []
    pages.append({'summary': 'Specifies autonomous liquid methane/ethane nautical submersibles, cryogenic bathymetry, dense nitrogen atmosphere autorotation, and hybrid aero-amphibious robotics on Titan.'})
    pages.append(create_page(
        title="Executive Summary & Titan Exploration Rung 6",
        lead="Establishes Level 6 autonomous amphibious and nautical robotics exploring Titan Kraken Mare (94 K).",
        ch_num=490,
        items=[
            {'heading': 'Nautical Submersible', 'text': 'Buoyancy-controlled submarine exploring liquid methane/ethane seas (depths up to 300 meters).'},
            {'heading': 'Cryogenic Acoustic Bathymetry', 'text': 'Acoustic sounder mapping sea floor composition and dissolved nitrogen bubble effervescence.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False.'}
        ],
        table=[
            ["Exploration Mode", "Vehicle Class", "Primary Domain", "Operating Temperature"],
            ["Nautical Submersible", "Liquid Methane Sub", "Kraken / Ligeia Mare", "94 K (-179 C)"],
            ["Aero-Amphibious", "VTOL Tilt-Rotor Drone", "Dense N2 Atmosphere (1.5 bar)", "90 K to 95 K"],
            ["Shoreline Crawler", "Paddle-Wheel Amphibian", "Hydrocarbon Mud Flats", "94 K"]
        ]
    ))
    pages.append({'title': 'Table of Contents'})

    p_defs = [
        ("Liquid Methane/Ethane Fluid Dynamics (94 K)", "Hydrodynamics in binary liquid hydrocarbon mixture: viscosity, surface tension, and speed of sound.", 490.1, ["rho_liquid = x_CH4 * rho_CH4 + x_C2H6 * rho_C2H6", "c_sound_94K = 1420 m/s"]),
        ("Autonomous Buoyancy Engine & Ballast Piston", "Variable-volume metal bellows adjusting displacement in varying density seas.", 490.2, ["Delta_B = g_titan * (rho_fluid * Delta_V - m_ballast)", "Depth_rate_mps = 0.25"]),
        ("Effervescence & Cavitation Bubble Nucleation", "Predicting dissolved nitrogen gas exsolution around propellers and active thermal heads.", 490.3, ["P_bubble = P_ambient - P_vapor - P_N2_dissolved", "Cavitation_margin >= 1.45"]),
        ("Acoustic Echo Sounding & Bottom Bathymetry", "Multi-beam sonar profiling hydrocarbon seabed topography through cryogenic liquids.", 491.1, ["z_seabed = c_sound * t_echo / 2", "Bathymetry_resolution_m <= 0.15"]),
        ("Sub-Surface Hydrocarbon Current Profiling (ADCP)", "Acoustic Doppler Current Profiler measuring convective tides and wind-driven drift.", 491.2, ["v_current = (Delta_f / f_0) * c_sound / (2 * cos(theta))", "Current_accuracy_cm_s <= 0.5"]),
        ("Chemical Stratification & Halocline Identification", "Continuous refractive index and conductivity profiling detecting methane-rich surface layers.", 491.3, ["dn/dT = -0.00065 K^-1", "Layer_boundary_precision_m <= 0.20"]),
        ("Dense Nitrogen Atmospheric Rotor Aerodynamics", "Hover and forward flight dynamics in 4.5x Earth air density and 0.14g gravity.", 492.1, ["T_rotor = C_T * rho_atm * A * (omega R)^2", "Hover_power_ratio = 0.08 x Earth"]),
        ("Autorotation Descent & Wind Gust Gust-Locking", "Safe engine-out autorotative gliding through thick cryogenic atmospheric columns.", 492.2, ["v_descent = sqrt(W / (0.5 * rho_atm * S * C_D))", "v_touchdown <= 1.2 m/s"]),
        ("Autonomous Methane Rain & Storm Detection", "Millimeter-wave radar detecting liquid methane precipitation downpours and convective squalls.", 492.3, ["Radar_reflectivity_Z = sum D_drop^6", "Rain_avoidance_range_km >= 15.0"]),
        ("Shoreline Beaching & Amphibious Transitions", "Autonomous egress from open sea onto slippery organic tholin mud beaches.", 493.1, ["mu_tholin_mud = 0.18", "Traction_mode = PADDLE_LUG"]),
        ("Tholin Sludge Rheology & Wheel Flotation", "Viscoplastic Bingham plastic modeling of organic dune and sediment deposits.", 493.2, ["tau = tau_yield + mu_plastic * gamma_dot", "Sinkage_margin >= 35 %"]),
        ("Autonomous Sample Piercing Core Drill on Frozen Organics", "Rotary-percussive sampling of cryogenic hydrocarbon ice bedrock.", 493.3, ["Penetration_rate_cm_min = 2.5", "Core_integrity >= 0.95"]),
        ("Cryogenic Radioisotope Stirling Generator (SRG) Heat Integration", "Thermal management redirecting Stirling waste heat to prevent internal electronics freezing.", 494.1, ["Q_waste_W = 250.0", "Internal_temp_C >= -20.0"]),
        ("Closed-Loop Inert Gas Purge System", "Positive pressure nitrogen blanket preventing combustible or explosive liquid ingress.", 494.2, ["P_internal = P_ambient + 0.15 bar", "Purge_gas_leakage <= 0.05 sccm"]),
        ("Liquid Hydrocarbon Turbogenerator Harvesting", "Auxiliary flow turbine generating electrical power from underwater tidal currents.", 494.3, ["P_hydro = 0.5 * rho * v^3 * A_rotor * C_p", "C_p_eff >= 0.38"]),
        ("Multi-Agent Aerobot & Nautical Sub Cooperative Mapping", "Aerial rotorcraft relaying GPS-like acoustic positioning beacons to submerged sub.", 495.1, ["USBL_accuracy_m <= 0.85", "Acoustic_link_kbps = 9.6"]),
        ("Autonomous Sea Surface Optical Slicks & Foam Detection", "Multispectral cameras identifying floating solid organics and atmospheric haze reflections.", 495.2, ["Polarization_contrast >= 0.42", "Detection_range_m = 500"]),
        ("Seafloor Organic Sediment Core Recovery", "Core catcher retaining ultra-volatile sediments during ascent to surface robot.", 495.3, ["Volatile_loss <= 0.5 %", "Sample_mass_g = 150.0"]),
        ("Underwater Optical Communication Attenuation", "Blue-green LED optical modem transmitting through ultra-clear liquid methane.", 496.1, ["alpha_attenuation = 0.015 m^-1 @ 470 nm", "Data_rate_mbps = 5.0 @ 25 m"]),
        ("Sub-Surface Emergency Positive Buoyancy Blowout", "Pyrotechnic chemical gas generator inflating external float for rapid emergency surface return.", 496.2, ["T_ascent_surface_s <= 35 s", "Max_depth_m = 300"]),
        ("Autonomous Navigation Along Complex Fjord Coastlines", "Sonar contour following preventing hull grounding against steep drowned river canyons.", 496.3, ["Clearance_distance_m >= 15.0", "Turn_rate_deg_s = 6.0"]),
        ("Cryogenic Hydrocarbon Ice Slush Jamming Alarms", "Thermal and torque sensors detecting frazil ice accretion around control surfaces.", 497.1, ["Accretion_detected = Delta_Torque > 25 %", "De-ice_pulse_power = 80 W"]),
        ("Methane/Ethane Evaporative Cooling Management", "Controlling rapid evaporative chilling upon vehicle atmospheric re-emergence.", 497.2, ["q_evap = h_fg * m_dot_evap", "dT_surface_dt <= 2.5 K/s"]),
        ("Organic Compound Chromatographic Fractionation", "Miniaturized gas chromatograph mass spectrometer (GCMS) analyzing dissolved organics.", 497.3, ["Mass_range_amu = 10 to 650", "Resolution_m_dm >= 1000"]),
        ("Autonomous Atmospheric Profile Sounding Flights", "Vertical spiraling flight collecting temperature, pressure, and wind profiles up to 5 km.", 498.1, ["Altitude_max_km = 5.0", "Climb_rate_mps = 2.0"]),
        ("Cryogenic Rotor De-Icing Ultrasonic Vibration", "Periodic ultrasonic excitation shedding methane condensation from composite blades.", 498.2, ["Shedding_interval_s = 120", "Aero_efficiency_retained >= 0.98"]),
        ("Autonomous Anchor Mooring in Sandy Hydrocarbon Bed", "Compliant harpoon micro-spine anchor securing vehicle against tidal currents.", 498.3, ["Holding_force_N >= 650", "Tether_length_m = 45.0"]),
        ("Long-Horizon Prebiotic Chemical Evolution Surveys", "Systematic searching for prebiotic amino acid precursors in tholin sediments.", 499.1, ["Prebiotic_threshold_ppb = 5.0", "Compound_catalog_size = 120"]),
        ("Earth Deep Space Relay Link Optimization from Titan", "Direct-to-Earth X-band uplink through 3.0-meter steerable high-gain antenna dish.", 499.2, ["Link_margin_db >= 4.5", "EIRP_dbw = 68.5"]),
        ("Level 6 Titan Exploration Verification Invariants", "Formal mathematical invariants ensuring amphibious submersible safety.", 499.3, ["INV_CRYO_SEAL = P_int >= P_ext", "INV_BUOYANCY_SAFE = Depth <= Max_Depth"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Titan Cryogenic Nautical Invariance', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 40",
        lead="Compliance matrix for Part 40 Titan Exploration.",
        table=[
            ["Req ID", "Element", "Method", "Margin"],
            ["REQ-40-01", "Submersible Buoyancy Control", "Hydrostatic Bellows Test", "Pass (0.25 m/s descent)"],
            ["REQ-40-02", "Cryo-Acoustic Bathymetry", "Sonar Sweep at 94 K", "Pass (< 0.15 m resolution)"],
            ["REQ-40-03", "Atmospheric Rotor Aerodynamics", "Cold Nitrogen Chamber", "Pass (0.08x Earth power)"],
            ["REQ-40-04", "Positive Nitrogen Purge Barrier", "Differential Pressure Sensor", "Pass (+0.15 bar delta)"],
            ["REQ-40-05", "Emergency Gas Float Ascent", "Pyrotechnic Deployment", "Pass (< 35 s to surface)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 40",
        lead="Analytical hydrodynamics and atmospheric flight dynamics in cryogenic conditions.",
        equations=[
            {'id': '40.INV.1', 'label': 'Hydrocarbon Sea Hydrostatic Pressure', 'latex': 'P(z) = P_atm + int_0^z rho_liquid(z) * g_titan dz', 'vars': 'Ambient hydrostatic pressure profile down to 300 m in Kraken Mare.'},
            {'id': '40.INV.2', 'label': 'Titan Rotor Dynamic Lift Equilibrium', 'latex': 'L_total = 0.5 * rho_atm * (Omega R)^2 * pi R^2 * sigma * C_l_mean >= m_vehicle * g_titan', 'vars': 'Minimum rotor speed required for stable hover in dense cold nitrogen.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 40",
        lead="Safety locks and fail-safe protocols for Titan planetary exploration.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Cavitation Emergency Safing', 'text': 'Propeller RPM automatically throttles down if acoustic sensors detect dissolved gas cavitation.'},
            {'heading': 'Negative Buoyancy Cutoff', 'text': 'If descent rate exceeds 0.5 m/s, emergency ballast weights are mechanically dropped by solenoid.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 40",
        lead="Standards conformance for extreme planetary robotics.",
        table=[
            ["Standard", "Description", "Status"],
            ["ISO 13628-6", "Subsea Production Control Systems", "Compliant"],
            ["AIAA R-103", "Atmospheric Flight Mechanics", "Compliant"],
            ["ECSS-E-ST-32C", "Structural Materials Handbook", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 40, 'doc_id': 'APPS-L6-VOL-40-TITAN-NAUTICAL', 'title': 'Titan Cryogenic Nautical & Atmospheric Robotics', 'subtitle': 'Liquid Hydrocarbon Submersibles, Cryogenic Acoustic Bathymetry & Dense Nitrogen Flight', 'pages': pages}


# =============================================================================
# VOLUME 4 (PART 41): DEEP CORE SUBSURFACE DRILLING RIG INFRASTRUCTURE
# =============================================================================
def get_volume_41_data():
    pages = []
    pages.append({'summary': 'Specifies autonomous kilometer-depth planetary coiled tubing drilling rigs, borehole casing deployment, acoustic mud pulse telemetry, and geophysical rock core retrieval.'})
    pages.append(create_page(
        title="Executive Summary & Deep Planetary Drilling Architecture Rung 6",
        lead="Establishes Level 6 autonomous subsurface drilling infrastructure penetrating 1,000+ meters into planetary crusts.",
        ch_num=500,
        items=[
            {'heading': 'Kilometer-Depth Drilling', 'text': 'Continuous autonomous coiled tubing drill string operations reaching depths $> 1000\text{ m}$.'},
            {'heading': 'Acoustic Mud Pulse Telemetry', 'text': 'Real-time telemetry and borehole logging transmitted via acoustic drill string compression waves.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False.'}
        ],
        table=[
            ["Drilling Subsystem", "Mechanism", "Target Depth", "Power Consumption"],
            ["Coiled Tubing Injector", "Titanium Composite Tubing", "1,000 to 2,500 m", "12.0 kW mechanical"],
            ["Downhole Percussive Bit", "Diamond-Enhanced Carbide", "Deep Igneous Bedrock", "8.5 kW downhole"],
            ["Borehole Telemetry", "Acoustic Drill-String Pulses", "Full Wellbore Length", "45 W telemetry"]
        ]
    ))
    pages.append({'title': 'Table of Contents'})

    p_defs = [
        ("Kilometer-Scale Coiled Tubing Rig Mechanics", "Continuous non-jointed flexible composite drill tubing reel and injector head dynamics.", 500.1, ["Tension_max = sigma_yield * A_tubing", "Inject_speed_mps = 0.05"]),
        ("Weight-on-Bit (WOB) Closed-Loop Autonomic Control", "Dynamic downhole load cell feedback regulating feed thrust preventing tube buckling.", 500.2, ["WOB_optimal = min(WOB_max, k_rock * UCS)", "sigma_WOB <= 150 N"]),
        ("Downhole Percussive Hammer Kinematics", "Pneumatic or electro-hydraulic downhole hammer pulverizing hard basalt and granite.", 500.3, ["f_impact = 45 Hz", "E_blow = 120 J", "ROP_m_hr >= 1.5"]),
        ("Drilling Fluid Circulation & Cuttings Transport", "Supercritical CO2 or compressed N2 circulation carrying cuttings to surface cyclone.", 501.1, ["v_annular >= 2.0 * v_terminal_cuttings", "Pressure_loss_bar <= 85.0"]),
        ("Surface Cyclone Cuttings Separation & Sieve Analysis", "Automated centrifugal separation of cuttings for real-time mineralogical analysis.", 501.2, ["Separation_efficiency >= 0.99", "Particle_size_d50_um = 75"]),
        ("Borehole Wall Collapse & Casing While Drilling (CWD)", "Simultaneous robotic steel/composite casing liner expansion preventing hole collapse.", 501.3, ["Collapse_pressure_bar >= 250", "Casing_expansion_ratio = 1.15"]),
        ("Acoustic Drill String Mud Pulse Telemetry", "High-frequency acoustic compression wave propagation through drill string wall.", 502.1, ["v_acoustic_string = 5100 m/s", "Data_rate_bps = 128", "SNR_db >= 14"]),
        ("Autonomous Downhole Measurement-While-Drilling (MWD)", "Triaxial fluxgate magnetometer and gamma-ray sensor logging geological strata.", 502.2, ["Inclination_accuracy_deg <= 0.1", "Azimuth_accuracy_deg <= 0.25"]),
        ("Borehole Directional Steering & Geo-Steering", "Active push-the-bit rotary steerable system navigating towards deep fault zones.", 502.3, ["Dogleg_severity_deg_30m <= 3.0", "Steering_response_s <= 10"]),
        ("Pressurized Core Barrel Sample Ingress & Latching", "Hermetic downhole sample barrel capturing intact bedrock core under in-situ pressure.", 503.1, ["Core_diameter_mm = 45.0", "Core_length_m = 1.5", "Pressure_retained >= 85 %"]),
        ("Downhole Core Slicing & Diamond Blade Severing", "Automated hydraulic core cutter severing core base before retrieval.", 503.2, ["Severing_torque_Nm = 120", "Cutting_time_min <= 4.0"]),
        ("Wireline Ultra-High-Speed Core Extraction Winch", "Carbon fiber wireline hoisting sample barrel to surface at 2.5 m/s.", 503.3, ["Hoist_speed_mps = 2.5", "Winch_safety_factor >= 4.0"]),
        ("Wellbore Pressure Blowout Preventer (BOP) Subsystem", "Automated shear rams isolating high-pressure subsurface aquifer or volatile gas breaches.", 504.1, ["Closure_time_s <= 1.2", "Pressure_rating_bar = 500.0"]),
        ("Autonomous Kill Mud Weighting & Density Injection", "Dynamic baryte or hematite slurry injection to balance sudden wellbore kicks.", 504.2, ["rho_kill_mud = P_formation / (g * Depth)", "Response_time_s <= 8.0"]),
        ("Gas Flare-Off & Cryogenic Condenser Safeguards", "Controlled combustion or condensation of flammable volatile pockets (CH4, H2S).", 504.3, ["Burner_efficiency >= 0.995", "Emission_monitoring = CONTINUOUS"]),
        ("Geothermal Heat Flux Logging Along Borehole Depth", "Distributed fiber-optic Bragg grating temperature profiling measuring geothermal gradient.", 505.1, ["dT_dz_K_km = 22.5", "Temperature_precision_mK = 5.0"]),
        ("Deep Hydrogeology Hydraulic Conductivity Logging", "Straddle packer injection tests determining bedrock permeability and aquifer yield.", 505.2, ["Conductivity_K_m_s = 1e-8", "Packer_seal_pressure_bar = 80.0"]),
        ("Autonomous Downhole Raman & Optical Micro-Imaging", "Miniaturized sapphire-window optical spectrometer scanning unpolished borehole wall.", 505.3, ["Spectral_resolution_nm = 0.5", "Illumination = 266 nm UV"]),
        ("Drill Bit Wear & Dull Grading Autonomous Diagnostics", "Acoustic signature and rotational torque variance predicting diamond cutter spalling.", 506.1, ["Bit_wear_grade_0_to_8 = 3.2", "Trip_prediction_accuracy >= 0.92"]),
        ("Automated Bit Exchange & Rotary Carousel Magazine", "Surface robotic arm swapping worn drill bits without human intervention.", 506.2, ["Bit_exchange_time_min = 12.0", "Torque_make_up_Nm = 4500"]),
        ("Reaming & Hole Cleaning Hydraulics Optimization", "Automated wiper trips dislodging accumulated debris beds in deviated wells.", 506.3, ["Annular_cleaning_ratio >= 0.95", "Torque_drag_reduction = 35 %"]),
        ("Surface Power Cogeneration from Geothermal Gradient", "Thermoelectric generation harvesting heat differential between borehole and surface.", 507.1, ["P_cogen_W = 450.0", "Delta_T_wellbore_C = 85.0"]),
        ("Micro-Seismic Hydraulic Fracturing Monitoring", "Surface geophone array tracking micro-fracture propagation in deep ice/rock strata.", 507.2, ["Magnitude_detection_limit = -2.5 M", "Location_accuracy_m <= 3.5"]),
        ("Cryogenic Deep Permafrost Drilling Fluid Freezing Prevention", "Electrically heated coiled tubing preventer freezing in -80 C surface permafrost.", 507.3, ["Heat_tracing_power_W_m = 45.0", "Fluid_temp_min_C = +5.0"]),
        ("Multi-Well Pad Drilling & Subsea/Sub-Regolith Spiders", "Skidding rig system drilling cluster of 6 directional wells from single compact pad.", 508.1, ["Skid_traverse_speed_m_hr = 15.0", "Well_spacing_m = 2.5"]),
        ("Autonomous Core Curation & Nitrogen Sealed Packaging", "Surface hermetic glovebox automated packaging under clean room Grade A nitrogen.", 508.2, ["Oxygen_content_ppm <= 0.1", "Sample_container_bar = 1.0"]),
        ("Deep Subsurface Biosphere Sterilization Verification", "PCR and ATP swab logging verifying zero surface organism introduction into deep crust.", 508.3, ["Bioburden_spores_wellbore <= 10", "Category = IV_C_SUBSURFACE"]),
        ("Long-Sol Autonomous Drilling Campaign Executive", "Multi-week supervisory executive orchestrating drilling, tripping, logging, and casing.", 509.1, ["Sol_duration_target = 60 sols", "Autonomy_level = FULL_SUPERVISORY"]),
        ("Drill Rig Wind & Dust Storm Structural Anchoring", "Dynamic guy wire tensioners stabilizing 15-meter mast against 120 km/h Martian gale.", 509.2, ["Guy_wire_tension_N = 12000", "Safety_factor_wind >= 2.5"]),
        ("Level 6 Deep Drilling Verification Invariants", "Formal mathematical invariants ensuring mechanical drill string integrity.", 509.3, ["INV_WELLBORE_INTEGRITY = P_pore < P_frac", "INV_TUBING_FATIGUE = N_cycles < N_endurance"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Deep Drilling Invariance', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 41",
        lead="Compliance matrix for Part 41 Deep Core Drilling Rig Infrastructure.",
        table=[
            ["Req ID", "Element", "Method", "Margin"],
            ["REQ-41-01", "Kilometer Coiled Tubing Rig", "1000m Deep Injection Test", "Pass (> 1000 m reached)"],
            ["REQ-41-02", "Acoustic Mud Pulse Link", "Compression Wave Demodulation", "Pass (128 bps, SNR > 14 dB)"],
            ["REQ-41-03", "Borehole Blowout Preventer", "Emergency Shear Ram Closure", "Pass (< 1.2 s closure)"],
            ["REQ-41-04", "Diamond Bit Wear Prediction", "Acoustic Torque FFT", "Pass (> 92% accuracy)"],
            ["REQ-41-05", "Pressurized Core Hermetic Seal", "Downhole Seal Validation", "Pass (> 85% pressure kept)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 41",
        lead="Governing mechanics for coiled tubing buckling and rock failure dynamics.",
        equations=[
            {'id': '41.INV.1', 'label': 'Coiled Tubing Helical Buckling Limit', 'latex': 'F_helical = 2 * sqrt(E * I * w_submerged * sin(theta) / r_clearance)', 'vars': 'Critical axial compressive force causing tubing helical lockup in wellbore.'},
            {'id': '41.INV.2', 'label': 'Borehole Mud Weight Stability Window', 'latex': 'P_pore(z) < P_mud(z) < P_fracture(z)', 'vars': 'Hydrostatic pressure window preventing both wellbore collapse and hydraulic fracturing.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 41",
        lead="Safety locks and fail-safe protocols for planetary drilling rigs.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Over-Torque Tubing Safeguard', 'text': 'Injector head immediately halts feed if drill string torque exceeds 85% of torsional yield strength.'},
            {'heading': 'Automatic Well Kill Trigger', 'text': 'Mud injection pumps switch to high-density weighted fluid automatically if wellbore influx rate exceeds 5.0 L/min.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 41",
        lead="Standards conformance for deep core drilling infrastructure.",
        table=[
            ["Standard", "Description", "Status"],
            ["API Spec 16D", "Control Systems for Drilling Well Control Equipment", "Compliant"],
            ["API Spec 5ST", "Coiled Tubing Specifications", "Compliant"],
            ["ISO 10423", "Drilling and Production Equipment - Wellhead and Tree", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 41, 'doc_id': 'APPS-L6-VOL-41-DEEP-DRILLING', 'title': 'Deep Core Subsurface Planetary Drilling Rigs', 'subtitle': 'Kilometer-Depth Coiled Tubing Rig Mechanics, Acoustic Mud Pulse Telemetry & Wellbore Control', 'pages': pages}


# =============================================================================
# VOLUME 5 (PART 42): VENUS SUPERCRITICAL ATMOSPHERE & HIGH-TEMP SIC AVIONICS
# =============================================================================
def get_volume_42_data():
    pages = []
    pages.append({'summary': 'Specifies autonomous robotics operating in 465 C / 92 bar supercritical CO2 corrosive atmosphere on Venus, high-temperature SiC avionics, clockwork mechanical computers, and variable-density buoyancy aero-platforms.'})
    pages.append(create_page(
        title="Executive Summary & Venus Extreme Environment Architecture Rung 6",
        lead="Establishes Level 6 autonomous surface and cloud-layer exploration under 465 C and 92 bar supercritical CO2.",
        ch_num=510,
        items=[
            {'heading': 'Extreme Temperature & Pressure', 'text': 'Continuous operation at 465 C and 92 bar supercritical CO2 with sulfuric acid droplets (pH < 0.5).'},
            {'heading': 'Silicon Carbide (SiC) Avionics', 'text': 'High-temperature wide-bandgap SiC JFET microelectronics operating uncooled $> 500\text{ C}$.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False.'}
        ],
        table=[
            ["Subsystem Layer", "Technology", "Temperature Rating", "Pressure Rating"],
            ["Computing & Logic", "Silicon Carbide (SiC) JFET Logic", "500 C continuous", "100 bar vacuum/gas"],
            ["Mechanical Backup", "High-Nickel Inconel Clockwork", "600 C continuous", "200 bar corrosive"],
            ["Atmospheric Buoyancy", "Phase-Change Metal Bellows Balloon", "465 C surface to 20 C cloud", "92 bar to 0.5 bar"]
        ]
    ))
    pages.append({'title': 'Table of Contents'})

    p_defs = [
        ("Supercritical CO2 Fluid Thermodynamics (465 C, 92 bar)", "Equation of state, dense gas properties, high Reynolds numbers, and thermal buoyancy.", 510.1, ["rho_sc_CO2 = 67.0 kg/m^3 @ surface", "mu_visc = 3.2e-5 Pa s", "Re >= 5e6"]),
        ("Sulfuric Acid Mist Corrosion & Protective Barrier Coatings", "Tantalum, gold-platinum plating, and chemical vapor deposited Si3N4 anti-corrosion barriers.", 510.2, ["Corrosion_rate_Ta <= 0.001 mm/yr", "pH_droplet = 0.1"]),
        ("High-Temperature Wide-Bandgap Silicon Carbide (SiC) JFETs", "500 C operational logic gates, operational amplifiers, and clock oscillators.", 510.3, ["Bandgap_SiC_4H = 3.26 eV", "Leakage_current <= 10 nA @ 500 C"]),
        ("Clockwork Mechanical Computer Logic (Automaton Rover)", "Pure mechanical planetary gears, differential analyzers, and fluidic logic gates.", 511.1, ["Logic_frequency_Hz = 10", "Material = Inconel 718", "Lubrication = WS2 / MoS2"]),
        ("High-Temperature Solid-State Non-Volatile Memory", "Ferroelectric or magnetic tunnel junction memory retaining bits at 500 C.", 511.2, ["Retention_years >= 10 @ 500 C", "Write_cycles >= 1e8"]),
        ("Pneumatic & Fluidic Jet Logic Actuation", "Supercritical atmospheric gas diverted through Coanda effect amplifiers.", 511.3, ["Switching_time_ms = 4.5", "Supply_pressure_bar = 95.0"]),
        ("Phase-Change Liquid Metal Thermal Energy Buffering", "Lithium hydride (LiH) heat sinks absorbing latent heat during surface dwell.", 512.1, ["L_fusion_LiH = 2.8 MJ/kg", "T_melt = 688 C", "Buffer_duration_hr = 4.5"]),
        ("Active Thermo-Acoustic Stirling Cryo-Cooling (500 C Sink)", "Heat engine driving refrigeration loop rejecting heat into 465 C environment.", 512.2, ["COP_cooling = 0.045", "Cold_tip_temp_C = 250 C"]),
        ("Aerodynamic Drag & Parachute Sizing in 67 kg/m^3 Gas", "Subsonic aerodynamic decelerators in dense supercritical gas columns.", 512.3, ["Terminal_velocity_mps = 3.5", "Parachute_diameter_m = 2.2"]),
        ("Venus Variable Altitude Balloon (Aerobot) Cycling", "Helium/bellows buoyancy vehicle oscillating between 55 km clouds (25 C) and surface.", 513.1, ["Altitude_range_km = 0 to 65", "Cycle_period_hr = 18.0"]),
        ("High-Temperature Balloon Envelope Permeation Barriers", "Fluoropolymer and metallized polyimide films resisting sulfuric acid permeation.", 513.2, ["He_loss_rate_pct_day <= 0.05", "Tensile_strength_MPa >= 180"]),
        ("Sulfuric Acid Atmospheric Cloud Water Harvesting", "Condensation traps collecting atmospheric H2SO4 for catalytic splitting into H2O and SO3.", 513.3, ["Collection_rate_L_day = 12.0", "Catalyst = Platinum/TiO2"]),
        ("Supercritical Gas Turbine Electric Power Generation", "Surface wind turbine generating continuous electrical power from 1.0 m/s dense winds.", 514.1, ["P_wind = 0.5 * 67.0 * 1.0^3 * A * C_p", "P_elec_W = 120.0 @ 1.2 m/s"]),
        ("High-Temperature Solid Oxide Fuel Cells (SOFC)", "Operating at 500 C directly utilizing atmospheric CO2 and stored methane fuel.", 514.2, ["Cell_voltage = 0.85 V", "Current_density = 450 mA/cm^2"]),
        ("Pyroelectric & Thermoelectric Energy Harvesting", "Harvesting diurnal temperature variations during altitude ascents/descents.", 514.3, ["P_TEG = (alpha * Delta_T)^2 / (4 R)", "Efficiency_pct = 7.5"]),
        ("Direct-to-Earth S-Band Synthetic Aperture Radar (SAR)", "High-temperature phased array radar piercing dense atmosphere for Earth downlink.", 515.1, ["Frequency_GHz = 2.3", "EIRP_dBW = 42.0", "Penetration_depth = 100%"]),
        ("Optical Lidar Atmospheric Window Navigation", "Near-infrared (1.0 um) lidar mapping surface topography through atmospheric haze.", 515.2, ["Wavelength_um = 1.05", "Max_range_km = 8.5"]),
        ("Infrasound Seismic Wave Planetary Interior Profiling", "Micro-barometers floating in cloud layers detecting Venusian quakes via atmospheric acoustic waves.", 515.3, ["Pressure_sensitivity_uPa = 10.0", "Bandwidth_Hz = 0.01 to 20.0"]),
        ("Autonomous Obstacle Avoidance in 10-Meter Visibility", "Acoustic sonar and thermal infrared imaging navigating zero-contrast basalt plains.", 516.1, ["Sonar_frequency_kHz = 40.0", "Reaction_distance_m = 12.0"]),
        ("High-Temperature Ceramic Capacitive Pressure Sensors", "Micromachined SiC diaphragm transducers measuring 0 to 120 bar without thermal drift.", 516.2, ["Accuracy_pct_FS = 0.05", "Thermal_drift_ppm_C <= 10"]),
        ("Mechanical Stepper Actuators with MoS2 Solid Lubrication", "High-nickel brushless motors operating without organic winding varnishes at 500 C.", 516.3, ["Holding_torque_Nm = 8.5", "Insulation = Ceramic Fiber"]),
        ("Volcanic Vent Autonomous Plume Trajectory Targeting", "Chemical sniffers tracking sulfur dioxide (SO2) spikes to locate active volcanic eruptions.", 517.1, ["SO2_anomaly_detection_ppm = 25.0", "Plume_bearing_deg <= 2.0"]),
        ("Supercritical Fluid Extraction of Surface Minerals", "Utilizing natural supercritical CO2 solvent properties to leach planetary minerals.", 517.2, ["Solubility_heavy_metals = ENHANCED", "Solvent_density_g_cm3 = 0.067"]),
        ("Atmospheric Lightning Discharge Electrostatic Discharge Hardening", "Faraday cage hull and lightning arrestor dissipating 100 kA cloud-to-cloud strikes.", 517.3, ["Peak_current_kA = 100.0", "Hull_voltage_spike_V <= 50.0"]),
        ("Automated Surface Drop Probe Deployment from Aerobot", "Releasing tethered or free-fall probe packages to short-lived high-temperature zones.", 518.1, ["Drop_mass_kg = 25.0", "Impact_attenuation_g <= 35.0"]),
        ("High-Temperature Optical Fiber Gyroscope (FOG)", "Pure silica core polarization-maintaining fiber coils reading yaw rates at 500 C.", 518.2, ["Bias_drift_deg_hr <= 0.05", "Fiber_coating = Polyimide/Metal"]),
        ("Autonomous Altitude Holding via Gas Vent & Ballast Dump", "Bang-bang buoyancy controller maintaining 52 km altitude floating equilibrium.", 518.3, ["Altitude_deadband_m = 50.0", "Valve_cycle_life >= 50000"]),
        ("Planetary Surface Descent Camera Rapid Exposure Profiling", "Ultrafast high-temperature CCD capturing surface images during final descent second.", 519.1, ["Exposure_time_us = 250", "Frame_rate_fps = 60"]),
        ("Long-Sol Autonomous Cloud Platform Fleet Coordination", "Cooperative formation flying of multiple balloons studying global superrotation winds.", 519.2, ["Superrotation_speed_mps = 100.0", "Swarm_coordination_range_km = 2500"]),
        ("Level 6 Venus Exploration Verification Invariants", "Formal mathematical invariants ensuring high-temperature avionics survivability.", 519.3, ["INV_THERMAL_SURVIVAL = T_internal <= 500 C", "INV_PRESSURE_SEAL = P_hull >= P_ext"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Venus Extreme Mechanics Invariance', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 42",
        lead="Compliance matrix for Part 42 Venus Supercritical Atmosphere.",
        table=[
            ["Req ID", "Element", "Method", "Margin"],
            ["REQ-42-01", "SiC JFET 500 C Logic", "Furnace Electrical Operational Run", "Pass (500 C continuous)"],
            ["REQ-42-02", "92 bar Supercritical Seal", "Hyperbaric Chamber Pressure Test", "Pass (120 bar proof)"],
            ["REQ-42-03", "Sulfuric Acid Resistance", "Concentrated H2SO4 Immersion", "Pass (< 0.001 mm/yr)"],
            ["REQ-42-04", "Clockwork Mechanical Backup", "Inconel Differential Spin Test", "Pass (10 Hz nominal)"],
            ["REQ-42-05", "Phase-Change Lithium Hydride", "Calorimetric Thermal Dwell", "Pass (> 4.5 hr buffer)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 42",
        lead="Supercritical fluid equation of state and wide-bandgap electron mobility.",
        equations=[
            {'id': '42.INV.1', 'label': 'Peng-Robinson Supercritical Equation', 'latex': 'P = R T / (V - b_m) - a_m(T) / (V^2 + 2 b_m V - b_m^2)', 'vars': 'CO2 density and compressibility factor under Venusian surface conditions.'},
            {'id': '42.INV.2', 'label': 'Silicon Carbide Intrinsic Carrier Density', 'latex': 'n_i(T) = sqrt(N_c N_v) * exp(-E_g / (2 k_B T))', 'vars': 'Ultra-low intrinsic thermal carrier generation in 4H-SiC at 773 K preventing thermal runaway.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 42",
        lead="Safety locks and fail-safe protocols for Venusian high-temperature platforms.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Thermal Runaway Dump', 'text': 'If internal electronic bay temperature exceeds 515 C, high-pressure helium purge activates immediately.'},
            {'heading': 'Supercritical Corrosive Isolation', 'text': 'Double-walled welded titanium-tantalum seals undergo continuous helium leak detection.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 42",
        lead="Standards conformance for extreme planetary environments.",
        table=[
            ["Standard", "Description", "Status"],
            ["MIL-STD-810H", "Environmental Engineering Considerations", "Compliant"],
            ["ASTM G31", "Laboratory Immersion Corrosion Testing of Metals", "Compliant"],
            ["IEEE 1451.4", "Transducer Electronic Data Sheets", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 42, 'doc_id': 'APPS-L6-VOL-42-VENUS-AVIONICS', 'title': 'Venus Supercritical Atmosphere & SiC Avionics', 'subtitle': '465 C / 92 bar Supercritical CO2 Fluid Mechanics, SiC JFET Avionics & Automaton Robotics', 'pages': pages}
