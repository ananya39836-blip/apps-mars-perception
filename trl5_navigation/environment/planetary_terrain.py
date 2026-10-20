"""Representative 3D Planetary Environment Simulation (TRL 5).

Provides continuous 3D DEM elevation fields, parabolic craters with raised rims,
semi-ellipsoidal rock/boulder fields, variable regolith friction patches,
and solar ray-traced shadow occlusion buffers with deterministic PRNG reproducibility.

All units in SI (meters, radians). Frame: World Frame (W), right-handed East-North-Up.
"""
from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from trl5_navigation import G_MARS, PROTOTYPE_LOCK, NAVIGATION_READY


class PlanetaryTerrain:
    """Configurable 3D planetary digital elevation model (DEM) and hazard field."""

    def __init__(
        self,
        size_x_m: float = 60.0,
        size_y_m: float = 60.0,
        resolution_m: float = 0.20,
        base_slope_deg: float = 0.0,
        undulation_amplitude_m: float = 0.5,
        undulation_wavelength_m: float = 15.0,
        seed: int = 42
    ) -> None:
        self.size_x = float(size_x_m)
        self.size_y = float(size_y_m)
        self.res = float(resolution_m)
        self.nx = int(round(self.size_x / self.res))
        self.ny = int(round(self.size_y / self.res))
        self.base_slope_deg = float(base_slope_deg)
        self.amplitude = float(undulation_amplitude_m)
        self.wavelength = float(undulation_wavelength_m)
        self.seed = int(seed)
        self.rng = np.random.default_rng(self.seed)

        # Coordinate axes
        self.x_coords = np.linspace(0.0, self.size_x, self.nx)
        self.y_coords = np.linspace(0.0, self.size_y, self.ny)
        self.X, self.Y = np.meshgrid(self.x_coords, self.y_coords, indexing="ij")

        # Elevation grid (Z) and hazard masks
        self.elevation = np.zeros((self.nx, self.ny), dtype=np.float64)
        self.rock_mask = np.zeros((self.nx, self.ny), dtype=bool)
        self.crater_mask = np.zeros((self.nx, self.ny), dtype=bool)
        self.regolith_friction = np.ones((self.nx, self.ny), dtype=np.float64) * 0.85  # Default nominal friction mu

        # List of explicit obstacle geometries for ground-truth validation
        self.boulders: List[Dict[str, float]] = []
        self.craters: List[Dict[str, float]] = []

        self._generate_base_topography()

    def _generate_base_topography(self) -> None:
        """Constructs baseline continuous undulating topography and regional slope."""
        # Regional planar tilt
        slope_rad = math.radians(self.base_slope_deg)
        regional_tilt = self.X * math.tan(slope_rad)

        # Multi-scale harmonic undulations (Perlin-like smooth waves)
        k1 = 2.0 * math.pi / self.wavelength
        k2 = 2.0 * math.pi / (self.wavelength * 0.45)
        wave1 = self.amplitude * np.sin(k1 * self.X + 0.3) * np.cos(k1 * self.Y + 0.5)
        wave2 = (self.amplitude * 0.35) * np.sin(k2 * self.X - 0.2) * np.sin(k2 * self.Y + 0.8)

        self.elevation = regional_tilt + wave1 + wave2

    def add_crater(
        self,
        center_x: float,
        center_y: float,
        radius_m: float,
        depth_m: float,
        rim_height_m: Optional[float] = None
    ) -> None:
        """Carves a parabolic impact crater with a raised ejecta rim."""
        r = float(radius_m)
        d = float(depth_m)
        rim_h = float(rim_height_m) if rim_height_m is not None else d * 0.25
        cx, cy = float(center_x), float(center_y)

        self.craters.append({"x": cx, "y": cy, "radius": r, "depth": d, "rim_h": rim_h})

        dist_sq = (self.X - cx)**2 + (self.Y - cy)**2
        dist = np.sqrt(dist_sq)

        # Inside crater bowl: parabolic depression
        in_bowl = dist <= r
        bowl_profile = -d * (1.0 - (dist[in_bowl] / r)**2)
        self.elevation[in_bowl] += bowl_profile
        self.crater_mask[in_bowl] = True

        # Raised rim and ejecta blanket: exponential decay outside rim
        rim_zone = (dist > r) & (dist <= r * 2.5)
        dr = dist[rim_zone] - r
        rim_profile = rim_h * np.exp(-2.5 * dr / r)
        self.elevation[rim_zone] += rim_profile

    def add_boulder(
        self,
        center_x: float,
        center_y: float,
        radius_m: float,
        height_m: float
    ) -> None:
        """Injects a semi-ellipsoidal rock / boulder obstacle."""
        r = float(radius_m)
        h = float(height_m)
        cx, cy = float(center_x), float(center_y)

        self.boulders.append({"x": cx, "y": cy, "radius": r, "height": h})

        dist_sq = (self.X - cx)**2 + (self.Y - cy)**2
        mask = dist_sq <= r**2

        rock_height = h * np.sqrt(np.maximum(0.0, 1.0 - dist_sq[mask] / (r**2)))
        self.elevation[mask] += rock_height
        self.rock_mask[mask] = True

    def populate_rock_field(
        self,
        num_rocks: int = 40,
        min_radius_m: float = 0.20,
        max_radius_m: float = 1.20,
        min_height_m: float = 0.15,
        max_height_m: float = 0.80,
        margin_m: float = 3.0
    ) -> None:
        """Populates a field of randomly distributed boulders with clear staging zones around start and goal."""
        for _ in range(num_rocks):
            for _attempt in range(50):
                rx = self.rng.uniform(margin_m, self.size_x - margin_m)
                ry = self.rng.uniform(margin_m, self.size_y - margin_m)
                # Keep clear staging zone around rover start (4, 4) and mission goal (25, 25)
                if math.hypot(rx - 4.0, ry - 4.0) < 4.5 or math.hypot(rx - 25.0, ry - 25.0) < 3.0:
                    continue
                break

            # Power law: small rocks are much more common than large boulders
            u = self.rng.uniform(0.0, 1.0)
            radius = min_radius_m + (max_radius_m - min_radius_m) * (u**2.2)
            height = min_height_m + (max_height_m - min_height_m) * (radius / max_radius_m)
            self.add_boulder(rx, ry, radius, height)

    def add_loose_regolith_patch(
        self,
        center_x: float,
        center_y: float,
        radius_m: float,
        friction_coeff: float = 0.35
    ) -> None:
        """Injects a low-cohesion loose sand patch with reduced friction/traction."""
        cx, cy, r = float(center_x), float(center_y), float(radius_m)
        dist_sq = (self.X - cx)**2 + (self.Y - cy)**2
        mask = dist_sq <= r**2
        self.regolith_friction[mask] = float(friction_coeff)

    def get_elevation_at(self, x: float, y: float) -> float:
        """Continuous bilinear interpolation of terrain elevation z = h(x, y)."""
        x_clamped = min(max(float(x), 0.0), self.size_x - 1e-4)
        y_clamped = min(max(float(y), 0.0), self.size_y - 1e-4)

        gx = x_clamped / self.res
        gy = y_clamped / self.res

        ix = int(math.floor(gx))
        iy = int(math.floor(gy))

        ix = min(ix, self.nx - 2)
        iy = min(iy, self.ny - 2)

        tx = gx - ix
        ty = gy - iy

        z00 = self.elevation[ix, iy]
        z10 = self.elevation[ix + 1, iy]
        z01 = self.elevation[ix, iy + 1]
        z11 = self.elevation[ix + 1, iy + 1]

        z0 = z00 * (1.0 - tx) + z10 * tx
        z1 = z01 * (1.0 - tx) + z11 * tx
        return float(z0 * (1.0 - ty) + z1 * ty)

    def get_surface_normal_and_slope(self, x: float, y: float, delta_m: float = 0.20) -> Tuple[np.ndarray, float]:
        """Calculates analytic surface normal vector n and terrain slope angle theta in radians."""
        d = float(delta_m)
        z_e = self.get_elevation_at(x + d, y)
        z_w = self.get_elevation_at(x - d, y)
        z_n = self.get_elevation_at(x, y + d)
        z_s = self.get_elevation_at(x, y - d)

        dz_dx = (z_e - z_w) / (2.0 * d)
        dz_dy = (z_n - z_s) / (2.0 * d)

        normal = np.array([-dz_dx, -dz_dy, 1.0], dtype=np.float64)
        normal /= np.linalg.norm(normal)

        # Slope is angle between surface normal and vertical Z axis [0, 0, 1]
        slope_rad = math.acos(np.clip(normal[2], -1.0, 1.0))
        return normal, float(slope_rad)

    def compute_solar_shadow_mask(self, sun_azimuth_deg: float = 45.0, sun_elevation_deg: float = 30.0) -> np.ndarray:
        """Ray-casts directional solar illumination to produce discrete shadow buffer."""
        az_rad = math.radians(sun_azimuth_deg)
        el_rad = math.radians(sun_elevation_deg)

        # Sun ray direction vector (pointing FROM terrain towards sun)
        ray_dx = math.cos(el_rad) * math.sin(az_rad)
        ray_dy = math.cos(el_rad) * math.cos(az_rad)
        ray_dz = math.sin(el_rad)

        shadow_mask = np.zeros((self.nx, self.ny), dtype=bool)
        step_len_m = self.res * 0.75
        max_dist_m = 25.0
        num_steps = int(max_dist_m / step_len_m)

        for step in range(1, num_steps + 1):
            sample_x = self.X + (step * step_len_m * ray_dx)
            sample_y = self.Y + (step * step_len_m * ray_dy)
            ray_z = self.elevation + (step * step_len_m * ray_dz)

            valid = (sample_x >= 0.0) & (sample_x < self.size_x) & (sample_y >= 0.0) & (sample_y < self.size_y)
            if not np.any(valid):
                break

            ix = np.clip((sample_x[valid] / self.res).astype(int), 0, self.nx - 1)
            iy = np.clip((sample_y[valid] / self.res).astype(int), 0, self.ny - 1)
            terrain_z = self.elevation[ix, iy]

            occluded = terrain_z > ray_z[valid]
            # Map back to full grid
            full_occluded = np.zeros_like(shadow_mask)
            full_occluded[valid] = occluded
            shadow_mask |= full_occluded

        return shadow_mask
