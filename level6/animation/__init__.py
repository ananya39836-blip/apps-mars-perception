"""Automated Planetary Perception System (APPS) — Level 6 Code-Generated Animation Suite.

Encompasses 8 Advanced Code-Generated Animation and Simulation Modalities:
1. Procedural Animation (Pygame, Manim): Parametric curves, easing kinematics, spirographs, particle dynamics.
2. 3D Graphics & Animation (Blender Python API, PyVista): 3D celestial bodies, spacecraft attitude, robotic arm meshes.
3. Generative AI for Video (Diffusers, SVD): Latent diffusion reverse denoising, motion flow, text-prompt conditioned video frames.
4. Physics-Based Simulation (MuJoCo, PyBullet): Rigid-body multibody dynamics, Runge-Kutta integrators, wheel-soil shear slip.
5. Computer Vision + Animation (OpenCV, MediaPipe): Reactive visual landmark tracking, optical flow fields, neuromorphic DVS events.
6. Robotics Simulation (ROS 2, Gazebo, Isaac Sim): Autonomous obstacle avoidance, 360° LiDAR raycasting, occupancy grid mapping.
7. Scientific Visualization (Matplotlib, Plotly): Equation-governed chaos (Lorenz attractor), orbital transfers, wave mechanics.
8. AI Visualization: Neural network attention flow, 3D Gaussian Splatting iterative densification, loss surface descent.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""

from .procedural_animator import ProceduralAnimator
from .three_d_animator import ThreeDGraphicsAnimator
from .generative_video_animator import GenerativeVideoAnimator
from .physics_animator import PhysicsSimulationAnimator
from .vision_reactive_animator import VisionReactiveAnimator
from .robotics_animator import RoboticsSimulationAnimator
from .scientific_animator import ScientificVisualizationAnimator
from .ai_visualization_animator import AIVisualizationAnimator

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False

__all__ = [
    "PROTOTYPE_LOCK",
    "NAVIGATION_READY",
    "ProceduralAnimator",
    "ThreeDGraphicsAnimator",
    "GenerativeVideoAnimator",
    "PhysicsSimulationAnimator",
    "VisionReactiveAnimator",
    "RoboticsSimulationAnimator",
    "ScientificVisualizationAnimator",
    "AIVisualizationAnimator",
]
