import unittest

from haptisense.bridge import UnityBridgeServer
from haptisense.simulation import SCENARIOS, simulate_contact


class SimulationAndBridgeTests(unittest.TestCase):
    def test_simulation_is_deterministic(self) -> None:
        samples_a, metrics_a = simulate_contact(duration_s=1.2, sample_rate_hz=200)
        samples_b, metrics_b = simulate_contact(duration_s=1.2, sample_rate_hz=200)
        self.assertEqual(samples_a, samples_b)
        self.assertEqual(metrics_a, metrics_b)
        self.assertGreater(metrics_a["peak_command_force_n"], 0.0)

    def test_bridge_packet_is_bounded(self) -> None:
        bridge = UnityBridgeServer()
        command = bridge.process_packet(
            {
                "penetration_m": 0.02,
                "vx": 0.1,
                "vy": -0.2,
                "vz": 0.0,
                "nx": 0.0,
                "ny": 1.0,
                "nz": 0.0,
                "ax": 2.0,
                "ay": 0.0,
                "az": 0.0,
                "texture": "fibrous_tissue",
            },
            now_s=bridge.last_time + 0.01,
        )
        magnitude = (command.fx**2 + command.fy**2 + command.fz**2) ** 0.5
        self.assertLessEqual(magnitude, bridge.safety.max_force_n)
        self.assertLessEqual(command.vibration_amplitude, bridge.safety.max_vibration_amplitude)

    def test_scenarios_produce_distinct_force_profiles(self) -> None:
        peaks = []
        for parameters in SCENARIOS.values():
            _, metrics = simulate_contact(
                duration_s=1.2,
                sample_rate_hz=200,
                stiffness_n_m=float(parameters["stiffness_n_m"]),
                damping_n_s_m=float(parameters["damping_n_s_m"]),
                friction_coefficient=float(parameters["friction_coefficient"]),
                texture_name=str(parameters["texture_name"]),
                base_scan_speed_m_s=float(parameters["base_scan_speed_m_s"]),
            )
            peaks.append(metrics["peak_command_force_n"])
        self.assertEqual(len(set(peaks)), len(SCENARIOS))


if __name__ == "__main__":
    unittest.main()
