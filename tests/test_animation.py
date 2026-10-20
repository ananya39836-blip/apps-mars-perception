"""Automated Tests for Level 6 Code-Generated Animation Suite.
Verifies all 8 animation modalities:
1. Procedural Animation (Pygame, Manim)
2. 3D Graphics & Animation (Blender Python API, PyVista)
3. Generative AI for Video (Diffusers, SVD)
4. Physics-Based Simulation (MuJoCo, PyBullet)
5. Computer Vision + Animation (OpenCV, MediaPipe)
6. Robotics Simulation (ROS 2, Gazebo, Isaac Sim)
7. Scientific Visualization (Matplotlib, Plotly)
8. AI Visualization (Transformer Attention, 3D Gaussian Splatting)
"""
import math
import numpy as np
import pytest

from level6.animation import (
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
    ProceduralAnimator,
    ThreeDGraphicsAnimator,
    GenerativeVideoAnimator,
    PhysicsSimulationAnimator,
    VisionReactiveAnimator,
    RoboticsSimulationAnimator,
    ScientificVisualizationAnimator,
    AIVisualizationAnimator,
)


def test_t106_animation_prototype_lock():
    """Verify safety lock invariants in animation suite."""
    assert PROTOTYPE_LOCK is True
    assert NAVIGATION_READY is False


def test_t107_procedural_animator():
    """Test procedural easing, spirographs, particle fountains, and script generators."""
    anim = ProceduralAnimator(fps=30, duration_sec=1.5)
    # Easing
    assert anim.ease_in_out(0.0) == 0.0
    assert anim.ease_in_out(1.0) == 1.0
    assert 0.4 < anim.ease_in_out(0.5) < 0.6
    assert 0.0 <= anim.ease_out_bounce(0.5) <= 1.0

    # Spirograph
    spiro = anim.generate_spirograph_trajectory(R=5.0, r=3.0, d=2.5, num_points=50)
    assert len(spiro["x"]) == 50
    assert spiro["arc_length"] > 0.0

    # Lissajous
    liss = anim.generate_lissajous_orbit(num_points=40)
    assert len(liss["x"]) == 40

    # Particle fountain
    fountain = anim.simulate_particle_fountain(num_particles=10)
    assert len(fountain) == anim.total_frames
    assert "x" in fountain[0] and "y" in fountain[0]

    # Plotly figure
    fig = anim.build_plotly_animated_figure()
    assert "data" in fig and "layout" in fig and "frames" in fig
    assert len(fig["frames"]) > 0

    # Code generation
    pygame_code = anim.generate_pygame_code()
    assert "pygame.init()" in pygame_code
    manim_code = anim.generate_manim_code()
    assert "from manim import *" in manim_code


def test_t108_three_d_graphics_animator():
    """Test 3D celestial ephemeris, robotic arm kinematics, and Blender/PyVista scripts."""
    anim = ThreeDGraphicsAnimator(time_steps=30)
    sim = anim.simulate_solar_system_3d()
    assert sim["time_steps"] == 30
    assert len(sim["earth"]["x"]) == 30
    assert len(sim["mars"]["x"]) == 30
    assert len(sim["spacecraft"]["x"]) == 30

    arm_frames = anim.simulate_robotic_arm_3d(steps=15)
    assert len(arm_frames) == 15
    assert len(arm_frames[0]["x"]) == 4  # 4 kinematic joints

    fig = anim.build_plotly_3d_figure()
    assert "data" in fig and "layout" in fig and "frames" in fig
    assert fig["layout"]["scene"]["xaxis"]["title"] == "X (AU)"

    blender_script = anim.generate_blender_script()
    assert "import bpy" in blender_script
    assert "primitive_uv_sphere_add" in blender_script

    pyvista_script = anim.generate_pyvista_script()
    assert "import pyvista as pv" in pyvista_script
    assert "open_gif" in pyvista_script


def test_t109_generative_video_animator():
    """Test latent diffusion reverse denoising simulation and Diffusers scripts."""
    anim = GenerativeVideoAnimator(steps=10, latent_dim=12)
    traj = anim.simulate_reverse_diffusion_steps("Martian landscape")
    assert len(traj) == 11  # 10 steps + initial
    # Verify SNR increases as t goes from 1000 down to 0
    assert traj[-1]["snr_db"] > traj[0]["snr_db"]
    assert len(traj[0]["latent_2d"]) == 12

    fig = anim.build_plotly_diffusion_figure()
    assert "frames" in fig
    assert len(fig["frames"]) == 11

    diffusers_script = anim.generate_diffusers_script()
    assert "AnimateDiffPipeline" in diffusers_script
    assert "export_to_gif" in diffusers_script

    svd_script = anim.generate_svd_script()
    assert "StableVideoDiffusionPipeline" in svd_script


