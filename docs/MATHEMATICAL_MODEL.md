# Mathematical & Kinematic Model Specification (Level 2)

> **Scientific Integrity & Verification Notice**:  
> This specification documents the mathematical, physical, and sensor models of the **Automated Planetary Perception System (APPS) Level 2 Research Prototype**.  
> All models are evaluated in synthetic procedural simulation and real planetary image transfer tests.  
> This software is an internal research prototype; it is **not** affiliated with, endorsed by, or certified by NASA or JPL.  
> Under `PROTOTYPE_LOCK = True`, `navigation_ready` is held strictly `False`.

---

## 1. Digital Elevation Model (DEM) & Continuous Terrain (Chapters 71 & 180)

### 1.1 Bilinear Surface Interpolation
Let terrain elevation be defined on a discrete grid $H \in \mathbb{R}^{N_y \times N_x}$ with spatial resolution $\Delta$ meters per cell. For any continuous planar coordinate $(x, y) \in [0, (N_x - 1)\Delta] \times [0, (N_y - 1)\Delta]$:

$$i = \lfloor x / \Delta \rfloor, \quad j = \lfloor y / \Delta \rfloor$$

$$u = \frac{x - i\Delta}{\Delta}, \quad v = \frac{y - j\Delta}{\Delta}, \quad u, v \in [0, 1)$$

The continuous surface elevation $z = h(x, y)$ is computed via bilinear interpolation:

$$h(x, y) = (1 - u)(1 - v) H_{j, i} + u(1 - v) H_{j, i+1} + (1 - u) v H_{j+1, i} + u v H_{j+1, i+1}$$

### 1.2 Analytic Surface Normals & Gradient
The continuous gradient $\nabla h(x, y) = \left(\frac{\partial h}{\partial x}, \frac{\partial h}{\partial y}\right)^T$ is evaluated directly:

$$\frac{\partial h}{\partial x} = \frac{1}{\Delta} \left[ (1 - v)(H_{j, i+1} - H_{j, i}) + v(H_{j+1, i+1} - H_{j+1, i}) \right]$$

$$\frac{\partial h}{\partial y} = \frac{1}{\Delta} \left[ (1 - u)(H_{j+1, i} - H_{j, i}) + u(H_{j+1, i+1} - H_{j, i+1}) \right]$$

The unit surface normal vector $\mathbf{n}(x, y) \in \mathbb{S}^2$ pointing into the upper hemisphere is:

$$\mathbf{n}(x, y) = \frac{\begin{pmatrix} -\frac{\partial h}{\partial x} \\ -\frac{\partial h}{\partial y} \\ 1 \end{pmatrix}}{\sqrt{1 + \left(\frac{\partial h}{\partial x}\right)^2 + \left(\frac{\partial h}{\partial y}\right)^2}}$$

### 1.3 Local Slope & Roughness
The scalar terrain slope angle $\theta_{slope}(x, y) \in [0, \pi/2]$ is defined as the deviation from the vertical unit vector $\hat{\mathbf{z}} = (0, 0, 1)^T$:

$$\cos \theta_{slope} = \mathbf{n}(x, y) \cdot \hat{\mathbf{z}} = \frac{1}{\sqrt{1 + \|\nabla h(x, y)\|^2}}$$

$$\theta_{slope}(x, y) = \arccos\left(\mathbf{n}(x, y) \cdot \hat{\mathbf{z}}\right) = \arctan\left(\|\nabla h(x, y)\|\right)$$

Local roughness $r_{rough}(x, y)$ is measured by local residual variance of elevation around the best-fit tangent plane within a window of radius $R_{footprint}$:

$$r_{rough}(x, y) = \sqrt{\frac{1}{|\Omega|} \sum_{(x', y') \in \Omega} \left(h(x', y') - \left[h(x, y) + \nabla h(x, y) \cdot \begin{pmatrix} x' - x \\ y' - y \end{pmatrix}\right]\right)^2}$$

---

## 2. Directional Solar Illumination & Ray-Traced Shadow Buffer (Chapter 71.2)

### 2.1 Sun Vector Geometry
The directional sun vector $\mathbf{s} \in \mathbb{S}^2$ is parametrized by solar azimuth $\phi_{sun} \in [0, 2\pi)$ (measured clockwise from North / $+y$) and solar elevation $\theta_{sun} \in (0, \pi/2]$ above the horizontal plane:

$$\mathbf{s} = \begin{pmatrix} \cos \theta_{sun} \sin \phi_{sun} \\ \cos \theta_{sun} \cos \phi_{sun} \\ \sin \theta_{sun} \end{pmatrix}$$

