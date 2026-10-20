# APPS Planetary Rover Autonomous Navigation System — Algorithm Design

**Document ID:** APPS-ALGO-TRL5-002  
**Target Maturity:** NASA TRL 5  
**Scope:** Core mathematical formulations of state estimation, mapping, traversability, planning, dynamics, and terramechanics.

---

## 1. Error-State Extended Kalman Filter (ES-EKF) Localization

State estimation combines high-rate ($100\text{ Hz}$) inertial propagation with low-rate ($10\text{ Hz}$) wheel odometry corrections using an Error-State Kalman formulation.

### 1.1 State Representation
The true state $x_t \in \mathbb{R}^5$ is decomposed into a nominal state $\hat{x}_t$ and an error state $\delta x_t$:

$$
x_t = \hat{x}_t \oplus \delta x_t, \quad \hat{x}_t = [p_x, p_y, \psi, v, b_g]^T
$$

where $p_x, p_y$ are 2D coordinates in map frame $\mathcal{W}$, $\psi$ is rover heading (yaw), $v$ is forward linear speed, and $b_g$ is gyroscope rate bias.

### 1.2 Kinematic Propagation Step ($100\text{ Hz}$)
Given measured angular rate $\tilde{\omega}$ and forward linear acceleration $\tilde{a}$:

$$
\begin{aligned}
\dot{\hat{p}}_x &= \hat{v} \cos\hat{\psi} \\
\dot{\hat{p}}_y &= \hat{v} \sin\hat{\psi} \\
\dot{\hat{\psi}} &= \tilde{\omega} - \hat{b}_g \\
\dot{\hat{v}} &= \tilde{a} \\
\dot{\hat{b}}_g &= 0
\end{aligned}
$$

Error-state transition matrix $F_k \approx I + F_c \Delta t$:

$$
F_k = \begin{bmatrix}
1 & 0 & -\hat{v}\sin\hat{\psi} \Delta t & \cos\hat{\psi} \Delta t & 0 \\
0 & 1 & \hat{v}\cos\hat{\psi} \Delta t & \sin\hat{\psi} \Delta t & 0 \\
0 & 0 & 1 & 0 & -\Delta t \\
0 & 0 & 0 & 1 & 0 \\
0 & 0 & 0 & 0 & 1
\end{bmatrix}
$$

Covariance propagation:

$$
P_{k|k-1} = F_k P_{k-1|k-1} F_k^T + Q_k
$$

where $Q_k = \text{diag}(\sigma_x^2, \sigma_y^2, \sigma_\psi^2, \sigma_v^2, \sigma_{bg}^2) \Delta t$.

### 1.3 Wheel Odometry Measurement Update ($10\text{ Hz}$)
The wheel odometry measurement provides forward linear speed $z_{v} = v_{\text{wheel}}$ and angular rate $z_{\omega} = \omega_{\text{wheel}}$.
Measurement matrix $H \in \mathbb{R}^{2 \times 5}$:

$$
H = \begin{bmatrix}
0 & 0 & 0 & 1 & 0 \\
0 & 0 & 0 & 0 & 1
\end{bmatrix}
$$

Innovation $y_k = z_k - H \hat{x}_{k|k-1}$ with measurement covariance $R = \text{diag}(\sigma_{v,\text{odom}}^2, \sigma_{\omega,\text{odom}}^2)$.  
Kalman gain:

$$
K_k = P_{k|k-1} H^T (H P_{k|k-1} H^T + R)^{-1}
$$

Joseph-form covariance update guarantees numerical positive semi-definiteness:

$$
P_{k|k} = (I - K_k H) P_{k|k-1} (I - K_k H)^T + K_k R K_k^T
$$

The nominal state is updated: $\hat{x}_{k|k} = \hat{x}_{k|k-1} + K_k y_k$.

---

## 2. 2.5D Elevation Grid & Spatial Mapping

Terrain is mapped into a discrete 2.5D regular grid $\mathcal{M} = \{(\bar{z}_{ij}, \sigma_{z,ij}^2, N_{ij})\}$ with spatial resolution $\Delta x = \Delta y = \text{res}$.

