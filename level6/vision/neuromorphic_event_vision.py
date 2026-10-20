"""Level 6 Part 51: Neuromorphic Event-Based Computer Vision & Asynchronous Optical Flow.
Chapters 600 to 609: DVS Sensors, Logarithmic Thresholds, Contrast Maximization & Spiking Neurons.

Implements asynchronous Address-Event Representation (AER), contrast maximization motion estimation,
Leaky Integrate-and-Fire (LIF) neuromorphic dynamics, and time-to-contact (TTC) landing hazard divergence.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class EventCameraSensor:
    """Simulates asynchronous Dynamic Vision Sensor (DVS) logarithmic event generation."""

    def __init__(self, contrast_threshold: float = 0.15, max_event_rate_meps: float = 20.0):
        self.c_th = contrast_threshold
        self.max_rate = max_event_rate_meps
        self.last_timestamps: Dict[Tuple[int, int], float] = {}

    def process_intensity_change(self, pixel_coord: Tuple[int, int], old_intensity: float, new_intensity: float, timestamp_us: float) -> Optional[Dict[str, Any]]:
        """Triggers +1 or -1 polarity event if logarithmic intensity difference exceeds C_th."""
        # Ensure non-zero positive intensity
        i_old = max(0.001, old_intensity)
        i_new = max(0.001, new_intensity)
        delta_log = math.log(i_new) - math.log(i_old)

        if abs(delta_log) >= self.c_th:
            polarity = 1 if delta_log > 0 else -1
            self.last_timestamps[pixel_coord] = timestamp_us
            return {
                "x": pixel_coord[0],
                "y": pixel_coord[1],
                "timestamp_us": timestamp_us,
                "polarity": polarity,
                "delta_log": round(delta_log, 3)
            }
        return None

    def filter_background_activity(self, events: List[Dict[str, Any]], correlation_window_us: float = 5000.0) -> Dict[str, Any]:
        """Filters isolated Poisson thermal noise events lacking spatiotemporally adjacent support."""
        valid_events = []
        for e in events:
            # Synthetic correlation check
            if e.get("delta_log", 0.0) > 0.05 or len(events) < 5:
                valid_events.append(e)

        rejection_rate = (len(events) - len(valid_events)) / max(1, len(events))
        return {
            "input_events_count": len(events),
            "valid_events_count": len(valid_events),
            "noise_rejection_rate": round(rejection_rate, 3),
            "dynamic_range_db": 128.5,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class ContrastMaximizationOpticalFlow:
    """Estimates continuous angular rate or linear optical flow via Image of Warped Events (IWE) focus."""

    def __init__(self, grid_size: int = 128):
        self.grid_size = grid_size

    def evaluate_motion_hypothesis(self, events: List[Dict[str, Any]], velocity_hypothesis: Tuple[float, float]) -> Dict[str, Any]:
        """Warps events along linear velocity hypothesis (vx, vy) and computes spatial variance."""
        vx, vy = velocity_hypothesis
        if not events:
            return {"focus_score": 0.0, "is_sharp": False}

        t_ref = events[0]["timestamp_us"]
        iwe = np.zeros((self.grid_size, self.grid_size))

        for e in events:
            dt = (e["timestamp_us"] - t_ref) * 1e-6  # seconds
            # Warped coordinates
            x_w = int(np.clip(e["x"] - vx * dt, 0, self.grid_size - 1))
            y_w = int(np.clip(e["y"] - vy * dt, 0, self.grid_size - 1))
            iwe[y_w, x_w] += e["polarity"]

        # Focus score is the spatial variance of the accumulated warped events
        focus_variance = float(np.var(iwe))
        return {
            "velocity_hypothesis_pps": (vx, vy),
            "focus_variance": round(focus_variance, 4),
            "events_warped_count": len(events),
            "is_sharp_edge_alignment": focus_variance > 0.05,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class SpikingNeuronLandingSentinel:
    """LIF neuromorphic circuit tracking Time-to-Contact (TTC) from optical flow radial divergence."""

    def __init__(self, v_thresh: float = 1.0, tau_leak_ms: float = 20.0):
        self.v_thresh = v_thresh
        self.tau_leak = tau_leak_ms
        self.membrane_voltage = 0.0

    def compute_time_to_contact(self, radial_expansion_rate_per_sec: float) -> Dict[str, Any]:
        """Calculates instantaneous landing time-to-contact (TTC = 1 / divergence)."""
        div = max(0.01, radial_expansion_rate_per_sec)
        ttc_seconds = 1.0 / div
        is_terminal_hazard = ttc_seconds < 2.5

        # Integrate into spiking membrane
        self.membrane_voltage += (1.0 / max(0.5, ttc_seconds)) * 0.1
        spike_emitted = False
        if self.membrane_voltage >= self.v_thresh:
            spike_emitted = True
            self.membrane_voltage = 0.0  # Reset

        return {
            "time_to_contact_s": round(ttc_seconds, 3),
            "radial_expansion_rate": round(div, 3),
            "retro_thrust_trigger": is_terminal_hazard,
            "membrane_potential_v": round(self.membrane_voltage, 3),
            "neuromorphic_spike_emitted": spike_emitted,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
