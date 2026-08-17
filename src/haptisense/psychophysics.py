"""Adaptive two-alternative forced-choice (2AFC) experiment utilities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import json
from math import exp
from pathlib import Path
import random
from statistics import mean, median


@dataclass(frozen=True, slots=True)
class Trial:
    participant_id: str
    modality: str
    trial_index: int
    reference: float
    comparison: float
    delta: float
    comparison_interval: int
    response_interval: int
    correct: bool
    reversal: bool
    synthetic: bool = True


class AdaptiveStaircase:
    """Two-down/one-up staircase for a 2AFC discrimination task."""

    def __init__(
        self,
        reference: float = 0.5,
        start_delta: float = 0.20,
        step: float = 0.025,
        min_delta: float = 0.005,
        max_delta: float = 0.40,
    ) -> None:
        if not 0 < min_delta <= start_delta <= max_delta:
            raise ValueError("delta bounds are inconsistent")
        self.reference = reference
        self.delta = start_delta
        self.step = step
        self.min_delta = min_delta
        self.max_delta = max_delta
        self.correct_streak = 0
        self.last_direction: int | None = None
        self.reversal_levels: list[float] = []

    def register(self, correct: bool) -> bool:
        direction = 0
        if correct:
            self.correct_streak += 1
            if self.correct_streak >= 2:
                direction = -1
                self.correct_streak = 0
        else:
            direction = 1
            self.correct_streak = 0

        reversal = bool(direction and self.last_direction and direction != self.last_direction)
        if reversal:
            self.reversal_levels.append(self.delta)
        if direction:
            self.delta = min(self.max_delta, max(self.min_delta, self.delta + direction * self.step))
            self.last_direction = direction
        return reversal

    def threshold(self, late_reversals: int = 8) -> float:
        levels = self.reversal_levels[-late_reversals:]
        return median(levels) if levels else self.delta


@dataclass(frozen=True, slots=True)
class SyntheticObserver:
    """Deterministic-with-seed observer used only to exercise the pipeline."""

    threshold: float
    slope: float = 0.018
    lapse_rate: float = 0.015

    def probability_correct(self, delta: float) -> float:
        logistic = 1.0 / (1.0 + exp(-(delta - self.threshold) / max(self.slope, 1e-9)))
        return min(1.0 - self.lapse_rate, 0.5 + 0.5 * logistic)


def run_synthetic_experiment(
    trials_per_modality: int = 72,
    seed: int = 255,
) -> tuple[list[Trial], dict[str, object]]:
    """Run visual and haptic staircases against explicitly synthetic observers."""

    if trials_per_modality < 12:
        raise ValueError("trials_per_modality must be at least 12")
    rng = random.Random(seed)
    observers = {
        "visual": SyntheticObserver(threshold=0.040, slope=0.014),
        "haptic": SyntheticObserver(threshold=0.068, slope=0.020),
    }
    records: list[Trial] = []
    modality_summary: dict[str, object] = {}

    for modality, observer in observers.items():
        staircase = AdaptiveStaircase()
        correct_count = 0
        for trial_index in range(1, trials_per_modality + 1):
            delta = staircase.delta
            interval = 1 if rng.random() < 0.5 else 2
            response_is_correct = rng.random() < observer.probability_correct(delta)
            response = interval if response_is_correct else 3 - interval
            reversal = staircase.register(response_is_correct)
            correct_count += int(response_is_correct)
            records.append(
                Trial(
                    participant_id="SYNTHETIC-001",
                    modality=modality,
                    trial_index=trial_index,
                    reference=staircase.reference,
                    comparison=staircase.reference + delta,
                    delta=delta,
                    comparison_interval=interval,
                    response_interval=response,
                    correct=response_is_correct,
                    reversal=reversal,
                )
            )

        modality_summary[modality] = {
            "estimated_threshold": round(staircase.threshold(), 6),
            "reversals": len(staircase.reversal_levels),
            "accuracy": round(correct_count / trials_per_modality, 6),
            "mean_late_reversal_level": round(mean(staircase.reversal_levels[-8:]), 6)
            if staircase.reversal_levels
            else None,
        }

    summary: dict[str, object] = {
        "data_class": "synthetic",
        "participant_id": "SYNTHETIC-001",
        "seed": seed,
        "design": "2AFC, two-down/one-up adaptive staircase",
        "trials_per_modality": trials_per_modality,
        "modalities": modality_summary,
        "warning": "Pipeline demonstration only; these are not human-subject results.",
    }
    return records, summary


def write_experiment_outputs(output_dir: str | Path, trials_per_modality: int = 72, seed: int = 255) -> dict[str, object]:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    trials, summary = run_synthetic_experiment(trials_per_modality, seed)
    with (path / "trials.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(trials[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(trial) for trial in trials)
    with (path / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    return summary
