"""Deterministic surgical-contact simulation and reviewer-friendly outputs."""

from __future__ import annotations

import csv
import json
from math import cos, pi, sin, sqrt
from pathlib import Path
from statistics import mean

from .cues import MultimodalCueSynthesizer, TEXTURES
from .force_models import BodyGroundedInertialCue, ContactState, KelvinVoigtSurface, Vec3
from .safety import SafetyEnvelope


def simulate_contact(
    duration_s: float = 4.0,
    sample_rate_hz: int = 500,
    *,
    stiffness_n_m: float = 650.0,
    damping_n_s_m: float = 7.0,
    friction_coefficient: float = 0.18,
    texture_name: str = "soft_tissue",
    base_scan_speed_m_s: float = 0.035,
) -> tuple[list[dict[str, float]], dict[str, object]]:
    if duration_s <= 0 or sample_rate_hz < 100:
        raise ValueError("duration must be positive and sample rate at least 100 Hz")

    if texture_name not in TEXTURES:
        raise ValueError(f"unknown texture: {texture_name}")
    surface = KelvinVoigtSurface(
        stiffness_n_m=stiffness_n_m,
        damping_n_s_m=damping_n_s_m,
        friction_coefficient=friction_coefficient,
    )
    inertial = BodyGroundedInertialCue()
    synthesizer = MultimodalCueSynthesizer()
    safety = SafetyEnvelope()
    texture = TEXTURES[texture_name]
    dt = 1.0 / sample_rate_hz
    samples: list[dict[str, float]] = []
    safety_events = 0

    for index in range(int(duration_s * sample_rate_hz)):
        time_s = index * dt
        active = 0.45 <= time_s <= duration_s - 0.30
        phase = 2.0 * pi * 0.62 * max(0.0, time_s - 0.45)
        raw_penetration = 0.0042 + 0.0028 * sin(phase) if active else 0.0
        penetration = max(0.0, raw_penetration)
        penetration_rate = 0.0028 * 2.0 * pi * 0.62 * cos(phase) if active else 0.0
        lateral_speed = base_scan_speed_m_s + 0.012 * sin(2.0 * pi * 0.35 * time_s) if active else 0.0
        velocity = Vec3(lateral_speed, -penetration_rate, 0.0)
        acceleration = Vec3(
            0.012 * 2.0 * pi * 0.35 * cos(2.0 * pi * 0.35 * time_s),
            0.0028 * (2.0 * pi * 0.62) ** 2 * sin(phase) if active else 0.0,
            0.0,
        )

        contact = surface.compute(ContactState(penetration, velocity))
        substrate_free = inertial.compute(acceleration) if active else Vec3()
        combined_force = contact.total * 0.82 + substrate_free * 0.18
        tangential_speed = Vec3(lateral_speed, 0.0, 0.0).norm()
        raw_cue = synthesizer.synthesize(combined_force, tangential_speed, texture)
        safe_cue, event = safety.apply(raw_cue, dt)
        safety_events += int(event.any)
        samples.append(
            {
                "time_s": time_s,
                "penetration_mm": penetration * 1_000.0,
                "contact_force_n": contact.total.norm(),
                "inertial_force_n": substrate_free.norm(),
                "command_force_n": safe_cue.force_n.norm(),
                "vibration_amplitude": safe_cue.vibration.amplitude,
                "vibration_frequency_hz": safe_cue.vibration.frequency_hz,
                "contact_strength": safe_cue.contact_strength,
            }
        )

    forces = [row["command_force_n"] for row in samples]
    amplitudes = [row["vibration_amplitude"] for row in samples]
    metrics: dict[str, object] = {
        "data_class": "deterministic simulation",
        "duration_s": duration_s,
        "sample_rate_hz": sample_rate_hz,
        "samples": len(samples),
        "texture": texture.name,
        "parameters": {
            "stiffness_n_m": stiffness_n_m,
            "damping_n_s_m": damping_n_s_m,
            "friction_coefficient": friction_coefficient,
            "base_scan_speed_m_s": base_scan_speed_m_s,
        },
        "peak_command_force_n": round(max(forces), 6),
        "rms_command_force_n": round(sqrt(mean(value * value for value in forces)), 6),
        "mean_vibration_amplitude": round(mean(amplitudes), 6),
        "safety_event_samples": safety_events,
        "warning": "Synthetic model output; not device calibration or participant evidence.",
    }
    return samples, metrics


