"""Temporal Map Fusion with Pose Uncertainty and Stale Frame Detection.
Chapter 215 / Part 12 Task 106.
"""
import numpy as np
from scipy import ndimage as ndi


class TemporalMapFusion:
    """Combines observations across steps while pose is uncertain without erasing correct warnings."""
    
    def __init__(self, shape: tuple = (96, 96), clearing_count_thresh: int = 4):
        self.H, self.W = shape
        self.hazard_belief = np.zeros(shape, dtype=np.float32)
        self.seen_mask = np.zeros(shape, dtype=bool)
        self.obs_count = np.zeros(shape, dtype=int)
        self.hazard_count = np.zeros(shape, dtype=int)
        self.clear_consecutive = np.zeros(shape, dtype=int)
        self.clearing_thresh = clearing_count_thresh
        self.last_frame = None

    def is_frame_frozen(self, new_frame: np.ndarray, tolerance: float = 1e-4) -> bool:
        """Detect stuck sensor hardware by comparing consecutive raw frames."""
        if self.last_frame is None:
            self.last_frame = new_frame.copy()
            return False
            
        if self.last_frame.shape != new_frame.shape:
            self.last_frame = new_frame.copy()
            return False
            
        diff = np.max(np.abs(self.last_frame - new_frame))
        frozen = bool(diff < tolerance)
        self.last_frame = new_frame.copy()
        return frozen

    def update(self, new_hazard: np.ndarray, observed_mask: np.ndarray,
               fuse_mode: str = "union", pose_sigma_cells: float = 0.0) -> dict:
        """Fuse new observation into accumulated temporal internal map.
        Union default with sigma spread: each hazard flag is dilated by pose sigma.
        """
        # Apply pose uncertainty spread mask
        eff_haz = new_hazard.copy()
        if pose_sigma_cells > 0.5:
            radius = int(round(pose_sigma_cells))
            struct = np.ones((2 * radius + 1, 2 * radius + 1), dtype=bool)
            eff_haz = ndi.binary_dilation(eff_haz > 0.30, structure=struct).astype(np.float32)

        # Update evidence counts
        both = self.seen_mask & observed_mask
        new_haz_cells = (eff_haz > 0.30) & observed_mask
        new_clear_cells = (eff_haz <= 0.30) & observed_mask
        
        self.obs_count[observed_mask] += 1
        self.hazard_count[new_haz_cells] += 1
        
        # Clearing logic
        self.clear_consecutive[new_clear_cells] += 1
        self.clear_consecutive[new_haz_cells] = 0

        if fuse_mode == "latest":
            # Latest-wins ablation
            self.hazard_belief = np.where(observed_mask, eff_haz, self.hazard_belief)
        else: # Union default
            # Retain hazard unless cleared by consistent clear observations
            cleared = self.clear_consecutive >= self.clearing_thresh
            union_val = np.maximum(self.hazard_belief, eff_haz)
            self.hazard_belief = np.where(observed_mask, union_val, self.hazard_belief)
            self.hazard_belief[cleared] = 0.0

        self.seen_mask |= observed_mask
        
        return {
            "hazard_belief": self.hazard_belief.copy(),
            "seen_mask": self.seen_mask.copy(),
            "newly_unsafe_count": int((both & new_haz_cells & (self.hazard_belief < 0.30)).sum())
        }
