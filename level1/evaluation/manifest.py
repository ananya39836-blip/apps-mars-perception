"""Cryptographic Manifest Builder and Pre-Registration Hashing Engine.
Part 9 Appendix BN & Part 10 Appendix BV (Tasks 71 & 87).
"""
import hashlib
import json
import os


def sha256_file(p: str) -> str:
    """Compute streaming SHA-256 hash of a file."""
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def build_manifest(paths: list) -> list:
    """Generate canonical manifest records for an archive release."""
    return [dict(path=p.replace("\\", "/"), sha256=sha256_file(p)) for p in sorted(paths) if os.path.exists(p)]


def verify_manifest(man: list) -> list:
    """Verify stored manifest against current filesystem. Returns list of mismatches."""
    bad = []
    for m in man:
        p = m["path"]
        if not os.path.exists(p) or sha256_file(p) != m["sha256"]:
            bad.append(p)
    return bad


def prereg_hash(d: dict) -> str:
    """Compute canonical deterministic SHA-256 hash of a pre-registration dictionary."""
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode()).hexdigest()
