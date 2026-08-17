"""Multimodal synthesis of kinesthetic and cutaneous cues."""

from __future__ import annotations

from dataclasses import dataclass

from .force_models import Vec3


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


@dataclass(frozen=True, slots=True)
class TextureProfile:
    name: str
    roughness: float
    spatial_frequency_cycles_m: float
    amplitude_gain: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.roughness <= 1.0:
            raise ValueError("roughness must be in [0, 1]")
        if self.spatial_frequency_cycles_m <= 0:
            raise ValueError("spatial_frequency_cycles_m must be positive")
        if self.amplitude_gain < 0:
            raise ValueError("amplitude_gain must be non-negative")


@dataclass(frozen=True, slots=True)
class VibrotactileCue:
    amplitude: float
    frequency_hz: float


@dataclass(frozen=True, slots=True)
class MultimodalCue:
    force_n: Vec3
    vibration: VibrotactileCue
    contact_strength: float


@dataclass(slots=True)
class MultimodalCueSynthesizer:
    """Map force, texture, and scan speed into a coherent haptic command."""

    reference_force_n: float = 4.0
    min_frequency_hz: float = 20.0
    max_frequency_hz: float = 250.0
    speed_for_full_amplitude_m_s: float = 0.08

    def synthesize(
        self,
        force_n: Vec3,
        tangential_speed_m_s: float,
        texture: TextureProfile,
    ) -> MultimodalCue:
        contact_strength = _clamp(force_n.norm() / max(self.reference_force_n, 1e-9), 0.0, 1.0)
        if force_n.norm() <= 1e-12:
            return MultimodalCue(force_n, VibrotactileCue(0.0, self.min_frequency_hz), 0.0)

        speed_factor = _clamp(
            tangential_speed_m_s / max(self.speed_for_full_amplitude_m_s, 1e-9),
            0.0,
            1.0,
        )
        frequency = _clamp(
            tangential_speed_m_s * texture.spatial_frequency_cycles_m,
            self.min_frequency_hz,
            self.max_frequency_hz,
        )
        amplitude = _clamp(
            texture.roughness
            * texture.amplitude_gain
            * (0.2 + 0.8 * contact_strength)
            * (0.15 + 0.85 * speed_factor),
            0.0,
            1.0,
        )
        return MultimodalCue(force_n, VibrotactileCue(amplitude, frequency), contact_strength)


TEXTURES: dict[str, TextureProfile] = {
    "soft_tissue": TextureProfile("soft_tissue", 0.38, 1_500.0, 0.82),
    "fibrous_tissue": TextureProfile("fibrous_tissue", 0.72, 2_200.0, 0.95),
    "smooth_membrane": TextureProfile("smooth_membrane", 0.16, 900.0, 0.60),
}
