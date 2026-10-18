# APPS Level 1 Failure Review: 20 Worst-Case Scenes (Chapter 170 / Task 82)

> **Research Disclaimer**: Synthetic procedural terrain research prototype. Evaluated under unmitigated baseline sensing to isolate edge-case failure modes and inform uncertainty-aware safety guards.

---

## 1. Executive Summary of Failure Review
As mandated by Chapter 170 and Verification Requirement 12 (`failures_recorded`), this document details the **20 worst-case failure scenes** ranked strictly by unmitigated missed hazard area (false-safe pixels).

- **Evaluation Population**: 50 procedurally generated test scenes across difficulty ladder D1–D5 with novel materials N1–N4, atmospheric haze (0.0–0.5), and low solar elevation angles (15°–50°).
- **Worst Scene Missed Area**: 1492 pixels (46.38% of total hazard area).
- **Median Missed Area (Top 20)**: 1079 pixels (42.21%).
- **Primary Causal Factors**: Atmospheric haze scattering flattening elevation disparity, extreme solar azimuth shadow occlusion, and low-contrast novel material albedo matching.

---

## 2. Table of 20 Worst Failure Scenes

| Rank | Scene ID | Seed | Condition | Total Hazard (px) | Missed Hazard (px) | Missed Area (%) | Overlay Artifact | Causal Summary |
|---|---|---|---|---|---|---|---|---|
| **1** | `SCENE_FAIL_003` | `7102` | D5-N3-Haze0.10-SunEl50° | 3217 | **1492** | **46.38%** | [`results/overlays/fail_01_seed_7102.png`](results/overlays/fail_01_seed_7102.png) | High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features. |
| **2** | `SCENE_FAIL_012` | `7111` | D5-N4-Haze0.10-SunEl45° | 2979 | **1349** | **45.28%** | [`results/overlays/fail_02_seed_7111.png`](results/overlays/fail_02_seed_7111.png) | Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries. |
| **3** | `SCENE_FAIL_048` | `7147` | D5-N4-Haze0.10-SunEl45° | 3150 | **1305** | **41.43%** | [`results/overlays/fail_03_seed_7147.png`](results/overlays/fail_03_seed_7147.png) | Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries. |
| **4** | `SCENE_FAIL_027` | `7126` | D5-N3-Haze0.10-SunEl50° | 3260 | **1285** | **39.42%** | [`results/overlays/fail_04_seed_7126.png`](results/overlays/fail_04_seed_7126.png) | High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features. |
| **5** | `SCENE_FAIL_004` | `7103` | D5-N4-Haze0.30-SunEl15° | 2569 | **1262** | **49.12%** | [`results/overlays/fail_05_seed_7103.png`](results/overlays/fail_05_seed_7103.png) | Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries. |
| **6** | `SCENE_FAIL_015` | `7114` | D5-N3-Haze0.10-SunEl50° | 3009 | **1229** | **40.84%** | [`results/overlays/fail_06_seed_7114.png`](results/overlays/fail_06_seed_7114.png) | High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features. |
| **7** | `SCENE_FAIL_050` | `7149` | D5-N2-Haze0.20-SunEl25° | 2584 | **1167** | **45.16%** | [`results/overlays/fail_07_seed_7149.png`](results/overlays/fail_07_seed_7149.png) | Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold. |
| **8** | `SCENE_FAIL_028` | `7127` | D5-N4-Haze0.30-SunEl15° | 3486 | **1148** | **32.93%** | [`results/overlays/fail_08_seed_7127.png`](results/overlays/fail_08_seed_7127.png) | Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries. |
| **9** | `SCENE_FAIL_046` | `7145` | D3-Haze0.35-SunEl25° | 2041 | **1112** | **54.48%** | [`results/overlays/fail_09_seed_7145.png`](results/overlays/fail_09_seed_7145.png) | Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes. |
| **10** | `SCENE_FAIL_039` | `7138` | D5-N3-Haze0.10-SunEl50° | 2556 | **1079** | **42.21%** | [`results/overlays/fail_10_seed_7138.png`](results/overlays/fail_10_seed_7138.png) | High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features. |
| **11** | `SCENE_FAIL_013` | `7112` | D5-N1-SunEl40° | 2620 | **1078** | **41.15%** | [`results/overlays/fail_11_seed_7112.png`](results/overlays/fail_11_seed_7112.png) | Bluish novel material patch (N1) exhibits low surface roughness, causing the texture extractor to classify it as benign bedrock. |
| **12** | `SCENE_FAIL_040` | `7139` | D5-N4-Haze0.30-SunEl15° | 2712 | **1047** | **38.61%** | [`results/overlays/fail_12_seed_7139.png`](results/overlays/fail_12_seed_7139.png) | Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries. |
| **13** | `SCENE_FAIL_023` | `7122` | D4-Haze0.20-SunEl30° | 2564 | **1016** | **39.63%** | [`results/overlays/fail_13_seed_7122.png`](results/overlays/fail_13_seed_7122.png) | Cul-de-sac bounding wall shadowed by low sun angle blends visually into basalt bedrock flatlands. |
| **14** | `SCENE_FAIL_037` | `7136` | D5-N1-SunEl40° | 3193 | **1015** | **31.79%** | [`results/overlays/fail_14_seed_7136.png`](results/overlays/fail_14_seed_7136.png) | Bluish novel material patch (N1) exhibits low surface roughness, causing the texture extractor to classify it as benign bedrock. |
| **15** | `SCENE_FAIL_002` | `7101` | D5-N2-Haze0.20-SunEl25° | 2471 | **983** | **39.78%** | [`results/overlays/fail_15_seed_7101.png`](results/overlays/fail_15_seed_7101.png) | Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold. |
| **16** | `SCENE_FAIL_005` | `7104` | D3-Haze0.40-SunEl30° | 2236 | **969** | **43.34%** | [`results/overlays/fail_16_seed_7104.png`](results/overlays/fail_16_seed_7104.png) | Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes. |
| **17** | `SCENE_FAIL_045` | `7144` | D5-N2-Haze0.40-SunEl20° | 2162 | **966** | **44.68%** | [`results/overlays/fail_17_seed_7144.png`](results/overlays/fail_17_seed_7144.png) | Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold. |
| **18** | `SCENE_FAIL_014` | `7113` | D5-N2-Haze0.20-SunEl25° | 2525 | **948** | **37.54%** | [`results/overlays/fail_18_seed_7113.png`](results/overlays/fail_18_seed_7113.png) | Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold. |
| **19** | `SCENE_FAIL_041` | `7140` | D3-Haze0.40-SunEl30° | 1962 | **948** | **48.32%** | [`results/overlays/fail_19_seed_7140.png`](results/overlays/fail_19_seed_7140.png) | Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes. |
| **20** | `SCENE_FAIL_007` | `7106` | D4-Haze0.15-SunEl35° | 2358 | **944** | **40.03%** | [`results/overlays/fail_20_seed_7106.png`](results/overlays/fail_20_seed_7106.png) | Cul-de-sac bounding wall shadowed by low sun angle blends visually into basalt bedrock flatlands. |

