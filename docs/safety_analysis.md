# System Safety and Hazard Analysis (TRL 7)
**Project Name**: APPS — Automated Planetary Perception System  
**Document Identifier**: APPS-TRL7-SAF-006  
**Safety Classification**: Research Prototype Safety Envelope  
**Standards Followed**: NASA-STD-8719.13 (Software Safety), MIL-STD-882E (System Safety), ISO 26262/21448 (SOTIF)  

---

## 1. Safety Principles and Philosophy

Planetary rovers operate millions of kilometers from Earth with signal round-trip communication delays between 6 and 44 minutes. Autonomous safety cannot rely on teleoperation. The APPS architecture adheres to four core tenets:

1. **Fail-Safe Determinism**: In the presence of any unrecoverable sensory anomaly, motor controller fault, or deadman timeout, the vehicle halts deterministically to a verified safe state.
2. **Compile-Time Safety Latches**: The repository is permanently configured with:
   ```python
   PROTOTYPE_LOCK = True       # Enforces research-only boundary
   NAVIGATION_READY = False    # Compile-time lock preventing accidental flight deployment
   ```
3. **Layered Defense-in-Depth**:
   - **Level 1 (Data Validation)**: NaN/Inf, non-monotonic timestamps, CRC-16 errors caught before reaching estimation filters.
   - **Level 2 (Geometric Clearance)**: 2.5D cost maps dilated by full vehicle radius + clearance margin ($1.40\text{ m}$).
   - **Level 3 (Kinodynamic Feasibility)**: Curvature bounded ($\kappa \le 1.50\text{ m}^{-1}$) to prevent kinematic tire scrub or rollover.
   - **Level 4 (Executive FDIR)**: 11-mode state machine enforcing recovery limits, safe stopping, and hardware E-Stop.

---

## 2. Failure Mode and Effects Analysis (FMEA)

| Failure Mode ID | Component / Subsystem | Failure Mechanism | Operational Consequence | Mitigating Architectural Mechanism | Criticality |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FM-01** | Tactical IMU | Accelerometer or gyro axis saturation / NaN spike | EKF divergence, incorrect vehicle attitude estimation | `SensorValidator` rejects invalid packets; ES-EKF falls back to kinematic prediction | **CRITICAL (Catastrophic without mitigation)** |
| **FM-02** | 3D LiDAR | Sensor blind dropouts (e.g. 2.0s link loss) | Perception elevation map blind sectors | Temporal elevation variance decay; inertial dead-reckoning hold | **MAJOR** |
| **FM-03** | Wheels / Regolith | Severe wheel sinkage & high slip ($s > 0.40$) | Rover becomes entrapped in loose regolith dune | Bekker-Wong compaction model detection; adaptive speed derating & backup recovery | **CRITICAL** |
| **FM-04** | Path Planner | Traversable corridor completely blocked by rock wall | Infinite loop / search space explosion | Iteration budget limit (3500); FDIR transition to `RECOVERY_MANEUVER` or `SAFE_STOP` | **MAJOR** |
| **FM-05** | Actuator Drive | Motor controller stall / overcurrent trip | Loss of differential drive authority | Certified `SafeStopController` ramps down velocity ($a = -0.20\text{ m/s}^2$) and latches brakes | **CATASTROPHIC** |
| **FM-06** | Ground Link | Deadman pulse timeout ($t > 500\text{ ms}$) | Unmonitored traverse | Hardware `EStopMonitor` trips emergency stop; zero drive current | **CRITICAL** |

---

## 3. Certified Safe-Stop Deceleration Profile

When an emergency stop or unrecoverable fault is asserted:
- Deceleration is commanded at a deterministic rate: $a_{\text{stop}} = -0.20\text{ m/s}^2$.
- When $|v| \le 0.02\text{ m/s}$, the actuator HAL asserts `brake_engaged = True` and locks mechanical friction brakes.
- The rover pose is verified stable before transitioning to `MISSION_COMPLETE` or `SAFE_STOP` latch.