### 2.1 Recursive Kalman Elevation Update
For every point cloud return $p = [x_p, y_p, z_p]^T$ falling into cell $(i, j)$:

$$
i = \left\lfloor \frac{x_p}{\Delta x} \right\rfloor, \quad j = \left\lfloor \frac{y_p}{\Delta y} \right\rfloor
$$

If cell $(i, j)$ is unobserved ($N_{ij} = 0$):

$$
\bar{z}_{ij} = z_p, \quad \sigma_{z,ij}^2 = \sigma_{\text{meas}}^2, \quad N_{ij} = 1
$$

If cell $(i, j)$ is already observed ($N_{ij} \ge 1$):

$$
K_{ij} = \frac{\sigma_{z,ij}^2}{\sigma_{z,ij}^2 + \sigma_{\text{meas}}^2}
$$

$$
\bar{z}_{ij} \leftarrow \bar{z}_{ij} + K_{ij} (z_p - \bar{z}_{ij})
$$

$$
\sigma_{z,ij}^2 \leftarrow (1 - K_{ij}) \sigma_{z,ij}^2
$$

$$
N_{ij} \leftarrow N_{ij} + 1
$$

### 2.2 Radial Negative Obstacle Detection (Drop-Offs & Crater Bowls)
Along radial rays casting outward from the rover $(r_x, r_y)$ over distance $d \le d_{\text{lookahead}}$:

$$
\Delta z = z_{\text{prev}} - z_{\text{curr}}
$$

A cell is flagged as a negative obstacle if:

$$
\Delta z > \Delta z_{\text{drop\_threshold}} = \max(0.08\text{ m}, \text{res} \cdot \tan(25^\circ))
$$

---

## 3. Multi-Criteria Traversability Estimation

The continuous traversability cost $C(i, j) \in [0, 1]$ integrates 5 physical hazards:

$$
C(i, j) = w_{\text{slope}} c_{\text{slope}} + w_{\text{step}} c_{\text{step}} + w_{\text{rough}} c_{\text{rough}} + w_{\text{clear}} c_{\text{clear}} + w_{\text{traction}} c_{\text{traction}}
$$

Normalized weights: $w_{\text{slope}} = 0.35, w_{\text{step}} = 0.25, w_{\text{rough}} = 0.15, w_{\text{clear}} = 0.25$.

1. **Slope Cost**: Evaluated from smoothed surface gradient $\nabla z = [\frac{\partial z}{\partial x}, \frac{\partial z}{\partial y}]^T$:
   $$\theta_{\text{slope}} = \arctan(\|\nabla z\|), \quad c_{\text{slope}} = \min\left(1.0, \frac{\theta_{\text{slope}}}{\theta_{\text{max}}}\right), \quad \theta_{\text{max}} = 25.0^\circ$$
2. **Step Height Cost**: Evaluated across 8-connected neighbor elevation differences:
   $$\Delta h_{\text{max}} = \max_{(dx, dy) \in \mathcal{N}_8} |z_{i,j} - z_{i+dx, j+dy}|, \quad c_{\text{step}} = \min\left(1.0, \frac{\Delta h_{\text{max}}}{h_{\text{step\_max}}}\right), \quad h_{\text{step\_max}} = 0.25\text{ m}$$
3. **Roughness Cost**: From elevation variance:
   $$c_{\text{rough}} = \min\left(1.0, \frac{\sigma_{z,ij}}{\sigma_{\text{rough\_thresh}}}\right), \quad \sigma_{\text{rough\_thresh}} = 0.15\text{ m}$$
4. **Obstacle Clearance Cost**: Euclidean distance transform $D(i, j) = \min_{p \in \mathcal{O}_{\text{lethal}}} \|(i\Delta x, j\Delta y) - p\|_2$:
   $$c_{\text{clear}} = \max\left(0.0, 1.0 - \frac{D(i, j)}{2 \cdot d_{\text{margin}}}\right), \quad d_{\text{margin}} = 0.30\text{ m}$$
5. **Lethal Interlock**:
   $$C(i, j) \equiv 1.0 \quad \forall (i, j) \in \mathcal{O}_{\text{lethal}} = \{\text{Rock}\} \cup \{\text{Crater}\} \cup \{\theta_{\text{slope}} > 25^\circ\} \cup \{\Delta h > 0.25\text{ m}\}$$

