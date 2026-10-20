# APPS NASA TRL 5 Implementation Roadmap & Phased Execution Plan

## 1. Engineering Strategy

To transform the **Automated Planetary Perception System (APPS)** into a technically rigorous, experimentally validated planetary rover perception and autonomous navigation research system demonstrating characteristics consistent with **Technology Readiness Level 5 (TRL 5)**, work is organized into an incremental, traceable 15-phase execution plan.

---

## 2. Phased Execution Roadmap

```mermaid
flowchart TD
    P1[Phase 1: Repo Audit & Docs] --> P2[Phase 2: Define TRL 5 Scope & Requirements]
    P2 --> P3[Phase 3: 3D Planetary Environment Engine]
    P3 --> P4[Phase 4: Sensor Rig & Perception Pipeline]
    P4 --> P5[Phase 5: Localization & Error-State EKF]
    P5 --> P6[Phase 6: Kinodynamic Hybrid A* Planner & Motion Control]
    P6 --> P7[Phase 7: Rover Multibody & Terramechanics Validation]
    P7 --> P8[Phase 8: Automated 15-Scenario Validation Campaign]
    P8 --> P9[Phase 9: Baseline Comparison & Ablation Studies]
    P9 --> P10[Phase 10: 11-State Operating FSM & Safe-Stop FDIR]
    P10 --> P11[Phase 11: Level 4 & 5 Extensions]
    P11 --> P12[Phase 12: Streamlit Validation Dashboard]
    P12 --> P13[Phase 13: Experiment Data & Reproducibility Harness]
    P13 --> P14[Phase 14: Automated Test Suite & CI Regression Guard]
    P14 --> P15[Phase 15: Final Engineering Evidence Package]
```

### Phase Schedule & Implementation Breakdown

| Phase | Title | Core Deliverables & Technical Scope |
|:---|:---|:---|
| **Phase 1** | Repository Audit & Preservation | Baseline test run (176/176 pass), architecture audit, capability matrix, technical debt ledger, roadmap. |
| **Phase 2** | Define TRL 5 Target Scope | System requirements, operational design domain (ODD), acceptance criteria, and traceability matrix in `docs/`. |
| **Phase 3** | Planetary Environment Simulation | Configurable 3D DEM, slope gradients ($\le 25^\circ$), crater generator, rock/boulder fields, loose regolith patches, narrow passages in `trl5_navigation/environment/`. |
| **Phase 4** | Real Multi-Sensor Perception Pipeline | Synthetic sensor rig (RGB-D, 3D LiDAR, 6-axis IMU, wheel odometry), point cloud coordinate transforms, 2.5D elevation grid with uncertainty, multi-criteria traversability cost map in `trl5_navigation/perception/`. |
| **Phase 5** | Localization & State Estimation | Explicit reference frames ($\mathcal{W}, \mathcal{M}, \mathcal{B}, \mathcal{S}$), Error-State Extended Kalman Filter (ES-EKF) fusing odometry and IMU, trajectory error metrics (ATE / RPE) in `trl5_navigation/localization/`. |
| **Phase 6** | Kinodynamic Path Planning & Control | Kinodynamic Hybrid $A^*$ / State-Lattice planner with minimum turning radius ($\kappa_{\max} = 1.5\text{ m}^{-1}$), swept chassis footprint collision checking, closed-loop path follower, and dynamic replanning in `trl5_navigation/planning/`. |
| **Phase 7** | Physics & Terramechanics Validation | 6-DOF rigid-body Newton-Euler equations under Martian gravity ($g = 3.71\text{ m/s}^2$), rocker-bogie kinematics, Bekker-Wong pressure-sinkage and drawbar pull validation in `trl5_navigation/dynamics/`. |
| **Phase 8** | 15-Scenario Validation Campaign | Automated multi-seed test campaign across 15 planetary scenario classes, logging JSON records of all primary metrics in `experiments/run_trl5_campaign.py`. |
| **Phase 9** | Baselines & Ablation Studies | Quantitative comparative benchmarking against 3 baselines (Straight-line, 2D Grid $A^*$, Terrain $A^*$) and 5 ablation conditions in `trl5_navigation/experiments/`. |
| **Phase 10** | Operating FSM & Safe-Stop FDIR | Formal 11-mode discrete state machine (`INITIALIZATION` to `FAULT`) with fail-safe safe-stop deceleration in `trl5_navigation/executive/`. |
| **Phase 11** | Level 4 & 5 Extensions | Cooperative aerial scout elevation relay and multi-rover decentralized map sharing in `trl5_navigation/extensions/`. |
| **Phase 12** | Professional Validation Dashboard | Interactive Streamlit dashboard (`apps_trl5_dashboard.py`) with 3D terrain, trajectory plots, real-time sensor views, traversability maps, and campaign analytics. |
| **Phase 13** | Experiment Management & CLI | Structured directories (`configs/`, `scenarios/`, `results/trl5/`, `reports/`), machine-readable JSON/CSV logs, and CLI reproduction harness. |
| **Phase 14** | Software Engineering & Testing | Comprehensive unit and integration test suite (`tests/test_trl5_*.py`), type hints, docstrings, and zero regressions across all 176 existing tests. |
| **Phase 15** | Final Engineering Evidence Package | Complete suite of 9 formal verification documents in `docs/` summarizing requirements, architecture, algorithms, and honest TRL 5 assessment. |
