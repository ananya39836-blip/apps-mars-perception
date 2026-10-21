# APPS Requirements Traceability Matrix (RTM) — TRL 8 Baseline

**Document ID**: `APPS-RTM-TRL8-001`  
**Revision**: 3.0.0  
**Classification**: NASA TRL 8 Verification Traceability  
**Safety Status**: Compile-Time Research Locks Active (`PROTOTYPE_LOCK = True`, `NAVIGATION_READY = False`)  

---

## 1. Traceability Methodology

Every requirement specified in `docs/system_requirements.md` is mapped forward to its implementing module, test verification procedure, test identifier, acceptance threshold, and qualification evidence location.

Verification Methods:
- **T**: Automated Unit / Integration Test
- **A**: Engineering Analysis / Mathematical Proof
- **D**: Behavioral Demonstration
- **I**: Code / Architectural Inspection

---

## 2. Requirements Traceability Matrix

| Req ID | Requirement Summary | Subsystem | Implementing Source File | Verification Method | Formal Test ID | Acceptance Threshold | Compliance Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TRL8-REQ-01** | Research Guard Latches | System Safety | `trl8_navigation/__init__.py` | `T`, `I` | `test_safety_invariants_latched` | `PROTOTYPE_LOCK == True`, `NAVIGATION_READY == False` | **VERIFIED** |
| **TRL8-REQ-02** | Coordinate Standardization | Sensors | `trl8_navigation/sensors/coordinate_transforms.py` | `T`, `A` | `test_transform_se3_composition_and_inverse` | Round-trip error $||\mathbf{T}\mathbf{T}^{-1}-\mathbf{I}|| \le 10^{-10}$ | **VERIFIED** |
| **TRL8-REQ-03** | CCSDS Telemetry Framing | Hardware / Tel | `trl8_navigation/hardware/hardware_interface.py` | `T` | `test_ccsds_telemetry_packet_framing` | Valid CRC-16 on uncorrupted packets; bit-flip drops | **VERIFIED** |
| **TRL8-REQ-04** | Telemetry Ingestion Gatekeeper | Sensors | `trl8_navigation/sensors/sensor_validator.py` | `T` | `test_sensor_validator_rejects_nan_inf` | 100% NaN/Inf rejected; zero crash | **VERIFIED** |
| **TRL8-REQ-05** | Point Cloud PMF Segmentation | Perception | `trl8_navigation/perception/point_cloud_processor.py` | `T` | `test_point_cloud_processor_voxel_and_ground` | Recall $\ge 90\%$, Precision $\ge 90\%$, Latency $\le 20\text{ ms}$ | **VERIFIED** |
| **TRL8-REQ-06** | 2.5D Elevation Kalman Mapping | Perception | `trl8_navigation/perception/elevation_mapping.py` | `T` | `test_elevation_mapping_kalman_update` | Monotonic variance reduction; RMSE $\le 0.05\text{ m}$ | **VERIFIED** |
| **TRL8-REQ-07** | Traversability Cost Assessment | Perception | `trl8_navigation/perception/traversability.py` | `T` | `test_traversability_evaluation_and_inflation` | Flat ground $C \le 0.15$; slope $>30^\circ \implies C=1.0$ | **VERIFIED** |
| **TRL8-REQ-08** | 15-State Error-State EKF | Localization | `trl8_navigation/localization/error_state_ekf.py` | `T`, `A` | `test_es_ekf_joseph_update` | Covariance positive definite; drift $\le 3.0\%$ | **VERIFIED** |
| **TRL8-REQ-09** | Dual-Mode Oracle vs Estimated | Localization | `trl8_navigation/localization/state_monitor.py` | `T` | `test_state_monitor_metrics` | ATE RMSE and RPE tracked without oracle bleed | **VERIFIED** |
| **TRL8-REQ-10** | Swept OBB Collision Checking | Planning | `trl8_navigation/planning/collision_checker.py` | `T` | `test_collision_checker_obb` | Zero false negatives; check latency $\le 0.10\text{ ms}$ | **VERIFIED** |
| **TRL8-REQ-11** | Kinodynamic Hybrid A* Planning | Planning | `trl8_navigation/planning/kinodynamic_hybrid_astar.py` | `T` | `test_kinodynamic_planner_curvature_bound` | Curvature $|\kappa| \le 1.50\text{ m}^{-1}$; search $\le 80\text{ ms}$ | **VERIFIED** |
| **TRL8-REQ-12** | Curvature Derating Tracking | Control | `trl8_navigation/control/path_tracker.py` | `T` | `test_path_tracker_pure_pursuit` | $a_{lat} \le 0.30\text{ m/s}^2$; cross-track error $\le 0.25\text{ m}$ | **VERIFIED** |
| **TRL8-REQ-13** | Certified Safe Stop Controller | Control | `trl8_navigation/control/safe_stop_controller.py` | `T` | `test_safe_stop_controller` | Stopping distance $\le 0.60\text{ m}$; monotonic halt | **VERIFIED** |
| **TRL8-REQ-14** | Rocker-Bogie & Terramechanics | Dynamics | `trl8_navigation/dynamics/rocker_bogie.py` | `T` | `test_rocker_bogie_kinematics` | Normal load sum equals $m \cdot g_{mars} \pm 1\%$; 6-wheel contact | **VERIFIED** |
| **TRL8-REQ-15** | 13-State Deterministic FDIR | Executive | `trl8_navigation/mission/state_machine.py` | `T`, `D` | `test_fdir_executive_transitions` | 13 explicit states; zero illegal transitions | **VERIFIED** |
| **TRL8-REQ-16** | Cycle Time Watchdog Monitor | FDIR | `trl8_navigation/fdir/watchdog.py` | `T` | `test_watchdog_deadline_monitor` | Synthetic delay $>100\text{ ms}$ trips fault counter | **VERIFIED** |
| **TRL8-REQ-17** | Monte-Carlo Qualification | Framework | `qualification/run_qualification_campaign.py` | `T`, `A` | `qualification_campaign_20_scenarios` | 20 operational scenarios executed; Wilson 95% CIs | **VERIFIED** |

---

## 3. Subsystem Cross-Traceability Summary

- **Total Requirements**: 17 Formal Requirements
- **Verification Coverage**: 100% of requirements mapped to automated unit/integration tests
- **Automated Verification**: `pytest tests/test_trl8_*.py`
- **Safety Critical Invariants**: `TRL8-REQ-01`, `TRL8-REQ-10`, `TRL8-REQ-13`, `TRL8-REQ-15`, `TRL8-REQ-16` (5 requirements with fail-safe hardware/software interlocks)
