# Public Engineering Standards Traceability Matrix (Chapters 102 & 171 / Task 83)

> **Scientific Honesty & Institutional Integrity Statement**:  
> APPS is an independent university research prototype using synthetic data. It is **not** a NASA project, is **not** endorsed by NASA or JPL, is **not** flight software, and is **not** flight-qualified. This traceability matrix establishes methodological rigor and software engineering discipline by aligning academic simulation practices with published agency engineering guidelines.

---

## 1. Five-Level Claim Hierarchy (Chapter 174.1)

To prevent misrepresentation and maintain transparency, all software capability claims adhere strictly to this five-tier hierarchy:

- **Level 1 (Inspired by)**: Conceptual alignment with public agency practice or published planetary robotics literature.
- **Level 2 (Implemented)**: Concrete implementation in project source code with functional tests.
- **Level 3 (Verified by Tests)**: Verified by automated, repeatable unit, integration, and statistical tests in continuous execution.
- **Level 4 (Independently Validated)**: Inspected, executed, and validated by an external, independent third-party auditor.
- **Level 5 (Formally Certified / Flight-Qualified)**: Spaceflight qualified under NASA-STD-8739.8 / NPR 7150.2.  
  *Never claimed or reachable by this prototype.*

---

## 2. Traceability Mapping Matrix

| Engineering Practice | Public Reference Document | Claim Level | Implementation Reference | Verification Evidence | Documented Remaining Gap |
|---|---|---|---|---|---|
| **Requirement Traceability** | NASA Systems Engineering Handbook (NASA/SP-2016-6105) §4.2 | **Level 3** | `docs/VALIDATION_REPORT.md` | `tools/assess_level1.py` | Evaluated strictly against synthetic procedural simulation; no physical vehicle or testbed trials. |
| **Mechanical Information Boundary** | JPL Rover Software Architecture / NASA SP-2016-6105 | **Level 3** | `level1/mission/simulator.py` | `results/boundary_tests.json` | Simulated software memory barrier; real rover encounters physical sensor crosstalk and hardware coupling. |
| **Bounded Execution Loops & Determinism** | Holzmann, "The Power of 10: Rules for Safety-Critical Code" & NPR 7150.2 | **Level 3** | `level1/navigation/planner_v2.py`, `level1/mission/loop.py` | `tests/test_level1.py::test_t10_watchdog_monitors` | Python language runtime lacks hard real-time deterministic timing and static memory bounds. |
| **Software Hazard Tracking & Analysis** | NASA-STD-8739.8 (Software Assurance & Safety) | **Level 2** | `docs/SAFETY_AND_FAILURE_ANALYSIS.md` | Hazard log H1–H17 reviewed | Qualitative academic hazard tracking; does not constitute a formal mission safety assurance case. |
| **Configuration Provenance & Audit** | NPR 7150.2 (NASA Software Engineering Requirements) §3.4 | **Level 3** | `configs/cfg.yaml`, `level1/evaluation/manifest.py` | `results/manifest.json`, `tests/test_level1.py` | Relies on local git repository state and SHA-256 digests; lacks signed hardware TPM attestations. |
| **Traversability Cost Mapping** | JPL Mars Exploration Rover (MER) & MSL Autonomous Driving Literature | **Level 2** | `level1/navigation/cost_map.py` | `results/weight_ablation_E23.json` | Uses 2D elevation slope proxy; lacks 3D multi-body wheel-soil sinkage dynamics and vehicle suspension. |
| **Watchdog & Runtime Health Monitors** | NASA Systems Engineering Handbook & NPR 7150.2 §3.8 | **Level 3** | `level1/navigation/monitors.py` | `results/outcome_tests.json` | Heuristic cycle count stall detection without hard RTOS hardware watchdog timers. |
| **Statistical Discipline & Rare-Event Modeling** | NASA Engineering & Safety Center (NESC) Statistical Guidelines | **Level 3** | `level1/evaluation/stats.py` | `results/E13_results.json` | Resampling done across procedural synthetic scene clusters; real Martian terrain has non-stationary spatial correlations. |
| **Predictive Calibration & Novelty Gating** | JPL Autonomous Systems Literature & GNC Standards | **Level 3** | `level1/perception/calibration.py`, `level1/perception/novelty.py` | `results/perception_run.json` | Calibrated on synthetic distributions; domain shift under real Martian atmospheric dust storms remains unquantified. |
| **Worst-Case Failure Recording** | NASA SP-2016-6105 §6.7 (System Failure Modes & Anomaly Reporting) | **Level 3** | `docs/FAILURE_REVIEW.md` | `results/failure_review.json` | Documents 20 worst simulation scenes; physical field testing required to identify environmental edge cases. |

---

## 3. Detailed Gap Analysis & Limitations

### 3.1 Software Runtime vs. Flight Computing
- **Flight Computing (RAD750 / BAE RAD5545)**: Space-grade radiation-hardened processors operate at ~133–466 MHz with strict memory allocations, RTOS (VxWorks / RTEMS), and flight software written in MISRA C/C++.
- **APPS Implementation**: Implemented in Python 3.14 on consumer x86_64 host. Garbage collection, dynamic memory allocation, and interpreter overhead preclude real-time certification.

### 3.2 Sensing & Perception Physics
- **Real Planetary Rovers**: Hazcams and Navcams employ calibrated stereoscopic cameras, active structured light, or LiDAR with optical calibration targets and thermal drift compensation.
- **APPS Implementation**: Uses synthetic 2.5D elevation heightmaps perturbed with Gaussian noise and procedural albedo/texture mapping.

### 3.3 Vehicle Kinodynamics
- **Real Planetary Rovers**: Rocker-bogie passive suspension distributes loads across 6 driven wheels; slip ratio and turn slips are continuously measured via visual odometry and IMU fusion.
- **APPS Implementation**: Grid-based 8-connected cellular stepping with footprint disk dilation ($r_{fp} \ge 1$ cell).

---

## 4. Verification Sign-Off
- **Documented Requirements Mapped**: 10 distinct software engineering practices.
- **Highest Claim Level**: Level 3 (Verified by test).
- **Prohibited Claims (Level 4 & 5)**: Explicitly zero claims made.
- **Requirement 14 (`traceability`) Status**: **MET**
