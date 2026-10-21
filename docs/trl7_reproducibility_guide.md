# Reproducibility and Operational Verification Guide (NASA TRL 7)
**Project Name**: APPS — Automated Planetary Perception System  
**Document Identifier**: APPS-TRL7-RPG-001  
**Software Baseline**: `2.7.0-trl7`  

---

## 1. System Requirements & Environment Setup

### 1.1 Python Environment
- Python Version: $\ge 3.10$ (tested on Python 3.10, 3.11, and 3.14 on Windows and Linux)
- Core Scientific Stack: `numpy`, `scipy`, `matplotlib`, `plotly`, `pytest`, `streamlit`

### 1.2 Verification of Safety Invariants
Before running any mission script or test, verify that the compile-time safety latches are active:
```python
import trl7_navigation as t7
assert t7.PROTOTYPE_LOCK is True
assert t7.NAVIGATION_READY is False
print("Safety locks verified:", t7.SOFTWARE_VERSION)
```

---

## 2. Executing Automated Test Suite

Run the full automated test suite (TRL 5 + TRL 7 regression and operational tests):
```bash
python -m pytest tests/test_trl7_perception.py tests/test_trl7_navigation.py -v
```
Expected output:
```
tests/test_trl7_perception.py::test_safety_invariants_latched PASSED
tests/test_trl7_perception.py::test_euler_quaternion_roundtrip PASSED
tests/test_trl7_perception.py::test_transform_se3_composition_and_inverse PASSED
tests/test_trl7_perception.py::test_sensor_validator_rejects_nan_inf PASSED
tests/test_trl7_perception.py::test_point_cloud_processor_voxel_and_ground PASSED
tests/test_trl7_perception.py::test_elevation_mapping_kalman_update PASSED
tests/test_trl7_perception.py::test_negative_obstacle_detection PASSED
tests/test_trl7_perception.py::test_traversability_evaluation_and_inflation PASSED
tests/test_trl7_perception.py::test_perception_metrics PASSED
tests/test_trl7_navigation.py::test_es_ekf_joseph_update PASSED
tests/test_trl7_navigation.py::test_state_monitor_metrics PASSED
tests/test_trl7_navigation.py::test_collision_checker_obb PASSED
tests/test_trl7_navigation.py::test_kinodynamic_planner_curvature_bound PASSED
tests/test_trl7_navigation.py::test_path_tracker_pure_pursuit PASSED
tests/test_trl7_navigation.py::test_safe_stop_controller PASSED
tests/test_trl7_navigation.py::test_rocker_bogie_kinematics PASSED
tests/test_trl7_navigation.py::test_terramechanics_soil_model PASSED
tests/test_trl7_navigation.py::test_fdir_executive_transitions PASSED
tests/test_trl7_navigation.py::test_closed_loop_short_mission PASSED

============================= 19 passed in 17.34s =============================
```

---

## 3. Executing the 20-Scenario Validation Campaign

To execute the Monte-Carlo campaign across all 20 standardized scenario classes and compute statistical Wilson confidence intervals:
```bash
python experiments/run_trl7_campaign.py
```
This produces structured evidence artifacts in `results/trl7/`:
- `results/trl7/campaign_summary.json`: Aggregated scenario metrics, Wilson score 95% CIs, ATE RMSEs, replans.
- `results/trl7/campaign_all_runs.csv`: Tabular run-by-run metrics across all seeds.
- `results/trl7/ablation_study.json`: Comparative metrics evaluating Full Pipeline vs Ablated variants.

---

## 4. Launching the Operational Ground Station Dashboard

To launch the real-time operational dashboard with 3D DEM visualizer, live telemetry feeds, and interactive scenario loader:
```bash
streamlit run apps_trl7_dashboard.py
```
Key Dashboard Capabilities:
- **3D Terrain Explorer**: Pan, zoom, and inspect continuous DEM topography, rock fields, and craters.
- **Closed-Loop Traverse Runner**: Dispatch autonomous rovers across any of the 20 scenario classes with animated ground-truth vs estimated trajectory traces.
- **Traversability Visualizer**: Heatmap inspection of slope, step hazard, and composite cost.
- **15-State ES-EKF Inspector**: Attitude quaternions, body velocity constraints, and error covariance traces.
- **Validation Manifest Downloader**: Export verification JSON manifests directly from the UI.
