"""CCSDS 133.0-B-1 Space Packet Protocol & Fixed-Point Telemetry Framing (TRL 4).
ECSS-E-ST-70-41C Packet Utilization Standard (PUS) Compatible.

Implements standard 6-octet Primary Header, CCSDS Unsegmented Time Code Secondary Header,
fixed-point payload quantization, and CRC-16-CCITT packet error control.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import struct
import time
from typing import Dict, Any, Tuple, Optional
import numpy as np

from gnc_core import (
    CCSDS_APID_GNC_TELEMETRY,
    CCSDS_APID_IMU_TELEMETRY,
    CCSDS_APID_XNAV_TELEMETRY,
    CCSDS_APID_CORRIDOR_CMD,
    PROTOTYPE_LOCK,
    NAVIGATION_READY,
)


def compute_crc16_ccitt(data: bytes, init_val: int = 0xFFFF) -> int:
    """Computes standard CRC-16-CCITT (Polynomial: x^16 + x^12 + x^5 + 1 / 0x1021)."""
    crc = init_val
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


class CCSDSSpacePacket:
    """Encapsulates a standard CCSDS Telemetry / Telecommand space packet."""

    def __init__(
        self,
        apid: int = CCSDS_APID_GNC_TELEMETRY,
        packet_type: int = 0,  # 0 = TM, 1 = TC
        sequence_count: int = 0,
        epoch_time_s: Optional[float] = None
    ) -> None:
        self.apid = int(apid) & 0x7FF  # 11 bits
        self.packet_type = int(packet_type) & 0x01
        self.sequence_count = int(sequence_count) & 0x3FFF  # 14 bits
        self.timestamp = time.time() if epoch_time_s is None else float(epoch_time_s)

    def encode_primary_header(self, payload_length_bytes: int) -> bytes:
        """Constructs 6-octet CCSDS Primary Header."""
        # Word 1: Version (3b=0) | Type (1b) | SecHdr (1b=1) | APID (11b)
        version = 0
        sec_hdr = 1
        word1 = ((version & 0x07) << 13) | ((self.packet_type & 0x01) << 12) | ((sec_hdr & 0x01) << 11) | (self.apid & 0x07FF)

        # Word 2: SeqFlags (2b=0b11 unsegmented) | PacketSequenceCount (14b)
        seq_flags = 0x03
        word2 = ((seq_flags & 0x03) << 14) | (self.sequence_count & 0x3FFF)

        # Word 3: Packet Data Length = (Secondary Header Length + Payload Length + CRC Length) - 1
        data_length = payload_length_bytes + 6 + 2 - 1  # 6 bytes time code + 2 bytes CRC
        word3 = data_length & 0xFFFF

        return struct.pack(">HHH", word1, word2, word3)

    def encode_secondary_header(self) -> bytes:
        """Constructs 6-octet CCSDS CUC Time Code (4 octets coarse + 2 octets fine)."""
        coarse_sec = int(self.timestamp) & 0xFFFFFFFF
        fine_fraction = int((self.timestamp - int(self.timestamp)) * 65536.0) & 0xFFFF
        return struct.pack(">IH", coarse_sec, fine_fraction)

    def pack_gnc_telemetry(
        self,
        pos_m: np.ndarray,
        vel_mps: np.ndarray,
        accel_mps2: np.ndarray,
        bank_deg: float,
        g_load: float
    ) -> bytes:
        """Packs GNC state into deterministic fixed-point binary representation.
        
        Fixed-Point Layout:
        - Position: 3 x INT64 in meters (resolution: 1 m, range: +/- 9.22e18 m)
        - Velocity: 3 x INT32 in mm/s (resolution: 1e-3 m/s)
        - Acceleration: 3 x INT16 in 1e-3 m/s^2 (resolution: 1 mm/s^2)
        - Bank Angle: 1 x INT16 in 1e-2 degrees (resolution: 0.01 deg)
        - G-Load: 1 x UINT16 in 1e-2 g (resolution: 0.01 g)
        Total Payload: 24 + 12 + 6 + 2 + 2 = 46 bytes
        """
        pos_int = [int(np.clip(p, -9223372036854775808, 9223372036854775807)) for p in pos_m[:3]]
        vel_int = [int(np.clip(v * 1000.0, -2147483648, 2147483647)) for v in vel_mps[:3]]
        acc_int = [int(np.clip(a * 1000.0, -32768, 32767)) for a in accel_mps2[:3]]
        bank_int = int(np.clip(bank_deg * 100.0, -32768, 32767))
        gload_int = int(np.clip(g_load * 100.0, 0, 65535))

        payload = struct.pack(
            ">3q3i3hhH",
            pos_int[0], pos_int[1], pos_int[2],
            vel_int[0], vel_int[1], vel_int[2],
            acc_int[0], acc_int[1], acc_int[2],
            bank_int,
            gload_int
        )

        prim_hdr = self.encode_primary_header(len(payload))
        sec_hdr = self.encode_secondary_header()
        raw_without_crc = prim_hdr + sec_hdr + payload
        crc = compute_crc16_ccitt(raw_without_crc)
        return raw_without_crc + struct.pack(">H", crc)

    @staticmethod
    def unpack_gnc_telemetry(packet_bytes: bytes) -> Dict[str, Any]:
        """Validates CRC-16 and decodes CCSDS packet into physical floating-point telemetry."""
        if len(packet_bytes) < 60:
            raise ValueError(f"Packet too short: {len(packet_bytes)} bytes < 60 bytes")

        # Verify CRC
        computed_crc = compute_crc16_ccitt(packet_bytes[:-2])
        packet_crc = struct.unpack(">H", packet_bytes[-2:])[0]
        if computed_crc != packet_crc:
            raise ValueError(f"CRC-16 mismatch: computed 0x{computed_crc:04X} != packet 0x{packet_crc:04X}")

        # Unpack Primary Header
        w1, w2, w3 = struct.unpack(">HHH", packet_bytes[:6])
        apid = w1 & 0x07FF
        seq_count = w2 & 0x3FFF

        # Unpack Secondary Header
        coarse_s, fine_s = struct.unpack(">IH", packet_bytes[6:12])
        timestamp = float(coarse_s) + float(fine_s) / 65536.0

        # Unpack Payload
        unpacked = struct.unpack(">3q3i3hhH", packet_bytes[12:-2])
        pos = np.array([unpacked[0], unpacked[1], unpacked[2]], dtype=float)
        vel = np.array([unpacked[3], unpacked[4], unpacked[5]], dtype=float) / 1000.0
        acc = np.array([unpacked[6], unpacked[7], unpacked[8]], dtype=float) / 1000.0
        bank_deg = unpacked[9] / 100.0
        g_load = unpacked[10] / 100.0

        return {
            "apid": apid,
            "sequence_count": seq_count,
            "timestamp_s": timestamp,
            "pos_m": pos,
            "vel_mps": vel,
            "acc_mps2": acc,
            "bank_deg": bank_deg,
            "g_load_g": g_load,
            "crc_valid": True,
        }
