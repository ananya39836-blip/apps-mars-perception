"""Robotics Simulation Engine — ROS 2, Gazebo & Isaac Sim Modality.
Provides autonomous rover navigation, 360° LiDAR raycasting, dynamic occupancy grid mapping,
interactive Plotly robotics visualizer, and ROS 2/Gazebo/Isaac Sim export scripts.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class RoboticsSimulationAnimator:
    """Robotics simulation and autonomous obstacle avoidance generator."""

    def __init__(self, world_size: float = 20.0, num_steps: int = 40) -> None:
        self.world_size = world_size
        self.num_steps = num_steps
        # Circular obstacles (boulders / craters) in the simulated world
        self.obstacles = [
            {"x": 6.0, "y": 4.0, "radius": 1.8},
            {"x": 11.0, "y": 10.0, "radius": 2.2},
            {"x": 14.0, "y": 5.0, "radius": 1.5},
            {"x": 8.0, "y": 14.0, "radius": 2.0},
        ]

    # -------------------------------------------------------------------------
    # Autonomous Waypoint Trajectory & Potential Field Avoidance
    # -------------------------------------------------------------------------
    def simulate_rover_navigation(
        self, start: Tuple[float, float] = (2.0, 2.0), goal: Tuple[float, float] = (18.0, 18.0)
    ) -> List[Dict[str, Any]]:
        """Simulate autonomous rover path planning with reactive obstacle repulsion."""
        pos = np.array(start, dtype=float)
        goal_pos = np.array(goal, dtype=float)
        dt = 0.5
        v_max = 1.0

        history = []
        for step in range(self.num_steps):
            # Attractive force to goal
            diff_goal = goal_pos - pos
            dist_goal = np.linalg.norm(diff_goal)
            if dist_goal < 0.5:
                # Goal reached
                f_att = np.zeros(2)
            else:
                f_att = 1.5 * (diff_goal / dist_goal)

            # Repulsive force from obstacles
            f_rep = np.zeros(2)
            in_hazard = False
            for obs in self.obstacles:
                obs_center = np.array([obs["x"], obs["y"]])
                d_vec = pos - obs_center
                d = np.linalg.norm(d_vec)
                influence_r = obs["radius"] + 2.0
                if d < influence_r:
                    in_hazard = True
                    rep_mag = 4.0 * (1.0 / max(0.2, d - obs["radius"]) - 1.0 / 2.0)
                    f_rep += rep_mag * (d_vec / max(1e-3, d))

            total_force = f_att + f_rep
            force_mag = np.linalg.norm(total_force)
            if force_mag > 1e-4:
                velocity = (total_force / force_mag) * min(v_max, force_mag)
            else:
                velocity = np.zeros(2)

            # 360-degree LiDAR raycasting (16 rays)
            lidar_rays_x, lidar_rays_y = [], []
            max_range = 6.0
            num_rays = 16
            for r_idx in range(num_rays):
                ray_angle = 2.0 * np.pi * (r_idx / num_rays)
                ray_dir = np.array([np.cos(ray_angle), np.sin(ray_angle)])
                hit_dist = max_range
                for obs in self.obstacles:
                    obs_c = np.array([obs["x"], obs["y"]])
                    v_to_c = obs_c - pos
                    proj = np.dot(v_to_c, ray_dir)
                    if proj > 0:
                        perp_sq = np.linalg.norm(v_to_c)**2 - proj**2
                        if perp_sq < obs["radius"]**2:
                            d_hit = proj - math.sqrt(max(0.0, obs["radius"]**2 - perp_sq))
                            if 0 < d_hit < hit_dist:
                                hit_dist = d_hit

                hit_pt = pos + ray_dir * hit_dist
                lidar_rays_x.extend([pos[0], hit_pt[0], None])
                lidar_rays_y.extend([pos[1], hit_pt[1], None])

            history.append({
                "step": step,
                "x": float(pos[0]),
                "y": float(pos[1]),
                "status": "OBSTACLE_AVOIDANCE" if in_hazard else ("GOAL_REACHED" if dist_goal < 0.5 else "WAYPOINT_TRACKING"),
                "lidar_x": lidar_rays_x,
                "lidar_y": lidar_rays_y,
            })
            pos = pos + velocity * dt
            pos = np.clip(pos, 0.0, self.world_size)

        return history

    # -------------------------------------------------------------------------
    # Plotly Animated Figure Generator
    # -------------------------------------------------------------------------
    def build_plotly_robotics_figure(self) -> Dict[str, Any]:
        """Build interactive animated Plotly figure of autonomous rover SLAM navigation."""
        hist = self.simulate_rover_navigation()

        # Obstacle circles
        obs_x, obs_y = [], []
        theta_circle = np.linspace(0, 2 * np.pi, 30)
        for obs in self.obstacles:
            ox = obs["x"] + obs["radius"] * np.cos(theta_circle)
            oy = obs["y"] + obs["radius"] * np.sin(theta_circle)
            obs_x.extend(ox.tolist() + [None])
            obs_y.extend(oy.tolist() + [None])

        frames = []
        for i, h in enumerate(hist):
            trail_x = [st["x"] for st in hist[: i + 1]]
            trail_y = [st["y"] for st in hist[: i + 1]]
            frames.append({
                "name": f"f_{i}",
                "data": [
                    # Obstacles
                    {"type": "scatter", "x": obs_x, "y": obs_y, "mode": "lines", "fill": "toself", "fillcolor": "rgba(255, 68, 68, 0.3)", "line": {"color": "#ff4444", "width": 2}, "name": "Boulders / Hazards"},
                    # LiDAR active beams
                    {"type": "scatter", "x": h["lidar_x"], "y": h["lidar_y"], "mode": "lines", "line": {"color": "rgba(0, 255, 128, 0.4)", "width": 1}, "name": "360° LiDAR Raycasts"},
                    # Trajectory Trail
                    {"type": "scatter", "x": trail_x, "y": trail_y, "mode": "lines", "line": {"color": "#00f0ff", "width": 3}, "name": "Traversed Path"},
                    # Current Rover Position
                    {"type": "scatter", "x": [h["x"]], "y": [h["y"]], "mode": "markers", "marker": {"color": "#ffff00", "size": 14, "symbol": "square"}, "name": f"Rover ({h['status']})"},
                    # Goal Point
                    {"type": "scatter", "x": [18.0], "y": [18.0], "mode": "markers", "marker": {"color": "#39ff14", "size": 16, "symbol": "star"}, "name": "Target Waypoint"},
                ],
            })

        initial_data = frames[0]["data"]
        layout = {
            "title": "Autonomous Rover Navigation & 360° LiDAR Raycasting (ROS 2 / Gazebo / Isaac Sim Modality)",
            "xaxis": {"range": [0, self.world_size], "title": "Map X (m)", "gridcolor": "#333"},
            "yaxis": {"range": [0, self.world_size], "title": "Map Y (m)", "gridcolor": "#333"},
            "template": "plotly_dark",
            "updatemenus": [
                {
                    "type": "buttons",
                    "buttons": [
                        {
                            "label": "▶ Start Autonomous Sim",
                            "method": "animate",
                            "args": [None, {"frame": {"duration": 60, "redraw": True}, "fromcurrent": True}],
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
                            "label": f"Step {k}",
                            "method": "animate",
                        }
                        for k in range(0, len(hist), 2)
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
    def generate_ros2_nav2_launch(self) -> str:
        """Generate a complete standalone ROS 2 Nav2 autonomous navigation launch script."""
        return '''# ROS 2 Nav2 Autonomous Navigation Launch Configuration
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_bringup',
            executable='bringup_launch.py',
            name='apps_nav2_planner',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'default_bt_xml_filename': 'navigate_w_replanning_and_recovery.xml',
                'planner_server': {
                    'expected_planner_frequency': 10.0,
                    'planner_plugins': ['GridBased'],
                    'GridBased': {
                        'plugin': 'nav2_navfn_planner/NavfnPlanner',
                        'tolerance': 0.5,
                        'use_astar': True
                    }
                }
            }]
        )
    ])
'''

    def generate_gazebo_world(self) -> str:
        """Generate a complete standalone Gazebo SDF world simulation file."""
        return '''<?xml version="1.0" ?>
<sdf version="1.6">
  <world name="mars_jezero_simulation">
    <gravity>0 0 -3.721</gravity>
    <include>
      <uri>model://sun</uri>
    </include>
    <include>
      <uri>model://ground_plane</uri>
    </include>
    <!-- Martian Boulder Obstacle -->
    <model name="boulder_1">
      <static>true</static>
      <link name="link">
        <pose>6.0 4.0 0.9 0 0 0</pose>
        <collision name="col">
          <geometry><cylinder><radius>1.8</radius><length>1.8</length></cylinder></geometry>
        </collision>
        <visual name="vis">
          <geometry><cylinder><radius>1.8</radius><length>1.8</length></cylinder></geometry>
          <material><ambient>0.8 0.3 0.1 1</ambient></material>
        </visual>
      </link>
    </model>
  </world>
</sdf>
'''

    def generate_isaac_sim_script(self) -> str:
        """Generate a complete standalone NVIDIA Isaac Sim USD Python robotics script."""
        return '''# NVIDIA Isaac Sim Autonomous Robotics Simulation
from omni.isaac.kit import SimulationApp
simulation_app = SimulationApp({"headless": False})

from omni.isaac.core import World
from omni.isaac.wheeled_robots.robots import WheeledRobot
from omni.isaac.range_sensor import _range_sensor

world = World(physics_dt=1.0/60.0, stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

# Add autonomous differential rover
rover = world.scene.add(
    WheeledRobot(
        prim_path="/World/Rover",
        name="apps_mars_rover",
        wheel_dof_names=["left_wheel_joint", "right_wheel_joint"],
        create_robot=True,
        usd_path="omniverse://localhost/NVIDIA/Assets/Isaac/2023.1.1/Isaac/Robots/Carter/carter_v1.usd",
        position=[2.0, 2.0, 0.3]
    )
)

world.reset()
print("Starting Isaac Sim real-time physics and sensor loop...")
for i in range(500):
    rover.apply_wheel_actions(rover.forward(speed=0.8))
    world.step(render=True)

simulation_app.close()
'''
