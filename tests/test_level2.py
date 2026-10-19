"""Level 2 Automated Unit and Integration Test Suite.
Verifies continuous 3D DEM, planar kinematics, camera projection, primitive planner,
interface schema lock, temporal fusion, and Level 2 evidence evaluation.
Chapters 209, 210, 211, 212, 213, 215, 216 (Part 12).
"""
import math
import numpy as np
import pytest

from level2.sim3d.terrain3d import Terrain3D, generate_dem_scene_3d
from level2.sim3d.simulator3d import Simulator3D
from level2.kinematics.rover_params import RoverParams
from level2.kinematics.kinematic_model import kin_step, compute_attitude, compute_slope_slip, simulate_kinematic_step
from level2.sensing.camera3d import Camera3D, depth_from_disparity
from level2.navigation.traversability25d import build_traversability_25d
from level2.navigation.primitive_planner import arc_pose, generate_primitives, rasterize_swept_footprint, plan_primitive
from level2.interface.schema import build_message, validate_message
from level2.evaluation.temporal_fusion import TemporalMapFusion
from level2.evaluation.latency import latency_report
from level2.evaluation.label_script_l2 import level2_label, release_gate_l2, KEYS_L2


# ---------------- 1. 3D Terrain & Solar Ray-Tracing (Task 102) ----------------
def test_t21_terrain3d_geometry():
    elev = np.zeros((32, 32), dtype=np.float32)
    elev[16:, :] = 2.0 # Step ledge
    t = Terrain3D(elev, cell_size_m=0.25)
    
    # Continuous interpolation check
    z_interp = t.get_elevation_continuous(1.0, 1.0)
    assert math.isclose(z_interp, 0.0, abs_tol=1e-3)
    
    # Surface normal check
    nx, ny, nz = t.get_normal_continuous(1.0, 1.0)
    assert math.isclose(nz, 1.0, abs_tol=1e-2)
    
    # Solar illumination check
    shaded = t.compute_solar_illumination(sun_azimuth_deg=45.0, sun_elevation_deg=30.0)
    assert shaded.shape == (32, 32, 3)
    assert np.all(np.isfinite(shaded))
    assert 0.0 <= shaded.min() <= shaded.max() <= 1.0


# ---------------- 2. Planar Kinematics & Footprint Model (Task 101) ----------------
def test_t22_kinematic_straight_line():
    state = (0.0, 0.0, 0.0)
    new_state, status, clips = kin_step(state, v_cmd=1.0, k_cmd=0.0, dt=1.0, v_max=1.5, k_max=1.0)
    assert status == "ok"
    assert math.isclose(new_state[0], 1.0, abs_tol=1e-5)
    assert math.isclose(new_state[1], 0.0, abs_tol=1e-5)
    assert math.isclose(new_state[2], 0.0, abs_tol=1e-5)
    assert clips == 0


def test_t22_kinematic_circular_arc():
    # Constant curvature k = 0.5 (radius = 2.0m). Circumference = 2*pi*r = 4*pi ~= 12.566m
    # At v = 1.0 m/s, completing full circle takes 12.566s
    state = (0.0, 0.0, 0.0)
    dt = 0.01
    n_steps = int(round((4.0 * math.pi) / (1.0 * dt)))
    for _ in range(n_steps):
        state, status, _ = kin_step(state, v_cmd=1.0, k_cmd=0.5, dt=dt, v_max=2.0, k_max=2.0)
    # Rover should return near (0, 0)
    dist_from_origin = math.hypot(state[0], state[1])
    assert dist_from_origin < 0.15


def test_t22_kinematic_clipping_and_invalid_input():
    state = (0.0, 0.0, 0.0)
    # Speed clip
    new_state, status, clips = kin_step(state, v_cmd=2.5, k_cmd=0.0, dt=1.0, v_max=1.0, k_max=1.0)
    assert clips == 1
    assert math.isclose(new_state[0], 1.0, abs_tol=1e-5)
    
    # Curvature clip
    _, _, clips_k = kin_step(state, v_cmd=0.5, k_cmd=3.0, dt=1.0, v_max=1.0, k_max=1.5)
    assert clips_k == 1
    
    # Non-finite input rejection
    unchanged_state, status_nan, _ = kin_step(state, v_cmd=float("nan"), k_cmd=0.0, dt=1.0)
    assert status_nan == "invalid_input"
    assert unchanged_state == state


def test_t22_slope_slip_and_attitude():
    params = RoverParams(max_safe_slope_deg=20.0, tip_slope_deg=30.0)
    # Mild slope: no slip
    slip_mild, eff_v_mild = compute_slope_slip(math.radians(10.0), v_cmd=0.5, params=params)
    assert slip_mild == 0.0
    assert math.isclose(eff_v_mild, 0.5)
    
    # Steep slope: traction loss
    slip_steep, eff_v_steep = compute_slope_slip(math.radians(25.0), v_cmd=0.5, params=params)
    assert slip_steep > 0.0
    assert eff_v_steep < 0.5


