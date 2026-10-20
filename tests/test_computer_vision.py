"""Automated Unit and Integration Test Suite for APPS Computer Vision Subsystems.
Chapters 570 to 619 & Parts 48 to 52.

Covers:
1. Vision Transformers & Multi-Spectral Attention (Part 48)
2. 3D Gaussian Splatting & Neural Radiance Fields (Part 49)
3. Dense Stereo Photogrammetry & SE(3) VIO (Part 50)
4. Neuromorphic Event Vision & Spiking Optical Flow (Part 51)
5. Sim-to-Real Domain Adaptation & Dust Dehazing (Part 52)
6. Prototype Locks & Safety Invariants
"""
import math
import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from level6.vision.vision_transformers import (
    PatchTokenizer, MultiHeadSelfAttention, MultiSpectralCrossAttention, QuantizedSpaceTransformer,
    PROTOTYPE_LOCK as P48_LOCK, NAVIGATION_READY as P48_NAV
)
from level6.vision.neural_radiance_fields import (
    GaussianSplat3D, DifferentiableSplatRasterizer, SolarShadowDecoupler,
    PROTOTYPE_LOCK as P49_LOCK, NAVIGATION_READY as P49_NAV
)
from level6.vision.stereo_photogrammetry import (
    StereoCalibrator, DenseSemiGlobalMatcher, VisualInertialOdometryLie,
    PROTOTYPE_LOCK as P50_LOCK, NAVIGATION_READY as P50_NAV
)
from level6.vision.neuromorphic_event_vision import (
    EventCameraSensor, ContrastMaximizationOpticalFlow, SpikingNeuronLandingSentinel,
    PROTOTYPE_LOCK as P51_LOCK, NAVIGATION_READY as P51_NAV
)
from level6.vision.domain_adaptation_dehaze import (
    AtmosphericDustDehazer, FourierDomainAdapter, EvidentialHazardSegmenter,
    PROTOTYPE_LOCK as P52_LOCK, NAVIGATION_READY as P52_NAV
)


# ---------------- 1. Vision Transformers & Multi-Spectral Attention (Part 48) ----------------
def test_t94_patch_tokenization_and_self_attention():
    tok = PatchTokenizer(img_size=128, patch_size=16, in_channels=6, embed_dim=256)
    dummy_frame = np.ones((6, 128, 128)) * 0.5
    res = tok.tokenize_frame(dummy_frame)
    assert res["num_tokens"] == 64
    assert res["embed_dim"] == 256
    assert res["prototype_lock"] is True

    attn = MultiHeadSelfAttention(embed_dim=256, num_heads=4)
    tokens = np.ones((64, 256)) * 0.1
    attn_res = attn.compute_attention(tokens)
    assert attn_res["flash_tiling_safe"] is True
    assert attn_res["sparsity_ratio"] >= 0.0


def test_t95_multi_spectral_cross_attention_and_int8_quant():
    cross = MultiSpectralCrossAttention(band_count=6)
    fuse = cross.fuse_spectral_cubes(pan_intensity=0.75, spectral_absorptions=[0.2, 0.8, 0.4, 0.3, 0.5, 0.6])
    assert fuse["cross_attention_convergence"] is True
    assert fuse["fused_saliency"] > 0.0
    assert fuse["geological_anomaly_flag"] is True

    quant = QuantizedSpaceTransformer(bitwidth=8)
    weights = np.random.randn(64, 64)
    q_res = quant.quantize_weights(weights)
    assert q_res["memory_compression_ratio"] == 4.0
    assert q_res["quant_rmse"] < 0.05
    assert q_res["seu_parity_intact"] is True


# ---------------- 2. 3D Gaussian Splatting & Radiance Fields (Part 49) ----------------
def test_t96_3d_gaussian_splat_covariance_and_projection():
    splat = GaussianSplat3D(
        position=np.array([0.0, 0.0, 3.5]),
        scale=np.array([0.1, 0.2, 0.05]),
        rotation_quat=np.array([1.0, 0.0, 0.0, 0.0]),
        color_rgb=np.array([0.8, 0.4, 0.2]),
        opacity=0.85
    )
    cov3d = splat.compute_3d_covariance()
    assert cov3d.shape == (3, 3)
    assert np.all(np.linalg.eigvals(cov3d) > 0)  # Positive definite

    extrinsic = np.eye(4)
    proj = splat.project_to_2d_camera(extrinsic, focal_length=600.0)
    assert proj["is_in_front_of_camera"] is True
    assert proj["depth_z"] == 3.5
    assert proj["cov_2d_det"] > 0.0


def test_t97_differentiable_rasterizer_and_solar_shadow():
    splats = [
        GaussianSplat3D(np.array([0.0, 0.0, 3.0 + i]), np.array([0.1, 0.1, 0.1]), np.array([1.0, 0, 0, 0]), np.array([0.5, 0.5, 0.5]), 0.5)
        for i in range(5)
    ]
    raster = DifferentiableSplatRasterizer()
    res = raster.render_point_batch(splats, np.eye(4))
    assert res["rendered_splats"] == 5
    assert res["final_transmittance"] < 0.1  # Significant ray absorption
    assert res["render_fps_estimate"] > 60.0

    decoupler = SolarShadowDecoupler(sun_azimuth_deg=0.0, sun_elevation_deg=45.0)
    surf_norm = np.array([0.0, 1.0, 1.0])
    decomp = decoupler.decompose_radiance(observed_radiance=0.6, surface_normal=surf_norm)
    assert 0.0 <= decomp["surface_albedo"] <= 1.0
    assert "is_shadowed" in decomp


