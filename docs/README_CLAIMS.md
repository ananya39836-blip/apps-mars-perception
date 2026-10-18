# README Claims Verification Table (Chapter 174 / Task 84)

| Claim ID | Exact Statement | Source File | Test Verification | Results File | Status |
|---|---|---|---|---|---|
| 1 | Procedural synthetic Mars-like terrain generation with difficulty ladder (D0 to D5) and multi-novel materials (N1 to N4). | `level1/terrain/generator_v2.py` | `tests/test_level1.py::test_t2_difficulty_ladder_generation` | `results/manifest.json` | **verified in code** |
| 2 | Multi-feature pixel extraction combining visual color/texture and geometric depth gradients. | `level1/perception/features_v2.py` | `tests/test_all.py::test_features_finite_and_sized` | `results/manifest.json` | **verified in code** |
| 3 | Gradient boosting ensemble classifier providing multi-class logits and predictive entropy. | `models/ensemble.py` | `tests/test_all.py::test_scene_shapes_and_labels` | `results/manifest.json` | **verified in code** |
| 4 | Out-of-distribution (OOD) novelty scoring via Mahalanobis distance in feature space and percentile-based RankGate. | `level1/perception/novelty.py` | `tests/test_all.py::test_mahalanobis_and_rank_gate` | `results/manifest.json` | **verified in code** |
| 5 | Calibrated temperature scaling fitted strictly on validation data to minimize expected calibration error (ECE). | `level1/perception/calibration.py` | `tests/test_level1.py` | `results/manifest.json` | **verified in code** |
| 6 | Footprint-aware traversability cost map builder with circular disk and Chebyshev obstacle inflation. | `level1/navigation/cost_map.py` | `tests/test_level1.py::test_t6_cost_and_footprint_inflation` | `results/manifest.json` | **verified in code** |
| 7 | Multi-criteria A* planner minimizing path length, obstacle risk, uncertainty, and slope energy proxy. | `level1/navigation/planner_v2.py` | `tests/test_level1.py::test_t7_astar_correctness` | `results/manifest.json` | **verified in code** |
| 8 | Route risk budgeting rejecting routes when cumulative risk proxy p_proxy > p_budget. | `level1/navigation/planner_v2.py` | `tests/test_level1.py::test_t9_risk_budget_rejection` | `results/manifest.json` | **verified in code** |
| 9 | Closed-loop replanning on obstacle discovery with watchdog monitors (no-progress, replan cap, sensor outage). | `level1/mission/loop.py` | `tests/test_level1.py::test_t10_watchdog_monitors` | `results/manifest.json` | **verified in code** |
| 10 | Independent route verification audit catching illegal jumps and newly blocked cells. | `level1/navigation/route_audit.py` | `tests/test_level1.py::test_t12_route_audit_validator` | `results/manifest.json` | **verified in code** |
| 11 | Statistical evaluation using cluster bootstrap resampling at the scene level with Wilson score rare-event bounds. | `level1/evaluation/stats.py` | `tests/test_all.py::test_wilson_and_rule_of_three` | `results/manifest.json` | **verified in code** |
| 12 | Cryptographic archive manifests and pre-registration hash locking. | `level1/evaluation/manifest.py` | `tests/test_level1.py::test_t18_manifest_integrity` | `results/manifest.json` | **verified in code** |
