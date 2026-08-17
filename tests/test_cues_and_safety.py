import unittest

from haptisense.cues import MultimodalCue, MultimodalCueSynthesizer, TextureProfile, VibrotactileCue
from haptisense.force_models import Vec3
from haptisense.safety import SafetyEnvelope


class CueAndSafetyTests(unittest.TestCase):
    def test_no_force_produces_no_vibration(self) -> None:
        synthesizer = MultimodalCueSynthesizer()
        texture = TextureProfile("test", 0.8, 1000.0)
        cue = synthesizer.synthesize(Vec3(), 0.1, texture)
        self.assertEqual(cue.vibration.amplitude, 0.0)

    def test_roughness_increases_amplitude(self) -> None:
        synthesizer = MultimodalCueSynthesizer()
        smooth = TextureProfile("smooth", 0.1, 1000.0)
        rough = TextureProfile("rough", 0.9, 1000.0)
        force = Vec3(0.0, 2.0, 0.0)
        self.assertGreater(
            synthesizer.synthesize(force, 0.05, rough).vibration.amplitude,
            synthesizer.synthesize(force, 0.05, smooth).vibration.amplitude,
        )

    def test_safety_envelope_clamps_force_and_amplitude(self) -> None:
        envelope = SafetyEnvelope(max_force_n=2.0, max_force_slew_n_s=10_000.0, max_vibration_amplitude=0.8)
        unsafe = MultimodalCue(Vec3(0.0, 8.0, 0.0), VibrotactileCue(1.2, 400.0), 1.0)
        safe, event = envelope.apply(unsafe, 0.01)
        self.assertLessEqual(safe.force_n.norm(), 2.0)
        self.assertEqual(safe.vibration.amplitude, 0.8)
        self.assertEqual(safe.vibration.frequency_hz, 250.0)
        self.assertTrue(event.force_clamped)
        self.assertTrue(event.amplitude_clamped)
        self.assertTrue(event.frequency_clamped)


if __name__ == "__main__":
    unittest.main()
