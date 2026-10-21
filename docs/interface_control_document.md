# APPS Interface Control Document (ICD) — TRL 8 Baseline

**Document ID**: `APPS-ICD-TRL8-001`  
**Revision**: 3.0.0  
**Classification**: NASA TRL 8 Interface Control Document  
**Safety Status**: Compile-Time Research Locks Active (`PROTOTYPE_LOCK = True`, `NAVIGATION_READY = False`)  

---

## 1. Scope & Purpose

This Interface Control Document (ICD) defines the mechanical, electrical, logical, and software interfaces across the 13 subsystems of the **Automated Planetary Perception System (APPS)** at **TRL 8**.

---

## 2. Standard Reference Frames & Units

All software interfaces enforce standard International System of Units (SI) and ISO 80000-1 conventions:

| Quantity | Base Unit | Symbol | Permissible Range |
| :--- | :--- | :--- | :--- |
| Length / Translation | Meters | $\text{m}$ | $[-1000.0, 1000.0]$ |
| Linear Velocity | Meters per second | $\text{m/s}$ | $[-0.50, 0.50]$ |
| Linear Acceleration | Meters per second squared | $\text{m/s}^2$ | $[-5.0, 5.0]$ |
| Linear Jerk | Meters per second cubed | $\text{m/s}^3$ | $[-2.0, 2.0]$ |
| Plane Angle | Radians | $\text{rad}$ | $[-\pi, \pi]$ |
| Angular Velocity | Radians per second | $\text{rad/s}$ | $[-1.0, 1.0]$ |
| Time / Timestamp | Seconds (SI) | $\text{s}$ | $[0.0, \infty)$ strictly monotonic |
| Curvature | Inverse meters | $\text{m}^{-1}$ | $[-1.50, 1.50]$ |

### Coordinate Frames
1. **World Frame ($\mathcal{W}$)**: Topocentric East-North-Up (ENU).
2. **Body Frame ($\mathcal{B}$)**: Forward (+X), Port/Left (+Y), Zenith/Up (+Z).
3. **LiDAR Frame ($\mathcal{L}$)**: Fixed mast mount at $[+1.0, 0.0, +1.8]^T_{\mathcal{B}}$.
4. **Camera Mast Frame ($\mathcal{C}$)**: Mast mount at $[+1.1, 0.0, +1.7]^T_{\mathcal{B}}$.
5. **IMU Frame ($\mathcal{I}$)**: Coincident with center of mass $[0.0, 0.0, 0.0]^T_{\mathcal{B}}$.

---

## 3. CCSDS Space Packet Binary Framing Specification

In accordance with **CCSDS 133.0-B-2**, all telemetry packets and actuator command frames comprise a mandatory 16-byte Primary Header followed by the Application Data Field and a 16-bit CRC checksum:

### Primary Header Layout (16 Bytes / 128 Bits)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|Type|SecH|     APID    |SeqFlags|     SequenceCount    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          PacketLength         |       Secondary Header        |
|                               |       (Timestamp Sec)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Secondary Header       |            Spare              |
|        (Timestamp Sub-sec)    |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Reserved            |         Checksum CRC-16       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Application Process Identifiers (APID) Table

| APID (Hex) | Subsystem Origin | Data Packet Type | Transmit Rate |
| :--- | :--- | :--- | :--- |
| `0x010` | Subsystem H (Sensors) | `IMU_TELEMETRY_PACKET` | 100 Hz |
| `0x020` | Subsystem H (Sensors) | `LIDAR_SCAN_PACKET` | 10 Hz |
| `0x030` | Subsystem H (Sensors) | `CAMERA_FRAME_PACKET` | 10 Hz |
| `0x040` | Subsystem H (Sensors) | `WHEEL_ODOM_PACKET` | 100 Hz |
| `0x050` | Subsystem B (Localization) | `EKF_STATE_PACKET` | 100 Hz |
| `0x060` | Subsystem A (Perception) | `TRAVERSABILITY_MAP_PACKET`| 10 Hz |
| `0x070` | Subsystem E (Planning) | `PLANNED_PATH_PACKET` | Event / 1 Hz |
| `0x080` | Subsystem G (Control) | `ACTUATOR_COMMAND_PACKET`| 10 Hz |
| `0x090` | Subsystem I (Executive) | `FDIR_STATUS_PACKET` | 10 Hz |
| `0x0A0` | Subsystem J (Watchdog) | `HEARTBEAT_HEALTH_PACKET`| 100 Hz |

