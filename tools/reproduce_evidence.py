"""Generate reproducible computational evidence. Never hardware measurements."""
import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from haptisense.simulation import simulate_contact, write_demo_outputs, write_comparison_outputs
from haptisense.psychophysics import write_experiment_outputs


def main():
    p = argparse.ArgumentParser(); p.add_argument("--output", default="results/review_2026-09-05")
    dest = Path(p.parse_args().output)
    if dest.exists(): raise SystemExit("Output exists; use a new path to preserve evidence")
    dest.mkdir(parents=True)
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                         cwd=ROOT, env=env, capture_output=True, text=True)
    (dest / "tests.txt").write_text(run.stdout + run.stderr)
    if run.returncode: raise SystemExit("Tests failed; report not generated")
    write_demo_outputs(dest / "demo", 4, 500)
    write_comparison_outputs(dest / "comparison", 4, 500)
    write_experiment_outputs(dest / "psychophysics", 72, 255)
    for _ in range(3): simulate_contact(4, 500)
    durations = []
    for _ in range(30):
        start = time.perf_counter_ns(); simulate_contact(4, 500)
        durations.append((time.perf_counter_ns() - start) / 1e6)
    ordered = sorted(durations)
    result = {"data_class": "host_offline_computational_benchmark", "python": platform.python_version(),
              "platform": platform.platform(), "machine": platform.machine(), "repeats": 30, "warmups": 3,
              "samples_per_run": 2000, "simulation_step_s": .002,
              "median_ms_per_run": statistics.median(durations), "p95_ms_per_run": ordered[28],
              "min_ms_per_run": min(durations), "max_ms_per_run": max(durations),
              "median_us_per_sample_including_metrics": statistics.median(durations) * 1000 / 2000,
              "all_durations_ms": durations,
              "warning": "Batch timing including metrics. Not a periodic deadline test, Unity timing, serial latency, or physical actuator evidence."}
    (dest / "benchmark.json").write_text(json.dumps(result, indent=2) + "\n")
    checksums = {}
    for directory in (ROOT / "src", ROOT / "tests", ROOT / "firmware", ROOT / "unity", ROOT / "tools"):
        for f in sorted(directory.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                checksums[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    (dest / "source_sha256.json").write_text(json.dumps(checksums, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