---

## 3. Case-by-Case Failure Analysis

### Case 1: SCENE_FAIL_003 (Seed 7102 — D5-N3-Haze0.10-SunEl50°)
- **Missed Hazard Area**: 1492 px out of 3217 px (46.38%).
- **Overlay Visualization**: [`results/overlays/fail_01_seed_7102.png`](results/overlays/fail_01_seed_7102.png)
- **Mechanism**: High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 2: SCENE_FAIL_012 (Seed 7111 — D5-N4-Haze0.10-SunEl45°)
- **Missed Hazard Area**: 1349 px out of 2979 px (45.28%).
- **Overlay Visualization**: [`results/overlays/fail_02_seed_7111.png`](results/overlays/fail_02_seed_7111.png)
- **Mechanism**: Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 3: SCENE_FAIL_048 (Seed 7147 — D5-N4-Haze0.10-SunEl45°)
- **Missed Hazard Area**: 1305 px out of 3150 px (41.43%).
- **Overlay Visualization**: [`results/overlays/fail_03_seed_7147.png`](results/overlays/fail_03_seed_7147.png)
- **Mechanism**: Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 4: SCENE_FAIL_027 (Seed 7126 — D5-N3-Haze0.10-SunEl50°)
- **Missed Hazard Area**: 1285 px out of 3260 px (39.42%).
- **Overlay Visualization**: [`results/overlays/fail_04_seed_7126.png`](results/overlays/fail_04_seed_7126.png)
- **Mechanism**: High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 5: SCENE_FAIL_004 (Seed 7103 — D5-N4-Haze0.30-SunEl15°)
- **Missed Hazard Area**: 1262 px out of 2569 px (49.12%).
- **Overlay Visualization**: [`results/overlays/fail_05_seed_7103.png`](results/overlays/fail_05_seed_7103.png)
- **Mechanism**: Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 6: SCENE_FAIL_015 (Seed 7114 — D5-N3-Haze0.10-SunEl50°)
- **Missed Hazard Area**: 1229 px out of 3009 px (40.84%).
- **Overlay Visualization**: [`results/overlays/fail_06_seed_7114.png`](results/overlays/fail_06_seed_7114.png)
- **Mechanism**: High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 7: SCENE_FAIL_050 (Seed 7149 — D5-N2-Haze0.20-SunEl25°)
- **Missed Hazard Area**: 1167 px out of 2584 px (45.16%).
- **Overlay Visualization**: [`results/overlays/fail_07_seed_7149.png`](results/overlays/fail_07_seed_7149.png)
- **Mechanism**: Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 8: SCENE_FAIL_028 (Seed 7127 — D5-N4-Haze0.30-SunEl15°)
- **Missed Hazard Area**: 1148 px out of 3486 px (32.93%).
- **Overlay Visualization**: [`results/overlays/fail_08_seed_7127.png`](results/overlays/fail_08_seed_7127.png)
- **Mechanism**: Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 9: SCENE_FAIL_046 (Seed 7145 — D3-Haze0.35-SunEl25°)
- **Missed Hazard Area**: 1112 px out of 2041 px (54.48%).
- **Overlay Visualization**: [`results/overlays/fail_09_seed_7145.png`](results/overlays/fail_09_seed_7145.png)
- **Mechanism**: Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 10: SCENE_FAIL_039 (Seed 7138 — D5-N3-Haze0.10-SunEl50°)
- **Missed Hazard Area**: 1079 px out of 2556 px (42.21%).
- **Overlay Visualization**: [`results/overlays/fail_10_seed_7138.png`](results/overlays/fail_10_seed_7138.png)
- **Mechanism**: High-albedo bright material (N3) causes sensor glare saturation, washing out high-frequency elevation edge features.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 11: SCENE_FAIL_013 (Seed 7112 — D5-N1-SunEl40°)
- **Missed Hazard Area**: 1078 px out of 2620 px (41.15%).
- **Overlay Visualization**: [`results/overlays/fail_11_seed_7112.png`](results/overlays/fail_11_seed_7112.png)
- **Mechanism**: Bluish novel material patch (N1) exhibits low surface roughness, causing the texture extractor to classify it as benign bedrock.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 12: SCENE_FAIL_040 (Seed 7139 — D5-N4-Haze0.30-SunEl15°)
- **Missed Hazard Area**: 1047 px out of 2712 px (38.61%).
- **Overlay Visualization**: [`results/overlays/fail_12_seed_7139.png`](results/overlays/fail_12_seed_7139.png)
- **Mechanism**: Dark rock-like material (N4) under low sun elevation creates deceptive shadows merged with shallow terrain, masking rock boundaries.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 13: SCENE_FAIL_023 (Seed 7122 — D4-Haze0.20-SunEl30°)
- **Missed Hazard Area**: 1016 px out of 2564 px (39.63%).
- **Overlay Visualization**: [`results/overlays/fail_13_seed_7122.png`](results/overlays/fail_13_seed_7122.png)
- **Mechanism**: Cul-de-sac bounding wall shadowed by low sun angle blends visually into basalt bedrock flatlands.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 14: SCENE_FAIL_037 (Seed 7136 — D5-N1-SunEl40°)
- **Missed Hazard Area**: 1015 px out of 3193 px (31.79%).
- **Overlay Visualization**: [`results/overlays/fail_14_seed_7136.png`](results/overlays/fail_14_seed_7136.png)
- **Mechanism**: Bluish novel material patch (N1) exhibits low surface roughness, causing the texture extractor to classify it as benign bedrock.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 15: SCENE_FAIL_002 (Seed 7101 — D5-N2-Haze0.20-SunEl25°)
- **Missed Hazard Area**: 983 px out of 2471 px (39.78%).
- **Overlay Visualization**: [`results/overlays/fail_15_seed_7101.png`](results/overlays/fail_15_seed_7101.png)
- **Mechanism**: Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 16: SCENE_FAIL_005 (Seed 7104 — D3-Haze0.40-SunEl30°)
- **Missed Hazard Area**: 969 px out of 2236 px (43.34%).
- **Overlay Visualization**: [`results/overlays/fail_16_seed_7104.png`](results/overlays/fail_16_seed_7104.png)
- **Mechanism**: Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 17: SCENE_FAIL_045 (Seed 7144 — D5-N2-Haze0.40-SunEl20°)
- **Missed Hazard Area**: 966 px out of 2162 px (44.68%).
- **Overlay Visualization**: [`results/overlays/fail_17_seed_7144.png`](results/overlays/fail_17_seed_7144.png)
- **Mechanism**: Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 18: SCENE_FAIL_014 (Seed 7113 — D5-N2-Haze0.20-SunEl25°)
- **Missed Hazard Area**: 948 px out of 2525 px (37.54%).
- **Overlay Visualization**: [`results/overlays/fail_18_seed_7113.png`](results/overlays/fail_18_seed_7113.png)
- **Mechanism**: Subtle low-contrast novel material (N2) matches background sand albedo while haze flattens depth gradients, bypassing threshold.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 19: SCENE_FAIL_041 (Seed 7140 — D3-Haze0.40-SunEl30°)
- **Missed Hazard Area**: 948 px out of 1962 px (48.32%).
- **Overlay Visualization**: [`results/overlays/fail_19_seed_7140.png`](results/overlays/fail_19_seed_7140.png)
- **Mechanism**: Narrow bottleneck corridor with steep sidewalls casts deep shadows at low solar elevation, causing shadow-edge false safes.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

### Case 20: SCENE_FAIL_007 (Seed 7106 — D4-Haze0.15-SunEl35°)
- **Missed Hazard Area**: 944 px out of 2358 px (40.03%).
- **Overlay Visualization**: [`results/overlays/fail_20_seed_7106.png`](results/overlays/fail_20_seed_7106.png)
- **Mechanism**: Cul-de-sac bounding wall shadowed by low sun angle blends visually into basalt bedrock flatlands.
- **Mitigation in System C**: System C incorporates multi-cue Mahalanobis OOD novelty gating ($RankGate$) and conservative unknown-cell frontier blocking ($r_{block} = 0.30, u_{block} = 0.35$). These safeguards flag unconfident and subtle novel regions as untraversable, driving the rover collision rate to 0.0% in Experiment E13.

---

## 4. Verification & Audit Sign-Off
- **Total Documented Failure Cases**: 20
- **Verification Evidence File**: `results/failure_review.json`
- **Requirement 12 (`failures_recorded`) Status**: **MET**
