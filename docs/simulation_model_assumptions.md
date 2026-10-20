# APPS Planetary Rover Autonomous Navigation System — Simulation Assumptions & Model Fidelity

**Document ID:** APPS-SIM-TRL5-003  
**Target Maturity:** NASA TRL 5  
**Compliance Standard:** NASA-STD-7009A (Standard for Models and Simulations)

---

## 1. Distinction of Physical, Empirical & Assumed Parameters

To maintain scientific integrity and prevent misleading representations, all simulation quantities are strictly classified according to their modeling basis:

| Category | Definition | Subsystems Governed |
| :--- | :--- | :--- |
| **Physically Simulated** | First-principles Newtonian mechanics, kinematics, and geometric ray tracing | 6-DOF Newton-Euler dynamics, $SE(3)$ coordinate transforms, LiDAR optical ray casting, Rocker-Bogie kinematic equilibrium. |
| **Empirically Approximated** | Validated empirical terramechanics formulas fitted to laboratory soil test data | Bekker pressure-sinkage relationship, Janosi-Hanamoto shear stress equations, Pure Pursuit path tracking. |
| **Assumed Parameters** | Planetary environment constants, vehicle structural dimensions, sensor noise figures | Martian gravity ($3.71\text{ m/s}^2$), rover mass ($185\text{ kg}$), tactical IMU Allan variance coefficients. |
| **Synthetic Approximations** | Computationally generated procedural digital elevation models (DEMs) | Multi-scale undulating surface topography, boulder fields, parabolic craters. |

> [!CAUTION]
> **Synthetic Data Disclaimer**: All digital elevation models, point clouds, stereo images, and IMU traces in this repository are **synthetically generated in a laboratory simulation environment**. They must never be represented or published as actual Mars rover or lunar surface flight data.

---

## 2. Geophysical Assumptions & Planetary Constants

### 2.1 Gravitational Acceleration
- Constant Martian surface gravity: $g_{\text{mars}} = 3.71\text{ m/s}^2$.
- Assumed homogeneous gravitational field across local $35\text{ m} \times 35\text{ m}$ site. Higher-order gravity harmonics ($J_2, J_3$) are neglected over rover-scale traverses.

### 2.2 Atmospheric & Lighting Assumptions
- Ambient Martian surface pressure: $\sim 600\text{ Pa}$ (negligible aerodynamic drag for ground velocities $\le 0.50\text{ m/s}$).
- Direct solar illumination: Solar azimuth $45.0^\circ$, elevation $30.0^\circ$ (nominal) down to $15.0^\circ$ (high-shadow condition SC-14).
- Specular shadow ray casting assumes opaque obstacles without diffuse atmospheric scattering.

### 2.3 Regolith Mechanical Properties
Soil parameters represent low-cohesion planetary simulant (e.g., Mojave Mars Simulant MMS-1 / JSC-1A):

| Parameter | Symbol | Nominal Value | High-Sinkage Value (SC-13) | Unit |
| :--- | :--- | :--- | :--- | :--- |
| **Cohesion** | $c$ | $1.20$ | $0.25$ | $\text{kPa}$ |
| **Internal Friction Angle** | $\phi$ | $34.0$ | $26.0$ | $\text{deg}$ |
| **Cohesive Sinkage Modulus** | $k_c$ | $1.40$ | $0.40$ | $\text{kPa}\cdot\text{m}^{1-n}$ |
| **Frictional Sinkage Modulus** | $k_\phi$ | $820.0$ | $280.0$ | $\text{kPa}\cdot\text{m}^{-n}$ |
| **Sinkage Exponent** | $n$ | $1.00$ | $0.85$ | dimensionless |
| **Shear Deformation Modulus**| $K_w$ | $0.025$ | $0.040$ | $\text{m}$ |
| **Nominal Friction Coefficient**| $\mu_{\text{nom}}$ | $0.85$ | $0.25$ | dimensionless |

---

## 3. Vehicle Structural & Kinematic Assumptions

The vehicle model is based on a flight-representative 6-wheel Rocker-Bogie chassis (comparable to Mars Exploration Rover MER / Curiosity class):

- **Vehicle Mass**: $m_{\text{rover}} = 185.0\text{ kg}$ (sprung mass).
- **Chassis Dimensions**: Length $L = 1.20\text{ m}$, Width $W = 0.90\text{ m}$, Height $H = 0.80\text{ m}$.
- **Wheel Geometry**: 6 rigid aluminum wheels, diameter $D_w = 0.50\text{ m}$, width $b_w = 0.16\text{ m}$.
- **Center of Mass (CoM)**: Centered laterally ($y_{\text{com}} = 0.0\text{ m}$), $x_{\text{com}} = 0.0\text{ m}$, $z_{\text{com}} = 0.35\text{ m}$ above ground level.
- **Maximum Speed Limit**: $v_{\text{max}} = 0.45\text{ m/s}$ ($1.62\text{ km/h}$).
- **Minimum Turning Radius**: $\rho_{\text{min}} = 0.67\text{ m}$ (equivalent maximum curvature $\kappa_{\text{max}} = 1.50\text{ m}^{-1}$).
- **Wheel-Ground Contact**: Quasi-static normal force distribution with equal wheel ground adherence across terrain gradients $\le 25^\circ$.

---

## 4. Verification and Limitations Boundaries

1. **Rigid Body vs Flexible Dynamics**: Structural flexibility of the rocker-bogie linkages, chassis frame elastic vibration, and wheel rim deformation are not modeled.
2. **Quasi-Static Terramechanics**: Bekker-Wong equations assume steady rolling; dynamic wheel bounce and high-speed slip transients ($> 2.0\text{ m/s}$) are outside the valid operational domain.
3. **Discrete Time Invariant**: All differential equations are integrated using discrete Euler/RK2 steps with fixed cycle time $\Delta t = 0.25\text{ s}$ for outer navigation loops and $\Delta t = 0.01\text{ s}$ for inner IMU loops.
4. **Deterministic PRNG**: Random noise draws use explicit 64-bit Mersenne Twister / PCG64 generators parameterized by fixed integer seeds (`seed=100, 117, 134, ...`) guaranteeing bit-for-bit experimental reproducibility.
