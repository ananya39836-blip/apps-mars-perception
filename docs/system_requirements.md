# APPS System Requirements Document (SRD) — NASA TRL 5 Target Scope

## 1. Targeted Technology Scope & Definition

As mandated by NASA Technology Readiness Level guidance (NASA Systems Engineering Handbook SP-6105 Rev 2):
> **TRL 5 Definition**: Component and/or breadboard validation in relevant environment. A high-fidelity lab or simulated relevant environment demonstrates the critical functions in a realistic configuration.

The bounded technology under evaluation for this assessment is:
> **"Autonomous planetary rover terrain perception, local mapping, traversability estimation, and collision-aware navigation in a representative simulated planetary environment."**

Higher-level exploratory capabilities (interstellar probes, Dyson swarms, quantum QKD, deep coiled drilling, supercritical Venus avionics) are explicitly decoupled from this surface rover autonomy maturity assessment.

---

## 2. Operational Design Domain (ODD) & Environmental Assumptions

The Operational Design Domain defines the bounded environmental conditions under which the autonomous system is specified to operate safely:

| Parameter | Operational Design Domain (ODD) Boundary | Justification / Physical Context |
|:---|:---|:---|
| **Gravity Field** | $g = 3.71\text{ m/s}^2$ (Martian surface) | Governs normal wheel forces, friction limits, and tip-over stability. |
| **Terrain Elevation Range** | Up to $\pm 10.0\text{ m}$ elevation variation over a $100\text{ m} \times 100\text{ m}$ site | Typical planetary landing site topography (Gale, Jezero, Shackleton rim). |
| **Maximum Slope Angle** | Pitch / Roll $\le 25.0^\circ$ ($0.436\text{ rad}$) | Mechanical rollover and wheel traction limit for $185\text{ kg}$ class rover. |
| **Obstacle Field Density** | Rock coverage up to $25\%$ by surface area; diameters $0.15\text{ m}$ to $2.5\text{ m}$ | Representative of rocky Martian plains (e.g. Viking, Pathfinder, Perseverance). |
| **Negative Obstacles** | Depressions and crater rims with vertical drops $> 0.25\text{ m}$ | Must be detected via sensor ray shadow casting and drop-out analysis. |
| **Regolith Properties** | Internal friction angle $\phi = 30^\circ - 38^\circ$, cohesion $c = 0.1 - 1.5\text{ kPa}$ | Bekker-Wong terramechanics parameters for medium to drift sand. |
| **Illumination & Glare** | Solar zenith angles $15^\circ$ to $75^\circ$; partial optical extinction $\tau \le 1.2$ | Dust storms and low-sun elevation shadow elongation. |
| **Sensor Horizon** | LiDAR range $0.5\text{ m}$ to $25.0\text{ m}$; Stereo Camera $1.0\text{ m}$ to $15.0\text{ m}$ | Lookahead distance sufficient for safe stopping at $0.5\text{ m/s}$. |

---

## 3. System Requirements (SR)

### 3.1 Perception Requirements
- **SR-PERC-01 (Sensor Simulation)**: The system shall generate synthetic sensor observations for a 3D LiDAR (point cloud with range noise $\sigma_r \le 0.03\text{ m}$ and incidence-angle dropouts), a Pinhole Depth Camera (range-squared uncertainty $u(Z) \propto Z^2$), a 6-axis Tactical IMU (bias drift $\le 5.0^\circ/\text{hr}$), and wheel odometers.
- **SR-PERC-02 (Coordinate Transformations)**: All sensor observations shall be transformed via explicit $SE(3)$ homogeneous matrices into the rover base frame $\mathcal{B}$ and world map frame $\mathcal{M}$ with zero-lag rigid body geometry.
- **SR-PERC-03 (Elevation Mapping & Uncertainty)**: The perception pipeline shall maintain a 2.5D local elevation grid with spatial resolution $\le 0.20\text{ m/cell}$, updating cell mean height and elevation variance $\sigma_z^2$ from point returns.
- **SR-PERC-04 (Traversability Cost Map)**: The system shall compute a continuous multi-criteria traversability cost $c \in [0.0, 1.0]$ per cell evaluated against:
  1. Surface gradient / slope (penalty for slopes $> 15^\circ$; non-traversable for slopes $> 25^\circ$).
  2. Surface roughness (elevation standard deviation within rover footprint).
  3. Step height obstacles (height discontinuities $> 0.25\text{ m}$).
  4. Negative obstacles (shadowed depressions and cliff edges).
  5. Regolith slip penalty (estimated traction factor from soil model).
