"""Unit tests for APPS-0.1 core perception and planning pipeline.
Part 3 Appendix K.
"""
import numpy as np
import pytest
import apps01 as A
from nav_v2 import coarse_v2, nav_eval_v2


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
