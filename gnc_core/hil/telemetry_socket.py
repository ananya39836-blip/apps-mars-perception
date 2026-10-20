"""Hardware-in-the-Loop (HIL) Breadboard Telemetry Socket Emulator (TRL 4).
Provides UDP and loopback packet transport for external breadboard validation.

Broadcasts and ingests binary CCSDS space packets to integrate external
flight processors (FreeRTOS, RTEMS, dSPACE, FPGA) with GNC simulation.

Under PROTOTYPE_LOCK = True, navigation_ready evaluates strictly to False.
"""
from __future__ import annotations
import socket
import select
from typing import Dict, Any, Optional, Tuple, List

from gnc_core import PROTOTYPE_LOCK, NAVIGATION_READY
from gnc_core.realtime.ccsds_packet import CCSDSSpacePacket


class HILTelemetrySocket:
    """Non-blocking UDP socket emulator for external HIL breadboard integration."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        tx_port: int = 50051,
        rx_port: int = 50052,
        enable_network: bool = True
    ) -> None:
        self.host = host
        self.tx_port = int(tx_port)
        self.rx_port = int(rx_port)
        self.enable_network = enable_network

        self.tx_socket: Optional[socket.socket] = None
        self.rx_socket: Optional[socket.socket] = None
        self.loopback_buffer: List[bytes] = []

        if self.enable_network:
            try:
                # Transmit socket (UDP)
                self.tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.tx_socket.setblocking(False)

                # Receive socket (UDP)
                self.rx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.rx_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.rx_socket.bind((self.host, self.rx_port))
                self.rx_socket.setblocking(False)
            except Exception:
                # Fallback to in-memory loopback if socket binding fails in sandboxed environments
                self.enable_network = False

    def send_telemetry_packet(self, ccsds_bytes: bytes) -> bool:
        """Sends binary CCSDS telemetry packet to external breadboard receiver."""
        self.loopback_buffer.append(ccsds_bytes)
        if len(self.loopback_buffer) > 100:
            self.loopback_buffer.pop(0)

        if self.enable_network and self.tx_socket is not None:
            try:
                self.tx_socket.sendto(ccsds_bytes, (self.host, self.tx_port))
                return True
            except Exception:
                return False
        return True

    def receive_command_packet(self) -> Optional[bytes]:
        """Polls for incoming telecommand packet from external breadboard."""
        if self.enable_network and self.rx_socket is not None:
            try:
                ready, _, _ = select.select([self.rx_socket], [], [], 0.0)
                if ready:
                    data, _ = self.rx_socket.recvfrom(2048)
                    return data
            except Exception:
                pass

        if self.loopback_buffer:
            return self.loopback_buffer.pop(0)
        return None

    def close(self) -> None:
        """Closes network sockets cleanly."""
        if self.tx_socket is not None:
            try:
                self.tx_socket.close()
            except Exception:
                pass
        if self.rx_socket is not None:
            try:
                self.rx_socket.close()
            except Exception:
                pass
