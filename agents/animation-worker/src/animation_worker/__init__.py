"""
Animation Worker Agent.

Autonomous worker agent for creating Roblox animations using Claude Agent SDK
with Gemini vision analysis for quality verification.
"""

from .agent import AnimationWorkerAgent
from .models import AnimationPhase, AnimationWorkerConfig, AnimationWorkerStatus

__all__ = [
    "AnimationWorkerAgent",
    "AnimationPhase",
    "AnimationWorkerConfig",
    "AnimationWorkerStatus",
]
