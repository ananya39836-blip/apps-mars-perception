"""Cooperative Aerial Scout (Rotorcraft) Navigation Extension (Level 4 / TRL 5).

Models a simulated Mars rotorcraft (Ingenuity-class scout) performing high-altitude
forward terrain reconnaissance, transmitting regional elevation priors to the surface rover,
and handling radio communication latency and packet dropouts.
"""
from __future__ import annotations
import math
from typing import Dict, Any, Tuple, Optional
import numpy as np

from trl5_navigation.environment.planetary_terrain import PlanetaryTerrain
from trl5_navigation.perception.elevation_mapping import ElevationMap25D


class CooperativeAerialScout:
    """Simulates an aerial scout vehicle providing forward elevation corridors to the rover."""

    def __init__(
        self,
        flight_altitude_m: float = 12.0,
        sensor_fov_deg: float = 80.0,
        comm_latency_s: float = 1.0,
        packet_loss_prob: float = 0.05,
        seed: int = 42
    ) -> None:
        self.altitude = float(flight_altitude_m)
        self.fov_rad = math.radians(sensor_fov_deg)
        self.comm_latency = float(comm_latency_s)
        self.packet_loss = float(packet_loss_prob)
        self.rng = np.random.default_rng(seed)

        # Ground footprint diameter from flight altitude: D = 2 * h * tan(FOV/2)
        self.footprint_radius_m = self.altitude * math.tan(self.fov_rad / 2.0)

    def scout_corridor(
        self,
        terrain: PlanetaryTerrain,
        waypoint_start_xy: np.ndarray,
        waypoint_goal_xy: np.ndarray,
        num_scout_waypoints: int = 6
    ) -> Dict[str, Any]:
        """Flies along planned corridor and returns regional elevation map."""
        # Check simulated communication link
        if self.rng.uniform(0.0, 1.0) < self.packet_loss:
            return {
                "comm_success": False,
                "reason": "RADIO_LINK_DROPOUT",
                "scouted_map": None,
                "latency_s": self.comm_latency,
            }

        scouted_map = ElevationMap25D(
            size_x_m=terrain.size_x,
            size_y_m=terrain.size_y,
            resolution_m=terrain.res * 2.0  # Coarser resolution for aerial scout
        )

        # Sample terrain elevations along flight path
        xs = np.linspace(waypoint_start_xy[0], waypoint_goal_xy[0], num_scout_waypoints)
        ys = np.linspace(waypoint_start_xy[1], waypoint_goal_xy[1], num_scout_waypoints)

        points_observed = []
        for wx, wy in zip(xs, ys):
            # Sample ground points in circular footprint
            for r in np.linspace(0.5, self.footprint_radius_m, 12):
                for theta in np.linspace(0.0, 2 * math.pi, 16, endpoint=False):
                    px = wx + r * math.cos(theta)
                    py = wy + r * math.sin(theta)
                    if 0.0 <= px < terrain.size_x and 0.0 <= py < terrain.size_y:
                        pz = terrain.get_elevation_at(px, py)
                        # Add slight aerial sensor noise
                        pz += self.rng.normal(0.0, 0.03)
                        points_observed.append([px, py, pz])

        if points_observed:
            scouted_map.update_from_point_cloud(
                np.array(points_observed, dtype=np.float64),
                sensor_origin_world=np.array([xs[0], ys[0], self.altitude])
            )

        return {
            "comm_success": True,
            "reason": "TELEMETRY_PACKET_DELIVERED",
            "scouted_map": scouted_map,
            "num_aerial_points": len(points_observed),
            "latency_s": self.comm_latency,
            "footprint_radius_m": round(self.footprint_radius_m, 2),
        }
