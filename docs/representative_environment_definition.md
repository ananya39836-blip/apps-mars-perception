# APPS Planetary Rover Autonomous Navigation System — Representative Environment Definition

**Document ID:** APPS-ENV-DEF-005  
**Target Maturity:** NASA TRL 6 (System/Subsystem Model or Prototype Demonstration in a Relevant Environment)  
**Reference Target Body:** Mars Surface (Chryse / Jezero / Gale Crater Analogues)  
**Safety Invariants:** `PROTOTYPE_LOCK = True`, `NAVIGATION_READY = False`  
**Reference Standards:** NASA-STD-7009A (Standard for Models and Simulations), NASA-HDBK-7002

---

## 1. Environmental Classification Taxonomy (NASA-STD-7009A)

To prevent misrepresenting synthetic simulations as physical flight data, all environmental models are formally categorized:

| Component | Classification | Mathematical / Physical Foundation | Fidelity Limitations |
| :--- | :--- | :--- | :--- |
| **Surface Gravity** | **Physically Grounded** | Constant downward acceleration $g_{\text{mars}} = 3.71\text{ m/s}^2$ ($0.378\,g_\oplus$). | Neglects higher-order spherical harmonic gravitational anomalies ($J_2, J_3$). |
| **Surface Topography (DEM)** | **Synthetic Procedural** | 3D continuous multi-octave harmonic elevation grid $Z(X, Y)$ with configurable slope gradients ($0^\circ - 25^\circ$). | Not actual HiRISE / HRSC digital terrain models; mathematically representative analog. |
| **Boulder Fields** | **Empirical Approximation** | Truncated power-law rock diameter distribution $N(D) \propto D^{-k}$ ($k \approx 2.5$) consistent with Golombek & Rapp (Mars Pathfinder / Viking). | Idealized geometric spheroids/cylinders; micro-fractures and sharp rock facet textures omitted. |
| **Impact Craters** | **Empirical Approximation** | Parabolic crater bowl depression with raised structural rims: $Z_{\text{bowl}}(r) = Z_0 - d \cdot (1 - (r/R)^2)$, $Z_{\text{rim}}(r) \propto h_{\text{rim}} e^{-(r-R)^2 / 2\sigma^2}$. | Simple crater morphology; complex central peak uplift craters omitted. |
| **Regolith Terramechanics** | **Semi-Empirical (Validated)** | Bekker-Wong pressure-sinkage: $p = \left(\frac{k_c}{b} + k_\phi\right) z^n$; Janosi-Hanamoto shear stress: $\tau(j) = (c + \sigma \tan \phi)(1 - e^{-j/K})$. | Assumes homogeneous regolith layer; depth-stratified permafrost or duricrust crusting not modeled. |
| **Solar Lighting & Shadows** | **Physically Grounded (Raymarching)** | Discrete directional ray-tracing with sun elevation angle $\theta_{\text{sun}} \in [15^\circ, 85^\circ]$ and azimuth $\phi_{\text{sun}}$. | Ambient diffuse scattering modeled via constant ambient factor (0.15); multiple scattering ignored. |
| **Atmospheric Visibility** | **Empirical Approximation** | Optical depth $\tau_{\text{dust}} \in [0.2, 1.5]$ causing LiDAR beam attenuation and Gaussian camera contrast degradation. | Dust deposition on optical lenses modeled via noise variance scaling rather than optical scattering. |

---

## 2. Rover Mechanical & Terramechanical Parameters

The baseline vehicle model represents a medium-class planetary exploration rover (Curiosity / Perseverance scale analog):

```
+-------------------------------------------------------------------+
| Rover Specification Parameter           | Value (SI Units)        |
+-------------------------------------------------------------------+
| Chassis Mass (m)                        | 850.0 kg                |
| Weight on Mars (W = m * g_mars)         | 3,153.5 N               |
| Overall Chassis Length (L)              | 2.80 m                  |
| Overall Chassis Width (W)               | 2.20 m                  |
| Overall Chassis Height (H)              | 1.80 m                  |
| Wheel Configuration                     | 6-Wheel Rocker-Bogie    |
| Wheel Radius (r_w)                      | 0.25 m                  |
| Wheel Width (b_w)                       | 0.40 m                  |
| Minimum Turning Radius (rho_min)        | 0.67 m                  |
| Maximum Forward Speed (v_max)           | 0.40 m/s                |
| Safe Nominal Traverse Speed (v_nom)     | 0.25 m/s                |
| Maximum Traversable Slope               | 25.0 deg (0.436 rad)    |
| Vehicle Tip-Over Static Limit           | 32.0 deg (0.559 rad)    |
| Maximum Traversable Step Height         | 0.25 m (equal to r_w)   |
| Safety Clearance Margin                 | 0.30 m                  |
+-------------------------------------------------------------------+
```

---

## 3. Operational Design Domain (ODD) Boundaries

The autonomous navigation system is designed, verified, and bounded to operate strictly within the following limits:

| Parameter | Nominal Operating Range | Maximum Demonstrated Limit | Out-of-Domain Failure State |
| :--- | :--- | :--- | :--- |
| **Regional Slope** | $0.0^\circ \le \theta \le 15.0^\circ$ | $20.0^\circ$ | $\theta > 25.0^\circ$ (Tip-over risk; motion prohibited) |
| **Obstacle Height** | $h \le 0.20\text{ m}$ (Roll-over) | $0.25\text{ m}$ (Clearance limit) | $h > 0.25\text{ m}$ (Lethal chassis strike) |
| **Crater Diameter** | $D \le 1.0\text{ m}$ | $7.0\text{ m}$ (Detected & bypassed) | Negative drop $> 0.25\text{ m}$ without rim warning |
| **Wheel Slip Ratio** | $s \le 0.15$ | $0.45$ (Evasive derating) | $s > 0.60$ (Entrapment; triggers SAFE_STOP) |
| **Lighting Elevation**| $30^\circ \le \theta_{\text{sun}} \le 75^\circ$ | $15^\circ$ (Deep shadows) | $\theta_{\text{sun}} < 10^\circ$ (Complete darkness without active illumination) |
| **Sensor Noise** | $\mu_{\text{noise}} = 1.0$ | $3.0\times$ baseline | Complete sensor loss $> 2.0\text{ s}$ without recovery |
| **RTOS Latency** | $\Delta t_{\text{plan}} \le 100\text{ ms}$ | $150\text{ ms}$ | Latency $> 250\text{ ms}$ (Trips execution watchdog) |

Transgressions beyond these verified boundaries immediately trigger the Fault Detection, Isolation, and Recovery (FDIR) executive to transition the rover into `SAFE_STOP`.
