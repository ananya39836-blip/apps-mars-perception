"""Synthetic Mars-like scene generator for APPS.
Includes base terrain generator and multi-material novel terrain extensions.
"""
import numpy as np
from scipy import ndimage as ndi

S = 96
CLASSES = ["bedrock", "sand", "rock", "steep_slope"]
HAZ = {2, 3, 4}

# Base materials albedo and texture
BASE_ALBEDO = {
    0: (.55, .34, .24),   # bedrock
    1: (.74, .55, .36),   # sand
    2: (.38, .29, .26),   # rock
    3: (.52, .33, .24),   # steep_slope
    4: (.30, .33, .40)    # default novel (N1)
}

# Task 6: Additional novel materials albedo and texture parameters
NOVEL_MATERIALS = {
    "N1": dict(albedo=(.30, .33, .40), tex=0.05, desc="Obvious: dark bluish hue, low texture"),
    "N2": dict(albedo=(.72, .53, .38), tex=0.15, desc="Subtle: close to sand albedo, distinct fine texture"),
    "N3": dict(albedo=(.85, .82, .75), tex=0.01, desc="Bright: high albedo, smooth low texture"),
    "N4": dict(albedo=(.25, .20, .18), tex=0.20, desc="Rock-like: dark with heavy texture, flat surface")
}

BASE_TEXTURE = {0: .10, 1: .02, 2: .12, 3: .10, 4: .05}


def noise(rng, sigma, amp=1.0, size=(S, S)):
    """Generate smoothed gaussian noise with periodic wrap boundary."""
    n = ndi.gaussian_filter(rng.standard_normal(size), sigma, mode="wrap")
    return amp * n / (n.std() + 1e-9)


def shadow_mask(H, az, el):
    """Ray march shadow mask over height map H along azimuth and elevation."""
    dy, dx = np.sin(az), np.cos(az)
    t = np.tan(el)
    sh = np.zeros_like(H, bool)
    for k in range(1, 14):
        Hs = ndi.shift(H, (k * dy, k * dx), order=1, mode="nearest")
        sh |= (Hs - k * t) > H + 0.02
    return sh


def make_scene(rng, ood=False, novel_type="N1"):
    """Generate a single 96x96 synthetic Mars-like scene.
    Returns:
        img: (96, 96, 3) float32 in [0, 1]
        depth: (96, 96) float32 height + noisy stereo simulated depth
        lab: (96, 96) int label map (0:bedrock, 1:sand, 2:rock, 3:steep_slope, 4:novel)
    """
    H = noise(rng, 14, 3.0) + noise(rng, 5, 0.9)
    for _ in range(rng.integers(0, 3)):  # ridges -> steep terrain
        y, x = rng.integers(10, S - 10, 2)
        a = rng.uniform(0, np.pi)
        yy, xx = np.mgrid[:S, :S]
        d = (yy - y) * np.cos(a) - (xx - x) * np.sin(a)
        H += rng.uniform(2, 4) * np.exp(-(d / rng.uniform(4, 8)) ** 2)
    lab = np.zeros((S, S), int)
    lowland = ndi.gaussian_filter(H, 3) < np.percentile(H, rng.uniform(30, 50))
    lab[lowland] = 1
    Hr = H.copy()
    rocks = np.zeros((S, S), bool)
    yy, xx = np.mgrid[:S, :S]
    for _ in range(rng.integers(5, 14)):
        y, x = rng.integers(4, S - 4, 2)
        ry, rx = rng.uniform(2, 5, 2)
        th = rng.uniform(0, np.pi)
        u = (xx - x) * np.cos(th) + (yy - y) * np.sin(th)
        v = -(xx - x) * np.sin(th) + (yy - y) * np.cos(th)
        m = (u / rx) ** 2 + (v / ry) ** 2 < 1
        rocks |= m
        Hr += m * rng.uniform(0.6, 1.4) * np.clip(1 - ((u / rx) ** 2 + (v / ry) ** 2), 0, 1) ** .5
    gy, gx = np.gradient(ndi.gaussian_filter(H, 1.0))
    steep = np.hypot(gx, gy) > 0.42
    lab[steep & ~lowland] = 3
    lab[rocks] = 2
    if ood:
        for _ in range(rng.integers(1, 3)):
            y, x = rng.integers(15, S - 15, 2)
            r = rng.uniform(8, 14)
            m = ((yy - y) ** 2 + (xx - x) ** 2 < r ** 2) & ~rocks
            m = ndi.binary_dilation(m, iterations=1) & ~rocks
            lab[m] = 4

    alb = np.zeros((S, S, 3))
    base = dict(BASE_ALBEDO)
    tex = dict(BASE_TEXTURE)
    if ood and novel_type in NOVEL_MATERIALS:
        base[4] = NOVEL_MATERIALS[novel_type]["albedo"]
        tex[4] = NOVEL_MATERIALS[novel_type]["tex"]

    for k, c in base.items():
        alb[lab == k] = c
    for k, a in tex.items():
        alb[lab == k] *= 1 + a * noise(rng, 0.8)[lab == k][:, None]

    az, el = rng.uniform(0, 2 * np.pi), np.radians(rng.uniform(25, 60))
    gy, gx = np.gradient(Hr)
    nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    sun = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)])
    shade = np.clip(nrm @ sun, 0, 1) * 0.85 + 0.15
    shade = np.where(shadow_mask(Hr, az, el), shade * 0.35, shade)
    img = alb * shade[..., None] * rng.uniform(.8, 1.2)
    img += rng.normal(0, 0.02, img.shape)
    img = np.clip(img, 0, 1)
    depth = Hr + rng.normal(0, 0.15, Hr.shape)
    return img.astype(np.float32), depth.astype(np.float32), lab


def dataset(n, seed, ood=False):
    """Generate n scenes starting from a master seed."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        img, d, lab = make_scene(rng, ood)
        out.append((img, d, lab))
    return out
