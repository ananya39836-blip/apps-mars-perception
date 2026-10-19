"""Level 2 3D Terrain Representation and Directional Solar Ray-Tracing.
Continuous Digital Elevation Model (DEM), Surface Normals, and Shadow Buffering.
Chapter 71 & 210 / Part 12 Task 102.
"""
import math
import numpy as np
from scipy import ndimage as ndi


class Terrain3D:
    """Continuous 3D terrain surface backed by a dense Digital Elevation Model (DEM)."""
    
    def __init__(self, elevation: np.ndarray, cell_size_m: float = 0.25,
                 albedo_map: np.ndarray = None, hazard_map: np.ndarray = None):
        self.elevation = np.asarray(elevation, dtype=np.float32)
        self.H, self.W = self.elevation.shape
        self.cell_size_m = float(cell_size_m)
        self.x_max_m = (self.W - 1) * self.cell_size_m
        self.y_max_m = (self.H - 1) * self.cell_size_m
        
        # Default or provided albedo
        if albedo_map is not None:
            self.albedo = np.asarray(albedo_map, dtype=np.float32)
        else:
            self.albedo = np.full((self.H, self.W, 3), [0.72, 0.45, 0.28], dtype=np.float32)
            
        if hazard_map is not None:
            self.hazard = np.asarray(hazard_map, dtype=bool)
        else:
            self.hazard = np.zeros((self.H, self.W), dtype=bool)

        # Precompute gradient, normals, slope and roughness
        self._compute_surface_geometry()

    def _compute_surface_geometry(self):
        gy, gx = np.gradient(self.elevation, self.cell_size_m)
        self.grad_x = gx
        self.grad_y = gy
        self.slope_rad = np.arctan(np.hypot(gx, gy))
        self.slope_deg = np.degrees(self.slope_rad)
        
        # Surface normals
        norm = np.sqrt(gx**2 + gy**2 + 1.0)
        self.normal_x = -gx / norm
        self.normal_y = -gy / norm
        self.normal_z = 1.0 / norm
        
        # Roughness: local standard deviation in 3x3 window divided by cell size
        mean_elev = ndi.uniform_filter(self.elevation, size=3)
        sq_elev = ndi.uniform_filter(self.elevation**2, size=3)
        var_elev = np.maximum(0.0, sq_elev - mean_elev**2)
        self.roughness = np.sqrt(var_elev) / self.cell_size_m

    def get_elevation_continuous(self, x_m: float, y_m: float) -> float:
        """Bilinear continuous elevation lookup at arbitrary metric coordinates (x_m, y_m)."""
        gx = x_m / self.cell_size_m
        gy = y_m / self.cell_size_m
        
        gx = max(0.0, min(self.W - 1.001, gx))
        gy = max(0.0, min(self.H - 1.001, gy))
        
        ix, iy = int(gx), int(gy)
        fx, fy = gx - ix, gy - iy
        
        z00 = self.elevation[iy, ix]
        z10 = self.elevation[iy, ix + 1]
        z01 = self.elevation[iy + 1, ix]
        z11 = self.elevation[iy + 1, ix + 1]
        
        return float((1 - fx) * (1 - fy) * z00 + fx * (1 - fy) * z10 + (1 - fx) * fy * z01 + fx * fy * z11)

    def get_normal_continuous(self, x_m: float, y_m: float) -> tuple:
        """Bilinear continuous normal vector (nx, ny, nz) lookup."""
        gx = max(0.0, min(self.W - 1.001, x_m / self.cell_size_m))
        gy = max(0.0, min(self.H - 1.001, y_m / self.cell_size_m))
        ix, iy = int(gx), int(gy)
        fx, fy = gx - ix, gy - iy
        
        nx = (1 - fx) * (1 - fy) * self.normal_x[iy, ix] + fx * (1 - fy) * self.normal_x[iy, ix + 1] + (1 - fx) * fy * self.normal_x[iy + 1, ix] + fx * fy * self.normal_x[iy + 1, ix + 1]
        ny = (1 - fx) * (1 - fy) * self.normal_y[iy, ix] + fx * (1 - fy) * self.normal_y[iy, ix + 1] + (1 - fx) * fy * self.normal_y[iy + 1, ix] + fx * fy * self.normal_y[iy + 1, ix + 1]
        nz = (1 - fx) * (1 - fy) * self.normal_z[iy, ix] + fx * (1 - fy) * self.normal_z[iy, ix + 1] + (1 - fx) * fy * self.normal_z[iy + 1, ix] + fx * fy * self.normal_z[iy + 1, ix + 1]
        length = math.sqrt(nx**2 + ny**2 + nz**2) + 1e-9
        return (float(nx / length), float(ny / length), float(nz / length))

    def compute_solar_illumination(self, sun_azimuth_deg: float = 45.0,
                                   sun_elevation_deg: float = 35.0) -> np.ndarray:
        """Realistic directional solar rendering with ray-traced shadow buffer masking.
        Returns shaded RGB image array (H, W, 3) in [0, 1].
        """
        az = math.radians(sun_azimuth_deg)
        el = math.radians(sun_elevation_deg)
        
        # Sun unit vector in DEM frame
        sun_dir = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)], dtype=np.float32)
        
        # Direct Lambertian cosine factor
        dot_product = self.normal_x * sun_dir[0] + self.normal_y * sun_dir[1] + self.normal_z * sun_dir[2]
        lambert = np.maximum(0.0, dot_product)
        
        # Ray-marching shadow buffer
        step_len_cells = 1.0
        dx_step = math.cos(az) * step_len_cells
        dy_step = math.sin(az) * step_len_cells
        dz_step = math.tan(el) * step_len_cells * self.cell_size_m
        
        shadow_mask = np.zeros((self.H, self.W), dtype=bool)
        max_ray_steps = int(min(self.H, self.W) * 0.4)
        
        for k in range(1, max_ray_steps):
            shift_y = int(round(k * dy_step))
            shift_x = int(round(k * dx_step))
            if abs(shift_y) >= self.H or abs(shift_x) >= self.W:
                break
                
            shifted_elev = ndi.shift(self.elevation, (shift_y, shift_x), order=1, mode="nearest")
            ray_elev = self.elevation + k * dz_step
            # If obstacle along the ray is higher than the ray elevation, cell is occluded
            shadow_mask |= (shifted_elev > ray_elev + 0.05)
            
        # Composite shading
        direct_light = np.where(shadow_mask, 0.0, lambert)
        ambient_light = 0.20
        total_light = np.clip(direct_light * 0.80 + ambient_light, 0.0, 1.0)
        
        rendered_rgb = self.albedo * total_light[..., None]
        return np.clip(rendered_rgb, 0.0, 1.0).astype(np.float32)


