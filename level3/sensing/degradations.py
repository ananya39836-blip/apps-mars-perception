"""Environmental Degradations & Negative Obstacle Sentinel for APPS Level 3.
Chapters 231, 232 & 237 (Part 14).

Simulates:
- Martian atmospheric dust storm extinction (optical depth tau_dust)
- Solar flare veiling glare and blooming
- Negative obstacle detection (drop-offs, craters, fissures)
"""
import math
from typing import Dict, List, Tuple
import numpy as np


def apply_atmospheric_dust_extinction(rgb_image: np.ndarray, optical_depth_tau: float = 0.45,
                                      dust_color: Tuple[float, float, float] = (0.75, 0.52, 0.32)) -> np.ndarray:
    """Attenuate image contrast and apply forward atmospheric dust scattering via Beer-Lambert law.
    I_obs = I_true * exp(-tau) + I_ambient * (1 - exp(-tau))
    """
    tau = max(0.0, float(optical_depth_tau))
    transmittance = math.exp(-tau)
    ambient_scatter = 1.0 - transmittance

    dust_arr = np.array(dust_color, dtype=np.float32)
    degraded = rgb_image * transmittance + dust_arr * ambient_scatter
    return np.clip(degraded, 0.0, 1.0)


def apply_solar_glare_blooming(rgb_image: np.ndarray, sun_in_fov: bool,
                               sun_pixel: Tuple[int, int],
                               glare_intensity: float = 0.65) -> np.ndarray:
    """Simulate lens veiling glare and CCD sensor blooming when the sun enters the camera FOV."""
    if not sun_in_fov:
        return rgb_image

    H, W, _ = rgb_image.shape
    u0, v0 = sun_pixel
    yy, xx = np.mgrid[:H, :W]
    dist_sq = (xx - u0)**2 + (yy - v0)**2
    sigma_glare = max(10.0, W * 0.25)
    glare_mask = glare_intensity * np.exp(-dist_sq / (2.0 * sigma_glare**2))

    glare_rgb = np.dstack([glare_mask] * 3)
    bloomed = np.clip(rgb_image + glare_rgb, 0.0, 1.0)
    return bloomed


class NegativeObstacleSentinel:
    """Detects geometric negative obstacles (craters, cliffs, step drop-offs) occluded from low perspective cameras."""

    def __init__(self, drop_threshold_m: float = 0.20, min_gap_length_m: float = 0.35,
                 cell_size_m: float = 0.25):
        self.drop_thresh = float(drop_threshold_m)
        self.min_gap_len = float(min_gap_length_m)
        self.cell_size = float(cell_size_m)

    def audit_radial_profiles(self, dem_elevation: np.ndarray,
                              rover_x_m: float, rover_y_m: float,
                              rover_yaw_rad: float, max_radius_m: float = 12.0,
                              n_rays: int = 36) -> Dict:
        """Scan radial lines of sight outward from rover to identify missing surface returns and negative drops."""
        H, W = dem_elevation.shape
        curr_gx = int(round(rover_x_m / self.cell_size))
        curr_gy = int(round(rover_y_m / self.cell_size))

        if not (0 <= curr_gx < W and 0 <= curr_gy < H):
            return {"negative_obstacles_found": 0, "hazard_mask": np.zeros((H, W), dtype=bool)}

        rover_z = dem_elevation[curr_gy, curr_gx]
        neg_hazard_mask = np.zeros((H, W), dtype=bool)
        n_detected = 0

        angles = np.linspace(rover_yaw_rad - math.pi / 3.0, rover_yaw_rad + math.pi / 3.0, n_rays)
        dist_steps = np.arange(self.cell_size * 2, max_radius_m, self.cell_size)

        for ang in angles:
            cos_a = math.cos(ang)
            sin_a = math.sin(ang)
            prev_z = rover_z

            for d in dist_steps:
                px = rover_x_m + cos_a * d
                py = rover_y_m + sin_a * d
                gx = int(round(px / self.cell_size))
                gy = int(round(py / self.cell_size))

                if 0 <= gx < W and 0 <= gy < H:
                    cur_z = dem_elevation[gy, gx]
                    step_drop = prev_z - cur_z

                    # Sudden downward drop exceeds threshold -> Negative Obstacle!
                    if step_drop >= self.drop_thresh:
                        neg_hazard_mask[gy, gx] = True
                        n_detected += 1
                    prev_z = cur_z

        return {
            "negative_obstacles_found": n_detected,
            "hazard_mask": neg_hazard_mask
        }

    def inspect_scan(self, step_drop_m: float) -> Dict:
        """Inspect a single obstacle drop measurement against threshold."""
        val = float(step_drop_m)
        is_hazard = (val >= self.drop_thresh)
        return {
            "negative_hazard_detected": is_hazard,
            "step_drop_m": val,
            "threshold_m": self.drop_thresh
        }


class EnvironmentalDegradationModel:
    """Atmospheric dust optical depth extinction and solar flare glare simulator."""

    def __init__(self):
        pass

    def apply_degradations(self, tau_dust: float = 0.80, sun_angle_deg: float = 25.0,
                           true_intensity: float = 1.0) -> Dict[str, float]:
        """Compute optical transmission factor, veiling glare ratio, and effective SNR."""
        tau = max(0.0, float(tau_dust))
        transmission = float(math.exp(-tau))
        
        # Glare ratio increases as sun angle approaches boresight (0 deg)
        ang_rad = math.radians(max(0.0, float(sun_angle_deg)))
        glare_ratio = float(max(0.0, min(1.0, math.exp(-ang_rad**2 / (2.0 * 0.40**2)) * 0.85)))
        
        # Noise floor combines ambient dust scatter and lens glare
        noise_floor = 0.02 + 0.15 * (1.0 - transmission) + 0.35 * glare_ratio
        signal = float(true_intensity) * transmission
        snr_db = float(10.0 * math.log10(max(1e-4, signal / max(1e-4, noise_floor))))

        return {
            "optical_transmission": transmission,
            "solar_glare_ratio": glare_ratio,
            "effective_snr_db": snr_db
        }
