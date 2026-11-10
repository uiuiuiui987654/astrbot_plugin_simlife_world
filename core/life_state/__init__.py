"""A small physiological layer for the virtual life simulation.

The schedule already knows *what* the character is doing.  This module adds a
consistent, deterministic answer to *how she feels*: energy, fullness (饱腹),
cleanliness and mood.  Values are derived from the day's timeline up to the
current minute, so they change naturally with sleep, meals, washing, exercise,
focused work and rest without storing another mutable state file.

The result is intentionally compact and read-only: dialogue prompts and the
observation-window HUD can consume it, while schedule generation can keep
working as before.

Split into themed modules; ``compute`` is the public entry point.
"""
from .compute import compute

__all__ = ["compute"]