- **SR-PERC-05 (Perception Quality Gate)**: In synthetic benchmark environments with known ground-truth hazard geometry, obstacle detection precision shall be $\ge 90\%$ and recall shall be $\ge 90\%$.

### 3.2 State Estimation Requirements
- **SR-LOC-01 (Error-State EKF)**: The state estimator shall fuse 6-axis IMU angular rates/accelerations with wheel odometry using an Error-State Extended Kalman Filter (ES-EKF) running at $\ge 20\text{ Hz}$.
- **SR-LOC-02 (Trajectory Accuracy)**: Under nominal terrain slip ($s \le 0.15$), the Absolute Trajectory Error (ATE RMSE) shall not exceed $0.50\text{ m}$ over a $30\text{ m}$ traverse.
- **SR-LOC-03 (Slip Watchdog)**: The estimator shall monitor wheel slip ratio $s = \frac{r\omega - v}{r\omega}$. If $s > 0.60$ for $\ge 1.0\text{ s}$, the system shall flag a `SLIP_ENTRAPMENT` event and trigger safe-stop.

### 3.3 Kinodynamic Planning & Control Requirements
- **SR-PLAN-01 (Kinodynamic Hybrid $A^*$)**: The global/local path planner shall plan feasible continuous trajectories in $SE(2)$ configuration space $(x, y, \theta)$ respecting the rover's minimum turning radius $\rho_{\min} \ge 0.67\text{ m}$ (curvature limit $\kappa_{\max} = 1.50\text{ m}^{-1}$).
- **SR-PLAN-02 (Footprint Collision Clearance)**: The planner shall evaluate swept chassis bounding box polygons ($1.20\text{ m} \times 0.90\text{ m}$) against the cost map, enforcing a configurable safety margin $\ge 0.30\text{ m}$.
- **SR-PLAN-03 (Closed-Loop Tracking & Control)**: The motion controller shall command linear and angular velocities $(v, \omega)$ bounded by $v_{\max} = 0.50\text{ m/s}$ and $|a_{\max}| \le 0.20\text{ m/s}^2$, tracking the planned path within a cross-track error $\le 0.25\text{ m}$.
- **SR-PLAN-04 (Dynamic Replanning)**: If a previously unmapped obstacle is detected within $3.0\text{ m}$ of the current path, the system shall trigger replanning within $\le 200\text{ ms}$.
- **SR-PLAN-05 (Certified Safe Stop)**: If no collision-free path exists to the goal, the system shall execute a certified safe-stop deceleration profile to halt without contacting obstacles.

### 3.4 Safety & Operating Mode State Machine Requirements
- **SR-FSM-01 (Operating Modes)**: The rover shall operate under an explicit 11-mode state machine:
  `INITIALIZATION`, `SELF_TEST`, `IDLE`, `PERCEPTION`, `LOCALIZATION`, `PLANNING`, `EXECUTION`, `REPLANNING`, `SAFE_STOP`, `RECOVERY`, `MISSION_COMPLETE`, `FAULT`.
- **SR-FSM-02 (Safety Invariants)**:
  1. A run resulting in an obstacle collision shall NEVER be classified as a success (`SAFE_STOP` or `FAULT` mandated).
  2. Missing sensor data or uninitialized state shall immediately transition to `FAULT`.
  3. `navigation_ready` shall remain compile-time locked to `False` under `PROTOTYPE_LOCK = True`.

---

## 4. Acceptance Criteria & Validation Metrics

| Requirement ID | Metric | Target Acceptance Threshold | Validation Method |
|:---|:---|:---|:---|
| **SR-PERC-04** | Traversability Cost Range | $c \in [0.0, 1.0]$; $c = 1.0$ on obstacles $> 0.25\text{ m}$ | Automated unit test |
| **SR-PERC-05** | Obstacle Detection Recall | $\ge 90.0\%$ on rocky obstacle fields | Ground-truth IoU evaluation |
| **SR-LOC-02** | Absolute Trajectory Error (ATE) | $\text{RMSE} \le 0.50\text{ m}$ over $30\text{ m}$ traverse | Ground-truth EKF comparison |
| **SR-PLAN-01** | Path Curvature Constraint | $|\kappa| \le 1.50\text{ m}^{-1}$ everywhere along trajectory | Geometric path assertion |
| **SR-PLAN-02** | Collision Count | Exactly $0$ collisions across all nominal & adverse trials | Continuous bounding-box check |
| **SR-PLAN-04** | Planning Latency | Mean $\le 100\text{ ms}$, Max $\le 250\text{ ms}$ | High-resolution CPU timer |
| **SR-CAMP-01** | Navigation Success Rate | $\ge 90.0\%$ in nominal scenarios; $0$ collisions in adverse | 15-scenario multi-seed campaign |
