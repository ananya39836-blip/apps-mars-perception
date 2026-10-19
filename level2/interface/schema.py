"""Level 2 Interface Message Schema, Validator, and Serialization.
Task 104 / Chapter 212 & Appendix CP (Part 12).
Strictly validates messages, enforces navigation_ready = False, and rejects truth keys.
"""
import hashlib
import json
import math
from typing import Dict, Any, Tuple

KNOWN_VERSIONS = {"1", "2"}
FORBIDDEN_KEYS = {"truth", "truth_grid", "hidden_obstacles", "_truth"}


def _finite(v):
    """Recursively verify all float numbers are finite."""
    if isinstance(v, float):
        return math.isfinite(v)
    if isinstance(v, dict):
        return all(_finite(x) for x in v.values())
    if isinstance(v, (list, tuple)):
        return all(_finite(x) for x in v)
    return True


def _keys(v):
    """Recursively yield all dictionary keys in the structure."""
    if isinstance(v, dict):
        for k, x in v.items():
            yield k
            yield from _keys(x)
    elif isinstance(v, (list, tuple)):
        for x in v:
            yield from _keys(x)


def compute_body_checksum(body: dict) -> str:
    """Compute deterministic SHA-256 digest of message body."""
    raw = json.dumps(body, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_message(msg: dict, last_seq: int = -1) -> str:
    """Validate interface message strictly.
    Returns:
        'ok' or specific rejection status:
        'unknown_version' | 'lock_violation' | 'bad_sequence' | 'non_finite' | 'forbidden_key' | 'checksum_mismatch'
    """
    if not isinstance(msg, dict):
        return "invalid_format"
        
    if str(msg.get("schema_version")) not in KNOWN_VERSIONS:
        return "unknown_version"
        
    # Non-negotiable prototype lock
    if msg.get("navigation_ready") is not False:
        return "lock_violation"
        
    # Sequence check
    seq = msg.get("seq")
    if not isinstance(seq, int) or seq <= last_seq:
        return "bad_sequence"
        
    # Finite numbers check
    if not _finite(msg):
        return "non_finite"
        
    # Information boundary truth-leakage hunt
    msg_keys = set(_keys(msg))
    if FORBIDDEN_KEYS & msg_keys:
        return "forbidden_key"
        
    # Checksum verification if body_checksum provided
    if "body_checksum" in msg and "body" in msg:
        expected = compute_body_checksum(msg["body"])
        if msg["body_checksum"] != expected:
            return "checksum_mismatch"
            
    return "ok"


def build_message(msg_type: str, seq: int, step: int, producer: str,
                  body: dict, schema_version: str = "2") -> dict:
    """Constructs a compliant Level 2 interface message with header, lock, and checksum."""
    chk = compute_body_checksum(body)
    return {
        "schema_version": schema_version,
        "type": msg_type,
        "seq": seq,
        "step": step,
        "producer": producer,
        "navigation_ready": False,
        "navigation_ready_reason": "prototype lock",
        "body": body,
        "body_checksum": chk
    }