def generate_dem_scene_3d(seed: int = 42, size: int = 96, cell_size_m: float = 0.25,
                          difficulty: str = "D1") -> Terrain3D:
    """Generate a procedural synthetic 3D continuous terrain DEM with rocky hazards and slopes."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[:size, :size]
    
    # Base rolling hills
    base_hills = ndi.gaussian_filter(rng.standard_normal((size, size)), sigma=12.0) * 1.5
    fine_undulation = ndi.gaussian_filter(rng.standard_normal((size, size)), sigma=4.0) * 0.35
    elev = base_hills + fine_undulation
    
    hazard_mask = np.zeros((size, size), dtype=bool)
    lab = np.zeros((size, size), dtype=int)
    
    # Obstacles & rocks
    n_rocks = 8 if difficulty in ("D0", "D1") else 16
    for _ in range(n_rocks):
        cy, cx = rng.integers(10, size - 10, 2)
        ry, rx = rng.uniform(2.0, 5.0, 2)
        dist_sq = ((yy - cy) / ry)**2 + ((xx - cx) / rx)**2
        mask = dist_sq < 1.0
        rock_height = rng.uniform(0.35, 1.20) * np.sqrt(np.maximum(0.0, 1.0 - dist_sq))
        elev += rock_height * mask
        hazard_mask |= (mask & (rock_height > 0.30))
        lab[mask] = 2  # Rock
        
    # Ridges & steep slope
    if difficulty in ("D2", "D3", "D5"):
        angle = rng.uniform(0, math.pi)
        d = (yy - size//2) * math.cos(angle) - (xx - size//2) * math.sin(angle)
        ridge = np.exp(-(d / 5.0)**2) * rng.uniform(1.8, 3.2)
        elev += ridge
        gy, gx = np.gradient(elev, cell_size_m)
        steep = np.hypot(gx, gy) > 0.45
        hazard_mask |= steep
        lab[steep] = 3  # Steep slope

    # Guarantee start pad is clear
    start_y = size // 2
    hazard_mask[start_y - 4:start_y + 5, 0:6] = False
    
    # Build RGB albedo
    albedo = np.zeros((size, size, 3), dtype=np.float32)
    albedo[lab == 0] = [0.65, 0.45, 0.30]  # Bedrock
    albedo[lab == 1] = [0.80, 0.58, 0.38]  # Sand
    albedo[lab == 2] = [0.42, 0.32, 0.28]  # Rock
    albedo[lab == 3] = [0.55, 0.38, 0.26]  # Steep slope
    
    return Terrain3D(elevation=elev, cell_size_m=cell_size_m, albedo_map=albedo, hazard_map=hazard_mask)
