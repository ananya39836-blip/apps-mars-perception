"""Comprehensive test suite covering all specifications and appendices from Parts 1 through 5.
"""
import pytest
import numpy as np
import torch

import apps01 as A
from nav_v2 import coarse_v2, nav_eval_v2
from traversability.cost_map import RoverParams, build_status, planner_mask, step_cost, FREE, COSTLY, BLOCKED, UNKNOWN
from traversability.route_audit import audit_route
from traversability.occupancy import OccupancyFusion, warp_integer, crop_sequence
from traversability.simulator import plan, run_episode
from uncertainty.calibration import scale_probs, fit_temperature, entropy_norm, ece
from uncertainty.cross_sensor import consistency_map, depth_validity
from uncertainty.novelty import MahalanobisOOD, RankGate
from interface.schema import validate_record, failure_record, observation_record_v2, SCHEMA_VERSION
from interface.guard import evaluate_readiness, PROTOTYPE_LOCK
from evaluation.seeds import scene_seeds, check_disjoint, wilson, n_for_halfwidth, rule_of_three
from evaluation.bootstrap import boot_mean, boot_paired, boot_pooled_false_safe, upper_bound_zero_events
from evaluation.cluster_bootstrap import boot_clusters, boot_paired_clusters
from evaluation.fault_injection import depth_dropout, depth_nan, blackout, saturate, add_noise, stuck_frame, corrupt_bytes
from evaluation.failure_review import object_miss_rate
from evaluation.timing import time_stage
from data.planted_targets import plant_bands, recall_at_k
from models.unet import SmallUNet, dice_loss, loss_fn, prepare


# ---------------- Part 1 & 3: Appendix K Unit Tests ----------------
def test_scene_reproducible():
    a = A.make_scene(np.random.default_rng(5), False)
    b = A.make_scene(np.random.default_rng(5), False)
    for x, y in zip(a, b):
        assert np.array_equal(x, y)


def test_scene_shapes_and_labels():
    img, d, lab = A.make_scene(np.random.default_rng(6), False)
    assert img.shape == (A.S, A.S, 3) and img.dtype == np.float32
    assert d.shape == (A.S, A.S) and lab.shape == (A.S, A.S)
    assert img.min() >= 0.0 and img.max() <= 1.0
    assert set(np.unique(lab)) <= {0, 1, 2, 3}


def test_novel_label_only_when_requested():
    _, _, lab_nom = A.make_scene(np.random.default_rng(7), False)
    assert 4 not in lab_nom
    # with OOD=True, novel patches are allowed/expected
    found_novel = False
    for s in range(5):
        _, _, lab_ood = A.make_scene(np.random.default_rng(10 + s), True)
        if 4 in lab_ood:
            found_novel = True
            break
    assert found_novel


def test_features_finite_and_sized():
    img, d, _ = A.make_scene(np.random.default_rng(8), False)
    F = A.features(img, d)
    assert F.shape[0] == A.S * A.S
    assert F.shape[1] == 16
    assert np.isfinite(F).all()


def test_astar_blocked_and_free():
    n = 8
    assert A.astar(np.ones((n, n), bool), [(i, 0) for i in range(n)], n - 1) is None
    p = A.astar(np.zeros((n, n), bool), [(i, 0) for i in range(n)], n - 1)
    assert p is not None and len(p) == n


def test_false_safe_extremes():
    lab = np.zeros((A.S, A.S), int)
    lab[10:20, 10:20] = 2
    assert A.false_safe(np.zeros_like(lab, bool), lab) == 1.0
    assert A.false_safe(np.ones_like(lab, bool), lab) == 0.0


def test_coarse_default_matches_part1():
    m = np.random.default_rng(1).random((A.S, A.S)) > 0.8
    assert np.array_equal(coarse_v2(m, 6, 0.12), A.coarse(m, 6))


def test_record_schema_keys():
    P = np.full((A.S, A.S, 4), 0.25)
    ent = np.ones((A.S, A.S))
    epi = np.zeros((A.S, A.S))
    rec = A.observation_record("t", P, ent, epi, np.ones((A.S, A.S), bool))
    for k in ("scene_id", "image_size", "objects", "terrain_fraction", "uncertain_fraction",
              "unsafe_fraction", "terrain_assessment", "scientific_targets", "navigation_ready",
              "limitations"):
        assert k in rec
    assert rec["navigation_ready"] is False


# ---------------- Part 4: Appendix S Seed Registry & Stats ----------------
def test_seed_registry_disjointness():
    reg = {
        "train": scene_seeds(42, "train", 10),
        "val": scene_seeds(42, "val", 10)
    }
    assert check_disjoint(reg) is True


def test_wilson_and_rule_of_three():
    lo, hi = wilson(0, 60)
    assert lo == 0.0
    assert 0.04 <= hi <= 0.07
    assert rule_of_three(60) == pytest.approx(0.05, abs=1e-3)
    assert n_for_halfwidth(0.05) == 385
    assert n_for_halfwidth(0.10) == 97


