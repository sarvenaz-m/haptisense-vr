import unittest

from haptisense.psychophysics import AdaptiveStaircase, run_synthetic_experiment


class PsychophysicsTests(unittest.TestCase):
    def test_two_correct_responses_make_task_harder(self) -> None:
        staircase = AdaptiveStaircase(start_delta=0.2, step=0.025)
        staircase.register(True)
        self.assertAlmostEqual(staircase.delta, 0.2)
        staircase.register(True)
        self.assertAlmostEqual(staircase.delta, 0.175)

    def test_error_makes_task_easier_and_records_reversal(self) -> None:
        staircase = AdaptiveStaircase(start_delta=0.2, step=0.025)
        staircase.register(True)
        staircase.register(True)
        reversed_now = staircase.register(False)
        self.assertTrue(reversed_now)
        self.assertGreater(staircase.delta, 0.175)

    def test_synthetic_experiment_is_reproducible(self) -> None:
        trials_a, summary_a = run_synthetic_experiment(trials_per_modality=40, seed=9)
        trials_b, summary_b = run_synthetic_experiment(trials_per_modality=40, seed=9)
        self.assertEqual(trials_a, trials_b)
        self.assertEqual(summary_a, summary_b)
        self.assertEqual(summary_a["data_class"], "synthetic")


if __name__ == "__main__":
    unittest.main()
