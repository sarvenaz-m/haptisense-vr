import unittest

from haptisense.force_models import BodyGroundedInertialCue, ContactState, KelvinVoigtSurface, Vec3


class KelvinVoigtSurfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model = KelvinVoigtSurface(
            stiffness_n_m=500.0,
            damping_n_s_m=5.0,
            friction_coefficient=0.2,
        )

    def test_zero_penetration_has_zero_force(self) -> None:
        force = self.model.compute(ContactState(0.0, Vec3(0.1, -0.1, 0.0)))
        self.assertAlmostEqual(force.total.norm(), 0.0)

    def test_force_increases_with_penetration(self) -> None:
        shallow = self.model.compute(ContactState(0.001, Vec3()))
        deep = self.model.compute(ContactState(0.004, Vec3()))
        self.assertGreater(deep.normal_magnitude_n, shallow.normal_magnitude_n)

    def test_friction_opposes_tangential_motion(self) -> None:
        force = self.model.compute(ContactState(0.003, Vec3(0.1, 0.0, 0.0)))
        self.assertLess(force.friction.x, 0.0)
        self.assertAlmostEqual(force.friction.y, 0.0)

    def test_body_grounded_cue_opposes_acceleration(self) -> None:
        model = BodyGroundedInertialCue(effective_mass_kg=0.2, smoothing=1.0)
        force = model.compute(Vec3(2.0, 0.0, 0.0))
        self.assertLess(force.x, 0.0)
        self.assertAlmostEqual(force.norm(), 0.4)


if __name__ == "__main__":
    unittest.main()
