# Earth Analog Field Test Operations Plan (TRL 7)
**Project Name**: APPS — Automated Planetary Perception System  
**Document Identifier**: APPS-TRL7-FTP-003  
**Field Test Locations**: JPL Mars Yard Analog (California), Basalt Quarry Analog Testbed (Iceland), Atacama Desert Dunes (Chile)  

---

## 1. Testbed Objectives & Analog Environment Fidelity

To achieve TRL 7, the autonomous navigation subsystem must be validated in an operationally representative field environment. Terrestrial planetary analog facilities provide key environmental stressors:

| Facility Name | Primary Analog Characteristics | Injected Environmental Stressors |
| :--- | :--- | :--- |
| **JPL Mars Yard Analog** | Scaled rock density (boulders 0.2m–1.0m), compaction slopes up to 20° | Chokepoints, high boulder density, line-of-sight occlusions |
| **Basalt Quarry Field Testbed** | Sharp unweathered basalt rock shards, varying micro-roughness | Severe surface roughness, high step hazards, sensor shock |
| **Atacama Desert Regolith** | High-porosity loose aeolian sand, dune slip faces (15°–25°) | High wheel sinkage, terramechanic slip ($s > 0.40$), low drawbar pull |
| **Synthetic 3D Sandbox** | Extreme low solar incidence angles (10°–15° sun elevation) | High dynamic range shadows, optical crater dropout |

---

## 2. Test Matrix: 20 Standardized Scenario Classes

The test campaign executes 20 rigorous scenario classes (SC-01 through SC-20):

```
+-------------------------------------------------------------------------------+
|                        TRL 7 OPERATIONAL TEST MATRIX                          |
+-------------------+-----------------------------------+-----------------------+
| Category          | Scenario Class                    | Evaluation Focus      |
+-------------------+-----------------------------------+-----------------------+
| Topographic       | SC-01 Flat Baseline               | Steady-state speed    |
| Complexity        | SC-02 Moderate Slopes             | Roll/pitch stability  |
|                   | SC-03 Steep Slopes (18°-22°)      | Climb limits          |
+-------------------+-----------------------------------+-----------------------+
| Obstacle &        | SC-04 Dense Boulder Field (>25%)  | Tortuous avoidance    |
| Geometry          | SC-05 Narrow Chokepoint Gate      | Clearance margin      |
|                   | SC-06 Negative Impact Craters     | Drop-off detection    |
+-------------------+-----------------------------------+-----------------------+
| Sensory           | SC-07 Elevated Sensor Noise (3.5x)| EKF robustness        |
| Perturbations     | SC-08 Sensor Dropouts (LiDAR link)| Dead-reckoning hold   |
|                   | SC-18 Uplink/Downlink Latency     | Control stability     |
|                   | SC-19 Telemetry Glitch & NaN      | Input validation      |
+-------------------+-----------------------------------+-----------------------+
| Terramechanics    | SC-09 High Cumulative Drift       | ATE error bound       |
| & Wheel Slip      | SC-10 Localized Slip Disturbance  | Recovery maneuver     |
|                   | SC-13 Dune Sand Simulant          | Drawbar pull limits   |
+-------------------+-----------------------------------+-----------------------+
| Online Dynamic    | SC-11 Unmapped Corridor Obstacle  | Online local replan   |
| Response          | SC-12 Dead-End Rock Cul-de-sac    | Back-up & escape      |
|                   | SC-14 Deep Solar Shadow Replan    | Contrast adaptation   |
+-------------------+-----------------------------------+-----------------------+
| Contingency       | SC-15 Actuator Stall / Fault Stop | Decel a = -0.20 m/s^2 |
| & Long Duration   | SC-16 Multi-Waypoint Traverse     | Extended >100m path   |
|                   | SC-17 Goal Inside Deep Crater     | Feasibility rejection |
|                   | SC-20 Combined Multihazard Stress | Simultaneous stressors|
+-------------------+-----------------------------------+-----------------------+
```

---

## 3. Operational Safety Protocol

1. **Physical E-Stop Tether / Radio Link**: Operators must maintain continuous line-of-sight and wireless deadman heartbeat. Lapsing beyond 500 ms commands an instantaneous brake lock.
2. **Exclusion Zone**: All personnel must remain outside a 5.0-meter radius around the vehicle during autonomous traversing.
3. **Tip-Over Abort Threshold**: If roll or pitch exceeds 28.0° (safety margin below 32° physical limit), the FDIR executive trips `SAFE_STOP`.
