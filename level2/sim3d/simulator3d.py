"""Level 2 3D Simulator Environment with Strict Information Boundary.
Chapters 71, 91, 180 (Part 12 Task 101).
"""
import math
from typing import Tuple
import numpy as np
from level2.sim3d.terrain3d import Terrain3D, generate_dem_scene_3d
from level2.sensing.camera3d import Camera3D
from level2.kinematics.rover_params import RoverParams
from level2.kinematics.kinematic_model import simulate_kinematic_step


class Simulator3D:
    """Isolated 3D Simulation Environment.
    Enforces the mechanical information boundary:
    Rover holds no handle to ground-truth 3D terrain elevation or hazard masks.
    """
    
    def __init__(self, terrain: Terrain3D = None, seed: int = 42,
                 difficulty: str = "D1", params: RoverParams = None):
        self._terrain = terrain if terrain is not None else generate_dem_scene_3d(seed=seed, difficulty=difficulty)
        self.params = params if params is not None else RoverParams()
        self.camera = Camera3D()
        
        # World limits
        self.x_max_m = self._terrain.x_max_m
        self.y_max_m = self._terrain.y_max_m
        self.goal_x_m = self.x_max_m - 1.0  # Goal is reaching east boundary
        
        # Ground truth state (x, y, z, theta, v, pitch, roll)
        start_y = self.y_max_m / 2.0
        start_z = self._terrain.get_elevation_continuous(0.5, start_y)
        self._true_state = (0.5, start_y, 0.0) # x, y, theta
        self._true_z = start_z

    def get_camera_observation(self, believed_pose: Tuple[float, float, float],
                               sensor_ok: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Produce perspective camera observation from vehicle pose.
        If sensor_ok is False, returns blank/zero frames.
        """
        if not sensor_ok:
            blank_rgb = np.zeros((self.camera.height, self.camera.width, 3), dtype=np.float32)
            blank_depth = np.full((self.camera.height, self.camera.width), np.nan, dtype=np.float32)
            return blank_rgb, blank_depth
            
        x, y, th = believed_pose
        rgb, depth, _ = self.camera.render_perspective_views(
            self._terrain, rover_x_m=x, rover_y_m=y, rover_yaw_rad=th
        )
        return rgb, depth

    def get_local_observation(self, believed_pose: Tuple[float, float, float],
                              sensor_ok: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Produce visible local terrain observation strictly through camera FOV sector and range."""
        if not sensor_ok:
            blank_haz = np.zeros((self._terrain.H, self._terrain.W), dtype=np.float32)
            blank_seen = np.zeros((self._terrain.H, self._terrain.W), dtype=bool)
            blank_unc = np.ones((self._terrain.H, self._terrain.W), dtype=np.float32)
            return blank_haz, blank_seen, blank_unc
            
        x, y, th = believed_pose
        return self.camera.compute_visible_terrain(
            self._terrain, rover_x_m=x, rover_y_m=y, rover_yaw_rad=th,
            grid_size=self._terrain.H, cell_size_m=self._terrain.cell_size_m
        )


    def step_kinematics(self, v_cmd: float, k_cmd: float, dt: float) -> dict:
        """Advance simulator by one kinematic time step dt under commanded speed and curvature."""
        step_res = simulate_kinematic_step(
            self._terrain, self._true_state, v_cmd=v_cmd, k_cmd=k_cmd, dt=dt, params=self.params
        )
        self._true_state = step_res["state"]
        self._true_z = step_res["z"]
        
        # Evaluate collision against ground-truth hazard
        gx = int(round(self._true_state[0] / self._terrain.cell_size_m))
        gy = int(round(self._true_state[1] / self._terrain.cell_size_m))
        
        in_bounds = (0 <= gx < self._terrain.W) and (0 <= gy < self._terrain.H)
        collided = False
        if in_bounds:
            collided = bool(self._terrain.hazard[gy, gx])
            
        step_res["in_bounds"] = in_bounds
        step_res["collided"] = collided
        step_res["is_goal"] = bool(self._true_state[0] >= self.goal_x_m)
        return step_res

    def mutate_unobserved_cell(self, x_m: float, y_m: float, is_hazard: bool):
        """Information boundary test helper: mutates ground truth DEM hazard."""
        gx = int(round(x_m / self._terrain.cell_size_m))
        gy = int(round(y_m / self._terrain.cell_size_m))
        if 0 <= gx < self._terrain.W and 0 <= gy < self._terrain.H:
            self._terrain.hazard[gy, gx] = is_hazard
