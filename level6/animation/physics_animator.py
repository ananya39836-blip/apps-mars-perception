"""Physics-Based Simulation Engine — MuJoCo & PyBullet Modality.
Provides multibody rigid-body dynamics with RK4 numerical integration,
chaotic double-pendulum physics, wheel-soil terramechanics slip,
interactive Plotly physics visualizer, and MuJoCo MJCF / PyBullet scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class PhysicsSimulationAnimator:
    """Rigid-body multibody physics and terramechanics simulation generator."""

    def __init__(self, g: float = 3.721, dt: float = 0.02, total_time: float = 4.0) -> None:
        self.g = g  # Martian gravity (m/s^2)
        self.dt = dt
        self.total_time = total_time
        self.steps = int(total_time / dt)

    # -------------------------------------------------------------------------
    # Chaotic Double Pendulum Multibody Dynamics (RK4)
    # -------------------------------------------------------------------------
    def simulate_double_pendulum(
        self,
        m1: float = 1.0,
        m2: float = 1.0,
        l1: float = 1.0,
        l2: float = 1.0,
        th1_init: float = np.pi / 2,
        th2_init: float = np.pi / 2,
    ) -> Dict[str, Any]:
        """Integrate equations of motion of a double pendulum using 4th-order Runge-Kutta."""
        state = np.array([th1_init, th2_init, 0.0, 0.0])  # [theta1, theta2, omega1, omega2]

        def derivatives(s: np.ndarray) -> np.ndarray:
            t1, t2, w1, w2 = s
            delta = t1 - t2

            den1 = l1 * (2 * m1 + m2 - m2 * np.cos(2 * t1 - 2 * t2))
            den2 = l2 * (2 * m1 + m2 - m2 * np.cos(2 * t1 - 2 * t2))

            dw1 = (
                -self.g * (2 * m1 + m2) * np.sin(t1)
                - m2 * self.g * np.sin(t1 - 2 * t2)
                - 2 * np.sin(delta) * m2 * (w2**2 * l2 + w1**2 * l1 * np.cos(delta))
            ) / den1

            dw2 = (
                2
                * np.sin(delta)
                * (
                    w1**2 * l1 * (m1 + m2)
                    + self.g * (m1 + m2) * np.cos(t1)
                    + w2**2 * l2 * m2 * np.cos(delta)
                )
            ) / den2

            return np.array([w1, w2, dw1, dw2])

        trajectory_x1, trajectory_y1 = [], []
        trajectory_x2, trajectory_y2 = [], []
        energies = []

        for _ in range(self.steps):
            t1, t2, w1, w2 = state
            x1 = l1 * np.sin(t1)
            y1 = -l1 * np.cos(t1)
            x2 = x1 + l2 * np.sin(t2)
            y2 = y1 - l2 * np.cos(t2)

            trajectory_x1.append(float(x1))
            trajectory_y1.append(float(y1))
            trajectory_x2.append(float(x2))
            trajectory_y2.append(float(y2))

            # Hamiltonian Energy Check
            ke = 0.5 * m1 * (l1 * w1) ** 2 + 0.5 * m2 * (
                (l1 * w1) ** 2 + (l2 * w2) ** 2 + 2 * l1 * l2 * w1 * w2 * np.cos(t1 - t2)
            )
            pe = -(m1 + m2) * self.g * l1 * np.cos(t1) - m2 * self.g * l2 * np.cos(t2)
            energies.append(float(ke + pe))

            # RK4 Step
            k1 = derivatives(state)
            k2 = derivatives(state + 0.5 * self.dt * k1)
            k3 = derivatives(state + 0.5 * self.dt * k2)
            k4 = derivatives(state + self.dt * k3)
            state = state + (self.dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

        return {
            "x1": trajectory_x1,
            "y1": trajectory_y1,
            "x2": trajectory_x2,
            "y2": trajectory_y2,
            "energy": energies,
            "steps": self.steps,
        }

    # -------------------------------------------------------------------------
    # Terramechanics Bekker-Wong Wheel-Soil Slip
    # -------------------------------------------------------------------------
    def compute_wheel_soil_shear(
        self, normal_pressure_kpa: float = 25.0, slip_ratio: float = 0.15
    ) -> Dict[str, float]:
        """Compute shear stress at rover wheel contact patch using Bekker-Wong equation."""
        c = 1.2  # Cohesion (kPa) for Martian regolith
        phi = np.radians(35.0)  # Internal friction angle
        K = 0.025  # Shear deformation modulus (m)
        j = slip_ratio * 0.15  # Shear displacement
        max_shear = c + normal_pressure_kpa * np.tan(phi)
        actual_shear = max_shear * (1.0 - np.exp(-j / K))
        drawbar_pull_n = float(actual_shear * 0.08 * 1000.0)  # 0.08 m^2 contact area
        return {
            "slip_ratio": slip_ratio,
            "max_shear_kpa": float(max_shear),
            "actual_shear_kpa": float(actual_shear),
            "drawbar_pull_n": drawbar_pull_n,
            "tractive_efficiency": float(1.0 - slip_ratio),
        }

    # -------------------------------------------------------------------------
    # Plotly Animated Double Pendulum Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_physics_figure(self) -> Dict[str, Any]:
        """Build interactive animated Plotly figure of chaotic double pendulum."""
        sim = self.simulate_double_pendulum()
        x1, y1 = sim["x1"], sim["y1"]
        x2, y2 = sim["x2"], sim["y2"]

        frames = []
        step_stride = 2
        for i in range(0, len(x1), step_stride):
            frames.append({
                "name": f"step_{i}",
                "data": [
                    # Links (Origin to Rod 1 to Rod 2)
                    {
                        "type": "scatter",
                        "x": [0.0, x1[i], x2[i]],
                        "y": [0.0, y1[i], y2[i]],
                        "mode": "lines+markers",
                        "line": {"color": "#00f0ff", "width": 4},
                        "marker": {"size": [10, 14, 18], "color": ["#ffffff", "#00d4ff", "#ff007f"]},
                        "name": "Rigid Links",
                    },
                    # Chaotic Tip Trace
                    {
                        "type": "scatter",
                        "x": x2[max(0, i - 40) : i + 1],
                        "y": y2[max(0, i - 40) : i + 1],
                        "mode": "lines",
                        "line": {"color": "#ff007f", "width": 2, "dash": "dot"},
                        "name": "Chaotic Tip Orbit",
                    },
                ],
            })

        initial_data = frames[0]["data"]
        layout = {
            "title": f"Chaotic Rigid-Body Pendulum RK4 Dynamics in Martian Gravity (g={self.g:.2f} m/s²)",
            "xaxis": {"range": [-2.5, 2.5], "title": "X (m)", "gridcolor": "#333"},
            "yaxis": {"range": [-2.5, 2.5], "title": "Y (m)", "gridcolor": "#333"},
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Run RK4 Physics",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 25, "redraw": True}, "fromcurrent": True}],
                        },
                        {
                            "label": "⏸ Pause",
                            "method": "animate",
                            "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}],
                        },
                    ],
                }
            ],
            "sliders": [
                {
                    "steps": [
                        {
                            "args": [[f"step_{s}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                            "label": f"{s * self.dt:.2f}s",
                            "method": "animate",
                        }
                        for s in range(0, len(x1), step_stride * 5)
                    ],
                    "x": 0.1,
                    "len": 0.9,
                }
            ],
        }
        return {"data": initial_data, "layout": layout, "frames": frames}

    # -------------------------------------------------------------------------
    # Code Generators
    # -------------------------------------------------------------------------
    def generate_mujoco_mjcf(self) -> str:
        """Generate a complete standalone MuJoCo XML (MJCF) model."""
        return '''<mujoco model="apps_mars_multibody_pendulum">
  <compiler angle="radian" coordinate="local"/>
  <option gravity="0 0 -3.721" timestep="0.002" integrator="RK4"/>
  <worldbody>
    <light diffuse=".8 .8 .8" pos="0 0 5" dir="0 0 -1"/>
    <geom type="plane" size="5 5 0.1" rgba="0.4 0.25 0.15 1"/>
    
    <!-- Base Mounting Joint -->
    <body pos="0 0 2.5">
      <joint name="pin1" type="hinge" axis="0 1 0"/>
      <geom type="capsule" fromto="0 0 0 0 0 -1" size="0.04" rgba="0 0.8 1 1"/>
      
      <!-- Second Link -->
      <body pos="0 0 -1">
        <joint name="pin2" type="hinge" axis="0 1 0"/>
        <geom type="capsule" fromto="0 0 0 0 0 -0.8" size="0.035" rgba="1 0 0.5 1"/>
        <geom type="sphere" pos="0 0 -0.8" size="0.08" rgba="1 1 0 1"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <motor joint="pin1" ctrlrange="-10 10" ctrllimited="true"/>
  </actuator>
</mujoco>
'''

    def generate_pybullet_script(self) -> str:
        """Generate a complete standalone PyBullet simulation script."""
        return '''# Physics-Based Simulation in PyBullet
import time
import pybullet as p
import pybullet_data

physicsClient = p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -3.721)  # Martian Gravity

planeId = p.loadURDF("plane.urdf")
startPos = [0, 0, 1]
startOrientation = p.getQuaternionFromEuler([0, 0, 0])
boxId = p.loadURDF("r2d2.urdf", startPos, startOrientation)

print("Starting PyBullet physics simulation loop...")
for i in range(2400):
    p.stepSimulation()
    time.sleep(1.0 / 240.0)

cubePos, cubeOrn = p.getBasePositionAndOrientation(boxId)
print(f"Final Robot Position: {cubePos}")
p.disconnect()
'''
