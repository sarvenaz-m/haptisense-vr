"""Core models for the HaptiSense VR research prototype."""

from .cues import MultimodalCueSynthesizer, TextureProfile, VibrotactileCue
from .force_models import BodyGroundedInertialCue, ContactState, KelvinVoigtSurface, Vec3
from .safety import SafetyEnvelope

__all__ = [
    "BodyGroundedInertialCue",
    "ContactState",
    "KelvinVoigtSurface",
    "MultimodalCueSynthesizer",
    "SafetyEnvelope",
    "TextureProfile",
    "Vec3",
    "VibrotactileCue",
]

__version__ = "0.3.0"
