"""Level 1 Procedural Terrain Generator (Mode A v2).
Chapters 96 & 110; Part 6 Task 45 & Part 7 Task 51.
"""
import numpy as np
from scipy import ndimage as ndi

S = 96
CLASSES = ["bedrock", "sand", "rock", "steep_slope"]
HAZ = {2, 3, 4}

NOVEL_MATERIALS = {
    "N1": dict(albedo=(.30, .33, .40), tex=0.05, desc="Obvious: dark bluish hue, low texture"),
    "N2": dict(albedo=(.72, .53, .38), tex=0.15, desc="Subtle: close to sand albedo, distinct fine texture"),
    "N3": dict(albedo=(.85, .82, .75), tex=0.01, desc="Bright: high albedo, smooth low texture"),
    "N4": dict(albedo=(.25, .20, .18), tex=0.20, desc="Rock-like: dark with heavy texture, flat surface")
}

BASE_ALBEDO = {
    0: (.55, .34, .24),
    1: (.74, .55, .36),
    2: (.38, .29, .26),
    3: (.52, .33, .24),
    4: (.30, .33, .40)
}
BASE_TEXTURE = {0: .10, 1: .02, 2: .12, 3: .10, 4: .05}


def noise(rng, sigma, amp=1.0, size=(S, S)):
    n = ndi.gaussian_filter(rng.standard_normal(size), sigma, mode="wrap")
    return amp * n / (n.std() + 1e-9)


def shadow_mask(H, az, el):
    dy, dx = np.sin(az), np.cos(az)
    t = np.tan(el)
    sh = np.zeros_like(H, bool)
    for k in range(1, 14):
        Hs = ndi.shift(H, (k * dy, k * dx), order=1, mode="nearest")
        sh |= (Hs - k * t) > H + 0.02
    return sh