### 2.2 Discrete Ray-Cast Shadow Buffer
For each terrain query point $\mathbf{p}_0 = (x_0, y_0, h(x_0, y_0) + \epsilon)^T$, an occlusion ray $\mathbf{r}(t) = \mathbf{p}_0 + t \mathbf{s}$ is traced outward for step lengths $t_k = k \cdot \delta_t$ up to a horizon distance $D_{max}$:

$$S(\mathbf{p}_0) = \begin{cases} 1 & \text{if } \exists k > 0 \text{ such that } r_z(t_k) < h(r_x(t_k), r_y(t_k)) \\ 0 & \text{otherwise (unoccluded, direct sun)} \end{cases}$$

### 2.3 Lambertian Diffuse Irradiance Model
Terrain surface irradiance $I(x, y)$ combines direct solar flux and ambient diffuse sky scatter:

$$I(x, y) = I_0 \cdot (1 - S(\mathbf{p}_0)) \cdot \max(0, \mathbf{n}(x, y) \cdot \mathbf{s}) + I_{ambient}$$

Areas where $S(\mathbf{p}_0) = 1$ receive only diffuse ambient scatter, simulating realistic harsh Martian low-sun shadowed topography.

---

## 3. Rover Kinematics, Footprint & Slip Dynamics (Chapter 84, 180)

### 3.1 Unicycle Kinematic State
The vehicle planar pose $\mathbf{q}(t)$ is governed by unicycle kinematics:

$$\mathbf{q}(t) = \begin{pmatrix} x(t) \\ y(t) \\ \theta(t) \end{pmatrix} \in \mathbb{R}^2 \times [-\pi, \pi)$$

Given commanded forward velocity $v(t)$ and steering curvature $\kappa(t)$, angular velocity is $\omega(t) = v(t) \kappa(t)$. The differential state evolution is:

$$\dot{x}(t) = v_{eff}(t) \cos \theta(t)$$

$$\dot{y}(t) = v_{eff}(t) \sin \theta(t)$$

$$\dot{\theta}(t) = \omega(t) = v_{eff}(t) \kappa(t)$$

### 3.2 Actuator Limits & Command Clipping
Commanded velocity and curvature are constrained by physical vehicle limits:

$$v \in [-v_{max}, v_{max}], \quad v_{max} = 0.50 \text{ m/s}$$

$$|\kappa| \le \kappa_{max}, \quad \kappa_{max} = 1.50 \text{ m}^{-1} \implies R_{min} = \frac{1}{\kappa_{max}} \approx 0.67 \text{ m}$$

$$|\omega| \le \omega_{max} = v_{max} \kappa_{max} = 0.75 \text{ rad/s}$$

Linear and angular accelerations are bounded by $|a| \le a_{max} = 0.25 \text{ m/s}^2$ and $|\alpha| \le \alpha_{max} = 0.50 \text{ rad/s}^2$. Any commanded input exceeding these bounds is clipped, and the mechanical clipping counter is incremented in telemetry.

### 3.3 3D Attitude & Tip-Over Limits
The rover chassis has wheelbase $L = 1.0\text{ m}$, track width $W = 0.8\text{ m}$, ground clearance $H_{clear} = 0.25\text{ m}$, and wheel radius $R_w = 0.15\text{ m}$. Contact points under the four corners in body coordinates are:

$$\mathbf{p}_{FL} = \left(\frac{L}{2}, \frac{W}{2}\right), \quad \mathbf{p}_{FR} = \left(\frac{L}{2}, -\frac{W}{2}\right), \quad \mathbf{p}_{RL} = \left(-\frac{L}{2}, \frac{W}{2}\right), \quad \mathbf{p}_{RR} = \left(-\frac{L}{2}, -\frac{W}{2}\right)$$

Transformed into world coordinates and evaluated on $h(x, y)$:
- Pitch angle $\phi$:

  $$\tan \phi = \frac{\frac{1}{2}(z_{FL} + z_{FR}) - \frac{1}{2}(z_{RL} + z_{RR})}{L}$$

- Roll angle $\psi$:

  $$\tan \psi = \frac{\frac{1}{2}(z_{FL} + z_{RL}) - \frac{1}{2}(z_{FR} + z_{RR})}{W}$$

A tip-over hazard or rollover occurs if:

$$\max(|\phi|, |\psi|) \ge \theta_{tip\_limit} = 30.0^\circ \quad (0.5236 \text{ rad})$$

### 3.4 Slope Traction Slip Model
Effective forward velocity is degraded by slope-induced wheel slip:

