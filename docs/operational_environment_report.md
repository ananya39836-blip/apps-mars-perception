# APPS Planetary Rover Autonomous Navigation System — Operational Environment Report

**Document ID:** APPS-ENV-TRL7-004  
**Target Maturity:** NASA TRL 7 (Operational Environment Demonstration)  
**Safety Invariants:** `PROTOTYPE_LOCK = True`, `NAVIGATION_READY = False`  
**Reference Analog:** Mars Yard / Basalt Test Track / Desert Terrain Analog vs Mars Surface  
**Standard References:** NASA-STD-7009A, NASA-HDBK-7002, NASA SP-2016-6105 Rev 2

---

## 1. Operational Environment Specification

In NASA systems engineering for planetary surface robotics, demonstrating a technology in an "operational environment" at TRL 7 requires testing in an Earth-based planetary analog field environment (such as a Mars Yard, volcanic basalt quarry, or desert test track) that exposes the complete hardware/software system to real-world physical terrain, natural lighting variations, dust occlusions, and non-linear ground interactions.

### 1.1 Environmental Comparison & Physical Scaling (Earth Analog vs. Mars Surface)

| Environmental Parameter | Earth Analog Field Testbed | Actual Mars Surface | Fidelity Analysis & Operational Scaling |
| :--- | :--- | :--- | :--- |
| **Gravitational Acceleration** | $g_\oplus = 9.81\text{ m/s}^2$ ($1.0\,g_\oplus$) | $g_{\text{mars}} = 3.71\text{ m/s}^2$ ($0.378\,g_\oplus$) | Earth testing exerts higher normal forces ($\approx 2.64\times$), increasing chassis wheel loading and ground compaction. Dynamics algorithms must scale traction thresholds accordingly. |
| **Atmospheric Pressure** | $1,013\text{ mbar}$ (Terrestrial atmosphere) | $6.0 - 9.0\text{ mbar}$ ($< 1\%$ Earth) | Earth testing operates in ambient air; flight vacuum thermal conditioning and carbon dioxide sublimation are not modeled. |
| **Ambient Temperature Range** | $-10^\circ\text{C}$ to $+40^\circ\text{C}$ | $-125^\circ\text{C}$ to $+20^\circ\text{C}$ | Cryogenic lubricant viscosity and motor torque degradation at $-100^\circ\text{C}$ require environmental chamber testing (TRL 8). |
| **Solar Illumination & Glint** | Direct sunlight ($1000\text{ W/m}^2$), specular reflections, and sky blue diffuse scattering. | Low-intensity sunlight ($590\text{ W/m}^2$), harsh high-contrast shadows, red/salmon sky glow from suspended ferric dust. | Earth field tests provide realistic optical glare, lens flare, dynamic camera exposure range, and deep shadow transitions representative of rover mast cameras. |
| **Terrain Topography & Rocks** | Natural fractured basalt boulders, gravel beds, regional slopes up to $20^\circ$, and fine sand drift patches. | Aeolian dunes, basaltic regolith, fractured impact ejecta, duricrust crusts, and impact crater depressions. | **Fully representative**: Earth analog boulder distributions and slope gradients accurately stress perception ground-plane segmentation, collision geometry, and tip-over stability. |
| **Soil Terramechanics & Slip** | Dry fine quartz sand / gravel ($c \approx 500 - 1000\text{ Pa}$, $\phi \approx 30^\circ - 36^\circ$). | Martian regolith simulant (JSC Mars-1A / MGS-1) ($c \approx 800\text{ Pa}$, $\phi \approx 34^\circ$). | **High fidelity**: Bekker-Wong pressure-sinkage and Janosi-Hanamoto shear displacement dynamics are directly validated on loose sand patches. |

---

## 2. Operational Design Domain (ODD) Boundaries

The TRL 7 prototype is designed and verified to operate strictly within the following bounded envelope:

```
+-------------------------------------------------------------------------+
| Operational Design Domain (ODD) Parameter   | Verified Operational Limit |
+-------------------------------------------------------------------------+
| Regional Traverse Slope                     | <= 20.0 deg (0.349 rad)   |
| Vehicle Static Rollover Tip-Over Limit      | 32.0 deg (0.559 rad)      |
| Maximum Obstacle Step Height                | 0.25 m (Wheel radius r_w) |
| Maximum Traversable Boulder Diameter        | 0.85 m (Evasively routed) |
| Maximum Crater Depression Depth             | 0.80 m (Detected & bypass)|
| Wheel Slip Ratio Operational Range          | s in [0.0, 0.45] (Derated)|
| Slip Entrapment Critical Threshold          | s > 0.60 (Latching stop)  |
| Solar Elevation Angle                       | theta_sun in [10°, 75°]   |
| Onboard RTOS Planning Latency Budget        | Delta t_plan <= 200.0 ms  |
| Minimum Path Obstacle Clearance Margin      | 0.30 m                    |
+-------------------------------------------------------------------------+
```

---

## 3. Physical vs. Simulated Demonstration Boundaries

NASA systems engineering mandates explicit declaration of testing boundaries:
1. **What Earth field analog testing demonstrates**:
   - Closed-loop perception, mapping, and planning from genuine optical/LiDAR point clouds under natural solar lighting.
   - Robustness of the ES-EKF under true sensor bias drift and physical wheel slip.
   - In-flight dynamic obstacle response when unknown physical boulders are placed in the path.
   - Hardware E-Stop emergency halting within deterministic safety margins.
2. **What Earth field testing cannot demonstrate (Residual TRL 7 Gaps)**:
   - Thermal survival under Martian cryogenic diurnal cycles ($-125^\circ\text{C}$).
   - Ionizing cosmic radiation and solar energetic particle effects on flight electronics.
   - Vehicle dynamics under true Martian gravity ($0.378\,g_\oplus$).
