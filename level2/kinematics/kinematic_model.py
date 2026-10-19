"""Planar Kinematic Vehicle Model with Command Clipping, Slope Slip and Attitude.
Appendix CN & Chapter 209 (Part 12 Task 101).
"""
import math
from typing import Tuple
import numpy as np
from level2.kinematics.rover_params import RoverParams


def kin_step(state: Tuple[float, float, float], v_cmd: float, k_cmd: float,
             dt: float, v_max: float = 0.50, k_max: float = 1.00) -> Tuple[Tuple[float, float, float], str, int]:
    """Execute one planar kinematic update step.
    Formula (Appendix CN):
        x_new = x + v * cos(theta) * dt
        y_new = y + v * sin(theta) * dt
        theta_new = theta + v * k * dt
    
    Returns:
        ((x_new, y_new, theta_new), status, clips)
    """
    if not all(math.isfinite(t) for t in (v_cmd, k_cmd, dt)) or dt <= 0:
        return state, "invalid_input", 0
        
    clips = 0
    v = max(-v_max, min(v_max, v_cmd))
    clips += int(v != v_cmd)
    
    k = max(-k_max, min(k_max, k_cmd))
    clips += int(k != k_cmd)
    
    x, y, th = state
    x_new = x + v * math.cos(th) * dt
    y_new = y + v * math.sin(th) * dt
    th_new = th + v * k * dt
    # Keep theta in [-pi, pi]
    th_new = (th_new + math.pi) % (2.0 * math.pi) - math.pi
    
    return (float(x_new), float(y_new), float(th_new)), "ok", int(clips)


def compute_attitude(terrain, x_m: float, y_m: float, theta_rad: float) -> Tuple[float, float]:
    """Compute vehicle pitch and roll angles in radians based on the DEM surface normal.
    Pitch: tilt about lateral axis (nose up/down).
    Roll: tilt about longitudinal axis (body roll left/right).
    """
    nx, ny, nz = terrain.get_normal_continuous(x_m, y_m)
    
    # Heading and lateral unit vectors in horizontal plane
    u_h = (math.cos(theta_rad), math.sin(theta_rad))
    v_l = (-math.sin(theta_rad), math.cos(theta_rad))
    
    # Projection of normal onto vehicle axes
    sin_pitch = -(nx * u_h[0] + ny * u_h[1])
    sin_roll = -(nx * v_l[0] + ny * v_l[1])
    
    pitch = math.asin(np.clip(sin_pitch, -1.0, 1.0))
    roll = math.asin(np.clip(sin_roll, -1.0, 1.0))
    return float(pitch), float(roll)


def compute_slope_slip(slope_rad: float, v_cmd: float, params: RoverParams) -> Tuple[float, float]:
    """Simulate wheel slip / traction loss on slopes.
    Returns:
        (slip_factor, effective_velocity)
    """
    if slope_rad <= params.max_safe_slope_rad:
        return 0.0, v_cmd
        
    excess = slope_rad - params.max_safe_slope_rad
    max_excess = params.tip_slope_rad - params.max_safe_slope_rad
    slip_factor = float(np.clip(excess / max_excess, 0.0, 1.0))
    
    # Traction degrades: effective speed drops and wheel spins
    effective_v = float(v_cmd * (1.0 - 0.70 * slip_factor))
    return slip_factor, effective_v


def simulate_kinematic_step(terrain, state: Tuple[float, float, float],
                           v_cmd: float, k_cmd: float, dt: float,
                           params: RoverParams = None) -> dict:
    """Full 3D kinodynamic vehicle update with clipping, attitude, and slope slip."""
    if params is None:
        params = RoverParams()
        
    x, y, th = state
    # Terrain elevation and normal at current pose
    z = terrain.get_elevation_continuous(x, y)
    pitch, roll = compute_attitude(terrain, x, y, th)
    slope = math.sqrt(pitch**2 + roll**2)
    
    # Check tip-over
    is_tipped = bool(slope >= params.tip_slope_rad)
    
    # Slope slip calculation
    slip_factor, eff_v = compute_slope_slip(slope, v_cmd, params)
    
    # Planar kinematics step
    new_state, status, clips = kin_step(state, eff_v, k_cmd, dt, params.v_max, params.k_max)
    
    return {
        "state": new_state,
        "x": new_state[0],
        "y": new_state[1],
        "z": z,
        "theta": new_state[2],
        "pitch_deg": math.degrees(pitch),
        "roll_deg": math.degrees(roll),
        "slope_deg": math.degrees(slope),
        "slip_factor": slip_factor,
        "is_tipped": is_tipped,
        "status": status,
        "clips": clips
    }
