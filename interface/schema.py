"""Output contract and schema validator for APPS perception records.
Chapter 8 & Chapter 69, Appendix AA (Part 5).
"""
import math
from typing import Dict, List, Any

SCHEMA_VERSION = "2.0"
REQUIRED = (
    "schema_version", "scene_id", "frame", "image_size", "model_version", "feature_version",
    "taxonomy_version", "config_hash", "objects", "terrain_fraction", "uncertain_fraction",
    "unsafe_fraction", "terrain_assessment", "scientific_targets", "navigation_ready",
    "navigation_reasons", "limitations", "status"
)


def _frac(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and 0.0 <= x <= 1.0


def validate_record(rec: Any) -> List[str]:
    """Returns a list of error strings; an empty list means the record is valid.
    Downstream code must reject a record with any error, and any unknown schema version.
    """
    if not isinstance(rec, dict):
        return ["record is not an object"]
    if rec.get("schema_version") != SCHEMA_VERSION:
        return [f"unsupported schema_version {rec.get('schema_version')!r}"]
    
    e = [f"missing key {k}" for k in REQUIRED if k not in rec]
    if e:
        return e
    
    if not _frac(rec["uncertain_fraction"]):
        e.append("uncertain_fraction not a fraction")
    if not _frac(rec["unsafe_fraction"]):
        e.append("unsafe_fraction not a fraction")
        
    tf = rec["terrain_fraction"]
    if not isinstance(tf, dict) or not all(_frac(v) for v in tf.values()):
        e.append("terrain_fraction malformed")
        
    if not (isinstance(rec["image_size"], list) and len(rec["image_size"]) == 2):
        e.append("image_size malformed")
        
    if rec["navigation_ready"] is not False:
        e.append("navigation_ready must be false in this prototype")
        
    if not rec["limitations"]:
        e.append("limitations empty")
        
    for o in rec["objects"]:
        if not _frac(o.get("mean_uncertainty")) or o.get("coord_frame") not in ("image_px", "map_cells"):
            e.append("object malformed")
            
    return e


def failure_record(scene_id: str, reason: str, versions: dict) -> dict:
    """Safe-by-default record for corrupt or missing input. Never reports anything as safe."""
    return dict(
        schema_version=SCHEMA_VERSION,
        scene_id=scene_id,
        frame=None,
        image_size=[0, 0],
        objects=[],
        terrain_fraction={},
        uncertain_fraction=1.0,
        unsafe_fraction=1.0,
        terrain_assessment=dict(status="failed", map_available=False, calibrated_on="none"),
        scientific_targets=[],
        navigation_ready=False,
        navigation_reasons=[reason],
        limitations=["input failed validation; treat the whole scene as unsafe"],
        status="failure",
        **versions
    )


def observation_record_v2(scene_id: str, P, ent, epi, unsafe,
                          model_version: str = "apps01_ensemble_5",
                          feature_version: str = "v1.0",
                          taxonomy_version: str = "v1.0",
                          config_hash: str = "cfg-0.1-default",
                          status: str = "ok") -> dict:
    """Creates a validated version 2.0 APPS observation record."""
    from scipy import ndimage as ndi
    CLASSES = ["bedrock", "sand", "rock", "steep_slope"]
    S = P.shape[0]
    objs = []
    rock = ndi.label(P.argmax(-1) == 2)[0]
    for i, sl in enumerate(ndi.find_objects(rock), 1):
        area = int((rock[sl] == i).sum())
        if area < 12:
            continue
        cy, cx = ndi.center_of_mass(rock == i)
        objs.append(dict(
            type="rock",
            location=[int(cx), int(cy)],
            coord_frame="image_px",
            area_px=area,
            obstacle_candidate=True,
            mean_uncertainty=float(ent[rock == i].mean())
        ))
    unc = ent > .35
    
    return dict(
        schema_version=SCHEMA_VERSION,
        scene_id=scene_id,
        frame=dict(name="camera_image_frame", origin="top-left pixel", axes="x right, y down", units="pixels"),
        image_size=[S, S],
        model_version=model_version,
        feature_version=feature_version,
        taxonomy_version=taxonomy_version,
        config_hash=config_hash,
        objects=objs,
        terrain_fraction={c: float((P.argmax(-1) == k).mean()) for k, c in enumerate(CLASSES)},
        uncertain_fraction=float(unc.mean()),
        unsafe_fraction=float(unsafe.mean()),
        terrain_assessment=dict(status="image_and_noisy_depth_only", map_available=True, calibrated_on="synthetic_data_only"),
        scientific_targets=[],
        navigation_ready=False,
        navigation_reasons=["prototype lock: research prototype, not flight software"],
        limitations=[
            "trained on synthetic terrain only; no Mars performance claimed",
            "cannot determine mineral composition",
            "depth is simulated noisy stereo"
        ],
        status=status
    )
