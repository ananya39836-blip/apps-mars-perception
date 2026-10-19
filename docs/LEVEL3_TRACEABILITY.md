# APPS Level 3 Traceability Matrix (NASA SP-2016-6105 & NPR 7150.2B)

| Standard / System Element | NASA Reference | Claim Level | Implementation Module | Automated Test File | Verification Evidence |
|---|---|---|---|---|---|
| **6-DOF Multibody Dynamics** | NASA SP-2016-6105 §4.2 | Level 3 (Verified by Test) | `level3/physics/multibody_6dof.py` | `tests/test_level3.py::test_t30` | Newton-Euler ODE & FASM margin |
| **Rocker-Bogie Equalization** | JPL AutoNav Standards | Level 3 (Verified by Test) | `level3/physics/rocker_bogie.py` | `tests/test_level3.py::test_t31` | 6-wheel normal load balance |
| **Bekker-Wong Soil Dynamics** | Planetary Terramechanics | Level 3 (Verified by Test) | `level3/physics/terramechanics.py` | `tests/test_level3.py::test_t32` | Sinkage & Drawbar Pull curves |
| **Slip-Sinkage Safeguard** | NPR 7150.2B Class B | Level 3 (Verified by Test) | `level3/monitors/slip_watchdog.py` | `tests/test_level3.py::test_t33` | Emergency safe stop trigger |
| **Tactical IMU Modeling** | IEEE 952 Allan Variance | Level 3 (Verified by Test) | `level3/sensing/multimodal_sensor.py` | `tests/test_level3.py::test_t34` | Gyro drift & bias random walk |
| **3D Flash LiDAR Scanning** | Spaceborne ToF Standards | Level 3 (Verified by Test) | `level3/sensing/multimodal_sensor.py` | `tests/test_level3.py::test_t35` | (N, 4) Point cloud returns |
| **Dust Storm Extinction** | Martian Radiative Transfer | Level 3 (Verified by Test) | `level3/sensing/degradations.py` | `tests/test_level3.py::test_t36` | Beer-Lambert contrast drop |
| **Negative Obstacle Sentinel**| AutoNav Terrain Hazards | Level 3 (Verified by Test) | `level3/sensing/degradations.py` | `tests/test_level3.py::test_t37` | Trench & cliff detection |
| **Factor Graph SLAM** | iSAM2 / GTSAM Architecture | Level 3 (Verified by Test) | `level3/estimation/factor_graph.py` | `tests/test_level3.py::test_t38` | IMU + VO + Wheel integration |
| **3D Voxel Grid & ESDF** | Continuous 3D Mapping | Level 3 (Verified by Test) | `level3/mapping/octomap_3d.py` | `tests/test_level3.py::test_t39` | Octree log-odds & distance |
| **Kinodynamic State-Lattice** | State-Space Sampling | Level 3 (Verified by Test) | `level3/planning/state_lattice_3d.py` | `tests/test_level3.py::test_t40` | ESDF clearance & risk budget |
| **Guaranteed Safe Stopping** | Inevitable Collision State | Level 3 (Verified by Test) | `level3/planning/nmpc_trajectory.py` | `tests/test_level3.py::test_t41` | Dynamic braking arc profiles |
| **Level 2 Regression** | NPR 7150.2B Verification | Level 3 (Verified by Test) | `tools/assess_level2.py` | `results/level3/l2_regression.json` | L2-met (internal) verified |
| **Level 1 Regression** | NPR 7150.2B Verification | Level 3 (Verified by Test) | `tools/assess_level1.py` | `results/level2/l1_regression.json` | L1-met (internal) verified |

All requirements verified by automated unit tests under `PROTOTYPE_LOCK = True`.
