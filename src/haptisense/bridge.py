"""Local UDP bridge between Unity contact states and haptic commands."""

from __future__ import annotations

from dataclasses import asdict
import json
import socket
import time

from .cues import MultimodalCueSynthesizer, TEXTURES
from .force_models import BodyGroundedInertialCue, ContactState, KelvinVoigtSurface, Vec3
from .hardware import HapticCommand
from .safety import SafetyEnvelope


class UnityBridgeServer:
    """Translate Unity JSON contact packets into safety-limited commands.

    The default addresses are loopback-only. The server is a readable research
    bridge, not a hard-real-time haptic servo loop.
    """

    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 9051,
        unity_host: str = "127.0.0.1",
        unity_port: int = 9050,
    ) -> None:
        self.listen_address = (listen_host, listen_port)
        self.unity_address = (unity_host, unity_port)
        self.surface = KelvinVoigtSurface()
        self.inertial = BodyGroundedInertialCue()
        self.synthesizer = MultimodalCueSynthesizer()
        self.safety = SafetyEnvelope()
        self.last_time = time.monotonic()

    @staticmethod
    def _vec(packet: dict[str, object], prefix: str) -> Vec3:
        return Vec3(
            float(packet.get(f"{prefix}x", 0.0)),
            float(packet.get(f"{prefix}y", 0.0)),
            float(packet.get(f"{prefix}z", 0.0)),
        )

    def process_packet(self, packet: dict[str, object], now_s: float | None = None) -> HapticCommand:
        now = time.monotonic() if now_s is None else now_s
        dt = min(0.02, max(0.0005, now - self.last_time))
        self.last_time = now
        texture_name = str(packet.get("texture", "soft_tissue"))
        texture = TEXTURES.get(texture_name, TEXTURES["soft_tissue"])
        velocity = self._vec(packet, "v")
        normal = self._vec(packet, "n")
        if normal.norm() <= 1e-12:
            normal = Vec3(0.0, 1.0, 0.0)
        acceleration = self._vec(packet, "a")
        state = ContactState(
            penetration_m=max(0.0, float(packet.get("penetration_m", 0.0))),
            velocity_m_s=velocity,
            surface_normal=normal,
        )
        contact = self.surface.compute(state)
        inertial_force = self.inertial.compute(acceleration)
        combined = contact.total * 0.82 + inertial_force * 0.18
        tangential = velocity - normal.normalized() * velocity.dot(normal.normalized())
        raw = self.synthesizer.synthesize(combined, tangential.norm(), texture)
        safe, _ = self.safety.apply(raw, dt)
        return HapticCommand.from_cue(safe, timestamp_s=now)

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(self.listen_address)
            print(
                f"HaptiSense bridge listening on udp://{self.listen_address[0]}:{self.listen_address[1]} "
                f"and sending to udp://{self.unity_address[0]}:{self.unity_address[1]}"
            )
            while True:
                payload, _ = server.recvfrom(16_384)
                try:
                    packet = json.loads(payload.decode("utf-8"))
                    command = self.process_packet(packet)
                    server.sendto(
                        json.dumps(asdict(command), separators=(",", ":")).encode("utf-8"),
                        self.unity_address,
                    )
                except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
                    print(f"Ignored invalid packet: {exc}")