def _write_svg(samples: list[dict[str, float]], output_path: Path) -> None:
    width, height = 1_120, 440
    left, right, top, bottom = 72, 28, 38, 62
    plot_w, plot_h = width - left - right, height - top - bottom
    max_time = samples[-1]["time_s"] or 1.0
    max_force = max(row["command_force_n"] for row in samples) or 1.0

    def points(key: str, scale_max: float) -> str:
        stride = max(1, len(samples) // 900)
        coords = []
        for row in samples[::stride]:
            x = left + plot_w * row["time_s"] / max_time
            y = top + plot_h * (1.0 - row[key] / scale_max)
            coords.append(f"{x:.1f},{y:.1f}")
        return " ".join(coords)

    force_points = points("command_force_n", max_force * 1.05)
    vibration_points = points("vibration_amplitude", 1.0)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<rect width="100%" height="100%" rx="16" fill="#F6FAFB"/>
<text x="{left}" y="25" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#17324D">Synthetic multimodal haptic profile</text>
<line x1="{left}" y1="{top + plot_h}" x2="{width-right}" y2="{top + plot_h}" stroke="#9BB3BD"/>
<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}" stroke="#9BB3BD"/>
<polyline fill="none" stroke="#007C83" stroke-width="3" points="{force_points}"/>
<polyline fill="none" stroke="#ED6A5A" stroke-width="2.4" points="{vibration_points}"/>
<text x="{left}" y="{height-20}" font-family="Arial, sans-serif" font-size="13" fill="#4A6472">Time (s)</text>
<text transform="translate(18 {top + plot_h/2}) rotate(-90)" font-family="Arial, sans-serif" font-size="13" fill="#4A6472">Normalised display scale</text>
<line x1="{width-292}" y1="24" x2="{width-262}" y2="24" stroke="#007C83" stroke-width="3"/>
<text x="{width-254}" y="29" font-family="Arial, sans-serif" font-size="12" fill="#17324D">safe force</text>
<line x1="{width-155}" y1="24" x2="{width-125}" y2="24" stroke="#ED6A5A" stroke-width="3"/>
<text x="{width-117}" y="29" font-family="Arial, sans-serif" font-size="12" fill="#17324D">vibration</text>
<text x="{width-318}" y="{height-18}" font-family="Arial, sans-serif" font-size="11" fill="#708993">Simulation only — no participant or device data</text>
</svg>'''
    output_path.write_text(svg, encoding="utf-8")


def write_demo_outputs(output_dir: str | Path, duration_s: float = 4.0, sample_rate_hz: int = 500) -> dict[str, object]:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    samples, metrics = simulate_contact(duration_s, sample_rate_hz)
    with (path / "haptic_trace.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(samples[0].keys()))
        writer.writeheader()
        writer.writerows(samples)
    with (path / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
        handle.write("\n")
    _write_svg(samples, path / "haptic_profile.svg")
    return metrics


SCENARIOS: dict[str, dict[str, float | str]] = {
    "soft_tissue": {
        "stiffness_n_m": 650.0,
        "damping_n_s_m": 7.0,
        "friction_coefficient": 0.18,
        "texture_name": "soft_tissue",
        "base_scan_speed_m_s": 0.035,
    },
    "fibrous_tissue": {
        "stiffness_n_m": 950.0,
        "damping_n_s_m": 11.0,
        "friction_coefficient": 0.26,
        "texture_name": "fibrous_tissue",
        "base_scan_speed_m_s": 0.042,
    },
    "smooth_membrane": {
        "stiffness_n_m": 1_200.0,
        "damping_n_s_m": 5.0,
        "friction_coefficient": 0.12,
        "texture_name": "smooth_membrane",
        "base_scan_speed_m_s": 0.028,
    },
}


def write_comparison_outputs(
    output_dir: str | Path,
    duration_s: float = 4.0,
    sample_rate_hz: int = 500,
) -> dict[str, object]:
    """Run the same trajectory across three virtual-tissue scenarios."""

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    scenarios: dict[str, object] = {}
    for name, parameters in SCENARIOS.items():
        _, metrics = simulate_contact(
            duration_s,
            sample_rate_hz,
            stiffness_n_m=float(parameters["stiffness_n_m"]),
            damping_n_s_m=float(parameters["damping_n_s_m"]),
            friction_coefficient=float(parameters["friction_coefficient"]),
            texture_name=str(parameters["texture_name"]),
            base_scan_speed_m_s=float(parameters["base_scan_speed_m_s"]),
        )
        scenarios[name] = metrics
        rows.append(
            {
                "scenario": name,
                "stiffness_n_m": parameters["stiffness_n_m"],
                "damping_n_s_m": parameters["damping_n_s_m"],
                "friction_coefficient": parameters["friction_coefficient"],
                "base_scan_speed_m_s": parameters["base_scan_speed_m_s"],
                "peak_command_force_n": metrics["peak_command_force_n"],
                "rms_command_force_n": metrics["rms_command_force_n"],
                "mean_vibration_amplitude": metrics["mean_vibration_amplitude"],
                "safety_event_samples": metrics["safety_event_samples"],
            }
        )

    summary: dict[str, object] = {
        "data_class": "deterministic scenario comparison",
        "duration_s": duration_s,
        "sample_rate_hz": sample_rate_hz,
        "scenarios": scenarios,
        "warning": "Synthetic model output; not tissue, device, or participant validation.",
    }
    with (path / "scenario_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (path / "scenario_comparison.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return summary
