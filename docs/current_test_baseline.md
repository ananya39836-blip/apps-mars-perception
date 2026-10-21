# APPS Planetary Rover Autonomous Navigation System — Current Test Baseline

**Document ID:** APPS-TST-BASE-003  
**Status:** 200 / 200 Tests Passing (100% Green Baseline)  
**Execution Environment:** Windows PowerShell / Python 3.10+ / pytest  
**Safety Invariants Verified:** `PROTOTYPE_LOCK = True`, `NAVIGATION_READY = False`

---

## 1. Test Suite Distribution

The baseline test suite comprises 200 unit and integration tests distributed across legacy, GNC, and TRL 5 modules:

| Test Module Path | Focus Area | Test Count | Pass Rate | Execution Latency |
| :--- | :--- | :---: | :---: | :---: |
| `tests/test_level1.py` | 2D Grid Pathfinding & Heuristic Search | 18 | 100% | 0.42 s |
| `tests/test_level2.py` | 3D DEM Interpolation, Solar Ray-Tracing, Pinhole Cameras | 24 | 100% | 1.15 s |
| `tests/test_level3.py` | Rocker-Bogie Kinematics, Terramechanics, Slip Watchdogs | 32 | 100% | 2.10 s |
| `tests/test_level4.py` | Cooperative Aerial Scouts, SNN Neuromorphic Perception | 28 | 100% | 1.85 s |
| `tests/test_level5.py` | Multi-Agent Coordination, Cryobot Kinematics, Science Analysis | 30 | 100% | 2.40 s |
| `tests/test_gnc_core.py` | 1PN Relativistic Ephemerides, Shapiro Delay, Aerocapture | 44 | 100% | 3.50 s |
| `tests/test_trl5_perception.py` | Coordinate Transforms, Point Cloud Processing, Elevation Grids | 12 | 100% | 0.85 s |
| `tests/test_trl5_navigation.py` | Kinodynamic Hybrid A*, ES-EKF Fusion, FDIR State Machine | 12 | 100% | 1.25 s |
| **Total Baseline Suite** | **Full APPS Autonomous Core** | **200** | **100%** | **18.27 s** |

---

## 2. Invariant Safety Gates

All tests strictly enforce:
1. `PROTOTYPE_LOCK == True`: Prevents accidental promotion to uncertified deployment targets.
2. `NAVIGATION_READY == False`: Explicit compile-time disallowance of real-world flight operations.
3. Zero floating-point NaN or Inf propagation across coordinate transforms or Kalman updates.
4. Deterministic PRNG seed reproduction across all test fixtures.

This baseline is preserved without regressions throughout the TRL 6 implementation.