---

## 4. Kinodynamic Hybrid A* Motion Planning

Path generation computes kinodynamically feasible non-holonomic trajectories satisfying bounded curvature limits.

### 4.1 Kinematic Bicycle Model
Continuous state $q = [x, y, \psi]^T \in SE(2)$:

$$
\dot{x} = v \cos\psi, \quad \dot{y} = v \sin\psi, \quad \dot{\psi} = v \cdot \kappa, \quad |\kappa| \le \kappa_{\text{max}} = \frac{1}{\rho_{\text{min}}} = 1.50\text{ m}^{-1}
$$

### 4.2 Motion Primitive Expansion
From node $q_n$, expansion evaluates 5 discrete steering curvatures:

$$
\kappa \in \{-\kappa_{\text{max}}, -0.5\kappa_{\text{max}}, 0, +0.5\kappa_{\text{max}}, +\kappa_{\text{max}}\}
$$

Edge cost over step length $L = 1.60\text{ m}$ integrates path distance, average terrain traversability cost $\bar{C}$, and steering penalties:

$$
\Delta g = L \cdot (1.0 + 2.5 \cdot \bar{C} + 0.15 \cdot |\kappa|)
$$

### 4.3 Heuristic Function
Weighted $A^*$ heuristic with goal heading alignment bias:

$$
h(q) = d_{\text{Euclid}}(q, q_{\text{goal}}) \cdot \left(1.0 + 0.30 \cdot \frac{|\Delta\psi_{\text{goal}}|}{\pi}\right)
$$

### 4.4 Analytic Goal Expansion
When within terminal docking distance $d \le 5.0\text{ m}$ from science target, direct analytic connection is evaluated. If collision-free and heading alignment $|\Delta\psi| \le 65^\circ$, the analytic branch connects directly, achieving sub-100 ms solve times.

---

## 5. Terramechanics & Multibody Rover Dynamics

### 5.1 Bekker Normal Pressure-Sinkage Model
Under normal wheel pressure $p$, regolith sinkage $z_0$ satisfies:

$$
p(z) = \left(\frac{k_c}{b_w} + k_\phi\right) z^n
$$

where $b_w = 0.16\text{ m}$ is wheel width, $k_c = 1.4\text{ kPa}\cdot\text{m}^{1-n}$ is cohesive modulus, $k_\phi = 820.0\text{ kPa}\cdot\text{m}^{-n}$ is frictional modulus, and $n = 1.0$ is sinkage exponent.

### 5.2 Janosi-Hanamoto Shear Stress Model
Shear stress $\tau$ at wheel-soil interface under slip displacement $j$:

$$
\tau(j) = \tau_{\text{max}} \left(1 - e^{-j / K_w}\right) = (c + p \tan\phi) \left(1 - e^{-j / K_w}\right)
$$

where $c = 1.2\text{ kPa}$ is regolith cohesion, $\phi = 34.0^\circ$ is internal friction angle, and $K_w = 0.025\text{ m}$ is shear deformation modulus.

### 5.3 Net Drawbar Pull (DP)
Net forward tractive pull available to accelerate the rover:

$$
DP = H_{\text{gross}} - R_c - R_b
$$

where gross thrust $H_{\text{gross}} = b_w r_w \int_{\theta_1}^{\theta_2} \tau(\theta) \cos\theta d\theta$, compaction resistance $R_c = \frac{b_w}{n+1} \left(\frac{k_c}{b_w} + k_\phi\right) z_0^{n+1}$, and $R_b$ is bulldozing resistance.

### 5.4 Rocker-Bogie Load Distribution
For a 6-wheeled vehicle on terrain tilted by regional angle $\theta$:

$$
\sum_{i=1}^6 N_i = m \cdot g_{\text{mars}} \cdot \cos\theta
$$

Differential bar kinematics average left and right bogie pitch angles:

$$
\theta_{\text{body}} = \frac{\theta_{\text{rocker,left}} + \theta_{\text{rocker,right}}}{2}
$$
