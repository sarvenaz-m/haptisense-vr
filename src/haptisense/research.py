"""Deterministic contact experiments with explicit units and verification scope.

The standard-linear-solid branch is integrated exactly for constant velocity
within each step. These are illustrative lumped models, not tissue fits or
actuator controllers. The browser implementation is independently parity-tested.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class ResearchConfig:
    model: str = "sls"
    stiffness: float = 650.0       # N/m, equilibrium stiffness
    damping: float = 7.0          # N.s/m, Kelvin branch only
    relaxation: float = 0.65      # Maxwell/equilibrium stiffness ratio
    tau: float = 0.25             # s
    nonlinear: float = 12000.0    # 1/m², cubic correction
    friction: float = 0.18
    roughness: float = 0.38
    spatial: float = 1500.0       # cycles/m
    depth: float = 0.006          # m
    speed: float = 0.035          # m/s, tangential
    rate: int = 500               # model samples/s
    duration: float = 4.0         # s
    force_limit: float = 6.0      # N, simulated command magnitude
    slew_limit: float = 180.0     # N/s

    def __post_init__(self):
        if self.model not in ("elastic", "kelvin", "sls"):
            raise ValueError("model must be elastic, kelvin or sls")
        bounds = {"stiffness": (1, 5000), "damping": (0, 100),
                  "relaxation": (0, 4), "tau": (0.01, 5),
                  "nonlinear": (0, 100000), "friction": (0, 1),
                  "roughness": (0, 1), "spatial": (100, 5000),
                  "depth": (0.0001, 0.012), "speed": (0, 0.15),
                  "rate": (100, 2000), "duration": (1, 12),
                  "force_limit": (0.1, 12), "slew_limit": (1, 1000)}
        for name, (low, high) in bounds.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be finite in [{low}, {high}]")
        if int(self.rate) != self.rate:
            raise ValueError("rate must be an integer")


def trajectory(t: float, config: ResearchConfig, protocol: str = "hold"):
    """Return penetration, its derivative and lateral position (SI units)."""
    u = t / config.duration
    if protocol == "hold":
        # Smooth approach, genuine stationary hold, smooth release.
        if u < 0.1 or u >= 0.9:
            fraction, derivative = 0.0, 0.0
        elif u < 0.3:
            p = (u - 0.1) / 0.2
            fraction = (1 - math.cos(math.pi * p)) / 2
            derivative = math.pi * math.sin(math.pi * p) / (0.4 * config.duration)
        elif u <= 0.65:
            fraction, derivative = 1.0, 0.0
        else:
            p = (u - 0.65) / 0.25
            fraction = (1 + math.cos(math.pi * p)) / 2
            derivative = -math.pi * math.sin(math.pi * p) / (0.5 * config.duration)
    elif protocol == "cycle":
        if u < 0.1 or u >= 0.9:
            fraction, derivative = 0.0, 0.0
        else:
            p = (u - 0.1) / 0.8
            fraction = math.sin(2 * math.pi * p) ** 2
            derivative = 2 * math.pi * math.sin(4 * math.pi * p) / (0.8 * config.duration)
    else:
        raise ValueError("protocol must be hold or cycle")
    return config.depth * fraction, config.depth * derivative, config.speed * t


class ResearchContact:
    def __init__(self, config: ResearchConfig):
        self.config = config
        self.memory = 0.0
        self.previous = (0.0, 0.0)

    def step(self, depth: float, velocity: float, lateral: float):
        c = self.config
        if not all(math.isfinite(v) for v in (depth, velocity, lateral)) or depth < 0 or depth > 0.02 or abs(velocity) > 1 or abs(lateral) > 1:
            self.memory, self.previous = 0.0, (0.0, 0.0)
            raise ValueError("contact input outside computational envelope")
        dt = 1 / c.rate
        elastic = c.stiffness * (depth + c.nonlinear * depth ** 3)
        viscous = c.damping * max(0.0, velocity) if c.model == "kelvin" else 0.0
        if depth <= 1e-12:
            self.memory, self.previous = 0.0, (0.0, 0.0)
            elastic = viscous = normal = friction = fx = fy = amplitude = frequency = 0.0
            limited = False
        else:
            a = math.exp(-dt / c.tau)
            self.memory = a * self.memory + c.stiffness * c.relaxation * c.tau * (1 - a) * velocity if c.model == "sls" else 0.0
            normal = max(0.0, elastic + viscous + self.memory)
            friction = -c.friction * normal * math.tanh(lateral / 0.004)
            norm = math.hypot(friction, normal)
            scale = min(1.0, c.force_limit / max(norm, 1e-12))
            target = (friction * scale, normal * scale)
            delta = (target[0] - self.previous[0], target[1] - self.previous[1])
            slew = min(1.0, c.slew_limit * dt / max(math.hypot(*delta), 1e-12))
            fx, fy = (self.previous[i] + delta[i] * slew for i in range(2))
            self.previous = (fx, fy)
            limited = scale < 1 or slew < 1
            amplitude = min(0.85, c.roughness * min(1, normal / 4) * min(1, abs(lateral) / 0.08))
            frequency = min(250.0, max(20.0, abs(lateral) * c.spatial)) if amplitude > 0 else 0.0
        return {"elastic_n": elastic, "viscous_n": viscous, "memory_n": self.memory,
                "normal_n": normal, "friction_n": friction, "fx_n": fx, "fy_n": fy,
                "command_n": math.hypot(fx, fy), "amplitude": amplitude,
                "frequency_hz": frequency, "limited": limited,
                "power_w": fx * lateral - fy * velocity}


def run_research(config: ResearchConfig | None = None, protocol: str = "hold"):
    c = config or ResearchConfig()
    if protocol not in ("hold", "cycle"):
        raise ValueError("protocol must be hold or cycle")
    contact = ResearchContact(c)
    rows = []
    for i in range(int(c.rate * c.duration) + 1):
        t = i / c.rate
        d, v, x = trajectory(t, c, protocol)
        rows.append({"t_s": t, "depth_m": d, "velocity_m_s": v, "x_m": x,
                     **contact.step(d, v, c.speed)})
    dt = 1 / c.rate
    metrics = {
        "samples": len(rows),
        "peak_command_n": max(r["command_n"] for r in rows),
        "rms_command_n": math.sqrt(sum(r["command_n"] ** 2 for r in rows) / len(rows)),
        "limited_samples": sum(r["limited"] for r in rows),
        "positive_command_work_j": sum(max(0, r["power_w"]) * dt for r in rows),
        "negative_command_work_j": sum(min(0, r["power_w"]) * dt for r in rows),
    }
    return {"schema": "haptisense.research.v1", "version": "0.3.0",
            "evidence": "synthetic_computational", "config": asdict(c),
            "protocol": protocol, "metrics": metrics, "rows": rows}


def write_research(output: str, config: ResearchConfig | None = None, protocol: str = "hold"):
    destination = Path(output)
    # A run is immutable by default; never silently erase earlier evidence.
    destination.mkdir(parents=True, exist_ok=False)
    result = run_research(config, protocol)
    (destination / "session.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    with (destination / "trace.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["rows"][0]))
        writer.writeheader()
        writer.writerows(result["rows"])
    comparisons = []
    for model in ("elastic", "kelvin", "sls"):
        run = run_research(replace(config or ResearchConfig(), model=model), protocol)
        comparisons.append({"model": model, **run["metrics"]})
    (destination / "comparison.json").write_text(json.dumps({
        "evidence": "synthetic_computational", "design": "same trajectory and shared parameters; model family varies",
        "results": comparisons}, indent=2) + "\n")
    return result["metrics"]
