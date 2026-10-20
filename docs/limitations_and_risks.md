# APPS Planetary Rover Autonomous Navigation System — Operational Limitations & Risk Assessment

**Document ID:** APPS-RISK-TRL5-004  
**Target Maturity:** NASA TRL 5  
**Compliance Standard:** NASA-STD-8719.13C (Software Safety Standard)

---

## 1. Operational Design Domain (ODD) Boundaries

The technology is validated strictly within the following physical and environmental operational limits:

| Parameter | Nominal Safe Domain | Degraded Operation Domain | Hard Non-Traversable Limit |
| :--- | :--- | :--- | :--- |
| **Regional Slope** | $\le 10.0^\circ$ | $10.0^\circ - 20.0^\circ$ (Speed derated) | $> 25.0^\circ$ (Tip-over risk) |
| **Obstacle Height** | $\le 0.15\text{ m}$ (Roll-over) | $0.15\text{ m} - 0.25\text{ m}$ | $> 0.25\text{ m}$ (Underbody strike) |
| **Crater Diameter** | $\le 1.0\text{ m}$ (Traversable rim) | $1.0\text{ m} - 3.0\text{ m}$ (Bypass) | $> 3.5\text{ m}$ (Entrapment bowl) |
| **Regolith Cohesion** | $\ge 1.0\text{ kPa}$ | $0.5\text{ kPa} - 1.0\text{ kPa}$ | $< 0.25\text{ kPa}$ (Deep sinkage) |
| **Max Traverse Speed** | $0.40\text{ m/s}$ | $0.15\text{ m/s} - 0.25\text{ m/s}$ | $0.0\text{ m/s}$ (Latching Safe-Stop) |
| **Sensor Range Noise** | $\sigma_r \le 0.03\text{ m}$ | $0.03\text{ m} - 0.08\text{ m}$ | $> 0.12\text{ m}$ |

---

## 2. Identified Failure Modes & FDIR Mitigation Strategies

### 2.1 FM-01: Wheel Slip Entrapment in Low-Cohesion Regolith
- **Description**: Encountering loose drifts or sand ripples causes excessive wheel slip ($s > 0.60$). Continued spinning digs the wheels into the substrate (sinkage $z_0 > 5\text{ cm}$), causing total mobility loss (similar to the *Spirit* rover at Troy).
- **Detection**: Real-time state monitor computes kinematic slip ratio $s = 1 - \frac{v_{\text{EKF}}}{r_w \omega}$.
- **FDIR Mitigation**: If $s > 0.60$ persists for $\ge 1.0\text{ s}$, the executive trips the slip watchdog, immediately halting drive motors with certified deceleration profile ($a = -0.20\text{ m/s}^2$) to preserve ground clearance before chassis bottoming out.

### 2.2 FM-02: Covariance Divergence Under Extended IMU Drift
- **Description**: Long dead-reckoning legs without wheel odometry or visual landmarks cause the Error-State EKF estimation covariance $P$ to grow unbounded.
- **Detection**: Continuous evaluation of the $3\sigma$ position covariance matrix trace $\text{Tr}(P_{pos}) = \sigma_x^2 + \sigma_y^2$.
- **FDIR Mitigation**: If $\text{Tr}(P) > 2.50\text{ m}^2$, the executive flags `LOCALIZATION_COVARIANCE_DIVERGENCE`, transitions to `SAFE_STOP`, and requests stationary multi-beam LiDAR re-mapping.

### 2.3 FM-03: Sudden Drop-Off / Negative Obstacle Occlusion
- **Description**: Forward craters or cliff edges present no positive returns above the ground plane; optical grazing angles cause the crater bowl to be hidden in shadow behind the raised rim.
- **Detection**: Radial ray tracing in the 2.5D elevation map detects downward elevation steps $> \text{res} \cdot \tan(25^\circ)$.
- **FDIR Mitigation**: Flagged cells are committed to `negative_obstacle_mask`, forcing traversability cost to $1.0$ and establishing an expansive safety clearance buffer ($d_{\text{margin}} = 0.30\text{ m}$) preventing path intersection.

### 2.4 FM-04: Dynamic Pop-Up Obstacles
- **Description**: Rocks dislodged from slopes or moving external agents intersect the active trajectory.
- **Detection**: $2\text{ Hz}$ periodic LiDAR scans update the 2.5D elevation grid; a $6.0\text{ m}$ forward lookahead corridor auditor continuously checks for intersections.
- **FDIR Mitigation**: If intersection is detected, the state machine transitions to `REPLANNING`, decelerates the vehicle ($v \le 0.15\text{ m/s}$), and computes an evasive bypass maneuver. If no collision-free path exists, it transitions to `SAFE_STOP`.

---

## 3. Residual Technology Readiness Gaps (TRL 5 $\rightarrow$ TRL 6)

The following items are required to advance the technology from synthetic laboratory maturity (TRL 5) to full engineering model field demonstration (TRL 6):

1. **Physical Analogue Field Testing**: Closed-loop execution on physical 6-wheel rover hardware at a certified terrestrial Mars analogue site (e.g., JPL Mars Yard, Atacama Desert, or Devon Island).
2. **Radiation-Tolerant Compute Target**: Porting and benchmarking the algorithms on spaceflight hardware (e.g., BAE RAD750, High-Performance Spaceflight Computing HPSC / RISC-V) running RTEMS.
3. **Stereo Camera Visual Odometry (VO)**: Adding feature-based optical visual odometry (FAST/ORB keypoints) to complement wheel odometry during severe slip.
4. **Thermal-Vacuum Environmental Hardening**: Packaging sensor interfaces to withstand extreme diurnal thermal cycles ($-120^\circ\text{C}$ to $+20^\circ\text{C}$) and dust accumulation on optical surfaces.