---

## 4. Subsystem Inter-Module Call Signatures

### 4.1 Sensor Data Validator (`Subsystem A/Sensors`)
```python
def validate_imu(packet: IMUPacket) -> bool:
    """Validates IMU telemetry:
    - Checks CRC-16 checksum
    - Asserts finite floats (no NaN, +Inf, -Inf)
    - Verifies monotonic timestamp (t > last_t)
    - Asserts linear acceleration magnitude <= 50.0 m/s^2
    - Asserts angular velocity magnitude <= 10.0 rad/s
    """
```

### 4.2 Error-State EKF (`Subsystem B/Localization`)
```python
def predict(self, accel_meas: np.ndarray, gyro_meas: np.ndarray, dt: float) -> None:
    """Propagates 15-state nominal kinematics and error covariance at 100 Hz."""

def update_wheel_odometry(self, forward_velocity: float, dt: float) -> None:
    """Updates EKF using forward velocity and Non-Holonomic Constraints (NHC)
    with Joseph-form covariance stabilization."""
```

### 4.3 Kinodynamic Hybrid A* Planner (`Subsystem E/Planning`)
```python
def plan(
    start_pose: Tuple[float, float, float],
    goal_pose: Tuple[float, float, float],
    costmap: np.ndarray,
    elevation: np.ndarray,
    res: float,
    timeout_s: float = 0.080
) -> Optional[List[Tuple[float, float, float]]]:
    """Computes kinodynamically feasible SE(2) path satisfying |kappa| <= 1.50 m^-1
    within bounded execution budget <= 80 ms."""
```

### 4.4 Motion Controller (`Subsystem G/Control`)
```python
def compute_steering(
    current_pose: Tuple[float, float, float],
    current_velocity: float,
    path: List[Tuple[float, float, float]]
) -> ActuatorCommandPacket:
    """Computes curvature-derated steering angle delta and linear velocity v."""
```

---

## 5. Error Codes & Fault Escalation Protocol

| Error Code (Hex) | Mnemonic | Description | Default Mitigation Action |
| :--- | :--- | :--- | :--- |
| `0x00` | `ERR_NONE` | Nominal operation | Continue execution |
| `0x11` | `ERR_SENSOR_CRC` | CRC-16 checksum mismatch | Drop packet, log warning |
| `0x12` | `ERR_SENSOR_NAN` | Corrupt float (`NaN`/`Inf`) | Drop packet, increment corrupt counter |
| `0x13` | `ERR_SENSOR_TIMEOUT` | No data for $\ge 300\text{ ms}$ | Flag sensor degraded, switch to dead reckoning |
| `0x21` | `ERR_EKF_DIVERGENCE` | Covariance trace $> 100.0$ | Force transition to `SAFE_STOP`, request re-bias |
| `0x31` | `ERR_PLANNER_TIMEOUT` | Plan search exceeded $80\text{ ms}$| Fall back to progressive truncated receding horizon |
| `0x32` | `ERR_PLANNER_BLOCKED` | All forward corridors impassable | Stop rover, execute $0.5\text{m}$ backtrack recovery |
| `0x41` | `ERR_COLLISION_HAZARD` | Lethal obstacle in swept corridor | Emergency brake ($a = -0.20\text{ m/s}^2$), trigger replan |
| `0x51` | `ERR_WATCHDOG_MISS` | Cycle time exceeded $100\text{ ms}$ | Increment fault counter; halt on 3 consecutive misses |