$$\sigma_{slip}(\theta_s) = \begin{cases} 0 & \text{if } \theta_s < \theta_{slip\_start} \\ \frac{\tan \theta_s - \tan \theta_{slip\_start}}{\tan \theta_{slip\_crit} - \tan \theta_{slip\_start}} & \text{if } \theta_{slip\_start} \le \theta_s \le \theta_{slip\_crit} \\ 1.0 & \text{if } \theta_s > \theta_{slip\_crit} \end{cases}$$

where $\theta_{slip\_start} = 15.0^\circ$ and $\theta_{slip\_crit} = 25.0^\circ$. The effective velocity realized is:

$$v_{eff} = v \cdot (1 - \sigma_{slip}(\theta_s))$$

---

## 4. Camera Projection & Stereo Depth Uncertainty (Chapters 71.3 & 92)

### 4.1 Pinhole Perspective Camera Model
A forward-facing camera is mounted at vehicle body offset $(x_{cam}, y_{cam}, z_{cam}) = (L/2, 0, H_{cam})$ with downward tilt pitch $\alpha_{cam}$. The intrinsic matrix $K$ is:

$$K = \begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}, \quad f_x = f_y = \frac{W_{img}}{2 \tan(\text{HFOV}/2)}$$

A 3D world point $\mathbf{P}_W = (X_W, Y_W, Z_W, 1)^T$ maps to pixel coordinates $(u, v)^T$ via extrinsic transform $T_{CW} = \begin{bmatrix} R_{CW} & \mathbf{t}_{CW} \\ \mathbf{0}^T & 1 \end{bmatrix}$:

$$\mathbf{P}_C = T_{CW} \mathbf{P}_W = \begin{pmatrix} X_C \\ Y_C \\ Z_C \end{pmatrix}$$

$$\begin{pmatrix} u \cdot Z_C \\ v \cdot Z_C \\ Z_C \end{pmatrix} = K \mathbf{P}_C \implies u = \frac{f_x X_C}{Z_C} + c_x, \quad v = \frac{f_y Y_C}{Z_C} + c_y$$

Points with $Z_C \le 0$ or $(u, v) \notin [0, W_{img}] \times [0, H_{img}]$ are outside the field of view.

### 4.2 Stereo Range-Squared Depth Uncertainty
Given stereo baseline $B$ and focal length $f$, optical disparity is $d = \frac{f B}{Z_C}$. Assuming subpixel disparity matching error with standard deviation $\sigma_d$:

$$\frac{\partial Z_C}{\partial d} = -\frac{f B}{d^2} = -\frac{Z_C^2}{f B}$$

$$\sigma_Z(Z_C) = \left|\frac{\partial Z_C}{\partial d}\right| \sigma_d = \frac{Z_C^2}{f B} \sigma_d$$

Depth measurement variance scales with the fourth power of range ($\sigma_Z^2 \propto Z_C^4$). In the 2.5D local cost builder, normalized epistemic depth uncertainty $u(\mathbf{x}) \in [0, 1]$ is modeled quadratically:

$$u(Z_C) = \min\left(1.0, \left(\frac{Z_C}{Z_{max}}\right)^2\right)$$

All unobserved ground, occluded regions behind rocks, and out-of-frame sectors are strictly initialized to $u = 1.0$ (blocked by default).

---

## 5. Kinodynamic Arc Primitives & Swept Footprint (Chapters 84.2, 129, 133)

### 5.1 Exact Arc Integration
Each motion primitive $m_i$ is parametrized by curvature $\kappa_i \in [-\kappa_{max}, \kappa_{max}]$ and arc length $L_{prim} = 1.50\text{ m}$. For any distance $s \in [0, L_{prim}]$ along primitive $i$, the pose $(x(s), y(s), \theta(s))$ relative to starting pose $(x_0, y_0, \theta_0)$ is:

$$\theta(s) = \theta_0 + \kappa_i s$$

$$x(s) = \begin{cases} x_0 + s \cos \theta_0 & \text{if } |\kappa_i| < 10^{-5} \\ x_0 + \frac{1}{\kappa_i} \left[ \sin(\theta_0 + \kappa_i s) - \sin \theta_0 \right] & \text{otherwise} \end{cases}$$

$$y(s) = \begin{cases} y_0 + s \sin \theta_0 & \text{if } |\kappa_i| < 10^{-5} \\ y_0 - \frac{1}{\kappa_i} \left[ \cos(\theta_0 + \kappa_i s) - \cos \theta_0 \right] & \text{otherwise} \end{cases}$$

