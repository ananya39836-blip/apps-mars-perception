"""Hardware-In-The-Loop (HIL) CCSDS Telemetry Streamer (TRL 6).

Implements real-time UDP socket streaming of rover sensor and autonomy telemetry
framed using standard CCSDS Space Packet Protocol (CCSDS 133.0-B-1). Enables external
breadboard flight computers and hardware-in-the-loop test benches to receive live feeds.
"""
from __future__ import annotations
import json
import socket
import struct
import time
import zlib
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class CCSDSSpacePacket:
    """Represents a standard CCSDS telemetry space packet."""
    apid: int
    sequence_count: int
    timestamp_s: float
    payload_dict: Dict[str, Any]
    raw_packet_bytes: bytes
    crc32: int


class HILTelemetryStreamer:
    """Manages UDP socket broadcast of CCSDS telemetry packets for HIL validation."""

    def __init__(
        self,
        dest_ip: str = "127.0.0.1",
        dest_port: int = 8088,
        apid: int = 0x0150,  # 336 = GNC/Autonomy Navigation Telemetry APID
        enabled: bool = True
    ) -> None:
        self.dest_ip = dest_ip
        self.dest_port = int(dest_port)
        self.apid = int(apid) & 0x07FF  # 11-bit APID
        self.enabled = bool(enabled)
        self.sequence_count = 0

        self.socket: Optional[socket.socket] = None
        if self.enabled:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except Exception:
                self.socket = None

    def pack_ccsds_telemetry(
        self,
        telemetry_payload: Dict[str, Any],
        timestamp_s: Optional[float] = None
    ) -> CCSDSSpacePacket:
        """Serializes telemetry payload into a binary CCSDS space packet."""
        t_sec = float(timestamp_s if timestamp_s is not None else time.time())
        json_bytes = json.dumps(telemetry_payload, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else str(x)).encode("utf-8")

        # 1. Primary Header (6 bytes):
        # Bits 0-2: Version = 000
        # Bit 3: Type = 0 (Telemetry)
        # Bit 4: Sec Header Flag = 1
        # Bits 5-15: APID (11 bits)
        word_0 = (0 << 13) | (1 << 11) | (self.apid & 0x07FF)

        # Bits 0-1: Sequence Flags = 11 (3 = Unsegmented)
        # Bits 2-15: Sequence Count (14 bits)
        word_1 = (3 << 14) | (self.sequence_count & 0x3FFF)

        # Secondary Header (8 bytes timestamp double) + Payload Length
        sec_hdr_bytes = struct.pack(">d", t_sec)
        user_data_bytes = sec_hdr_bytes + json_bytes

        # Packet Length = Total Data Field Bytes - 1
        packet_len = len(user_data_bytes) - 1
        if packet_len > 65535:
            # Clip if payload exceeds 64KB
            user_data_bytes = user_data_bytes[:65535]
            packet_len = 65534

        hdr_bytes = struct.pack(">HHH", word_0, word_1, packet_len)
        full_packet = hdr_bytes + user_data_bytes
        packet_crc = zlib.crc32(full_packet) & 0xFFFFFFFF
        final_packet_bytes = full_packet + struct.pack(">I", packet_crc)

        packet_obj = CCSDSSpacePacket(
            apid=self.apid,
            sequence_count=self.sequence_count,
            timestamp_s=t_sec,
            payload_dict=telemetry_payload,
            raw_packet_bytes=final_packet_bytes,
            crc32=packet_crc,
        )

        self.sequence_count = (self.sequence_count + 1) % 16384
        return packet_obj

    def stream_packet(self, telemetry_payload: Dict[str, Any], timestamp_s: Optional[float] = None) -> bool:
        """Packs and transmits telemetry packet over UDP socket."""
        packet = self.pack_ccsds_telemetry(telemetry_payload, timestamp_s)
        if self.socket is not None and self.enabled:
            try:
                self.socket.sendto(packet.raw_packet_bytes, (self.dest_ip, self.dest_port))
                return True
            except Exception:
                return False
        return False

    @staticmethod
    def unpack_ccsds_packet(raw_bytes: bytes) -> Tuple[bool, Optional[CCSDSSpacePacket]]:
        """Parses and verifies raw binary CCSDS packet."""
        if len(raw_bytes) < 18:  # 6 hdr + 8 sec_hdr + 4 crc
            return False, None

        # Verify CRC
        payload_wo_crc = raw_bytes[:-4]
        recv_crc = struct.unpack(">I", raw_bytes[-4:])[0]
        calc_crc = zlib.crc32(payload_wo_crc) & 0xFFFFFFFF
        if recv_crc != calc_crc:
            return False, None

        word_0, word_1, packet_len = struct.unpack(">HHH", raw_bytes[:6])
        apid = word_0 & 0x07FF
        seq_count = word_1 & 0x3FFF

        t_sec = struct.unpack(">d", raw_bytes[6:14])[0]
        json_bytes = raw_bytes[14:-4]
        try:
            payload_dict = json.loads(json_bytes.decode("utf-8"))
        except Exception:
            payload_dict = {}

        pkt = CCSDSSpacePacket(
            apid=apid,
            sequence_count=seq_count,
            timestamp_s=t_sec,
            payload_dict=payload_dict,
            raw_packet_bytes=raw_bytes,
            crc32=recv_crc,
        )
        return True, pkt

    def close(self) -> None:
        """Closes UDP socket descriptor."""
        if self.socket is not None:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
