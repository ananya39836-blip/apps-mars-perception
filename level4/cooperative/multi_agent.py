"""Heterogeneous Cooperative Autonomy: Aerial Scout & Rover Multi-Agent Coordination.
Level 4: Part 21 (Chapters 300 to 309).

Implements heterogeneous multi-agent autonomy:
1. Aerial Scout (Mars Rotorcraft) Trajectory & Scouting Executive.
2. Scout-to-Rover Elevation Map Downlinking & Fusion.
3. Autonomous Safe Landing Site Certification (Slope, Roughness, Obstacle Clearance).
4. Direct Line-of-Sight RF Communications Margin Modeling.
"""
import math
from typing import Dict, List, Tuple
import numpy as np


class AerialScoutMission:
    """Represents an autonomous aerial scout sortie ahead of the ground rover."""
    def __init__(self, scout_id: str = "Ingenuity-L4", max_flight_range_m: float = 350.0):
        self.scout_id = scout_id
        self.max_flight_range_m = max_flight_range_m
        self.flight_speed_mps = 3.5
        self.altitude_agl_m = 10.0 # Above Ground Level

    def plan_scout_sortie(
        self, rover_pos: Tuple[float, float], strategic_goal: Tuple[float, float]
    ) -> Dict:
        """Plans a forward scouting sortie along strategic heading to map rover blind zones."""
        dx = strategic_goal[0] - rover_pos[0]
        dy = strategic_goal[1] - rover_pos[1]
        dist_to_goal = math.hypot(dx, dy)
        
        # Flight distance limited by max flight range
        flight_dist = min(self.max_flight_range_m, dist_to_goal * 0.8)
        heading = math.atan2(dy, dx)
        
        scout_target_x = rover_pos[0] + flight_dist * math.cos(heading)
        scout_target_y = rover_pos[1] + flight_dist * math.sin(heading)
        
        flight_duration_s = (flight_dist * 2.0) / self.flight_speed_mps + 30.0 # out-and-back + hover
        
        waypoints = [
            {'step': 'TAKEOFF', 'pos': (rover_pos[0], rover_pos[1], self.altitude_agl_m)},
            {'step': 'MID_SURVEY', 'pos': (rover_pos[0] + 0.5 * flight_dist * math.cos(heading), rover_pos[1] + 0.5 * flight_dist * math.sin(heading), self.altitude_agl_m)},
            {'step': 'APEX_SURVEY', 'pos': (scout_target_x, scout_target_y, self.altitude_agl_m)},
            {'step': 'RETURN_HOVER', 'pos': (rover_pos[0], rover_pos[1], self.altitude_agl_m)},
            {'step': 'LANDING', 'pos': (rover_pos[0] + 5.0, rover_pos[1] + 5.0, 0.0)}
        ]
        
        return {
            'scout_id': self.scout_id,
            'flight_distance_m': float(flight_dist),
            'flight_duration_s': float(flight_duration_s),
            'survey_target_pos': (float(scout_target_x), float(scout_target_y)),
            'waypoints': waypoints,
            'mapping_footprint_m2': float(flight_dist * 25.0) # 25m swath width
        }


class LandingSiteCertifier:
    """Certifies autonomous landing zones for the aerial scout rotorcraft."""
    def __init__(self, max_allowable_slope_deg: float = 8.0, max_rock_height_m: float = 0.12):
        self.max_slope_deg = max_allowable_slope_deg
        self.max_rock_height_m = max_rock_height_m

    def certify_candidate_landing_zone(
        self,
        center_xy: Tuple[float, float],
        local_slopes_deg: List[float],
        detected_obstacle_heights_m: List[float]
    ) -> Dict:
        """Evaluates whether a 5m x 5m candidate landing zone is safe for touchdown."""
        mean_slope = float(np.mean(local_slopes_deg)) if local_slopes_deg else 0.0
        max_slope = float(np.max(local_slopes_deg)) if local_slopes_deg else 0.0
        max_rock = float(np.max(detected_obstacle_heights_m)) if detected_obstacle_heights_m else 0.0
        
        slope_safe = max_slope <= self.max_slope_deg
        rock_safe = max_rock <= self.max_rock_height_m
        is_certified = slope_safe and rock_safe
        
        # Safety margin metric [0, 1]
        slope_margin = max(0.0, 1.0 - (max_slope / self.max_slope_deg))
        rock_margin = max(0.0, 1.0 - (max_rock / self.max_rock_height_m))
        safety_score = 0.5 * slope_margin + 0.5 * rock_margin if is_certified else 0.0
        
        return {
            'landing_center': center_xy,
            'mean_slope_deg': round(mean_slope, 2),
            'max_slope_deg': round(max_slope, 2),
            'max_rock_height_m': round(max_rock, 3),
            'slope_safe': slope_safe,
            'rock_safe': rock_safe,
            'is_certified_for_landing': is_certified,
            'safety_score': round(safety_score, 4)
        }


class MultiAgentCommunicationsLink:
    """Models UHF/ZigBee radio link between ground rover and aerial scout."""
    def __init__(self, tx_power_dbm: float = 20.0, frequency_mhz: float = 900.0):
        self.tx_power_dbm = tx_power_dbm
        self.frequency_mhz = frequency_mhz

    def evaluate_rf_link(self, distance_m: float, line_of_sight_occluded: bool = False) -> Dict:
        """Calculates free-space path loss and RF link margin."""
        # Free-space path loss: FSPL = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        d_km = max(0.001, distance_m / 1000.0)
        fspl_db = 20.0 * math.log10(d_km) + 20.0 * math.log10(self.frequency_mhz) + 32.44
        
        extra_attenuation_db = 25.0 if line_of_sight_occluded else 0.0
        rx_power_dbm = self.tx_power_dbm - fspl_db - extra_attenuation_db
        
        receiver_sensitivity_dbm = -105.0 # Low-SWaP radio receiver threshold
        link_margin_db = rx_power_dbm - receiver_sensitivity_dbm
        is_link_established = link_margin_db >= 6.0 # 6 dB NASA flight margin
        
        # Max data downlink throughput
        throughput_kbps = 250.0 if link_margin_db > 12.0 else (50.0 if is_link_established else 0.0)

        return {
            'distance_m': round(distance_m, 1),
            'fspl_db': round(fspl_db, 2),
            'rx_power_dbm': round(rx_power_dbm, 2),
            'link_margin_db': round(link_margin_db, 2),
            'is_link_established': is_link_established,
            'throughput_kbps': throughput_kbps
        }
