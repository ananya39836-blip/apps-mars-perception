# APPS Technical Debt & Architectural Gaps Analysis

## 1. Executive Summary

This document identifies specific technical debt, architectural shortcuts, and engineering gaps present in the current codebase that must be remediated to support a credible **NASA TRL 5** assessment for the defined planetary rover terrain perception and autonomous navigation technology scope.

---

## 2. Identified Technical Debt Items

### Debt Item 1: Simulator "Oracle" Pose Dependency
- **Symptom**: In several Level 2 and Level 3 navigation loops, planning and local cost-map centering assume exact, noise-free vehicle coordinates directly from the ground-truth simulation state.
- **Risk**: Overstates navigation performance. Masks the real-world impact of wheel slip, accelerometer drift, and accumulated dead-reckoning errors on traversability mapping and collision avoidance.
- **Remediation**: Implement a standalone Error-State Extended Kalman Filter (ES-EKF) module fusing 6-axis IMU angular rates/accelerations with wheel odometry under non-zero slip. Navigation algorithms must consume the estimated state and covariance rather than ground truth, while retaining ground truth strictly for metric evaluation (ATE / RPE).

### Debt Item 2: Restricted Local Planner Horizon
- **Symptom**: `level2/navigation/primitive_planner.py` evaluates only a single $1.5\text{ m}$ forward circular arc step. When a longer-distance goal (e.g. $20\text{ m}$ across a rocky field) is commanded, there is no continuous kinodynamic path search connecting the rover to the distant target.
- **Risk**: Rover becomes easily trapped in local minima (e.g. U-shaped obstacles, dead ends, or rock clusters) and cannot plan globally optimal, collision-free maneuvers.
- **Remediation**: Implement a Kinodynamic Hybrid $A^*$ / State-Lattice global planner operating in $SE(2)$ configuration space $(x, y, \theta)$ with continuous Dubins/Reeds-Shepp or kinodynamic arc expansions, bounded by minimum turning radius ($\kappa_{\max} = 1.50\text{ m}^{-1}$) and physical rover footprint swept collision checks.

### Debt Item 3: Fragmented Sensor and Coordinate Transformation Pipelines
- **Symptom**: Sensor models (pinhole camera in `level2/`, 3D Flash LiDAR in `level3/`, tactical IMU in `level3/`) exist as standalone classes with disjoint coordinate frame definitions.
- **Risk**: Inconsistent spatial transformations between sensor optical centers, rover base frame ($\mathcal{B}$), map frame ($\mathcal{M}$), and planetary world frame ($\mathcal{W}$).
- **Remediation**: Establish a unified coordinate transform module with explicit $SE(3)$ transformation matrices ($T_{\mathcal{B}\mathcal{S}}, T_{\mathcal{W}\mathcal{B}}$), converting raw sensor point clouds and depth images into a common world/map-aligned elevation grid.

### Debt Item 4: Absence of Formal Operating Mode State Machine
- **Symptom**: Navigation control relies on script-level conditionals and isolated boolean flags (`emergency_stop`, `corridor_locked`).
- **Risk**: Ambiguous transitions during unexpected faults, sensor dropouts, or localization degradation. Inability to guarantee safe-stop latching.
- **Remediation**: Implement a discrete, deterministic 11-mode state machine (`INITIALIZATION`, `SELF_TEST`, `IDLE`, `PERCEPTION`, `LOCALIZATION`, `PLANNING`, `EXECUTION`, `REPLANNING`, `SAFE_STOP`, `RECOVERY`, `MISSION_COMPLETE`, `FAULT`) with explicit precondition and postcondition guards.

### Debt Item 5: Lack of Standardized Multi-Scenario Benchmark Campaign
- **Symptom**: Previous experiments were executed via ad-hoc scripts with varying parameters, making automated multi-seed statistical aggregation and cross-baseline comparisons difficult to reproduce in a single command.
- **Risk**: Insufficient statistical confidence (e.g. small sample sizes, unquantified variances) to substantiate a TRL 5 claim.
- **Remediation**: Build an automated campaign runner (`experiments/run_trl5_campaign.py`) executing 15 standardized scenario classes across deterministic seeds (e.g. 5–20 seeds per class), logging machine-readable JSON records of all primary metrics (ATE, clearance, replans, latency, success rate) and comparing against 3 baseline algorithms and 5 ablation conditions.

### Debt Item 6: Scope Conflation across Architectural Levels
- **Symptom**: The overarching repository bundles extreme deep-space and interstellar concepts (CV-QKD, Dyson swarms, 1PN relativistic orbits, Titan submarines) with surface rover perception.
- **Risk**: Confuses the operational design domain (ODD) of surface rover autonomy with unverified planetary and interstellar mission claims.
- **Remediation**: Formally separate the core surface rover autonomy scope into a dedicated package (`trl5_navigation/`), documenting that TRL 5 assessment applies strictly to surface rover terrain perception and navigation, while higher-level concepts are treated as distinct research extensions.
