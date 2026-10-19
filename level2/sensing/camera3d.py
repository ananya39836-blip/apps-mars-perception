"""Level 2 Synthetic Perspective Camera Model and 3D Depth Reprojection.
Chapters 71.3, 92, 196 (Part 11 Task 97 & Part 12 Task 102).
"""
import math
from typing import Tuple
import numpy as np


class Camera3D:
    """Forward-facing perspective camera with intrinsic and extrinsic projection."""
    
    def __init__(self, width: int = 64, height: int = 64,
                 fov_deg: float = 90.0, mount_height_m: float = 1.0,
                 pitch_down_deg: float = 15.0, baseline_m: float = 0.20,
                 z_min: float = 0.4, z_max: float = 16.0):
        self.width = width
        self.height = height
        self.fov_deg = fov_deg
        self.mount_height = float(mount_height_m)
        self.pitch_down_rad = math.radians(pitch_down_deg)
        self.baseline_m = float(baseline_m)
        self.z_min = float(z_min)
        self.z_max = float(z_max)
        
        # Intrinsics
        fov_rad = math.radians(fov_deg)
        self.fx = (width / 2.0) / math.tan(fov_rad / 2.0)
        self.fy = self.fx
        self.cx = width / 2.0
        self.cy = height / 2.0
        self.K = np.array([
            [self.fx, 0.0, self.cx],
            [0.0, self.fy, self.cy],
            [0.0, 0.0, 1.0]
        ], dtype=np.float32)

    def render_perspective_views(self, terrain, rover_x_m: float, rover_y_m: float,
                                 rover_yaw_rad: float, sun_azimuth_deg: float = 45.0,
                                 sun_elevation_deg: float = 35.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Render perspective RGB image and Depth map from rover 3D pose."""
        rover_z_m = terrain.get_elevation_continuous(rover_x_m, rover_y_m)
        cam_x = rover_x_m
        cam_y = rover_y_m
        cam_z = rover_z_m + self.mount_height
        
        rgb_buf = np.zeros((self.height, self.width, 3), dtype=np.float32)
        depth_buf = np.full((self.height, self.width), np.nan, dtype=np.float32)
        haz_buf = np.zeros((self.height, self.width), dtype=bool)
        
        shaded_dem = terrain.compute_solar_illumination(sun_azimuth_deg, sun_elevation_deg)
        
        # Ray-march through camera pixels
        pitch = -self.pitch_down_rad
        yaw = rover_yaw_rad
        
        # Precompute ray directions in world frame
        u_coords = np.linspace(0, self.width - 1, self.width)
        v_coords = np.linspace(0, self.height - 1, self.height)
        uu, vv = np.meshgrid(u_coords, v_coords)
        
        # Pinhole ray in camera optical frame (Z forward, X right, Y down)
        ray_x_c = (uu - self.cx) / self.fx
        ray_y_c = (vv - self.cy) / self.fy
        ray_z_c = np.ones_like(ray_x_c)
        norms = np.sqrt(ray_x_c**2 + ray_y_c**2 + 1.0)
        
        # Ray direction in rover frame
        # Optical to vehicle frame: x_v = z_c, y_v = -x_c, z_v = -y_c
        ray_fwd = ray_z_c / norms
        ray_lat = -ray_x_c / norms
        ray_vert = -ray_y_c / norms
        
        # Apply pitch tilt
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        ray_x_veh = ray_fwd * cos_p - ray_vert * sin_p
        ray_z_veh = ray_fwd * sin_p + ray_vert * cos_p
        ray_y_veh = ray_lat
        
        # Apply yaw to world frame
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        ray_x_w = ray_x_veh * cos_y - ray_y_veh * sin_y
        ray_y_w = ray_x_veh * sin_y + ray_y_veh * cos_y
        ray_z_w = ray_z_veh
        
        # Intersect rays with continuous DEM surface using step sampling
        dist_steps = np.linspace(self.z_min, self.z_max, 24)
        for d in dist_steps:
            px = cam_x + ray_x_w * d
            py = cam_y + ray_y_w * d
            pz = cam_z + ray_z_w * d
            
            gx = (px / terrain.cell_size_m).astype(int)
            gy = (py / terrain.cell_size_m).astype(int)
            
            in_bounds = (gx >= 0) & (gx < terrain.W) & (gy >= 0) & (gy < terrain.H)
            active = in_bounds & np.isnan(depth_buf)
            
            if np.any(active):
                dem_z = terrain.elevation[gy[active], gx[active]]
                hit = pz[active] <= dem_z
                if np.any(hit):
                    hit_mask = np.zeros_like(depth_buf, dtype=bool)
                    hit_mask[active] = hit
                    depth_buf[hit_mask] = d
                    rgb_buf[hit_mask] = shaded_dem[gy[hit_mask], gx[hit_mask]]
                    haz_buf[hit_mask] = terrain.hazard[gy[hit_mask], gx[hit_mask]]

        sky_mask = np.isnan(depth_buf)
        rgb_buf[sky_mask] = [0.82, 0.65, 0.45]
        return rgb_buf, depth_buf, haz_buf

    def compute_visible_terrain(self, terrain, rover_x_m: float, rover_y_m: float,
                                rover_yaw_rad: float, grid_size: int = 96,
                                cell_size_m: float = 0.25) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculates dense observed field of view and inverse depth uncertainty map on local 2.5D DEM.
        Returns:
            (believed_hazard, observed_mask, uncertainty_map)
        """
        yy, xx = np.mgrid[:grid_size, :grid_size]
        cell_x_m = xx * cell_size_m
        cell_y_m = yy * cell_size_m
        
        dx = cell_x_m - rover_x_m
        dy = cell_y_m - rover_y_m
        d = np.hypot(dx, dy)
        ang = np.arctan2(dy, dx)
        heading_diff = np.abs((ang - rover_yaw_rad + math.pi) % (2 * math.pi) - math.pi)
        
        half_fov = math.radians(self.fov_deg) / 2.0
        in_sector = (d <= self.z_max) & (heading_diff <= half_fov)
        
        # Vehicle body footprint is always observed and free
        body_radius_cells = 6
        curr_gx = int(round(rover_x_m / cell_size_m))
        curr_gy = int(round(rover_y_m / cell_size_m))
        dist_body = np.hypot(xx - curr_gx, yy - curr_gy)
        at_body = dist_body <= body_radius_cells
        
        seen_mask = in_sector | at_body
        
        # Error and uncertainty grow with the square of range (Chapter 196.2 / Appendix CK)
        # Z = f*B/d, delta_Z ~ Z^2 * delta_d / (f*B)
        rel_range = np.clip(d / self.z_max, 0.0, 1.0)
        uncertainty = np.where(seen_mask, 0.10 + 0.85 * (rel_range**2), 1.0).astype(np.float32)
        uncertainty[at_body] = 0.10
        
        # Hazard projection
        believed_haz = np.zeros((grid_size, grid_size), dtype=np.float32)
        believed_haz[seen_mask & terrain.hazard] = 0.90
        believed_haz[at_body] = 0.0
        
        return believed_haz, seen_mask, uncertainty

    def reproject_to_local_grid(self, depth_map: np.ndarray, hazard_pred: np.ndarray,
                                rover_x_m: float, rover_y_m: float, rover_yaw_rad: float,
                                rover_z_m: float = 0.0, grid_size: int = 96,
                                cell_size_m: float = 0.25) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Reprojects depth & hazard predictions back to vehicle/world local grid."""
        yy, xx = np.mgrid[:grid_size, :grid_size]
        cell_x_m = xx * cell_size_m
        cell_y_m = yy * cell_size_m
        dx = cell_x_m - rover_x_m
        dy = cell_y_m - rover_y_m
        d = np.hypot(dx, dy)
        ang = np.arctan2(dy, dx)
        heading_diff = np.abs((ang - rover_yaw_rad + math.pi) % (2 * math.pi) - math.pi)
        half_fov = math.radians(self.fov_deg) / 2.0
        in_sector = (d <= self.z_max) & (heading_diff <= half_fov)

        body_radius_cells = 6
        curr_gx = int(round(rover_x_m / cell_size_m))
        curr_gy = int(round(rover_y_m / cell_size_m))
        dist_body = np.hypot(xx - curr_gx, yy - curr_gy)
        at_body = dist_body <= body_radius_cells

        seen_mask = in_sector | at_body
        rel_range = np.clip(d / self.z_max, 0.0, 1.0)
        uncertainty = np.where(seen_mask, 0.10 + 0.85 * (rel_range**2), 1.0).astype(np.float32)
        uncertainty[at_body] = 0.10

        believed_haz = np.zeros((grid_size, grid_size), dtype=np.float32)
        if hazard_pred is not None and np.any(hazard_pred > 0.3):
            believed_haz[in_sector] = float(np.mean(hazard_pred[hazard_pred > 0.3]))
        believed_haz[at_body] = 0.0

        return believed_haz, seen_mask, uncertainty


def depth_from_disparity(d: np.ndarray, f_px: float, baseline_m: float,
                         z_min: float = 0.4, z_max: float = 20.0) -> np.ndarray:
    """Stereo depth calculation (Appendix CK / Part 11 Task 97).
    Formula: Z = f * B / d.
    Disparities near zero or negative are marked NaN.
    """
    d_arr = np.asarray(d, dtype=float)
    z = np.full(d_arr.shape, np.nan, dtype=np.float32)
    valid = np.isfinite(d_arr) & (d_arr > 0.0)
    z[valid] = (f_px * baseline_m) / d_arr[valid]
    z[(z < z_min) | (z > z_max)] = np.nan
    return z
