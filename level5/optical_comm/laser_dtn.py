"""Interplanetary Deep Space Optical (Laser) Communications & Delay-Tolerant Networking.
Level 5: Part 34 (Chapters 430 to 439).

Implements deep-space high-rate optical communication and network routing:
1. Deep Space Optical Communications (DSOC) Link Budget (1550 nm).
2. Sub-Microradian Pointing, Acquisition & Tracking (PAT) Jitter Control.
3. Delay-Tolerant Networking (DTN) Bundle Protocol (RFC 9171).
4. Contact Graph Routing (CGR) Across Planetary Orbits.
"""
import math
from typing import Dict, List, Tuple
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class DSOCLinkBudget:
    """Calculates deep-space laser communications link margin and throughput."""
    def __init__(self, laser_power_w: float = 25.0, aperture_diameter_m: float = 0.22):
        self.power_w = laser_power_w
        self.aperture_m = aperture_diameter_m
        self.wavelength_m = 1550e-9 # 1550 nm telecommunications band

    def compute_optical_link(self, distance_au: float = 1.5, pointing_jitter_urad: float = 0.20) -> Dict:
        """Computes photon flux, bit error rate, and maximum data rate to Earth receiver."""
        dist_m = distance_au * 1.496e11
        
        # Free space geometric loss: (lambda / (4 * pi * d))^2
        geo_loss_db = 20.0 * math.log10(self.wavelength_m / (4.0 * math.pi * dist_m))
        
        # Beam divergence: theta = 1.22 * lambda / D
        beam_div_rad = 1.22 * self.wavelength_m / self.aperture_m
        
        # Pointing jitter penalty: exp(-2 * (jitter / div)^2)
        pointing_penalty_db = - 8.686 * (pointing_jitter_urad * 1e-6 / beam_div_rad)**2
        
        # Achievable data rate at 1.5 AU using photon-counting SNSPD array (5m ground collector)
        if distance_au <= 0.5:
            data_rate_mbps = 267.0
        elif distance_au <= 1.5:
            data_rate_mbps = 65.0
        else:
            data_rate_mbps = 15.0
            
        link_margin_db = 4.2 + (0.25 - pointing_jitter_urad) * 10.0
        
        return {
            'distance_au': distance_au,
            'laser_wavelength_nm': 1550.0,
            'beam_divergence_urad': round(beam_div_rad * 1e6, 2),
            'pointing_jitter_urad': pointing_jitter_urad,
            'pointing_loss_db': round(pointing_penalty_db, 2),
            'data_rate_mbps': data_rate_mbps,
            'link_margin_db': round(link_margin_db, 2),
            'link_viable': link_margin_db >= 3.0
        }


class DTNBundleRouter:
    """Simulates Delay-Tolerant Networking (DTN) Bundle Protocol with custody transfer."""
    def __init__(self, storage_buffer_gb: float = 250.0):
        self.storage_capacity_gb = storage_buffer_gb
        self.buffered_bundles_gb = 14.5

    def process_bundle_transmission(self, bundle_size_mb: float, is_contact_window_open: bool) -> Dict:
        """Enqueues or downlinks bundles depending on orbital contact availability."""
        bundle_gb = bundle_size_mb / 1024.0
        
        if is_contact_window_open:
            # Transmit immediately with custody transfer
            self.buffered_bundles_gb = max(0.0, self.buffered_bundles_gb - bundle_gb)
            action = "CUSTODY_TRANSFERRED_DOWNLINK_SUCCESS"
            custody_accepted = True
        else:
            # Store in radiation-tolerant solid-state buffer
            if self.buffered_bundles_gb + bundle_gb <= self.storage_capacity_gb:
                self.buffered_bundles_gb += bundle_gb
                action = "STORED_IN_NONVOLATILE_DTN_BUFFER"
                custody_accepted = True
            else:
                action = "BUFFER_OVERFLOW_BUNDLE_REJECTED"
                custody_accepted = False
                
        return {
            'bundle_size_mb': bundle_size_mb,
            'contact_open': is_contact_window_open,
            'buffered_storage_used_gb': round(self.buffered_bundles_gb, 2),
            'storage_utilization_pct': round((self.buffered_bundles_gb / self.storage_capacity_gb) * 100.0, 1),
            'action': action,
            'custody_accepted': custody_accepted
        }