# ---------------- 3. Primitive Arc Generator (Task 103) ----------------
def test_t23_primitive_arc_pose():
    # Straight line arc
    dx, dy, dth = arc_pose(k=0.0, length=2.0)
    assert math.isclose(dx, 2.0)
    assert math.isclose(dy, 0.0)
    assert math.isclose(dth, 0.0)
    
    # Mirror symmetry: k = +0.5 vs k = -0.5 (Appendix CO / S12.2)
    dx_pos, dy_pos, dth_pos = arc_pose(k=0.5, length=2.0)
    dx_neg, dy_neg, dth_neg = arc_pose(k=-0.5, length=2.0)
    assert math.isclose(dx_pos, dx_neg, rel_tol=1e-4)
    assert math.isclose(dy_pos, -dy_neg, rel_tol=1e-4)
    assert math.isclose(dth_pos, -dth_neg, rel_tol=1e-4)
    assert math.isclose(dx_pos, 1.683, rel_tol=1e-2)
    assert math.isclose(dy_pos, 0.919, rel_tol=1e-2)


def test_t24_swept_footprint_collision():
    # Rasterize straight primitive of length 1.5m at (0, 0)
    swept = rasterize_swept_footprint(0.0, 0.0, 0.0, k=0.0, length_m=1.5, cell_size_m=0.25)
    assert len(swept) > 5
    # Should include cells along positive x-axis
    cols = [c[1] for c in swept]
    assert max(cols) >= 5


# ---------------- 4. Camera Projection & Stereo Depth (Task 97) ----------------
def test_t25_stereo_depth_from_disparity():
    # f = 800 px, B = 0.20 m, d = 16 px -> Z = 800 * 0.20 / 16 = 10.0 m (Section S11.7)
    d = np.array([16.0, 8.0, 4.0, 0.0, -2.0])
    z = depth_from_disparity(d, f_px=800.0, baseline_m=0.20, z_min=0.5, z_max=50.0)
    assert math.isclose(z[0], 10.0, rel_tol=1e-4)
    assert math.isclose(z[1], 20.0, rel_tol=1e-4)
    assert math.isclose(z[2], 40.0, rel_tol=1e-4)
    assert np.isnan(z[3]) # Zero disparity invalid
    assert np.isnan(z[4]) # Negative disparity invalid


# ---------------- 5. Interface Schema & Guard (Task 104) ----------------
def test_t27_interface_schema_and_lock():
    msg = build_message("plan_record", seq=1, step=0, producer="planner", body={"status": "ok"})
    assert validate_message(msg, last_seq=0) == "ok"
    
    # Security violation: navigation_ready cannot be set to True
    illegal_msg = dict(msg, navigation_ready=True)
    assert validate_message(illegal_msg, last_seq=0) == "lock_violation"
    
    # Information boundary breach: forbidden truth key
    leak_msg = build_message("plan_record", seq=2, step=1, producer="test", body={"truth_grid": [1, 2]})
    assert validate_message(leak_msg, last_seq=1) == "forbidden_key"
    
    # Out of sequence
    bad_seq_msg = dict(msg, seq=0)
    assert validate_message(bad_seq_msg, last_seq=5) == "bad_sequence"


# ---------------- 6. Temporal Map Fusion (Task 106) ----------------
def test_t28_temporal_fusion_retention():
    fusion = TemporalMapFusion(shape=(16, 16), clearing_count_thresh=3)
    new_haz = np.zeros((16, 16), dtype=np.float32)
    new_haz[5, 5] = 0.80
    obs_mask = np.ones((16, 16), bool)
    
    fusion.update(new_haz, obs_mask, fuse_mode="union")
    assert fusion.hazard_belief[5, 5] > 0.5
    
    # Sensor miss next step
    empty_haz = np.zeros((16, 16), dtype=np.float32)
    fusion.update(empty_haz, obs_mask, fuse_mode="union")
    # Union must keep the warning
    assert fusion.hazard_belief[5, 5] > 0.5


# ---------------- 7. Level 2 Label Evaluation (Task 107) ----------------
def test_t29_level2_label_evaluation():
    # Test plan from Chapter 216.4 / Section S12.8
    ev_all_pass = {k: dict(exists=True, executed=True, passed=True) for k in KEYS_L2}
    assert level2_label(ev_all_pass) == "L2-met (internal)"
    
    # One key missing
    ev_missing = dict(ev_all_pass)
    ev_missing.pop("kinematic_model")
    assert level2_label(ev_missing) == "L2-not-met"
    
    # One key exists False
    ev_exists_false = dict(ev_all_pass)
    ev_exists_false["transfer_eval"] = dict(exists=False, executed=True, passed=True)
    assert level2_label(ev_exists_false) == "L2-not-met"
    
    # One key executed False
    ev_unexecuted = dict(ev_all_pass)
    ev_unexecuted["local_planner"] = dict(exists=True, executed=False, passed=True)
    assert level2_label(ev_unexecuted) == "L2-partial"
    
    # One key failed
    ev_failed = dict(ev_all_pass)
    ev_failed["interface_schema"] = dict(exists=True, executed=True, passed=False)
    assert level2_label(ev_failed) == "L2-partial"
    
    # Empty dict
    assert level2_label({}) == "L2-not-met"
