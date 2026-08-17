"""Device abstraction and safe local transports for haptic commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import socket
import time
from typing import Protocol

from .cues import MultimodalCue


@dataclass(frozen=True, slots=True)
class HapticCommand:
    timestamp_s: float
    fx: float
    fy: float
    fz: float
    vibration_amplitude: float
    vibration_frequency_hz: float
    contact_strength: float

    @classmethod
    def from_cue(cls, cue: MultimodalCue, timestamp_s: float | None = None) -> "HapticCommand":
        return cls(
            timestamp_s=time.monotonic() if timestamp_s is None else timestamp_s,
            fx=cue.force_n.x,
            fy=cue.force_n.y,
            fz=cue.force_n.z,
            vibration_amplitude=cue.vibration.amplitude,
            vibration_frequency_hz=cue.vibration.frequency_hz,
            contact_strength=cue.contact_strength,
        )


class HapticDevice(Protocol):
    def connect(self) -> None: ...
    def write(self, command: HapticCommand) -> None: ...
    def close(self) -> None: ...


class MockHapticDevice:
    """In-memory device for tests and demonstrations."""

    def __init__(self) -> None:
        self.connected = False
        self.commands: list[HapticCommand] = []

    def connect(self) -> None:
        self.connected = True

    def write(self, command: HapticCommand) -> None:
        if not self.connected:
            raise RuntimeError("device is not connected")
        self.commands.append(command)

    def close(self) -> None:
        self.connected = False


class UdpJsonDevice:
    """Send commands as JSON datagrams to a local visualization or adapter."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9050) -> None:
        self.address = (host, port)
        self._socket: socket.socket | None = None

    def connect(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def write(self, command: HapticCommand) -> None:
        if self._socket is None:
            raise RuntimeError("device is not connected")
        payload = json.dumps(asdict(command), separators=(",", ":")).encode("utf-8")
        self._socket.sendto(payload, self.address)

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
