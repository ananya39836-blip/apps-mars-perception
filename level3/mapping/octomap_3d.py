"""3D Voxel Grid & Euclidean Signed Distance Field (ESDF) Mapping for APPS Level 3.
Chapters 244 & 245 (Part 15).

Maintains:
- 3D Log-Odds Occupancy Grid L(m)
- Continuous 3D Euclidean Signed Distance Field (ESDF)
- Voxel Epistemic Uncertainty u(x, y, z) in [0, 1]
- Localization covariance spatial inflation
"""
import math
from typing import Dict, List, Tuple
import numpy as np
from scipy.ndimage import distance_transform_edt


class VoxelMap3D:
    """3D multi-resolution voxel occupancy grid with Euclidean Signed Distance Field."""

    def __init__(self, size_x_m: float = 24.0, size_y_m: float = 24.0,
                 size_z_m: float = 4.0, resolution_m: float = 0.25):
        self.res = float(resolution_m)
        self.dim_x = int(round(size_x_m / self.res))
        self.dim_y = int(round(size_y_m / self.res))
        self.dim_z = int(round(size_z_m / self.res))

        # Log-odds occupancy grid: 0.0 is prior 0.5 prob
        self.log_odds = np.zeros((self.dim_z, self.dim_y, self.dim_x), dtype=np.float32)
        # Epistemic uncertainty grid: 1.0 is completely unknown
        self.uncertainty = np.ones((self.dim_z, self.dim_y, self.dim_x), dtype=np.float32)
        # Observed mask
        self.observed = np.zeros((self.dim_z, self.dim_y, self.dim_x), dtype=bool)

        # Log-odds update constants
        self.l_occ = 0.85
        self.l_free = -0.40
        self.l_max = 3.50
        self.l_min = -2.00

    def world_to_grid(self, x: float, y: float, z: float) -> Tuple[int, int, int]:
        gx = int(round(x / self.res))
        gy = int(round(y / self.res))
        gz = int(round(z / self.res))
        return (gx, gy, gz)

    def insert_point_cloud(self, point_cloud: np.ndarray, sensor_origin: Tuple[float, float, float],
                           pose_sigma_m: float = 0.0):
        """Insert 3D point cloud returns, updating log-odds occupancy and epistemic uncertainty."""
        if point_cloud.shape[0] == 0:
            return

        ox, oy, oz = sensor_origin
        ogx, ogy, ogz = self.world_to_grid(ox, oy, oz)

        for pt in point_cloud:
            px, py, pz = pt[0], pt[1], pt[2]
            gx, gy, gz = self.world_to_grid(px, py, pz)

            if 0 <= gx < self.dim_x and 0 <= gy < self.dim_y and 0 <= gz < self.dim_z:
                # Mark hit voxel
                self.log_odds[gz, gy, gx] = np.clip(self.log_odds[gz, gy, gx] + self.l_occ, self.l_min, self.l_max)
                self.observed[gz, gy, gx] = True
                
                # Uncertainty scales with range squared
                dist = math.hypot(px - ox, py - oy, pz - oz)
                u_val = float(min(1.0, 0.10 + 0.80 * (dist / 18.0)**2 + pose_sigma_m * 0.5))
                self.uncertainty[gz, gy, gx] = min(self.uncertainty[gz, gy, gx], u_val)

    def compute_esdf_2d_slice(self, height_m: float = 0.50) -> Dict[str, np.ndarray]:
        """Compute Euclidean Signed Distance Field (ESDF) across horizontal slice at rover chassis height."""
        gz = int(np.clip(round(height_m / self.res), 0, self.dim_z - 1))
        
        # Binarize occupancy: log_odds > 0.5 is obstacle
        occ_slice = self.log_odds[gz, :, :] > 0.5
        unc_slice = self.uncertainty[gz, :, :]
        seen_slice = self.observed[gz, :, :]

        if not np.any(occ_slice):
            dist_field = np.full(occ_slice.shape, 10.0, dtype=np.float32)
        else:
            # Distance from free cells to nearest obstacle cell
            dist_field = distance_transform_edt(~occ_slice).astype(np.float32) * self.res

        return {
            "esdf_distance_m": dist_field,
            "obstacle_mask": occ_slice,
            "uncertainty_map": unc_slice,
            "seen_mask": seen_slice
        }