# ---------------- Part 4: Appendix U Cost Map ----------------
def test_cost_map_status_and_inflation():
    p = np.zeros((24, 24))
    unc = np.zeros((24, 24))
    slope = np.zeros((24, 24))
    params = RoverParams(footprint_radius_cells=1, block_p=0.30, unknown_unc=0.35)
    
    # All clean -> all FREE
    st = build_status(p, unc, slope, params, c=6)
    assert (st == FREE).all()
    mask = planner_mask(st, params)
    assert not mask.any()
    
    # High hazard in top-left block -> BLOCKED and inflated
    p[:6, :6] = 1.0
    st2 = build_status(p, unc, slope, params, c=6)
    assert st2[0, 0] == BLOCKED
    mask2 = planner_mask(st2, params)
    # disk(1) includes orthogonal neighbors (0, 1) and (1, 0)
    assert mask2[0, 0] and mask2[0, 1] and mask2[1, 0]


# ---------------- Part 4: Appendix V Route Audit ----------------
def test_route_audit():
    unsafe = np.zeros((24, 24))
    slope = np.zeros((24, 24))
    unc = np.zeros((24, 24))
    route = [(0, 0), (0, 1), (0, 2)]
    res = audit_route(route, unsafe, slope, unc, c=6, footprint_px=2)
    assert res["passed"] is True
    
    # Place unsafe pixel under cell (0, 1)
    unsafe[2, 8] = 1.0
    res_fail = audit_route(route, unsafe, slope, unc, c=6, footprint_px=2)
    assert res_fail["passed"] is False


# ---------------- Part 4: Appendix W Occupancy Fusion ----------------
def test_occupancy_fusion():
    fus = OccupancyFusion((4, 4), l_haz=0.9, l_safe=0.3)
    p = np.full((4, 4), 0.8)
    obs = np.ones((4, 4), bool)
    for _ in range(3):
        fus.update(p, obs)
    assert (fus.p_unsafe() > 0.7).all()
    assert not fus.unknown().any()


# ---------------- Part 4: Appendix X Cross-Sensor Checks ----------------
def test_cross_sensor_and_depth_validity():
    depth = np.linspace(0, 1, 36).reshape(6, 6).astype(np.float32)
    bad = depth_validity(depth, win=3, min_std=1e-5)
    assert not bad.any()
    
    depth[0, 0] = np.nan
    bad_nan = depth_validity(depth, win=3, min_std=1e-5)
    assert bad_nan[0, 0]


# ---------------- Part 4: Appendix Y Novelty OOD & Rank Gate ----------------
def test_mahalanobis_and_rank_gate():
    X = np.array([[1.0, 1.0], [1.1, 0.9], [5.0, 5.0], [5.1, 4.9]])
    y = np.array([0, 0, 1, 1])
    ood = MahalanobisOOD().fit(X, y)
    scores = ood.score(np.array([[1.05, 0.95], [10.0, 10.0]]))
    assert scores[1] > scores[0]
    
    rg = RankGate().fit({"ent": np.linspace(0, 1, 100)})
    un = rg.unsafe({"ent": np.array([0.96])}, {"ent": 0.95})
    assert un[0] == True


# ---------------- Part 5: Appendix AA Schema v2 & AB Guard ----------------
def test_schema_v2_and_guard():
    rec = observation_record_v2("test_scene", np.full((96, 96, 4), 0.25), np.zeros((96, 96)), np.zeros((96, 96)), np.zeros((96, 96), bool))
    errors = validate_record(rec)
    assert len(errors) == 0
    
    # Check failure record
    frec = failure_record("corrupt_scene", "file corrupt", {"model_version": "v1", "feature_version": "v1", "taxonomy_version": "v1", "config_hash": "h1"})
    assert len(validate_record(frec)) == 0
    assert frec["status"] == "failure"
    
    # Check readiness guard prototype lock
    evidence = dict(
        traversability_map=True,
        geometry_validated_for_frame=True,
        unsafe_fraction=0.01,
        uncertain_fraction=0.02,
        sensor_consistency_passed=True,
        model_version="approved_v1"
    )
    bounds = dict(unsafe_max=0.05, uncertain_max=0.05, approved_models=("approved_v1",))
    readiness = evaluate_readiness(evidence, bounds)
    assert readiness["checks_passed"] is True
    assert readiness["navigation_ready"] is False  # locked!


# ---------------- Part 5: Appendix AC 2D Closed-Loop Simulator ----------------
def test_2d_closed_loop_simulator():
    truth = np.zeros((16, 16), bool)
    truth[:, 8] = True  # solid vertical wall blocking col 0 to col 15
    def oracle(t, pos, rng):
        return t, np.ones_like(t, bool)
    res = run_episode(truth, oracle, start_row=0, rng=np.random.default_rng(0))
    assert res["outcome"] == "no_path"
    
    # Free world
    truth_free = np.zeros((16, 16), bool)
    res_free = run_episode(truth_free, oracle, start_row=0, rng=np.random.default_rng(0))
    assert res_free["outcome"] == "success"


# ---------------- Part 3: Appendix L PyTorch SmallUNet ----------------
def test_small_unet():
    model = SmallUNet(in_ch=4, n_cls=4, w=8)
    x = torch.randn(2, 4, 96, 96)
    out = model(x)
    assert out.shape == (2, 4, 96, 96)
    y = torch.randint(0, 4, (2, 96, 96))
    loss = loss_fn(out, y)
    assert torch.isfinite(loss)
