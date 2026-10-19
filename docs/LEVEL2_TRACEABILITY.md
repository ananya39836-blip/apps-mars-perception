# APPS Level 2 Traceability Matrix (Task 109 / Chapter 218)

> **Notice**: Research prototype in simulation. No spaceflight qualification or NASA compliance.

| Engineering Practice | Authoritative Reference Document | Claim Level | APPS Implementation | Remaining Gap |
|---|---|---|---|---|
| **Data Provenance & Licence Tracking** | NASA SP-2016-6105 §4.2 / Open Science Guidelines | **Level 3** | `results/level2/data_provenance.json` | Relies on public archives; no ground telemetry |
| **Interface Definition & Lock Guard** | NPR 7150.2 §3.4 / JPL Flight Architecture | **Level 3** | `level2/interface/schema.py` | Python memory boundary; no hardware bus |
| **Planar Vehicle Kinematics** | Siegwart & Nourbakhsh, 'Autonomous Mobile Robots' | **Level 2** | `level2/kinematics/kinematic_model.py` | Kinematics geometry only; no suspension dynamics |
| **Kinodynamic Arc Primitives** | Howard et al., 'State Space Sampling for Mars Rovers' | **Level 3** | `level2/navigation/primitive_planner.py` | Flat contact assumptions; no wheel sinkage |
| **2.5D Elevation Traversability** | JPL MER/MSL Autonomous Driving Papers | **Level 2** | `level2/navigation/traversability25d.py` | 2.5D DEM proxy; no 3D multi-body rocks |
| **Temporal Map Fusion & Drift Guard** | NASA NESC Statistical & GNC Guidelines | **Level 3** | `level2/evaluation/temporal_fusion.py` | Synthetic drift distributions |
| **Execution Latency Budgeting** | Holzmann, 'Power of 10 Safety Rules' | **Level 3** | `level2/evaluation/latency.py` | Host development machine; not onboard flight CPU |
| **Level 1 Backward Regression** | NPR 7150.2 Software Verification | **Level 3** | `results/level2/l1_regression.json` | Simulation regression suite |

### Claim Levels: Restricted to Level 1–3 (Zero claims of Level 4 or 5).