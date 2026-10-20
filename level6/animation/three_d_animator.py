"""3D Graphics & Animation Engine — Blender Python API & PyVista Modality.
Provides 3D planetary ephemeris, spacecraft cruise attitude keyframing,
robotic kinematic links, interactive Plotly 3D visualizers, and Blender/PyVista scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class ThreeDGraphicsAnimator:
    """3D Mesh and Celestial Kinematics Generator for Blender & PyVista workflows."""

    def __init__(self, simulation_days: float = 365.25, time_steps: int = 60) -> None:
        self.simulation_days = simulation_days
        self.time_steps = time_steps

    # -------------------------------------------------------------------------
    # Planetary Ephemeris Simulation
    # -------------------------------------------------------------------------
    def simulate_solar_system_3d(self) -> Dict[str, Any]:
        """Compute 3D heliocentric orbits for Sun, Earth, Mars, and Spacecraft."""
        t = np.linspace(0, 2 * np.pi, self.time_steps)

        # Sun at origin
        sun = {"x": [0.0], "y": [0.0], "z": [0.0], "radius": 0.25, "color": "#ffcc00"}

        # Earth (1.0 AU, period = 1.0 yr)
        r_earth = 1.0
        earth_x = (r_earth * np.cos(t)).tolist()
        earth_y = (r_earth * np.sin(t)).tolist()
        earth_z = [0.0] * self.time_steps

        # Mars (1.524 AU, inclination = 1.85 deg, period = 1.88 yr)
        r_mars = 1.524
        mars_inc = np.radians(1.85)
        t_mars = t / 1.88
        mars_x = (r_mars * np.cos(t_mars)).tolist()
        mars_y = (r_mars * np.sin(t_mars) * np.cos(mars_inc)).tolist()
        mars_z = (r_mars * np.sin(t_mars) * np.sin(mars_inc)).tolist()

        # Interplanetary Transfer Spacecraft (Hohmann ellipse connecting Earth to Mars)
        a_transfer = (r_earth + r_mars) / 2.0
        e_transfer = (r_mars - r_earth) / (r_mars + r_earth)
        nu = np.linspace(0, np.pi, self.time_steps)  # True anomaly from perihelion to aphelion
        r_craft = a_transfer * (1.0 - e_transfer**2) / (1.0 + e_transfer * np.cos(nu))
        sc_x = (r_craft * np.cos(nu)).tolist()
        sc_y = (r_craft * np.sin(nu)).tolist()
        sc_z = (0.5 * r_craft * np.sin(nu) * np.sin(mars_inc)).tolist()

        return {
            "time_steps": self.time_steps,
            "sun": sun,
            "earth": {"x": earth_x, "y": earth_y, "z": earth_z},
            "mars": {"x": mars_x, "y": mars_y, "z": mars_z},
            "spacecraft": {"x": sc_x, "y": sc_y, "z": sc_z},
        }

    # -------------------------------------------------------------------------
    # Robotic Arm 3-DOF Kinematics
    # -------------------------------------------------------------------------
    def simulate_robotic_arm_3d(
        self, l1: float = 1.0, l2: float = 0.8, l3: float = 0.5, steps: int = 30
    ) -> List[Dict[str, List[float]]]:
        """Simulate 3D joint trajectories of planetary rover exploration arm."""
        t = np.linspace(0, np.pi, steps)
        frames = []
        for val in t:
            q1 = 0.5 * np.sin(val)  # Base azimuth
            q2 = 0.8 * np.cos(val)  # Shoulder elevation
            q3 = -0.6 * np.sin(2 * val)  # Elbow flex

            # Base joint at origin
            p0 = [0.0, 0.0, 0.0]
            p1 = [0.0, 0.0, 0.3]
            p2 = [
                p1[0] + l1 * np.cos(q1) * np.cos(q2),
                p1[1] + l1 * np.sin(q1) * np.cos(q2),
                p1[2] + l1 * np.sin(q2),
            ]
            p3 = [
                p2[0] + l2 * np.cos(q1) * np.cos(q2 + q3),
                p2[1] + l2 * np.sin(q1) * np.cos(q2 + q3),
                p2[2] + l2 * np.sin(q2 + q3),
            ]
            frames.append({
                "x": [p0[0], p1[0], p2[0], p3[0]],
                "y": [p0[1], p1[1], p2[1], p3[1]],
                "z": [p0[2], p1[2], p2[2], p3[2]],
            })
        return frames

    # -------------------------------------------------------------------------
    # Plotly 3D Animated Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_3d_figure(self) -> Dict[str, Any]:
        """Build interactive 3D heliocentric planetary transfer animation."""
        sim = self.simulate_solar_system_3d()
        n = sim["time_steps"]

        frames = []
        for i in range(n):
            frames.append({
                "name": f"f_{i}",
                "data": [
                    # Sun
                    {"type": "scatter3d", "x": [0], "y": [0], "z": [0], "mode": "markers", "marker": {"color": "gold", "size": 14}, "name": "Sun"},
                    # Earth Orbit & Position
                    {"type": "scatter3d", "x": sim["earth"]["x"], "y": sim["earth"]["y"], "z": sim["earth"]["z"], "mode": "lines", "line": {"color": "#4da6ff", "width": 2}, "name": "Earth Orbit"},
                    {"type": "scatter3d", "x": [sim["earth"]["x"][i]], "y": [sim["earth"]["y"][i]], "z": [sim["earth"]["z"][i]], "mode": "markers", "marker": {"color": "#0077ff", "size": 8}, "name": "Earth"},
                    # Mars Orbit & Position
                    {"type": "scatter3d", "x": sim["mars"]["x"], "y": sim["mars"]["y"], "z": sim["mars"]["z"], "mode": "lines", "line": {"color": "#ff6644", "width": 2}, "name": "Mars Orbit"},
                    {"type": "scatter3d", "x": [sim["mars"]["x"][i]], "y": [sim["mars"]["y"][i]], "z": [sim["mars"]["z"][i]], "mode": "markers", "marker": {"color": "#cc3300", "size": 7}, "name": "Mars"},
                    # Spacecraft Transfer Trajectory & Current Position
                    {"type": "scatter3d", "x": sim["spacecraft"]["x"][: i + 1], "y": sim["spacecraft"]["y"][: i + 1], "z": sim["spacecraft"]["z"][: i + 1], "mode": "lines", "line": {"color": "#39ff14", "width": 4}, "name": "Transfer Path"},
                    {"type": "scatter3d", "x": [sim["spacecraft"]["x"][i]], "y": [sim["spacecraft"]["y"][i]], "z": [sim["spacecraft"]["z"][i]], "mode": "markers", "marker": {"color": "#39ff14", "size": 9, "symbol": "diamond"}, "name": "Spacecraft APPS-6"},
                ],
            })

        initial_data = frames[0]["data"]
        layout = {
            "title": "3D Interplanetary Heliocentric Cruise & Orbital Mechanics (Blender / PyVista Modality)",
            "scene": {
                "xaxis": {"range": [-2.0, 2.0], "title": "X (AU)", "backgroundcolor": "#111"},
                "yaxis": {"range": [-2.0, 2.0], "title": "Y (AU)", "backgroundcolor": "#111"},
                "zaxis": {"range": [-0.5, 0.5], "title": "Z (AU)", "backgroundcolor": "#111"},
                "camera": {"eye": {"x": 1.4, "y": -1.4, "z": 1.1}},
            },
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Launch 3D Simulation",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 40, "redraw": True}, "fromcurrent": True}],
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
                            "label": f"Sol {k * 5}",
                            "method": "animate",
                        }
                        for k in range(0, n, 4)
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
    def generate_blender_script(self) -> str:
        """Generate a complete standalone Blender Python API (`bpy`) animation script."""
        return '''# 3D Graphics Animation in Blender Python API (bpy)
import bpy
import math

# Clear existing objects in scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# 1. Create Sun at center with emission material
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
sun = bpy.context.active_object
sun.name = "Sun"
mat_sun = bpy.data.materials.new(name="SunEmission")
mat_sun.use_nodes = True
nodes = mat_sun.node_tree.nodes
nodes.clear()
node_emit = nodes.new(type='ShaderNodeEmission')
node_emit.inputs['Color'].default_value = (1.0, 0.8, 0.1, 1.0)
node_emit.inputs['Strength'].default_value = 15.0
node_out = nodes.new(type='ShaderNodeOutputMaterial')
mat_sun.node_tree.links.new(node_emit.outputs['Emission'], node_out.inputs['Surface'])
sun.data.materials.append(mat_sun)

# 2. Create Mars Sphere and keyframe its 3D orbit
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(8.0, 0, 0))
mars = bpy.context.active_object
mars.name = "Mars"

# Keyframe 120 frames of planetary orbit
total_frames = 120
for f in range(1, total_frames + 1):
    bpy.context.scene.frame_set(f)
    angle = 2.0 * math.pi * (f / total_frames)
    mars.location = (8.0 * math.cos(angle), 8.0 * math.sin(angle), 0.3 * math.sin(angle))
    mars.rotation_euler = (0, 0.44, angle * 4.0)  # Axial tilt and spin
    mars.keyframe_insert(data_path="location", frame=f)
    mars.keyframe_insert(data_path="rotation_euler", frame=f)

# 3. Add Keyframed Camera tracking Mars
bpy.ops.object.camera_add(location=(14, -14, 8), rotation=(1.1, 0, 0.8))
camera = bpy.context.active_object
bpy.context.scene.camera = camera
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = total_frames
print("Blender 3D Planetary Orbit Animation Created Successfully.")
'''

    def generate_pyvista_script(self) -> str:
        """Generate a complete standalone PyVista 3D animation script."""
        return '''# 3D Graphics Animation in PyVista
import numpy as np
import pyvista as pv

plotter = pv.Plotter(window_size=[1024, 768])
plotter.set_background('#0b0e14')

# Create Sun Sphere
sun_mesh = pv.Sphere(radius=1.2, center=(0, 0, 0))
plotter.add_mesh(sun_mesh, color='gold', lighting=False)

# Create Mars Sphere
mars_mesh = pv.Sphere(radius=0.6, center=(5.0, 0, 0))
mars_actor = plotter.add_mesh(mars_mesh, color='#cc4422', smooth_shading=True)

# Generate GIF orbit
plotter.open_gif("mars_interplanetary_orbit.gif")
n_frames = 90
for f in range(n_frames):
    angle = 2.0 * np.pi * (f / n_frames)
    new_center = [5.0 * np.cos(angle), 5.0 * np.sin(angle), 0.2 * np.sin(angle)]
    translated_mars = pv.Sphere(radius=0.6, center=new_center)
    mars_actor.mapper.SetInputData(translated_mars)
    plotter.camera_position = [(12 * np.cos(angle * 0.3), 12 * np.sin(angle * 0.3), 6), (0, 0, 0), (0, 0, 1)]
    plotter.write_frame()

plotter.close()
print("PyVista 3D Animation saved to mars_interplanetary_orbit.gif")
'''
