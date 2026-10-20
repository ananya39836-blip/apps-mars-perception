"""Procedural Animation Engine — Pygame & Manim Modality.
Provides mathematical curve generation, easing kinematics, particle dynamics,
interactive Plotly animated figure dicts, and runnable Pygame/Manim scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class ProceduralAnimator:
    """Procedural parametric animation and kinematic easing generator."""

    def __init__(self, fps: int = 30, duration_sec: float = 3.0) -> None:
        self.fps = fps
        self.duration_sec = duration_sec
        self.total_frames = int(fps * duration_sec)

    # -------------------------------------------------------------------------
    # Easing Functions (Manim / Animation standard)
    # -------------------------------------------------------------------------
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Smooth ease-in-out S-curve interpolation for t in [0, 1]."""
        t = max(0.0, min(1.0, float(t)))
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bouncing deceleration rate function."""
        t = max(0.0, min(1.0, float(t)))
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375

    # -------------------------------------------------------------------------
    # Parametric Curves & Spirographs
    # -------------------------------------------------------------------------
    def generate_spirograph_trajectory(
        self, R: float = 5.0, r: float = 3.0, d: float = 2.5, num_points: int = 200
    ) -> Dict[str, np.ndarray]:
        """Generate parametric hypotrochoid / spirograph coordinates."""
        theta = np.linspace(0, 4 * np.pi, num_points)
        diff = R - r
        x = diff * np.cos(theta) + d * np.cos(diff * theta / r)
        y = diff * np.sin(theta) - d * np.sin(diff * theta / r)
        return {
            "theta": theta,
            "x": x,
            "y": y,
            "arc_length": float(np.sum(np.hypot(np.diff(x), np.diff(y)))),
        }

    def generate_lissajous_orbit(
        self, a: float = 3.0, b: float = 2.0, delta: float = np.pi / 2, num_points: int = 150
    ) -> Dict[str, np.ndarray]:
        """Generate harmonic Lissajous parametric orbit."""
        t = np.linspace(0, 2 * np.pi, num_points)
        x = np.sin(a * t + delta)
        y = np.sin(b * t)
        return {"t": t, "x": x, "y": y}

    # -------------------------------------------------------------------------
    # Particle Fountain Simulation
    # -------------------------------------------------------------------------
    def simulate_particle_fountain(
        self, num_particles: int = 50, gravity: float = 9.81
    ) -> List[Dict[str, Any]]:
        """Simulate ballistic procedural particle fountain across discrete frames."""
        np.random.seed(42)
        particles = []
        for i in range(num_particles):
            angle = np.random.uniform(np.pi / 4, 3 * np.pi / 4)
            speed = np.random.uniform(4.0, 10.0)
            particles.append({
                "id": i,
                "vx": speed * np.cos(angle),
                "vy": speed * np.sin(angle),
                "lifetime": np.random.uniform(1.5, self.duration_sec),
            })

        frames_data = []
        dt = self.duration_sec / self.total_frames
        for f in range(self.total_frames):
            t = f * dt
            xs, ys, alphas = [], [], []
            for p in particles:
                if t <= p["lifetime"]:
                    px = p["vx"] * t
                    py = max(0.0, p["vy"] * t - 0.5 * gravity * (t**2))
                    alpha = 1.0 - (t / p["lifetime"])
                else:
                    px, py, alpha = 0.0, 0.0, 0.0
                xs.append(px)
                ys.append(py)
                alphas.append(alpha)
            frames_data.append({"frame_idx": f, "t": t, "x": xs, "y": ys, "alpha": alphas})
        return frames_data

    # -------------------------------------------------------------------------
    # Plotly Animated Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_animated_figure(self) -> Dict[str, Any]:
        """Build interactive animated Plotly figure definition dictionary."""
        spiro = self.generate_spirograph_trajectory(num_points=120)
        xs, ys = spiro["x"].tolist(), spiro["y"].tolist()

        frames = []
        for i in range(1, len(xs) + 1):
            frames.append({
                "name": f"frame_{i}",
                "data": [
                    {
                        "type": "scatter",
                        "x": xs[:i],
                        "y": ys[:i],
                        "mode": "lines",
                        "line": {"color": "#00f0ff", "width": 3},
                        "name": "Procedural Path",
                    },
                    {
                        "type": "scatter",
                        "x": [xs[i - 1]],
                        "y": [ys[i - 1]],
                        "mode": "markers",
                        "marker": {"color": "#ff007f", "size": 12, "symbol": "circle"},
                        "name": "Current Head",
                    },
                ],
            })

        initial_data = [
            {
                "type": "scatter",
                "x": [xs[0]],
                "y": [ys[0]],
                "mode": "lines",
                "line": {"color": "#00f0ff", "width": 3},
                "name": "Procedural Path",
            },
            {
                "type": "scatter",
                "x": [xs[0]],
                "y": [ys[0]],
                "mode": "markers",
                "marker": {"color": "#ff007f", "size": 12},
                "name": "Current Head",
            },
        ]

        layout = {
            "title": "Procedural Parametric Spirograph & Easing Motion (Pygame / Manim Modality)",
            "xaxis": {"range": [-8, 8], "title": "X Coordinate (m)", "gridcolor": "#333"},
            "yaxis": {"range": [-8, 8], "title": "Y Coordinate (m)", "gridcolor": "#333"},
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Play",
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
                            "args": [[f"frame_{k}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
                            "label": str(k),
                            "method": "animate",
                        }
                        for k in range(1, len(xs) + 1, 5)
                    ],
                    "transition": {"duration": 0},
                    "x": 0.1,
                    "len": 0.9,
                }
            ],
        }
        return {"data": initial_data, "layout": layout, "frames": frames}

    # -------------------------------------------------------------------------
    # Code Generators
    # -------------------------------------------------------------------------
    def generate_pygame_code(self) -> str:
        """Generate a complete standalone executable Pygame script."""
        return '''# Procedural Animation in Pygame
import sys
import math
import pygame

pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("APPS Procedural Spirograph & Particle Engine")
clock = pygame.time.Clock()

trail = []
t = 0.0

running = True
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    t += 0.02
    R, r, d = 160.0, 96.0, 80.0
    x = int(WIDTH / 2 + (R - r) * math.cos(t) + d * math.cos((R - r) * t / r))
    y = int(HEIGHT / 2 + (R - r) * math.sin(t) - d * math.sin((R - r) * t / r))
    trail.append((x, y))
    if len(trail) > 400:
        trail.pop(0)

    screen.fill((15, 18, 26))
    if len(trail) > 1:
        pygame.draw.lines(screen, (0, 240, 255), False, trail, 2)
    pygame.draw.circle(screen, (255, 0, 127), (x, y), 8)

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    def generate_manim_code(self) -> str:
        """Generate a complete standalone executable Manim script."""
        return '''# Procedural Animation in Manim
from manim import *

class ProceduralSpirographScene(Scene):
    def construct(self):
        title = Text("APPS Procedural Parametric Trajectory", font_size=36, color=BLUE)
        self.play(Write(title))
        self.play(title.animate.to_edge(UP))

        R, r, d = 3.0, 1.8, 1.5
        curve = ParametricFunction(
            lambda t: np.array([
                (R - r) * np.cos(t) + d * np.cos((R - r) * t / r),
                (R - r) * np.sin(t) - d * np.sin((R - r) * t / r),
                0.0
            ]),
            t_range=[0, 4 * PI, 0.02],
            color=TEAL
        )
        dot = Dot(point=curve.get_start(), color=PINK, radius=0.12)
        
        self.play(Create(curve), run_time=4.0, rate_func=smooth)
        self.play(MoveAlongPath(dot, curve), run_time=4.0, rate_func=linear)
        self.wait(1)
'''
