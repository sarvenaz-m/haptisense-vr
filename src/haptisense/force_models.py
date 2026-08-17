"""Physics models for compliant contact and body-grounded inertial cues.

The models use SI units. They are intentionally deterministic and independent
of any game engine or proprietary haptic SDK.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "Vec3":
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    __rmul__ = __mul__

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def norm(self) -> float:
        return sqrt(self.dot(self))

    def normalized(self) -> "Vec3":
        magnitude = self.norm()
        return Vec3() if magnitude <= 1e-12 else self * (1.0 / magnitude)

    def clamp_magnitude(self, maximum: float) -> "Vec3":
        if maximum < 0:
            raise ValueError("maximum must be non-negative")
        magnitude = self.norm()
        return self if magnitude <= maximum or magnitude <= 1e-12 else self * (maximum / magnitude)


@dataclass(frozen=True, slots=True)
class ContactState:
    """Instantaneous state of a virtual tool relative to a surface."""

    penetration_m: float
    velocity_m_s: Vec3
    surface_normal: Vec3 = Vec3(0.0, 1.0, 0.0)

    def __post_init__(self) -> None:
        if self.penetration_m < 0:
            raise ValueError("penetration_m must be non-negative")
        if self.surface_normal.norm() <= 1e-12:
            raise ValueError("surface_normal must be non-zero")


@dataclass(frozen=True, slots=True)
class ContactForce:
    total: Vec3
    normal: Vec3
    friction: Vec3
    normal_magnitude_n: float


@dataclass(slots=True)
class KelvinVoigtSurface:
    """Compliant normal contact with regularized Coulomb friction.

    ``stiffness_n_m`` models elasticity and ``damping_n_s_m`` dissipates
    energy while the tool moves into the surface. Friction is regularized near
    zero tangential speed to avoid discontinuous commands.
    """

    stiffness_n_m: float = 650.0
    damping_n_s_m: float = 7.0
    friction_coefficient: float = 0.18
    friction_regularization_m_s: float = 0.004

    def compute(self, state: ContactState) -> ContactForce:
        if state.penetration_m <= 0.0:
            zero = Vec3()
            return ContactForce(zero, zero, zero, 0.0)

        normal = state.surface_normal.normalized()
        signed_normal_speed = state.velocity_m_s.dot(normal)
        speed_into_surface = max(0.0, -signed_normal_speed)
        normal_magnitude = max(
            0.0,
            self.stiffness_n_m * state.penetration_m
            + self.damping_n_s_m * speed_into_surface,
        )
        normal_force = normal * normal_magnitude

        tangential_velocity = state.velocity_m_s - normal * signed_normal_speed
        tangential_speed = tangential_velocity.norm()
        regularized_scale = min(
            1.0,
            tangential_speed / max(self.friction_regularization_m_s, 1e-9),
        )
        friction_magnitude = self.friction_coefficient * normal_magnitude * regularized_scale
        friction_force = -tangential_velocity.normalized() * friction_magnitude
        return ContactForce(
            total=normal_force + friction_force,
            normal=normal_force,
            friction=friction_force,
            normal_magnitude_n=normal_magnitude,
        )


@dataclass(slots=True)
class BodyGroundedInertialCue:
    """Approximate a reaction cue from controller/hand acceleration.

    A moving mass produces an apparent reaction ``-m*a``. A one-pole filter
    limits high-frequency noise before a safety clamp is applied. This is a
    model for research prototyping, not a calibrated actuator controller.
    """

    effective_mass_kg: float = 0.12
    smoothing: float = 0.22
    max_force_n: float = 4.0
    _filtered_force: Vec3 = Vec3()

    def reset(self) -> None:
        self._filtered_force = Vec3()

    def compute(self, acceleration_m_s2: Vec3) -> Vec3:
        if not 0.0 < self.smoothing <= 1.0:
            raise ValueError("smoothing must be in (0, 1]")
        target = -acceleration_m_s2 * self.effective_mass_kg
        self._filtered_force = (
            self._filtered_force * (1.0 - self.smoothing) + target * self.smoothing
        ).clamp_magnitude(self.max_force_n)
        return self._filtered_force