def test_t110_physics_simulation_animator():
    """Test RK4 double pendulum physics, energy bounds, and terramechanics slip."""
    anim = PhysicsSimulationAnimator(g=3.721, dt=0.01, total_time=1.0)
    sim = anim.simulate_double_pendulum()
    assert len(sim["x1"]) == anim.steps
    assert len(sim["x2"]) == anim.steps
    assert len(sim["energy"]) == anim.steps
    # Energy should remain within reasonable finite bounds for RK4
    assert np.all(np.isfinite(sim["energy"]))

    # Terramechanics Bekker-Wong
    shear = anim.compute_wheel_soil_shear(normal_pressure_kpa=20.0, slip_ratio=0.10)
    assert shear["actual_shear_kpa"] > 0.0
    assert shear["actual_shear_kpa"] <= shear["max_shear_kpa"]
    assert shear["drawbar_pull_n"] > 0.0

    fig = anim.build_plotly_physics_figure()
    assert "data" in fig and "frames" in fig

    mjcf = anim.generate_mujoco_mjcf()
    assert "<mujoco" in mjcf
    assert 'integrator="RK4"' in mjcf

    pybullet_code = anim.generate_pybullet_script()
    assert "import pybullet as p" in pybullet_code
    assert "stepSimulation" in pybullet_code


def test_t111_vision_reactive_animator():
    """Test reactive optical flow vector fields, skeletal landmarks, and CV scripts."""
    anim = VisionReactiveAnimator(frame_width=320, frame_height=240, num_frames=15)
    flow = anim.simulate_reactive_optical_flow()
    assert len(flow) == 15
    assert flow[0]["mean_flow_magnitude"] >= 0.0
    assert len(flow[0]["grid_x"]) > 0

    skel = anim.simulate_rover_landmark_skeleton()
    assert len(skel) == 15
    assert len(skel[0]["landmarks"]) == 12  # 12 rover chassis points

    fig = anim.build_plotly_vision_figure()
    assert "frames" in fig
    assert len(fig["frames"]) == 15

    cv_script = anim.generate_opencv_optical_flow_script()
    assert "calcOpticalFlowFarneback" in cv_script
    assert "arrowedLine" in cv_script

    mp_script = anim.generate_mediapipe_script()
    assert "mediapipe as mp" in mp_script
    assert "draw_landmarks" in mp_script


def test_t112_robotics_simulation_animator():
    """Test autonomous rover path planning, 360 LiDAR raycasts, and ROS2/Gazebo/Isaac scripts."""
    anim = RoboticsSimulationAnimator(world_size=20.0, num_steps=20)
    hist = anim.simulate_rover_navigation(start=(1.0, 1.0), goal=(15.0, 15.0))
    assert len(hist) == 20
    assert "lidar_x" in hist[0] and len(hist[0]["lidar_x"]) > 0
    # Rover moves forward towards goal
    dist_start = math.hypot(15.0 - 1.0, 15.0 - 1.0)
    dist_end = math.hypot(15.0 - hist[-1]["x"], 15.0 - hist[-1]["y"])
    assert dist_end < dist_start

    fig = anim.build_plotly_robotics_figure()
    assert "frames" in fig
    assert len(fig["frames"]) == 20

    ros_launch = anim.generate_ros2_nav2_launch()
    assert "nav2_bringup" in ros_launch
    assert "NavfnPlanner" in ros_launch

    gazebo_world = anim.generate_gazebo_world()
    assert "<sdf version=" in gazebo_world
    assert "mars_jezero_simulation" in gazebo_world

    isaac_script = anim.generate_isaac_sim_script()
    assert "omni.isaac" in isaac_script
    assert "WheeledRobot" in isaac_script


def test_t113_scientific_visualization_animator():
    """Test Lorenz attractor ODE integration, wave interference, and Matplotlib scripts."""
    anim = ScientificVisualizationAnimator(dt=0.01, num_points=100)
    sim = anim.simulate_lorenz_attractor()
    assert sim["num_points"] == 100
    assert len(sim["x"]) == 100
    assert len(sim["y"]) == 100
    assert len(sim["z"]) == 100

    waves = anim.simulate_wave_interference(grid_size=10, num_frames=5)
    assert len(waves) == 5
    assert len(waves[0]["z"]) == 10

    fig = anim.build_plotly_scientific_figure()
    assert "frames" in fig
    assert len(fig["frames"]) > 0

    mpl_code = anim.generate_matplotlib_func_animation_script()
    assert "FuncAnimation" in mpl_code
    assert "plt.show()" in mpl_code

    plotly_code = anim.generate_plotly_figure_script()
    assert "plotly.graph_objects as go" in plotly_code


def test_t114_ai_visualization_animator():
    """Test Transformer multi-head attention propagation, 3D Gaussian densification, and scripts."""
    anim = AIVisualizationAnimator(num_tokens=6, num_layers=3)
    layers = anim.simulate_attention_propagation()
    assert len(layers) == 3
    # Softmax rows should sum to 1.0
    for lay in layers:
        mat = np.array(lay["attention_matrix"])
        row_sums = np.sum(mat, axis=-1)
        assert np.allclose(row_sums, 1.0, atol=1e-5)
        assert lay["mean_entropy"] > 0.0

    splats = anim.simulate_gaussian_splat_densification(initial_splats=10, iterations=3)
    assert len(splats) == 3
    # Splats count should grow over iterations
    assert splats[-1]["splat_count"] > splats[0]["splat_count"]

    fig = anim.build_plotly_ai_figure()
    assert "frames" in fig
    assert len(fig["frames"]) == 3

    torch_code = anim.generate_pytorch_attention_viz_script()
    assert "MultiheadAttention" in torch_code

    splat_code = anim.generate_gaussian_splat_viz_script()
    assert "Scatter3d" in splat_code or "go.Scatter" in splat_code