# ---------------- 3. Dense Stereo Photogrammetry & VIO (Part 50) ----------------
def test_t98_stereo_calibration_epipolar_and_thermal_baseline():
    calib = StereoCalibrator(focal_length_px=1000.0, baseline_m=0.40)
    b_cold = calib.compute_effective_baseline(mast_temperature_c=-80.0)
    assert b_cold < 0.40  # Contraction in deep cryogenic cold
    assert b_cold > 0.399

    epipolar = calib.evaluate_epipolar_constraint((120.0, 50.0), (100.0, 50.2))
    assert epipolar["epipolar_constraint_satisfied"] is True
    assert epipolar["disparity_px"] == 20.0


def test_t99_dense_sgm_matching_and_range_uncertainty():
    matcher = DenseSemiGlobalMatcher()
    costs = [10.0, 8.5, 3.2, 5.8, 12.0]
    match = matcher.match_disparity_profile(costs)
    assert match["disparity_integer"] == 2
    assert 1.5 < match["disparity_subpixel"] < 2.5
    assert match["is_unique"] is True

    uncert = matcher.compute_range_uncertainty(depth_z_m=8.0, focal_length_px=1200.0, baseline_m=0.40)
    assert uncert["sigma_z_m"] > 0.0
    assert uncert["depth_safe_for_traverse"] is True


def test_t100_vio_lie_group_kinematics_and_degeneracy():
    vio = VisualInertialOdometryLie()
    prop = vio.propagate_kinematics(np.array([0.0, 0.0, 3.71]), np.array([0.0, 0.0, 0.1]), dt_s=0.1)
    assert prop["motion_stable"] is True

    features = [
        np.array([1.0, 0.0, 1.0]),
        np.array([0.0, 1.0, 1.0]),
        np.array([-1.0, 0.0, 1.0]),
        np.array([0.0, -1.0, 1.0])
    ]
    deg = vio.check_visual_degeneracy(features)
    assert deg["safe_for_pure_visual_nav"] is True
    assert deg["is_degenerate"] is False


# ---------------- 4. Neuromorphic Event Vision (Part 51) ----------------
def test_t101_dvs_logarithmic_event_and_noise_filtering():
    cam = EventCameraSensor(contrast_threshold=0.15)
    e = cam.process_intensity_change((10, 20), old_intensity=0.5, new_intensity=0.8, timestamp_us=100.0)
    assert e is not None
    assert e["polarity"] == 1
    assert e["x"] == 10 and e["y"] == 20

    filt = cam.filter_background_activity([e], correlation_window_us=1000.0)
    assert filt["valid_events_count"] == 1
    assert filt["dynamic_range_db"] >= 120.0


def test_t102_contrast_maximization_and_ttc_spiking_sentinel():
    cmax = ContrastMaximizationOpticalFlow(grid_size=64)
    dummy_events = [
        {"x": 10 + i, "y": 20, "timestamp_us": 100.0 + i * 1000.0, "polarity": 1}
        for i in range(10)
    ]
    res = cmax.evaluate_motion_hypothesis(dummy_events, velocity_hypothesis=(100.0, 0.0))
    assert res["events_warped_count"] == 10
    assert "focus_variance" in res

    sentinel = SpikingNeuronLandingSentinel(v_thresh=1.0)
    ttc = sentinel.compute_time_to_contact(radial_expansion_rate_per_sec=0.5)
    assert ttc["time_to_contact_s"] == 2.0
    assert ttc["retro_thrust_trigger"] is True  # TTC < 2.5 s triggers warning


# ---------------- 5. Sim-to-Real Domain Adaptation & Dehazing (Part 52) ----------------
def test_t103_dust_storm_dehazing_and_koschmieder_model():
    dehazer = AtmosphericDustDehazer(airlight_intensity=0.85, beta_extinction=0.08)
    t = dehazer.estimate_transmission(depth_m=15.0)
    assert 0.10 <= t <= 1.0

    res = dehazer.dehaze_pixel(observed_val=0.75, depth_m=10.0)
    assert res["dust_penetration_verified"] is True
    assert 0.0 <= res["recovered_radiance"] <= 1.0


def test_t104_fourier_domain_adaptation_and_evidential_hazard():
    fda = FourierDomainAdapter(beta_cutoff=0.1)
    syn = np.ones((64, 64)) * 0.4
    real = np.ones((64, 64)) * 0.6
    res = fda.adapt_spectral_amplitudes(syn, real)
    assert res["phase_geometry_intact"] is True
    assert res["sim_to_real_miou_gain_pct"] > 10.0

    seg = EvidentialHazardSegmenter(uncertainty_threshold=0.35)
    safe_eval = seg.evaluate_pixel_evidence(logits=[8.0, 0.1, 0.0, 0.0])
    assert safe_eval["predicted_class"] == "BEDROCK"
    assert safe_eval["is_safe_to_traverse"] is True
    assert safe_eval["uncertainty_rejection_active"] is False

    hazard_eval = seg.evaluate_pixel_evidence(logits=[0.1, 0.1, 0.1, 0.1])
    assert hazard_eval["uncertainty_rejection_active"] is True  # Low evidence -> high uncertainty


# ---------------- 6. Prototype Locks & Safety Invariants ----------------
def test_t105_vision_prototype_locks_and_invariants():
    assert P48_LOCK is True and P48_NAV is False
    assert P49_LOCK is True and P49_NAV is False
    assert P50_LOCK is True and P50_NAV is False
    assert P51_LOCK is True and P51_NAV is False
    assert P52_LOCK is True and P52_NAV is False
