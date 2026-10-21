# Comprehensive Failure and Off-Nominal Analysis (TRL 7)
**Project Name**: APPS — Automated Planetary Perception System  
**Document Identifier**: APPS-TRL7-FAR-007  
**Software Release Baseline**: `2.7.0-trl7`  

---

## 1. Introduction

Operating in unstructured planetary analog terrain subjects autonomous navigation systems to high-entropy disruptions. This document details empirical observations, root-cause analyses, and mitigation behaviors across 8 off-nominal scenario classes executed during the TRL 7 campaign.

---

## 2. Off-Nominal Scenario Case Studies

### 2.1 SC-08: Intermittent 3D LiDAR Dropouts (2.0s Duration)
- **Stress Condition**: Synthetic communication packet drops mimicking cable harness flexing or LiDAR processor bus starvation. LiDAR packets zeroed out for 2.0 consecutive seconds during traverse.
- **Observed Behavior**: Elevation map maintained historical terrain returns with progressive temporal variance inflation ($\Delta \sigma^2 = 0.01\cdot \Delta t$). State estimation smoothly sustained pose estimation via tactical IMU strapdown and wheel odometry.
- **Outcome**: Rover completed $28.5\text{ m}$ traverse with zero collisions and $< 0.18\text{ m}$ ATE drift.

### 2.2 SC-10: Localized Low-Traction Slip Disturbance ($\mu = 0.22$)
- **Stress Condition**: Rover encounters a $12\text{m} \times 12\text{m}$ patch of loose aeolian sand with friction coefficient $\mu = 0.22$, inducing drive wheel spin.
- **Observed Behavior**: Non-holonomic velocity constraints in the 15-state ES-EKF prevented spurious lateral velocity runaway. Janosi-Hanamoto terramechanics model tracked reduced drawbar pull ($DP$).
- **Outcome**: Pure pursuit speed derated smoothly, exiting the slip patch safely without high-centering.

### 2.3 SC-11: Unmapped Corridor Obstacle
- **Stress Condition**: A $1.4\text{ m}$ diameter boulder is unmapped during initial global planning and detected only when the rover approaches within $12\text{ m}$ sensor range.
- **Observed Behavior**: Forward ray sweeps updated the 2.5D elevation grid; traversability cost dilated $1.40\text{ m}$ around the boulder; active path collision monitor detected path obstruction 4 cells ahead; executive state transitioned `TRAVERSING -> OBSTACLE_AVOIDANCE -> PLANNING`.
- **Outcome**: A 4-point detour was planned and executed within 210 ms. Traverse continued with zero mission pause.

### 2.4 SC-12: Completely Blocked Canyon Wall (Cul-de-sac)
- **Stress Condition**: Rover enters a dead-end canyon where rock formations form an unbroken $15\text{ m}$ impassable barrier across the target path.
- **Observed Behavior**: Kinodynamic Hybrid A* exhausted forward motion primitives against inflated impassable walls. Executive transitioned to `RECOVERY_MANEUVER`, commanding reverse gear primitives to back up $3.5\text{ m}$ and pivot into an open side corridor.
- **Outcome**: Dead-end recognized; rover reversed safely without collision.

### 2.5 SC-15: Critical Actuator Controller Stall at $t = 15\text{ s}$
- **Stress Condition**: Hardware fault code `0x01` injected at $t = 15.0\text{ s}$, simulating drive motor controller thermal overcurrent trip.
- **Observed Behavior**:
  1. $t = 15.00\text{ s}$: Fault code broadcast in `ActuatorTelemetry`.
  2. $t = 15.05\text{ s}$: Executive transitioned `TRAVERSING -> FAULT_ISOLATION -> SAFE_STOP`.
  3. $t = 15.05 - 16.95\text{ s}$: `SafeStopController` executed constant-jerk deceleration: $a = -0.20\text{ m/s}^2$.
  4. $t = 16.95\text{ s}$: Speed reached $v < 0.02\text{ m/s}$; mechanical brakes latched.
- **Outcome**: Certified fail-safe halt confirmed. Zero vehicle overrun.

### 2.6 SC-17: Unreachable Goal Inside Crater Bowl
- **Stress Condition**: Operator commanded a science waypoint dead-center inside a $5.0\text{ m}$ diameter, $1.8\text{ m}$ deep impact crater (impassable slope $> 28^\circ$).
- **Observed Behavior**: Collision checker flagged the goal position inside the crater bowl as impassable; planner identified no collision-free terminal arc within tolerance.
- **Outcome**: Executive rejected goal incursion and entered safe standoff station-keeping at crater rim.

### 2.7 SC-19: Telemetry Packet Glitches & Clock Non-Monotonicity
- **Stress Condition**: Packet injection of NaN/Inf floats, corrupted CRC-16 checksums, and negative timestamp steps.
- **Observed Behavior**: `SensorValidator` dropped 100% of corrupted packets; logged anomaly event; state estimator maintained continuity.
- **Outcome**: Zero crash, zero division-by-zero, uninterrupted mission execution.

### 2.8 SC-20: Combined Multi-Hazard Stress
- **Stress Condition**: Simultaneous steep slopes ($14^\circ$), 20 boulders, low regolith traction ($\mu = 0.40$), low sun elevation ($15^\circ$, long shadows), and 2.5x sensor noise.
- **Observed Behavior**: Integrated perception and kinodynamic path tracker negotiated tortuous ridge routes, derating velocity down to $0.14\text{ m/s}$ on high-curvature segments.
- **Outcome**: Mission completed with $0.158\text{ m}$ ATE RMSE.
