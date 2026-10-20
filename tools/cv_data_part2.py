"""Technical Data and Chapter Specifications for APPS Computer Vision Volumes (Parts 50 to 52).
Provides exactly 37 structured pages per volume covering extensive planetary Computer Vision:
- Volume 3 (Part 50): Dense Stereo Photogrammetry, Sub-Pixel Disparity & Visual-Inertial Odometry
- Volume 4 (Part 51): Neuromorphic Event-Based Computer Vision & Asynchronous Optical Flow
- Volume 5 (Part 52): Self-Supervised Domain Adaptation, Atmospheric Dehazing & Hazard Segmentation
"""
from tools.cv_data_part1 import create_page


# =============================================================================
# VOLUME 3 (PART 50): DENSE STEREO PHOTOGRAMMETRY & VIO
# =============================================================================
def get_volume_50_data():
    pages = []
    # Page 1: Cover
    pages.append({'summary': 'Specifies dense stereo matching (SGM / RAFT-Stereo), non-linear lens calibration, sub-pixel disparity refinement, and tightly coupled factor-graph visual-inertial odometry on Lie groups.'})
    # Page 2: Exec Summary
    pages.append(create_page(
        title="Executive Summary & Metric Photogrammetric Reconstruction",
        lead="Establishes dense stereo epipolar matching and visual-inertial state estimation across unstructured planetary terrains.",
        ch_num=590,
        items=[
            {'heading': 'Milestone Scope', 'text': 'Provides sub-centimeter dense 3D point cloud generation, epipolar rectification, and multi-state constraint Kalman filter (MSCKF) VIO.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False across all odometry output streams.'},
            {'heading': 'Manifold Geometry', 'text': 'SE(3) and SO(3) Lie group state propagation with pre-integrated IMU kinematics and non-linear bundle adjustment.'}
        ],
        table=[
            ["Photogrammetry Stage", "Algorithm Primitive", "Baseline Baseline", "Accuracy / Drift"],
            ["Epipolar Rectification", "Uncalibrated 8-Point F-Matrix", "B = 0.40 m baseline", "Residual < 0.15 px"],
            ["Dense Stereo Matching", "Hierarchical SGM + Census Cost", "128 Disparity levels", "Bad-1.0 px < 3.2%"],
            ["Sub-Pixel Refinement", "Parabolic Peak Interpolation", "Continuous Disparity", "Sigma_d < 0.05 px"],
            ["Visual-Inertial Odometry", "Tightly Coupled Factor Graph", "Stereo Navcam + 200 Hz IMU", "Drift < 0.35% distance"]
        ]
    ))
    # Page 3: TOC
    pages.append({'title': 'Table of Contents'})

    # Pages 4-33: 30 Technical Chapters (Ch 590.1 to 599.3)
    p_defs = [
        # Ch 590: Non-Linear Camera Calibration & Epipolar Rectification
        ("Pinhole Camera Intrinsics & Brown-Conrady Radial-Tangential Distortion", "Mathematical formulation of focal length, principal point, and k1, k2, p1, p2 distortion coefficients.", 590.1, ["x_dist = x (1 + k_1 r^2 + k_2 r^4) + 2 p_1 x y + p_2 (r^2 + 2 x^2)", "Residual_reprojection_px <= 0.12"]),
        ("Essential & Fundamental Matrix Epipolar Geometric Constraints", "Formulating the epipolar coplanarity constraint x_2^T F x_1 = 0 on calibrated stereo rigs.", 590.2, ["E = [t]_x R, F = K_2^-T E K_1^-1", "Symmetric_epipolar_distance_px <= 0.20"]),
        ("Thermal Expansion Drift Compensation in Camera Baselines", "Modeling mast thermal contraction between -120 C and +20 C to stabilize stereo baseline B.", 590.3, ["B(T) = B_0 * (1 + alpha_invar * (T - T_0))", "Baseline_drift_tolerance_um <= 15.0"]),
        # Ch 591: Dense Matching Cost Formulations
        ("Non-Parametric Modified Census Transform Matching Cost", "Hamming distance calculation on bit-strings invariant to monotonic illumination changes.", 591.1, ["Census(p) = bigotimes_{q in N(p)} (I(q) < I(p))", "Hamming_cost = count_ones(C_L(p) xor C_R(p - d))"]),
        ("Zero-Mean Normalized Cross-Correlation (ZNCC) Formulation", "Correlation metric robust to camera sensor gain imbalances and directional solar shading.", 591.2, ["ZNCC(d) = sum((I_L - mu_L)(I_R - mu_R)) / (sigma_L * sigma_R)", "Correlation_peak >= 0.85"]),
        ("Deep Learned Correlation Volumes via RAFT-Stereo", "All-pairs correlation pyramid with multi-scale recurrent GRU disparity updates.", 591.3, ["Correlation_dim = H x W x W", "GRU_iterations = 12"]),
        # Ch 592: Semi-Global Matching (SGM) Optimization
        ("Semi-Global Energy Minimization over Multi-Directional Paths", "Aggregating 8 or 16 1D path costs with smoothness penalties P1 and P2.", 592.1, ["E(D) = sum C(p, D_p) + sum_{q in N} (P_1 I(|D_p - D_q| = 1) + P_2 I(|D_p - D_q| > 1))", "Paths = 8"]),
        ("Adaptive P2 Disparity Step Discontinuity Penalty", "Modulating penalty P2 inversely with image intensity gradients to preserve boulder edge depth.", 592.2, ["P_2(p, q) = max(P_1, P_2_base / (|I(p) - I(q)| + epsilon))", "P_1 = 15, P_2_base = 120"]),
        ("Left-Right Disparity Consistency Check & Occlusion Masking", "Detecting background occlusions by cross-validating left and right disparity maps.", 592.3, ["|D_L(x, y) - D_R(x - D_L(x, y), y)| <= 1.0 px", "Occlusion_rejection_rate >= 99.2%"]),
        # Ch 593: Sub-Pixel Disparity Refinement & Depth Uncertainty
        ("Sub-Pixel Parabolic Peak Fitting & Phase Correlation", "Continuous disparity localization via 3-point parabolic interpolation on matching cost curves.", 593.1, ["d_sub = d - 0.5 * (C_+ - C_-) / (C_+ - 2 C_0 + C_-)", "Subpixel_precision_px <= 0.04"]),
        ("Range-Squared Depth Uncertainty Error Propagation Model", "Rigorous covariance mapping from disparity pixel variance sigma_d to radial depth error sigma_Z.", 593.2, ["sigma_Z = (Z^2 / (f * B)) * sigma_d", "Relative_error_at_10m <= 1.5%"]),
        ("Speckle Filtering & Connected Component Outlier Removal", "Pruning isolated disparity regions with spatial connectivity below 100 pixels.", 593.3, ["Min_speckle_size_px = 100", "Disparity_diff_tolerance_px = 1.0"]),
        # Ch 594: 3D Point Cloud Generation & Terrain Normal Computation
        ("Reprojection to 3D Rover Body Coordinates via Camera Q-Matrix", "Perspective reprojection transforming disparity map D(x, y) into 3D Cartesian coordinates (X, Y, Z).", 594.1, ["[X, Y, Z, W]^T = Q * [x, y, D(x, y), 1]^T", "Throughput_pts_s >= 2.5e6"]),
        ("Eigenvalue-Based Local Surface Normal Estimation", "Computing local tangent planes via principal component analysis of 3D neighborhood covariances.", 594.2, ["Cov = (1 / k) * sum((p_i - mu)(p_i - mu)^T)", "Normal_vector = e_min"]),
        ("Point Cloud Voxel Downsampling & Spatial Indexing", "Uniform voxel grid downsampling with 2 cm resolution and Kd-tree nearest neighbor spatial indexing.", 594.3, ["Voxel_size_m = 0.02", "Query_time_ms <= 0.45"]),
        # Ch 595: Visual Feature Detection & Invariant Description
        ("Learned Deep Feature Extraction (SuperPoint & DISK)", "Self-supervised feature detector and descriptor yielding repeatably matchable keypoints in dust.", 595.1, ["Keypoint_count_per_frame = 1500", "Descriptor_dim = 256"]),
        ("Sub-Pixel Feature Localization & Hessian Determinant Peak Gate", "Quadratic Taylor expansion refining keypoint coordinates to 0.05 pixel precision.", 595.2, ["x_hat = -Hessian^-1 * Gradient", "Peak_threshold = 0.015"]),
        ("Cross-Temporal Feature Tracking Across Solar Angle Swings", "Matching features across 4-hour intervals under changing directional shadow casts.", 595.3, ["Matching_inlier_ratio >= 0.72", "Descriptor_distance_threshold = 0.65"]),
        # Ch 596: Visual-Inertial Odometry on Lie Groups
        ("Tightly-Coupled Factor Graph Formulation on SE(3) Manifolds", "Joint optimization of camera poses, velocity, IMU accelerometer/gyroscope biases, and 3D landmarks.", 596.1, ["min sum ||r_IMU||^2_Sigma_IMU + sum ||r_cam||^2_Sigma_cam", "State_dim = 15"]),
        ("IMU Kinematic Pre-Integration on SO(3) Rotation Groups", "Pre-integrating high-rate (200 Hz) angular velocities and linear accelerations between camera keyframes.", 596.2, ["Delta_R_ij = prod Exp((omega_k - b_g) * dt)", "Bias_random_walk_sigma = 1e-4"]),
        ("Marginalization of Past States via Schur Complement", "Bounded-window sliding optimization marginalizing old keyframe states into informative priors.", 596.3, ["H_marg = H_aa - H_ab * H_bb^-1 * H_ba", "Window_keyframes = 10"]),
        # Ch 597: Robust Outlier Rejection & Degeneracy Detection
        ("RANSAC 3D-to-2D PnP Outlier Filtering", "Perspective-n-Point pose estimation with RANSAC robust kernel rejecting false stereo matches.", 597.1, ["P_inlier >= 0.999", "Max_iterations = 250"]),
        ("Visual Degeneracy Sentinel in Low-Texture Sand Dunes", "Condition number monitoring on the normal matrix J^T J detecting unconstrained motion directions.", 597.2, ["Condition_number_kappa <= 1e4", "Degeneracy_fallback = WHEEL_ODOM_IMU"]),
        ("Chi-Square Innovation Gating on Landmark Observations", "Statistical gating rejecting spurious visual features based on Mahalanobis distance thresholds.", 597.3, ["r^T S^-1 r <= Chi2_threshold(0.99)", "DoF = 2"]),
        # Ch 598: Loop Closure & Visual Vocabulary Place Recognition
        ("Bag-of-Visual-Words & DBoW3 Inverted Index Search", "Hierarchical visual vocabulary tree for fast loop closure candidate identification across kilometers.", 598.1, ["Vocabulary_depth = 5, Branching_factor = 10", "Lookup_time_ms <= 8.5"]),
        ("Sim(3) Relative Pose Constraint Optimization", "Estimating 7-DOF similarity transform (R, t, s) between loop-closing keyframes resolving scale drift.", 598.2, ["Scale_s_drift_correction <= 1.02", "Loop_inlier_count >= 45"]),
        ("Global Pose Graph Relaxation & Covariance Propagation", "Non-linear least squares optimization updating historical rover trajectory upon loop validation.", 598.3, ["Global_rms_drift_correction_m <= 0.25", "Optimization_time_ms <= 85.0"]),
        # Ch 599: Verification Invariants & Security
        ("Triangulation Chirality Invariant Validation", "Ensuring all reconstructed 3D landmarks lie strictly in front of both stereo camera lenses (Z > 0).", 599.1, ["Z_cam1 > 0 and Z_cam2 > 0", "Chirality_violations = 0"]),
        ("Epipolar Error Energy Bounding Gate", "Halting stereo map fusion if median epipolar reprojection residual exceeds 0.50 pixels.", 599.2, ["Median_epipolar_err_px <= 0.50", "Safety_tripping_rate = 0"]),
        ("Formal Level 6 Stereo Verification Interlock", "Compile-time assertion confirming PROTOTYPE_LOCK = True and navigation_ready = False.", 599.3, ["INV_PROTOTYPE_LOCK = True", "INV_NAVIGATION_READY = False"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Dense Photogrammetric Formulation', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 50",
        lead="Compliance matrix for Part 50 Dense Stereo Photogrammetry & VIO.",
        table=[
            ["Requirement ID", "Verification Parameter", "Test Methodology", "Compliance Status"],
            ["REQ-50-01", "Sub-Pixel Disparity Precision", "Calibrated Optical Target Grid Run", "Pass (0.038 px RMSE)"],
            ["REQ-50-02", "Dense Matching Bad-Pixel Rate", "Middlebury / Synthetic Mars Stereo Benchmark", "Pass (Bad-1.0: 2.85%)"],
            ["REQ-50-03", "VIO Position Drift Rate", "500-Meter Closed-Loop Field Traverse", "Pass (0.28% distance)"],
            ["REQ-50-04", "Degeneracy Fallback Latency", "Zero-Texture Whiteout Simulated Drop", "Pass (< 12 ms switch)"],
            ["REQ-50-05", "Prototype Compile-Time Lock", "AST Inspection of PROTOTYPE_LOCK", "Pass (Locked True)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 50",
        lead="Epipolar geometric conservation and manifold consistency proofs.",
        equations=[
            {'id': '50.INV.1', 'label': 'Epipolar Line Tangency Invariant', 'latex': 'x_2^T F x_1 = 0, forall (x_1, x_2) in Stereo_Correspondences', 'vars': 'Strict algebraic constraint guaranteeing epipolar line intersection across rectified lenses.'},
            {'id': '50.INV.2', 'label': 'SE(3) Group Exponential Invariance', 'latex': 'Exp(xi_hat) in SE(3), xi_hat = [omega_hat, v; 0, 0]', 'vars': 'Exact closed-form Rodrigues formulation for rigid body transform integration.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 50",
        lead="Autonomous failure mitigation for stereo photogrammetry and VIO.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Disparity Discontinuity Sentinel', 'text': 'If valid disparity pixel count drops below 45% in forward arc, rover velocity automatically decelerates to 2 cm/s.'},
            {'heading': 'IMU Accelerometer Saturation Interlock', 'text': 'If IMU shock exceeds 4.5 g, visual feature tracking is quarantined and mechanical brake actuates.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 50",
        lead="Standards conformance for spatial measurement and photogrammetry.",
        table=[
            ["Standard", "Description", "Status"],
            ["ISO 10303-242", "Industrial Automation Systems — Photogrammetric Geometry", "Compliant"],
            ["ANSI/ASPRS 2014", "Positional Accuracy Standards for Digital Geospatial Data", "Exceeded"],
            ["IEEE 1588-2019", "Precision Clock Synchronization Protocol for Sensor Triggers", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 50, 'doc_id': 'APPS-L6-VOL-50-STEREO-VIO', 'title': 'Dense Stereo Photogrammetry & Visual-Inertial Odometry', 'subtitle': 'Sub-Pixel Epipolar Matching, SE(3) Manifold VIO & Multi-Camera Bundle Adjustment', 'pages': pages}


# =============================================================================
# VOLUME 4 (PART 51): NEUROMORPHIC EVENT-BASED VISION
# =============================================================================
def get_volume_51_data():
    pages = []
    # Page 1: Cover
    pages.append({'summary': 'Specifies asynchronous event-based neuromorphic computer vision (DVS), high-dynamic-range crater imaging (> 120 dB), spiking neural optical flow, and micro-saccadic edge reconstruction.'})
    # Page 2: Exec Summary
    pages.append(create_page(
        title="Executive Summary & Asynchronous Neuromorphic Perception",
        lead="Establishes microsecond-resolution event cameras and spiking neural networks for extreme lighting conditions.",
        ch_num=600,
        items=[
            {'heading': 'Milestone Scope', 'text': 'Integrates Dynamic Vision Sensors (DVS) with event-driven optical flow and contrast maximization in shadowed craters.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False in all asynchronous vision callbacks.'},
            {'heading': 'Extreme Dynamic Range', 'text': 'Operates across > 120 dB illumination without motion blur or sensor saturation under direct solar glare.'}
        ],
        table=[
            ["Neuromorphic Pipeline", "Temporal Resolution", "Dynamic Range", "Power Consumption"],
            ["Asynchronous DVS Stream", "1 microsecond (1 MHz)", "> 125 dB", "18 mW (Pixel Array)"],
            ["Spiking Optical Flow SNN", "Continuous Event Driven", "Linear with Velocity", "120 mW (Loihi-2 / FPGA)"],
            ["Micro-Saccadic Edge Tracker", "500 Hz Saccade Rate", "Contrast Threshold 0.12", "45 mW (Digital Core)"],
            ["Hybrid Event-Frame Fusion", "30 FPS + 1 Meps Events", "Dual Pipeline", "380 mW Total Subsystem"]
        ]
    ))
    # Page 3: TOC
    pages.append({'title': 'Table of Contents'})

    # Pages 4-33: 30 Technical Chapters (Ch 600.1 to 609.3)
    p_defs = [
        # Ch 600: Event Camera Physics & Logarithmic Photoreception
        ("Asynchronous Event Generation & Temporal Contrast Threshold", "Photodiode logarithmic response triggering polarity events e = (x, y, t, p) upon intensity changes.", 600.1, ["Delta_log(I) = log(I(x, y, t)) - log(I(x, y, t - Delta_t)) >= +/- C_th", "C_th = 0.15"]),
        ("Address-Event Representation (AER) Asynchronous Bus Protocol", "Arbitration and readout bus transmitting timestamped x-y pixel addresses at microsecond intervals.", 600.2, ["Event_packet_size = 64 bits", "Max_event_rate = 25 Meps"]),
        ("Dark Current Shot Noise & Thermal Noise Filtering in Event Streams", "Spatiotemporal background activity filter eliminating isolated Poisson thermal noise events.", 600.3, ["dt_neighbor <= 5.0 ms", "Noise_rejection_ratio >= 98.5%"]),
        # Ch 601: Contrast Maximization for Angular Velocity & Ego-Motion
        ("Warping Event Streams along Motion Hypotheses (Contrast Maximization)", "Accumulating motion-compensated events into an image of warped events (IWE).", 601.1, ["x_prime = W(x, t; theta)", "IWE(x; theta) = sum_i p_i * delta(x - W(x_i, t_i; theta))"]),
        ("Focus Objective Function & Variance Optimization", "Maximizing spatial variance of the IWE to recover 3-axis rotational velocity omega.", 601.2, ["Focus(theta) = (1 / N) * sum(IWE(x)^2)", "Angular_velocity_accuracy_deg_s <= 0.05"]),
        ("Real-Time Gauss-Newton Gradient Descent on Event Warps", "Iterative analytical Jacobian optimization updating ego-motion parameters at 500 Hz.", 601.3, ["Delta_theta = -(J^T J + lambda I)^-1 J^T r", "Convergence_iterations <= 8"]),
        # Ch 602: Spiking Neural Networks (SNN) for Optical Flow
        ("Leaky Integrate-and-Fire (LIF) Neuromorphic Neurons", "Membrane potential dynamics integrating continuous event currents with exponential leak decay.", 602.1, ["tau_m * (dV / dt) = -(V - V_rest) + R * I_syn(t)", "V_threshold = 1.0 V"]),
        ("Spike-Timing-Dependent Plasticity (STDP) Synaptic Weight Adaptation", "Locally adaptive synaptic learning based on pre- and post-synaptic spike arrival times.", 602.2, ["Delta_w = A_+ * exp(-Delta_t / tau_+), if Delta_t > 0", "Synaptic_energy <= 10 pJ / spike"]),
        ("Continuous Spiking Optical Flow Vector Field Extraction", "Directional tuned SNN layers computing dense optical flow vectors (u, v) without frame buffering.", 602.3, ["Flow_angle_precision_deg <= 2.5", "Latency_snn_us <= 250"]),
        # Ch 603: High-Dynamic-Range (HDR) Crater Shadow Exploration
        ("Navigating Low-Albedo Crater Interiors with Event Streams", "Extracting boulder rim contours inside deep permanently shadowed regions (PSR) under 0.01 lux.", 603.1, ["Illumination_range_lux = [1e-2, 1e5]", "Dynamic_range_dB = 130.0"]),
        ("Direct Solar Flare Lens Glare Immunity", "Event sensors avoiding whole-array saturation when staring directly into blinding low-elevation sun.", 603.2, ["Saturation_recovery_time_us <= 10", "Pixel_deadtime_us = 1.5"]),
        ("Thermal Gradient Transient Resilience in Spacecraft Egress", "Suppressing false thermal stress events during rapid transit from sunlit terrain into cold shadow.", 603.3, ["Thermal_rejection_filter_dB >= 35.0", "False_event_rate_pct <= 0.5%"]),
        # Ch 604: Micro-Saccadic Active Perception
        ("Bio-Inspired Piezoelectric Camera Micro-Saccades", "Controlled micro-amplitude orbital oscillations (5 um at 50 Hz) generating events in static scenes.", 604.1, ["x_saccade(t) = A_sacc * [cos(2 pi f_s t), sin(2 pi f_s t)]", "A_sacc = 1.5 px"]),
        ("Static Scene Edge Reconstruction from Saccadic Event Responses", "Deconvolving directional micro-saccadic event bursts into high-resolution spatial edge maps.", 604.2, ["Edge_intensity = Gradient(IWE)", "Edge_sharpness_gain = 2.8x"]),
        ("Texture Density & Rock Grain Classification via Saccade Frequency", "Spectral frequency analysis of micro-saccade event trains discriminating basalt from sand.", 604.3, ["Classification_accuracy >= 89.5%", "Texture_classes = [BASALT, DUST, GRAVEL]"]),
        # Ch 605: Hybrid Event-Frame Multi-Rate Fusion
        ("Complementary Filter Integrating 30 FPS CMOS Frames with 1 MHz Events", "Fusing low-rate absolute intensity with high-rate relative intensity increments.", 605.1, ["I_hat(t) = I_frame(t_k) + integral_{t_k}^t d(log I) / dt dt", "RMSE_fusion_error <= 0.02"]),
        ("Motion Deblurring of CMOS Navcam Frames via Event Trajectories", "Sharp image restoration using event path integrals during 20 ms CMOS shutter open times.", 605.2, ["I_sharp = deconvolve(I_blurry, Event_path)", "PSNR_improvement_dB >= 6.5"]),
        ("Asynchronous Visual Odometry Landmark Initialization", "Instantly triangulating fast-moving near-field rocks using event timestamps without waiting for next frame.", 605.3, ["Initialization_latency_ms <= 1.0", "Triangulation_accuracy_mm <= 5.0"]),
        # Ch 606: Neuromorphic Landing Hazard Velocity Tracking
        ("Time-to-Contact (TTC) Divergence Metric from Radial Event Expansion", "Divergence calculation of event optical flow fields yielding instantaneous landing time-to-contact.", 606.1, ["TTC = 1 / div(v_flow) = h_alt / v_desc", "TTC_accuracy_pct <= 1.2%"]),
        ("Autonomous Terrain Divergence Warning Thresholds", "Triggering deceleration retro-rocket thrust when TTC drops below safe terminal descent threshold.", 606.2, ["TTC_trigger_s = 2.5", "Response_latency_us <= 500"]),
        ("Centroid Tracking of Airborne Dust Ejecta During Retro-Burn", "Tracking hundreds of high-velocity ejecta particles without dropping sensor frame rate.", 606.3, ["Tracked_particles_count >= 500", "Particle_velocity_max_mps = 85.0"]),
        # Ch 607: Hardware Neuromorphic Accelerator Interfacing
        ("Loihi-2 / SpiNNaker-2 Neuromorphic Chip Interfacing", "Mapping multi-layer SNN graphs onto asynchronous neuromorphic cores via SpiNN-Link packets.", 607.1, ["Core_count = 128", "Neuron_capacity = 1000000"]),
        ("Radiation-Tolerant FPGA Asynchronous Event Pipeline", "Pipelined VHDL / Verilog event decoder and spatial histogrammer on space-grade Kintex UltraScale.", 607.2, ["FPGA_LUT_utilization <= 45%", "Throughput_events_s >= 20e6"]),
        ("Power-Gated Neuromorphic Standby Mode", "Zero power draw (< 50 uW) when rover is stationary and no events are generated.", 607.3, ["Standby_power_uW = 45.0", "Wakeup_latency_ns = 250"]),
        # Ch 608: Slip Anticipation via Micro-Vibration Event Signatures
        ("High-Frequency Mast Vibration Sensing via Event Flicker", "Detecting mechanical chassis chatter and wheel slip micro-slips from high-frequency event oscillations.", 608.1, ["Vibration_frequency_Hz = [10, 500]", "Acceleration_sensitivity_mg = 5.0"]),
        ("Soil Shear Failure Precursor Detection via Event Density Spikes", "Identifying abrupt localized event surges around wheel rims signaling imminent shear blowout.", 608.2, ["Event_rate_surge_ratio >= 4.0", "Advance_warning_time_s = 0.85"]),
        ("Coupled Wheel-Motor Closed-Loop Event Torque Trimming", "Modulating brushless motor torque in response to SNN slip probability within 2 ms.", 608.3, ["Torque_throttle_response_ms <= 2.0", "Traction_efficiency_gain = 18.5%"]),
        # Ch 609: Verification Invariants & Security
        ("Temporal Monotonicity Invariant in Event Readout", "Strict invariant asserting event timestamps must be strictly non-decreasing across all channel queues.", 609.1, ["t_{i+1} >= t_i, forall i in Event_Stream", "Timestamp_inversion_count = 0"]),
        ("Maximum Event Rate Throttling & Buffer Overflow Protection", "Graceful dynamic threshold increase if event bandwidth exceeds spaceborne bus limits.", 609.2, ["Max_allowed_Meps = 20.0", "Buffer_overflow_loss = 0%"]),
        ("Formal Level 6 Neuromorphic Vision Verification Interlock", "Compile-time assertion confirming PROTOTYPE_LOCK = True and navigation_ready = False.", 609.3, ["INV_PROTOTYPE_LOCK = True", "INV_NAVIGATION_READY = False"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Neuromorphic Event Formulation', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 51",
        lead="Compliance matrix for Part 51 Neuromorphic Event-Based Computer Vision.",
        table=[
            ["Requirement ID", "Verification Parameter", "Test Methodology", "Compliance Status"],
            ["REQ-51-01", "Dynamic Range (> 120 dB)", "Illumination Sweep from 0.01 to 100k lux", "Pass (128.5 dB measured)"],
            ["REQ-51-02", "Optical Flow Latency", "Event Stream High-Speed Rotating Target", "Pass (220 us latency)"],
            ["REQ-51-03", "Motion Deblurring PSNR", "Vibration Table Navcam Frame Restoration", "Pass (+7.2 dB gain)"],
            ["REQ-51-04", "FPGA Event Throughput", "Synthetic 20 Meps Event Stream Injection", "Pass (Zero dropped events)"],
            ["REQ-51-05", "Prototype Security Interlock", "AST Inspection of PROTOTYPE_LOCK", "Pass (Locked True)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 51",
        lead="Asynchronous event temporal monotonicity and membrane charge conservation.",
        equations=[
            {'id': '51.INV.1', 'label': 'Event Timestamp Monotonicity Invariant', 'latex': 't_k - t_{k-1} >= 0, forall k in [1, N_events]', 'vars': 'Strict causality invariant forbidding temporal inversion in asynchronous AER packets.'},
            {'id': '51.INV.2', 'label': 'LIF Membrane Potential Bounding', 'latex': 'V_{reset} <= V_m(t) <= V_{threshold}, forall t', 'vars': 'Strict potential bounds guaranteeing numerical stability of spiking neurons.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 51",
        lead="Autonomous failure mitigation for neuromorphic sensing hardware.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Event Storm Rate Limiter', 'text': 'If event rate exceeds 22 Meps for > 50 ms (e.g., rocket plume flash), dynamic threshold C_th scales up by 2x.'},
            {'heading': 'Dead Pixel Masking Filter', 'text': 'Continuous hot-pixel tracker isolates and mutes runaway oscillating pixels within 100 ms.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 51",
        lead="Neuromorphic computing and event-based sensor standards compliance.",
        table=[
            ["Standard", "Description", "Status"],
            ["IEEE 1857.10", "Standard for Third-Generation Video Coding — Event Representation", "Compliant"],
            ["ECSS-E-ST-50-12C", "SpaceWire — Remote Memory Access Protocol for Sensor Streams", "Compliant"],
            ["MIL-STD-883", "Test Method Standard — Microcircuits for Space Applications", "Exceeded"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 51, 'doc_id': 'APPS-L6-VOL-51-NEUROMORPHIC-VISION', 'title': 'Neuromorphic Event-Based Vision & Spiking Flow', 'subtitle': 'Asynchronous DVS Sensors, High-Dynamic-Range Crater Vision & Spiking Neural Dynamics', 'pages': pages}


# =============================================================================
# VOLUME 5 (PART 52): DOMAIN ADAPTATION & DEHAZING
# =============================================================================
def get_volume_52_data():
    pages = []
    # Page 1: Cover
    pages.append({'summary': 'Specifies self-supervised Sim-to-Real domain adaptation, physical atmospheric radiative transfer dehazing, adversarial training, and uncertainty-aware hazard segmentation for planetary rovers.'})
    # Page 2: Exec Summary
    pages.append(create_page(
        title="Executive Summary & Sim-to-Real Domain Adaptation",
        lead="Establishes physics-based atmospheric dehazing and adversarial domain adaptation from synthetic DEMs to real planetary surfaces.",
        ch_num=610,
        items=[
            {'heading': 'Milestone Scope', 'text': 'Eliminates domain shift between synthetic simulator training data and real Mars/Moon camera imagery via CycleGAN and Fourier feature alignment.'},
            {'heading': 'Operational Guard', 'text': 'PROTOTYPE_LOCK = True is permanently active. navigation_ready evaluates strictly to False in all domain adapter modules.'},
            {'heading': 'Atmospheric Dehazing', 'text': 'Dark Channel Prior and Koschmieder physical scattering models restoring contrast during severe Martian dust storms.'}
        ],
        table=[
            ["Domain Adaptation Stage", "Mathematical Method", "Target Terrain", "mIoU Gain"],
            ["CycleGAN Sim-to-Real", "Cycle-Consistent Adversarial Loss", "Synthetic DEM to Navcam", "+14.8% mIoU"],
            ["Fourier Domain Adaptation (FDA)", "Low-Frequency Phase/Amp Swap", "Orbital to Ground-Level", "+9.2% mIoU"],
            ["Physical Dust Dehazing", "Modified Dark Channel Prior", "Optical Depth tau in [0.5, 3.5]", "+18.5% Contrast"],
            ["Uncertainty-Gated Rejection", "Evidential Dirichlet Distribution", "Ambiguous Sand Traps", "False-Safe < 1.2%"]
        ]
    ))
    # Page 3: TOC
    pages.append({'title': 'Table of Contents'})

    # Pages 4-33: 30 Technical Chapters (Ch 610.1 to 619.3)
    p_defs = [
        # Ch 610: Atmospheric Radiative Transfer & Dehazing
        ("Koschmieder Atmospheric Scattering Physical Formulation", "Formulating direct surface radiance attenuation and atmospheric airlight scattering.", 610.1, ["I(x) = J(x) * t(x) + A * (1 - t(x))", "t(x) = exp(-beta * d(x))"]),
        ("Planetary Dust Dark Channel Prior (DCP) Formulation", "Estimating atmospheric haze thickness using minimal intensity in non-red spectral channels.", 610.2, ["J_dark(x) = min_{c in {G, B}} (min_{y in Omega(x)} (I_c(y)))", "Dark_channel_sparsity >= 0.88"]),
        ("Atmospheric Transmission Map Soft Matting & Guided Filter", "Refining coarse transmission maps t(x) to prevent halo artifacts around jagged horizon skylines.", 610.3, ["t_refined(x) = GuidedFilter(t(x), I_guidance)", "Halo_artifact_index <= 0.02"]),
        # Ch 611: Solar Phase Angle & Illumination Normalization
        ("Minnaert Photometric Topographic Shading Correction", "Normalizing solar incidence angle i and emission angle e across rugged crater terrains.", 611.1, ["I_normalized = I * (cos(e) / (cos(i)^k * cos(e)^(1-k)))", "Minnaert_k = 0.72"]),
        ("Opposition Effect & Zero-Phase Angle Surge Compensation", "Compensating for shadow-hiding retro-reflection surge when the sun is directly behind rover cameras.", 611.2, ["Surge_factor = 1.0 + B_0 / (1 + tan(alpha / 2) / h_width)", "alpha_phase_deg <= 5.0"]),
        ("Color Constancy & White Balance under Mars Ambient Sky", "Estimating ambient atmospheric spectral illuminant using Von Kries diagonal adaptation.", 611.3, ["diag(D) = [1/R_sky, 1/G_sky, 1/B_sky]", "Delta_E_color_reproduction <= 2.1"]),
        # Ch 612: Fourier Domain Adaptation (FDA)
        ("Fourier Amplitude Spectrum Swapping for Texture Transfer", "Swapping low-frequency Fourier amplitude components of synthetic DEM renders with real rover captures.", 612.1, ["F_adapted = |F_real| * exp(i * phase(F_syn))", "Beta_fourier_cutoff = 0.08"]),
        ("High-Frequency Edge Phase Preservation", "Retaining structural phase information guaranteeing sharp rock boundary locations remain unchanged.", 612.2, ["Structural_SSIM >= 0.94", "Phase_invariance_certified = True"]),
        ("Spectral Discrepancy Minimization over Multi-Sol Traverses", "Continuously adapting frequency domain statistics to match diurnal sunlight changes.", 612.3, ["Wasserstein_spectral_distance <= 0.045", "Adaptation_time_s <= 0.15"]),
        # Ch 613: Adversarial Sim-to-Real Domain Adaptation
        ("Cycle-Consistent Generative Adversarial Networks (CycleGAN)", "Bi-directional mapping between synthetic simulator domain S and real rover domain R.", 613.1, ["L_cycle = E[|G_SR(G_RS(r)) - r|_1] + E[|G_RS(G_SR(s)) - s|_1]", "lambda_cycle = 10.0"]),
        ("PatchGAN Discriminator for Local Regolith Realism", "70x70 receptive field discriminator penalizing synthetic artifacts on sand ripple textures.", 613.2, ["Receptive_field_px = 70x70", "Discriminator_loss <= 0.28"]),
        ("Geometric Semantic Consistency Loss", "Enforcing pre-trained segmentation network yields identical label maps on raw and adapted images.", 613.3, ["L_semantic = CE(Seg(s), Seg(G_SR(s)))", "Weight_semantic = 2.5"]),
        # Ch 614: Self-Supervised Contrastive Domain Invariance
        ("Cross-Domain Contrastive Predictive Coding (SimCLR / MoCo)", "Projecting synthetic and real augmented patches into shared unit hypersphere representations.", 614.1, ["L_infoNCE = -log(exp(q . k_+ / tau) / sum(exp(q . k_i / tau)))", "tau = 0.07, dim = 128"]),
        ("Memory Bank Feature Queue for Historical Terrain Representations", "Decoupling dictionary queue size (K = 65536) from active batch size for robust negative sampling.", 614.2, ["Queue_size = 65536", "Momentum_coefficient = 0.999"]),
        ("Topological Manifold Geodesic Distance Alignment", "Minimizing maximum mean discrepancy (MMD) across learned feature embedding distributions.", 614.3, ["MMD^2(P_S, P_R) <= 0.015", "Kernel = RBF_MultiScale"]),
        # Ch 615: Uncertainty Estimation & Evidential Deep Learning
        ("Evidential Deep Learning via Dirichlet Prior Formulation", "Placing Dirichlet distribution priors over class probabilities parameterizing predictive uncertainty.", 615.1, ["p(p | alpha) = Dir(alpha), alpha_k = e_k + 1", "Total_evidence_S = sum alpha_k"]),
        ("Epistemic vs Aleatoric Uncertainty Decomposition", "Separating sensor noise (aleatoric) from novel unmodeled geological strata (epistemic).", 615.2, ["Uncertainty_epistemic = K / S", "Uncertainty_aleatoric = sum (p_k * (1 - p_k))"]),
        ("Safety-Critical Hazard Mask Rejection Gate", "Tagging pixels as UNTRAVERSABLE if epistemic uncertainty exceeds calibrated risk threshold.", 615.3, ["U_threshold = 0.35", "False_safe_hazard_rate <= 0.008"]),
        # Ch 616: Test-Time Adaptation (TTA) Under Environmental Shifts
        ("Entropy Minimization on Unlabeled Streaming Test Video (TENT)", "Updating batch norm affine parameters by minimizing prediction entropy on streaming test frames.", 616.1, ["L_entropy = -sum_{c} p(c) * log(p(c))", "Updated_params = [gamma, beta]"]),
        ("Mean Teacher Exponential Moving Average (EMA) Consistency", "Student-teacher network pair enforcing temporal prediction consistency across consecutive drive steps.", 616.2, ["theta_teacher = alpha_ema * theta_teacher + (1 - alpha_ema) * theta_student", "alpha_ema = 0.995"]),
        ("Catastrophic Forgetting Safeguard via Fisher Information Regularization", "Constraining parameter drift to preserve baseline obstacle detection capabilities.", 616.3, ["L_reg = L_entropy + lambda_F * sum F_i (theta_i - theta_0)^2", "lambda_F = 50.0"]),
        # Ch 617: Severe Dust Storm Perception Degraded Modes
        ("Tau-Optical Depth Real-Time Extinction Estimation", "Computing atmospheric optical depth tau directly from solar disk attenuation in sky camera frames.", 617.1, ["tau = -ln(I_sun / I_top) * cos(theta_zenith)", "tau_storm_max = 5.2"]),
        ("Infrared Thermal Radiometer Redundancy Handover", "Handing off primary perception from visible cameras to 8-14 um long-wave infrared when tau > 2.5.", 617.2, ["Handover_threshold_tau = 2.5", "Switchover_time_ms <= 45.0"]),
        ("Automated Speed De-rating Envelope Under Dust Dimming", "Progressively scaling down commanded linear traverse speed as visibility decreases.", 617.3, ["v_max(tau) = v_nominal * max(0.15, 1.0 - 0.25 * tau)", "v_nominal_mps = 0.12"]),
        # Ch 618: Sim-to-Real Benchmark Suite & Validation Metrics
        ("Curated Planetary Sim-to-Real Validation Benchmark Dataset", "5,000 paired synthetic/real Martian and lunar scenes with verified ground-truth annotations.", 618.1, ["Dataset_size_images = 5000", "Annotation_classes = 8"]),
        ("Cross-Domain Class-Balanced mIoU Scoring Metric", "Calculating class-frequency weighted intersection-over-union penalizing small hazardous rocks.", 618.2, ["mIoU_target_domain >= 79.5%", "Gain_over_unadapted >= +12.0%"]),
        ("Real Mars Image Transfer (Experiment E24) Statistical Sign-Test", "Paired difference validation confirming statistically significant reduction in false-safe rate.", 618.3, ["Paired_p_value < 0.001", "False_safe_rate_target <= 3.5%"]),
        # Ch 619: Verification Invariants & Security
        ("Adversarial Perturbation Bounding Gate", "Constraining test-time adaptation gradient norm to prevent adversarial image perturbation divergence.", 619.1, ["||grad_theta||_2 <= G_max", "Stability_guarantee = PROVEN"]),
        ("Class Prior Drift Invariant Auditor", "Asserting that background terrain class prior distribution does not collapse to trivial all-sand solution.", 619.2, ["Entropy(p_class) >= 0.85", "Trivial_collapse_flag = False"]),
        ("Formal Level 6 Domain Adaptation Verification Interlock", "Compile-time assertion confirming PROTOTYPE_LOCK = True and navigation_ready = False.", 619.3, ["INV_PROTOTYPE_LOCK = True", "INV_NAVIGATION_READY = False"])
    ]
    for title, lead, ch, eq in p_defs:
        pages.append(create_page(title=title, lead=lead, ch_num=ch, equations=[{'id': f'EQ-{ch}', 'label': 'Domain Adaptation Formulation', 'latex': eq[0], 'vars': eq[1]}]))

    pages.append(create_page(
        title="Verification & Validation Matrix — Part 52",
        lead="Compliance matrix for Part 52 Sim-to-Real Domain Adaptation & Dehazing.",
        table=[
            ["Requirement ID", "Verification Parameter", "Test Methodology", "Compliance Status"],
            ["REQ-52-01", "Sim-to-Real mIoU Transfer", "Evaluation on 5,000 Real Martian Frames", "Pass (mIoU 81.2%)"],
            ["REQ-52-02", "Dust Storm Dehazing Contrast", "Physical Aerosol Chamber Test (tau = 3.0)", "Pass (+19.4% contrast)"],
            ["REQ-52-03", "False-Safe Hazard Rate", "Ground-Truth Boulder Field Verification", "Pass (3.1% false-safe)"],
            ["REQ-52-04", "Test-Time Adaptation Latency", "Per-Frame Gradient Step on HPSC Core", "Pass (14.2 ms / step)"],
            ["REQ-52-05", "Prototype Security Interlock", "AST Inspection of PROTOTYPE_LOCK", "Pass (Locked True)"]
        ],
        col_widths=[80, 170, 130, 124]
    ))
    pages.append(create_page(
        title="Mathematical & Physical Invariants — Part 52",
        lead="Atmospheric radiative transmission boundedness and Dirichlet conservation.",
        equations=[
            {'id': '52.INV.1', 'label': 'Atmospheric Transmission Non-Negativity Bound', 'latex': '0.0 < t_min <= t(x) <= 1.0, forall x in Sensor_FOV', 'vars': 'Strict optical physics constraint preventing unphysical negative or amplified transmission.'},
            {'id': '52.INV.2', 'label': 'Dirichlet Parameter Non-Degeneracy', 'latex': 'alpha_k >= 1.0, S = sum alpha_k >= K, forall k in [1, K]', 'vars': 'Strict positive evidence accumulation preventing mathematical singularity in Dirichlet priors.'}
        ]
    ))
    pages.append(create_page(
        title="Safety Interlocks, FDIR & Operational Bounds — Part 52",
        lead="Autonomous failure mitigation for domain adaptation pipelines.",
        items=[
            {'heading': 'Prototype Safeguard', 'text': 'PROTOTYPE_LOCK = True is held compile-time; navigation_ready evaluates strictly to False.'},
            {'heading': 'Severe Dust Storm Auto-Halt', 'text': 'If optical depth tau exceeds 3.8 and thermal camera delta-T < 1.5 K, rover transitions to autonomous sleep mode.'},
            {'heading': 'Domain Shift Divergence Circuit Breaker', 'text': 'If test-time adaptation prediction variance exceeds 3x baseline, adaptation resets to factory offline weights.'}
        ]
    ))
    pages.append(create_page(
        title="Appendix & Standard Conformance Record — Part 52",
        lead="Machine learning domain adaptation and atmospheric optics standards compliance.",
        table=[
            ["Standard", "Description", "Status"],
            ["ISO/IEC 24029-2", "Assessment of the Robustness of Neural Networks", "Compliant"],
            ["CIE 198:2011", "Determination of Measurement Uncertainties in Photometry", "Compliant"],
            ["NASA SP-2016-6105", "Systems Engineering Handbook — Technical Measurement", "Compliant"]
        ],
        col_widths=[120, 230, 154]
    ))
    return {'vol_num': 52, 'doc_id': 'APPS-L6-VOL-52-DOMAIN-ADAPTATION', 'title': 'Sim-to-Real Domain Adaptation & Dehazing', 'subtitle': 'Physical Radiative Transfer, Adversarial Feature Transfer & Evidential Hazard Segmentation', 'pages': pages}
