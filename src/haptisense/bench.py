"""Bench-only vibrotactile adapter. Never a force-feedback servo or medical device.

Simulation, mock serial and physical serial evidence remain distinct. The UNO
adapter maps amplitude to PWM duty; ERM mechanical frequency is NOT controlled.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import socket
import time
from dataclasses import asdict
from pathlib import Path

from .bridge import UnityBridgeServer
from .cues import TEXTURES


def validate_packet(packet: object) -> dict:
    if not isinstance(packet, dict):
        raise ValueError("packet must be an object")
    limits = {"penetration_m": (0, .05), **{k: (-5, 5) for k in ("vx", "vy", "vz")},
              **{k: (-100, 100) for k in ("ax", "ay", "az")},
              **{k: (-1, 1) for k in ("nx", "ny", "nz")}}
    clean = {}
    for key, (low, high) in limits.items():
        default = 1.0 if key == "ny" else 0.0
        value = packet.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (float, int)):
            raise ValueError(f"{key} must be a number")
        value = float(value)
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"{key} outside finite bench envelope")
        clean[key] = value
    if sum(clean[k] ** 2 for k in ("nx", "ny", "nz")) < 1e-12:
        raise ValueError("surface normal cannot be zero")
    texture = packet.get("texture", "soft_tissue")
    if not isinstance(texture, str) or texture not in TEXTURES:
        raise ValueError("unknown texture")
    clean["texture"] = texture
    return clean


def encode_pwm(sequence: int, amplitude: float, max_pwm: int = 64) -> bytes:
    if isinstance(sequence, bool) or not isinstance(sequence, int) or not 0 <= sequence <= 2**31-1:
        raise ValueError("invalid sequence")
    if isinstance(amplitude, bool) or not math.isfinite(amplitude) or not 0 <= amplitude <= 1:
        raise ValueError("amplitude outside [0,1]")
    if isinstance(max_pwm, bool) or not isinstance(max_pwm, int) or not 0 <= max_pwm <= 64:
        raise ValueError("bench cap must be 0..64")
    return f"H1,{sequence},{round(amplitude * max_pwm)}\n".encode("ascii")


def decode_ack(line: bytes) -> dict:
    try:
        parts = line.decode("ascii").strip().split(",")
        if len(parts) != 5 or parts[0] != "A1":
            raise ValueError("bad ack shape")
        seq, pwm, adc, elapsed = map(int, parts[1:])
        if not (0 <= seq <= 2**31-1 and 0 <= pwm <= 64 and 0 <= adc <= 1023 and 0 <= elapsed <= 2**32-1):
            raise ValueError("ack outside protocol ranges")
        return {"sequence": seq, "applied_pwm": pwm, "adc_raw": adc, "device_ms": elapsed}
    except (UnicodeError, TypeError) as exc:
        raise ValueError("bad ack encoding") from exc


class BenchController:
    def __init__(self, stale_s: float = .1):
        if not math.isfinite(stale_s) or not 0 < stale_s <= .2:
            raise ValueError("stale timeout must be in (0, .2]")
        self.bridge = UnityBridgeServer()
        self.stale_s = stale_s
        self.last_received = None
        self.sequence = 0
        self.amplitude = 0.0

    def stop(self):
        self.amplitude = 0.0
        self.last_received = None
        self.bridge.safety.reset()
        self.bridge.inertial.reset()

    def receive(self, packet: object, now_s: float):
        try:
            if not math.isfinite(now_s) or now_s < 0:
                raise ValueError("invalid monotonic timestamp")
            if self.last_received is not None and now_s < self.last_received:
                raise ValueError("time cannot go backwards")
            clean = validate_packet(packet)
            # Reject non-contact inertia as a tactile contact command.
            if clean["penetration_m"] == 0:
                self.stop()
                clean.update(ax=0.0, ay=0.0, az=0.0)
            command = self.bridge.process_packet(clean, now_s)
            self.amplitude = command.vibration_amplitude
            self.last_received = now_s
            return command
        except (ValueError, TypeError):
            self.stop()
            raise

    def wire(self, now_s: float) -> bytes:
        if not math.isfinite(now_s):
            self.stop()
            raise ValueError("invalid timestamp")
        if self.last_received is None or not 0 <= now_s - self.last_received < self.stale_s:
            self.stop()
        self.sequence = (self.sequence + 1) % (2**31)
        return encode_pwm(self.sequence, self.amplitude)


def serve(output: str, seconds: float, port: int = 9051, serial_port: str | None = None,
          arm: bool = False):
    if not math.isfinite(seconds) or not 0 < seconds <= 300:
        raise ValueError("duration must be 0..300 seconds")
    if not 1024 <= port <= 65535:
        raise ValueError("invalid port")
    if serial_port and not arm:
        raise ValueError("physical serial needs --arm-bench after circuit review")
    if arm and not serial_port:
        raise ValueError("--arm-bench requires --serial-port")
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError("Choose a new output path; never overwrite evidence")
    controller = BenchController()
    serial = None
    try:
        if serial_port:
            import serial as pyserial
            serial = pyserial.Serial(serial_port, 115200, timeout=.03, write_timeout=.05)
            time.sleep(2)  # UNO bootloader reset; not a measured latency.
            serial.reset_input_buffer()
        with destination.open("x", newline="") as out, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", port))
            sock.setblocking(False)
            fields = ["data_class", "host_monotonic_s", "sequence", "requested_pwm",
                      "ack_status", "ack_pwm", "adc_raw", "device_ms", "serial_roundtrip_ms", "packet_status"]
            writer = csv.DictWriter(out, fields)
            writer.writeheader()
            start = next_tick = time.monotonic()
            while time.monotonic() - start < seconds:
                status = "no_packet"
                # Bounded drain keeps a local packet flood from starving watchdog updates.
                for _ in range(32):
                    try:
                        raw, _ = sock.recvfrom(4096)
                    except BlockingIOError:
                        break
                    try:
                        command = controller.receive(json.loads(raw.decode("utf-8")), time.monotonic())
                        sock.sendto(json.dumps(asdict(command), allow_nan=False).encode(), ("127.0.0.1", 9050))
                        status = "accepted"
                    except (ValueError, TypeError, UnicodeError):
                        controller.stop()
                        status = "rejected_stopped"
                        break
                now = time.monotonic()
                wire = controller.wire(now)
                _, seq, pwm = wire.decode().strip().split(",")
                row = dict(data_class="physical_serial_ack" if serial else "mock_no_hardware",
                           host_monotonic_s=now, sequence=seq, requested_pwm=pwm,
                           ack_status="not_applicable", packet_status=status)
                if serial:
                    t0 = time.perf_counter_ns()
                    serial.write(wire)
                    line = serial.readline()
                    elapsed = (time.perf_counter_ns() - t0) / 1e6
                    try:
                        ack = decode_ack(line)
                        if ack["sequence"] != int(seq):
                            raise ValueError("ack sequence mismatch")
                        row.update(ack_status="matched", ack_pwm=ack["applied_pwm"], adc_raw=ack["adc_raw"],
                                   device_ms=ack["device_ms"], serial_roundtrip_ms=elapsed)
                    except ValueError:
                        row["ack_status"] = "invalid_or_timeout_stopped"
                        writer.writerow(row)
                        raise RuntimeError("Serial acknowledgement failed; bench stopped")
                writer.writerow(row)
                out.flush()
                next_tick += .02  # Nominal 50 Hz transport, not a real-time guarantee.
                if next_tick < time.monotonic():
                    next_tick = time.monotonic()
                time.sleep(max(0, next_tick - time.monotonic()))
    finally:
        controller.stop()
        if serial:
            try:
                serial.write(controller.wire(time.monotonic()))
            finally:
                serial.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--seconds", type=float, default=30)
    p.add_argument("--port", type=int, default=9051)
    p.add_argument("--serial-port")
    p.add_argument("--arm-bench", action="store_true")
    a = p.parse_args()
    serve(a.output, a.seconds, a.port, a.serial_port, a.arm_bench)


if __name__ == "__main__":
    main()