### 5.2 Swept Footprint Collision Rasterization
At discrete sample intervals $\Delta s = 0.10\text{ m}$ along arc $\gamma_i(s)$, the vehicle footprint polygon is constructed as an oriented bounding box of length $L_{body} = 1.20\text{ m}$ and width $W_{body} = 0.90\text{ m}$ centered at $(x(s), y(s))$ with orientation $\theta(s)$.

The set of grid cells $\Omega_{swept}(m_i)$ covered by the union of bounding boxes along primitive $m_i$ is rasterized. A primitive is immediately discarded if any swept cell $\mathbf{x} \in \Omega_{swept}(m_i)$ satisfies:

$$\text{HardBlocked}(\mathbf{x}) \iff \left( r(\mathbf{x}) \ge r_{block} \;\lor\; u(\mathbf{x}) \ge u_{block} \;\lor\; s(\mathbf{x}) \ge s_{block} \;\lor\; \text{Unknown}(\mathbf{x}) \right)$$

where default thresholds are $r_{block} = 0.70$, $u_{block} = 0.85$, and $s_{block} = 22.0^\circ$.

---

## 6. Multi-Criteria 2.5D Cost Function & Risk Budget (Chapter 94)

### 6.1 Cell Traversability Cost
For any traversable cell $\mathbf{x}$, traversability cost $c(\mathbf{x})$ is:

$$c(\mathbf{x}) = w_d + w_r r(\mathbf{x}) + w_u u(\mathbf{x}) + w_e (1 + k_s s(\mathbf{x})) + w_g g(\mathbf{x})$$

where:
- $w_d = 1.0$: Distance penalty.
- $w_r = 5.0$: Calibrated hazard risk weight.
- $w_u = 3.0$: Epistemic uncertainty penalty.
- $w_e = 0.5$: Slope energy penalty with coefficient $k_s = 0.05$.
- $w_g = 2.0$: Step obstacle / terrain roughness penalty.

### 6.2 Route Risk Budget Rejection
For any candidate trajectory sequence of cells $\mathbf{x}_1, \dots, \mathbf{x}_K$, the catastrophic encounter proxy probability $p_{proxy}$ is:

$$p_{proxy} = 1 - \prod_{k=1}^K (1 - r(\mathbf{x}_k))$$

If $p_{proxy} > p_{budget}$ (where $p_{budget} = 0.15$), the route is rejected with termination code `rejected_budget`.

---

## 7. Multi-Frame Temporal Fusion & Observation Clearing (Chapter 180, Appendix CR)

### 7.1 Pose Covariance Spread
Let $\mathbf{q}_t \sim \mathcal{N}(\hat{\mathbf{q}}_t, \Sigma_t)$ be the estimated vehicle pose with odometry error covariance $\Sigma_t \in \mathbb{R}^{3 \times 3}$. To account for localisation smear, new hazard observations are convolved with a Gaussian spatial uncertainty kernel:

$$K_{\Sigma}(\Delta x, \Delta y) = \frac{1}{2\pi \sigma_p^2} \exp\left(-\frac{\Delta x^2 + \Delta y^2}{2 \sigma_p^2}\right), \quad \sigma_p = \sqrt{\sigma_{x}^2 + \sigma_{y}^2}$$

### 7.2 Consecutive Clear Clearing Rule
To protect against transient sensor misses while preventing permanent ghost obstacles, a cell previously marked as hazard ($r \ge r_{block}$) is downgraded only after $N_{clear} = 3$ consecutive clear observations:

$$r_t(\mathbf{x}) = \begin{cases} \max(r_{prev}(\mathbf{x}), r_{curr}(\mathbf{x})) & \text{if } r_{curr}(\mathbf{x}) \ge r_{block} \\ r_{prev}(\mathbf{x}) - \Delta r_{decay} & \text{if } c_{clear}(\mathbf{x}) \ge N_{clear} \\ r_{prev}(\mathbf{x}) & \text{otherwise} \end{cases}$$

### 7.3 Frozen-Frame Failure Detection
For successive camera feature frames $\mathbf{z}_t, \mathbf{z}_{t-1}$, the frame innovation metric is:

$$\delta_z = \frac{1}{|\mathcal{F}|} \sum_{k \in \mathcal{F}} |z_t(k) - z_{t-1}(k)|$$

If $\delta_z < \epsilon_{frozen}$ while vehicle commanded velocity $|v| > 0$ for $N_{frozen} \ge 3$ consecutive timesteps, the frozen-frame watchdog triggers an immediate `safe_stop`.