def make_scene_v2(rng, difficulty: str = "D1", novel_type: str = "N1",
                  passage_gap_cells: int = 6, haze_density: float = 0.0,
                  sun_elevation_deg: float = 40.0, start_row: int = 48):
    """Generate a Level 1 procedural synthetic terrain scene.
    
    Difficulty levels:
        D0: Open field, no hazards
        D1: Scattered rocks
        D2: Ridge with steep slope + rocks
        D3: Narrow passage with placed obstacle pair
        D4: Dead end requiring backtrack
        D5: Multi-hazard combination + novel material patch
    """
    yy, xx = np.mgrid[:S, :S]
    lab = np.zeros((S, S), int)
    
    # 1. Base height field
    if difficulty == "D0":
        H = noise(rng, 16, 0.5)
        steep = np.zeros((S, S), bool)
        rocks = np.zeros((S, S), bool)
        Hr = H.copy()
    else:
        H = noise(rng, 14, 3.0) + noise(rng, 5, 0.9)
        n_ridges = 0 if difficulty in ("D1", "D3") else rng.integers(1, 3)
        for _ in range(n_ridges):
            y, x = rng.integers(10, S - 10, 2)
            a = rng.uniform(0, np.pi)
            d = (yy - y) * np.cos(a) - (xx - x) * np.sin(a)
            H += rng.uniform(2.5, 4.5) * np.exp(-(d / rng.uniform(4, 7)) ** 2)
        
        lowland = ndi.gaussian_filter(H, 3) < np.percentile(H, rng.uniform(30, 45))
        lab[lowland] = 1
        Hr = H.copy()
        rocks = np.zeros((S, S), bool)
        
        # Obstacle placement based on difficulty
        if difficulty == "D1":
            n_rocks = rng.integers(6, 12)
        elif difficulty == "D2":
            n_rocks = rng.integers(8, 15)
        elif difficulty == "D3":
            # Placed obstacle pair forming a narrow corridor
            mid_y, mid_x = S // 2, S // 2
            half_gap = max(1, passage_gap_cells * 3)  # pixel equivalent
            wall_m1 = (np.abs(xx - mid_x) < 8) & (yy < mid_y - half_gap)
            wall_m2 = (np.abs(xx - mid_x) < 8) & (yy > mid_y + half_gap)
            rocks |= (wall_m1 | wall_m2)
            Hr += rocks * 1.5
            n_rocks = rng.integers(3, 6)
        elif difficulty == "D4":
            # Cul-de-sac / Dead-end U-shaped wall
            u_wall = ((xx > 35) & (xx < 65) & (yy > 25) & (yy < 70)) & ~((xx > 45) & (xx < 65) & (yy > 35) & (yy < 60))
            rocks |= u_wall
            Hr += rocks * 1.5
            n_rocks = rng.integers(3, 6)
        elif difficulty == "D5":
            n_rocks = rng.integers(10, 18)
        else:
            n_rocks = rng.integers(6, 12)

        for _ in range(n_rocks):
            y, x = rng.integers(6, S - 6, 2)
            ry, rx = rng.uniform(2.5, 5.5, 2)
            th = rng.uniform(0, np.pi)
            u = (xx - x) * np.cos(th) + (yy - y) * np.sin(th)
            v = -(xx - x) * np.sin(th) + (yy - y) * np.cos(th)
            m = (u / rx) ** 2 + (v / ry) ** 2 < 1.0
            rocks |= m
            Hr += m * rng.uniform(0.7, 1.5) * np.clip(1.0 - ((u / rx) ** 2 + (v / ry) ** 2), 0, 1) ** 0.5

        gy, gx = np.gradient(ndi.gaussian_filter(H, 1.0))
        steep = np.hypot(gx, gy) > 0.42
        lab[steep & ~lowland] = 3
        lab[rocks] = 2

    # 2. Novel terrain patches (for D5 or explicit novel flag)
    if difficulty == "D5":
        for _ in range(rng.integers(1, 3)):
            y, x = rng.integers(15, S - 15, 2)
            r = rng.uniform(8, 14)
            m = ((yy - y) ** 2 + (xx - x) ** 2 < r ** 2) & ~rocks
            m = ndi.binary_dilation(m, iterations=1) & ~rocks
            lab[m] = 4

    # 3. Ensure start cell (start_row, 0) is guaranteed hazard-free (finding F4)
    r_start = np.clip(start_row, 0, S - 1)
    lab[max(0, r_start - 3):min(S, r_start + 4), 0:6] = 0

    # 4. Albedo and Texture mapping
    alb = np.zeros((S, S, 3), dtype=np.float32)
    base = dict(BASE_ALBEDO)
    tex = dict(BASE_TEXTURE)
    if novel_type in NOVEL_MATERIALS:
        base[4] = NOVEL_MATERIALS[novel_type]["albedo"]
        tex[4] = NOVEL_MATERIALS[novel_type]["tex"]

    for k, c in base.items():
        alb[lab == k] = c
    for k, a in tex.items():
        alb[lab == k] *= 1.0 + a * noise(rng, 0.8)[lab == k][:, None]

    # 5. Shading and Illumination
    az = rng.uniform(0, 2 * np.pi)
    el = np.radians(sun_elevation_deg)
    gy, gx = np.gradient(Hr)
    nrm = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    sun = np.array([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)])
    shade = np.clip(nrm @ sun, 0, 1) * 0.85 + 0.15
    shade = np.where(shadow_mask(Hr, az, el), shade * 0.35, shade)
    img = alb * shade[..., None] * rng.uniform(.85, 1.15)
    img += rng.normal(0, 0.02, img.shape)
    img = np.clip(img, 0.0, 1.0).astype(np.float32)

    # 6. Atmospheric haze blending if specified
    if haze_density > 0.0:
        dust_col = np.array([0.82, 0.65, 0.45], dtype=np.float32)
        w_haze = 1.0 - np.exp(-haze_density * (Hr - Hr.min()))
        w_haze = np.clip(w_haze[..., None], 0.0, 0.85)
        img = (1.0 - w_haze) * img + w_haze * dust_col
        img = np.clip(img, 0.0, 1.0).astype(np.float32)

    depth = (Hr + rng.normal(0, 0.15, Hr.shape)).astype(np.float32)
    truth_haz = np.isin(lab, list(HAZ))

    metadata = dict(
        difficulty=difficulty,
        novel_type=novel_type if difficulty == "D5" else None,
        sun_azimuth_deg=float(np.degrees(az)),
        sun_elevation_deg=float(sun_elevation_deg),
        haze_density=float(haze_density),
        rock_pixel_count=int((lab == 2).sum()),
        steep_pixel_count=int((lab == 3).sum()),
        novel_pixel_count=int((lab == 4).sum()),
        generator_version="2.0"
    )
    return img, depth, lab, truth_haz, metadata
