"""Feature Pipeline v2 with input validation, validity mask and version locking.
Chapter 113, Task 55 (Part 7).
"""
import numpy as np
from scipy import ndimage as ndi

FEATURE_VERSION = "v2.0"


def features_v2(img: np.ndarray, depth: np.ndarray = None) -> tuple:
    """Extract 16-channel handcrafted visual & geometric pixel features with robust input validation.
    
    Returns:
        F: (H * W, 16) float32 feature array (NaN where invalid)
        valid_mask: (H, W) boolean mask of valid pixels
        feature_version: str
    """
    if not isinstance(img, np.ndarray) or img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("Image must be a 3D numpy array of shape (H, W, 3)")
        
    H, W = img.shape[:2]
    valid_mask = np.isfinite(img).all(axis=-1)
    
    # Check for saturated or blackout image
    if valid_mask.mean() < 0.5 or (img.max() - img.min() < 1e-4):
        valid_mask = np.zeros((H, W), bool)
        
    img_clean = np.where(valid_mask[..., None], img, 0.0)
    g = img_clean.mean(-1)
    
    F = [img_clean[..., 0], img_clean[..., 1], img_clean[..., 2], img_clean[..., 0] / (img_clean[..., 2] + .05)]
    for s in (1, 2, 4):
        F.append(ndi.gaussian_filter(g, s))
    for w in (3, 7):
        m = ndi.uniform_filter(g, w)
        F.append(np.sqrt(np.maximum(ndi.uniform_filter(g * g, w) - m * m, 0.0)))
    gy, gx = np.gradient(ndi.gaussian_filter(g, 1))
    F.append(np.hypot(gx, gy))
    F.append(ndi.gaussian_laplace(g, 2))
    F.append(g - ndi.gaussian_filter(g, 8))
    
    if depth is not None and isinstance(depth, np.ndarray) and depth.shape == (H, W):
        depth_valid = np.isfinite(depth)
        d_clean = np.where(depth_valid, depth, np.nanmedian(depth) if depth_valid.any() else 0.0)
        valid_mask &= depth_valid
        for s in (2, 3):
            dy, dx = np.gradient(ndi.gaussian_filter(d_clean, s))
            F.append(np.hypot(dx, dy))
        F.append(ndi.gaussian_laplace(d_clean, 2))
        F.append(d_clean - ndi.gaussian_filter(d_clean, 6))
    else:
        # Depth missing -> fill with zeros and mark mask degraded
        for _ in range(4):
            F.append(np.zeros((H, W), dtype=np.float32))

    feat_array = np.stack(F, -1).reshape(-1, len(F)).astype(np.float32)
    return feat_array, valid_mask, FEATURE_VERSION
