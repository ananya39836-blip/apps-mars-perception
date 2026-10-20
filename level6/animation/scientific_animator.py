"""Scientific Visualization Engine — Matplotlib & Plotly Modality.
Provides mathematical equation-driven animations, non-linear chaos (Lorenz Attractor),
wave mechanics, interactive Plotly animated visualizer, and Matplotlib FuncAnimation scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class ScientificVisualizationAnimator:
    """Scientific visualization and differential equation animation generator."""

    def __init__(self, dt: float = 0.01, num_points: int = 600) -> None:
        self.dt = dt
        self.num_points = num_points

    # -------------------------------------------------------------------------
    # Lorenz Strange Attractor Non-Linear Differential Equations
    # -------------------------------------------------------------------------
    def simulate_lorenz_attractor(
        self,
        sigma: float = 10.0,
        rho: float = 28.0,
        beta: float = 8.0 / 3.0,
        x0: float = 0.1,
        y0: float = 0.0,
        z0: float = 0.0,
    ) -> Dict[str, List[float]]:
        """Integrate 3D non-linear chaotic Lorenz attractor ODEs."""
        xs = [x0]
        ys = [y0]
        zs = [z0]

        x, y, z = x0, y0, z0
        for _ in range(self.num_points - 1):
            dx = sigma * (y - x) * self.dt
            dy = (x * (rho - z) - y) * self.dt
            dz = (x * y - beta * z) * self.dt
            x += dx
            y += dy
            z += dz
            xs.append(float(x))
            ys.append(float(y))
            zs.append(float(z))

        return {"x": xs, "y": ys, "z": zs, "num_points": self.num_points}

    # -------------------------------------------------------------------------
    # Multi-Harmonic Wave Dynamics
    # -------------------------------------------------------------------------
    def simulate_wave_interference(
        self, grid_size: int = 30, num_frames: int = 25
    ) -> List[Dict[str, Any]]:
        """Simulate mathematical 2D wave interference over discrete time steps."""
        x = np.linspace(-4, 4, grid_size)
        y = np.linspace(-4, 4, grid_size)
        xx, yy = np.meshgrid(x, y)

        r1 = np.sqrt((xx - 1.2)**2 + yy**2)
        r2 = np.sqrt((xx + 1.2)**2 + yy**2)

        frames = []
        for f in range(num_frames):
            t = f * 0.2
            z = np.sin(2.5 * r1 - 3.0 * t) / (r1 + 0.5) + np.sin(2.5 * r2 - 3.0 * t) / (r2 + 0.5)
            frames.append({"frame": f, "t": t, "z": z.tolist()})
        return frames

    # -------------------------------------------------------------------------
    # Plotly Animated Lorenz Attractor Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_scientific_figure(self) -> Dict[str, Any]:
        """Build interactive animated Plotly figure of mathematical Lorenz butterfly trajectory."""
        sim = self.simulate_lorenz_attractor()
        xs, ys, zs = sim["x"], sim["y"], sim["z"]

        frames = []
        step_stride = 15
        for i in range(step_stride, len(xs) + 1, step_stride):
            frames.append({
                "name": f"f_{i}",
                "data": [
                    # Trajectory path (X vs Z projection)
                    {
                        "type": "scatter",
                        "x": xs[:i],
                        "y": zs[:i],
                        "mode": "lines",
                        "line": {"color": "#ff007f", "width": 2},
                        "name": "Chaotic Manifold Trace",
                    },
                    # Leading particle
                    {
                        "type": "scatter",
                        "x": [xs[i - 1]],
                        "y": [zs[i - 1]],
                        "mode": "markers",
                        "marker": {"color": "#00f0ff", "size": 10},
                        "name": "Phase State",
                    },
                ],
            })

        initial_data = frames[0]["data"]
        layout = {
            "title": "Mathematical Chaos: Lorenz Attractor Equations (dx/dt=σ(y-x), dy/dt=x(ρ-z)-y, dz/dt=xy-βz)",
            "xaxis": {"range": [-25, 25], "title": "X State (Convective Roll Rate)", "gridcolor": "#333"},
            "yaxis": {"range": [0, 50], "title": "Z State (Vertical Temperature Profile)", "gridcolor": "#333"},
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Integrate Attractor",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 30, "redraw": True}, "fromcurrent": True}],
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
                            "args": [[f"f_{k}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                            "label": f"t={k * self.dt:.1f}s",
                            "method": "animate",
                        }
                        for k in range(step_stride, len(xs) + 1, step_stride * 2)
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
    def generate_matplotlib_func_animation_script(self) -> str:
        """Generate a complete standalone Matplotlib FuncAnimation script."""
        return '''# Scientific Visualization with Matplotlib FuncAnimation
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Lorenz Differential Equation Parameters
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
dt = 0.01
num_steps = 1000

xs, ys, zs = [0.1], [0.0], [0.0]
for _ in range(num_steps):
    x, y, z = xs[-1], ys[-1], zs[-1]
    xs.append(x + sigma * (y - x) * dt)
    ys.append(y + (x * (rho - z) - y) * dt)
    zs.append(z + (x * y - beta * z) * dt)

fig = plt.figure(figsize=(10, 7), facecolor='#0b0e14')
ax = fig.add_subplot(111, projection='3d', facecolor='#0b0e14')
ax.set_title("Scientific Animation: Lorenz Strange Attractor", color='white', fontsize=14)

line, = ax.plot([], [], [], color='#00f0ff', lw=1.2)
point, = ax.plot([], [], [], marker='o', color='#ff007f', markersize=8)

ax.set_xlim(-25, 25)
ax.set_ylim(-35, 35)
ax.set_zlim(0, 50)
ax.tick_params(colors='gray')

def update(frame):
    line.set_data(xs[:frame], ys[:frame])
    line.set_3d_properties(zs[:frame])
    point.set_data([xs[frame]], [ys[frame]])
    point.set_3d_properties([zs[frame]])
    ax.view_init(elev=18, azim=frame * 0.4)
    return line, point

anim = FuncAnimation(fig, update, frames=range(1, num_steps, 5), interval=30, blit=False)
plt.show()
'''

    def generate_plotly_figure_script(self) -> str:
        """Generate a complete standalone Plotly animated HTML export script."""
        return '''# Scientific Visualization with Plotly
import plotly.graph_objects as go
import numpy as np

t = np.linspace(0, 4 * np.pi, 100)
x = np.sin(t)
y = np.cos(2 * t)

fig = go.Figure(
    data=[go.Scatter(x=[x[0]], y=[y[0]], mode="markers+lines", line=dict(color="#00f0ff", width=3))],
    layout=go.Layout(
        title="Harmonic Lissajous Scientific Trajectory",
        template="plotly_dark",
        updatemenus=[dict(type="buttons", buttons=[dict(label="Play", method="animate", args=[None])])]
    ),
    frames=[go.Frame(data=[go.Scatter(x=x[:k], y=y[:k])]) for k in range(1, 100, 2)]
)
fig.write_html("scientific_animation.html")
print("Plotly scientific animation written to scientific_animation.html")
'''
