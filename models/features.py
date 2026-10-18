"""Feature extraction module for APPS.
Chapter 24.4 and Chapter 45.1.
"""
import numpy as np
from scipy import ndimage as ndi

FEATURE_VERSION = "v1.0"


def features(img: np.ndarray, depth: np.ndarray) -> np.ndarray:
    """Extract 16-channel handcrafted visual & geometric pixel features.
    
    Inputs:
        img: (H, W, 3) float32 RGB
        depth: (H, W) float32 noisy depth
    Returns:
        F: (H * W, 16) float32 feature array
    """
    g = img.mean(-1)
    F = [img[..., 0], img[..., 1], img[..., 2], img[..., 0] / (img[..., 2] + .05)]
    for s in (1, 2, 4):
        F.append(ndi.gaussian_filter(g, s))
    for w in (3, 7):
        m = ndi.uniform_filter(g, w)
        F.append(np.sqrt(np.maximum(ndi.uniform_filter(g * g, w) - m * m, 0)))
    gy, gx = np.gradient(ndi.gaussian_filter(g, 1))
    F.append(np.hypot(gx, gy))
    F.append(ndi.gaussian_laplace(g, 2))
    F.append(g - ndi.gaussian_filter(g, 8))
    for s in (2, 3):
        dy, dx = np.gradient(ndi.gaussian_filter(depth, s))
        F.append(np.hypot(dx, dy))
    F.append(ndi.gaussian_laplace(depth, 2))
    F.append(depth - ndi.gaussian_filter(depth, 6))
    return np.stack(F, -1).reshape(-1, len(F)).astype(np.float32)
