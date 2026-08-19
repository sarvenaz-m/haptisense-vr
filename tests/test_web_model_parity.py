import csv
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from haptisense.simulation import SCENARIOS, simulate_contact


ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is required for browser-model parity tests")
class WebModelParityTests(unittest.TestCase):
    @staticmethod
    def _node_json(script: str) -> object:
        completed = subprocess.run(
            [str(NODE), "-e", script],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_default_scenario_metrics_match_python(self) -> None:
        script = """
const model = require('./docs/assets/haptic-model.js');
const metrics = Object.fromEntries(
  Object.keys(model.presets).map((key) => [key, model.simulate({ presetKey: key }).metrics])
);
process.stdout.write(JSON.stringify(metrics));
"""
        browser = self._node_json(script)
        for preset, scenario in (
            ("soft", "soft_tissue"),
            ("fibrous", "fibrous_tissue"),
            ("membrane", "smooth_membrane"),
        ):
            parameters = SCENARIOS[scenario]
            _, python = simulate_contact(
                stiffness_n_m=float(parameters["stiffness_n_m"]),
                damping_n_s_m=float(parameters["damping_n_s_m"]),
                friction_coefficient=float(parameters["friction_coefficient"]),
                texture_name=str(parameters["texture_name"]),
                base_scan_speed_m_s=float(parameters["base_scan_speed_m_s"]),
            )
            web = browser[preset]
            self.assertEqual(web["samples"], python["samples"])
            self.assertEqual(web["sampleRate"], python["sample_rate_hz"])
            self.assertEqual(web["peak"], python["peak_command_force_n"])
            self.assertEqual(web["rms"], python["rms_command_force_n"])
            self.assertEqual(web["meanVibration"], python["mean_vibration_amplitude"])
            self.assertEqual(web["safetyEvents"], python["safety_event_samples"])

    def test_staircase_matches_committed_trials(self) -> None:
        script = """
const data = require('./docs/assets/psychophysics-data.js');
process.stdout.write(JSON.stringify(data));
"""
        browser = self._node_json(script)
        committed: dict[str, list[float]] = {"visual": [], "haptic": []}
        with (ROOT / "results" / "psychophysics" / "trials.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            for row in csv.DictReader(handle):
                committed[row["modality"]].append(float(row["delta"]))

        for modality in ("visual", "haptic"):
            self.assertEqual(len(browser[modality]), 72)
            for web_value, csv_value in zip(browser[modality], committed[modality]):
                self.assertAlmostEqual(web_value, csv_value, places=12)


if __name__ == "__main__":
    unittest.main()
