"""Stateful safety limits applied after scientific cue synthesis."""

from __future__ import annotations

from dataclasses import dataclass

from .cues import MultimodalCue, VibrotactileCue
from .force_models import Vec3


@dataclass(frozen=True, slots=True)
class SafetyEvent:
    force_clamped: bool = False
    slew_clamped: bool = False
    amplitude_clamped: bool = False
    frequency_clamped: bool = False

    @property
    def any(self) -> bool:
        return any((self.force_clamped, self.slew_clamped, self.amplitude_clamped, self.frequency_clamped))


@dataclass(slots=True)
class SafetyEnvelope:
    max_force_n: float = 6.0
    max_force_slew_n_s: float = 180.0
    max_vibration_amplitude: float = 0.85
    min_frequency_hz: float = 20.0
    max_frequency_hz: float = 250.0
    _previous_force: Vec3 = Vec3()

    def reset(self) -> None:
        self._previous_force = Vec3()

    def apply(self, cue: MultimodalCue, dt_s: float) -> tuple[MultimodalCue, SafetyEvent]:
        if dt_s <= 0:
            raise ValueError("dt_s must be positive")

        force_clamped = cue.force_n.norm() > self.max_force_n
        limited_force = cue.force_n.clamp_magnitude(self.max_force_n)
        delta = limited_force - self._previous_force
        max_delta = self.max_force_slew_n_s * dt_s
        slew_clamped = delta.norm() > max_delta
        limited_force = self._previous_force + delta.clamp_magnitude(max_delta)
        self._previous_force = limited_force

        amplitude = min(self.max_vibration_amplitude, max(0.0, cue.vibration.amplitude))
        frequency = min(self.max_frequency_hz, max(self.min_frequency_hz, cue.vibration.frequency_hz))
        event = SafetyEvent(
            force_clamped=force_clamped,
            slew_clamped=slew_clamped,
            amplitude_clamped=amplitude != cue.vibration.amplitude,
            frequency_clamped=frequency != cue.vibration.frequency_hz,
        )
        return (
            MultimodalCue(
                force_n=limited_force,
                vibration=VibrotactileCue(amplitude, frequency),
                contact_strength=cue.contact_strength,
            ),
            event,
        )
