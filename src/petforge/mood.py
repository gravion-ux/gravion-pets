"""Mood engine: four stats, event deltas, and a derived mood label."""

from __future__ import annotations

from dataclasses import dataclass, field

STATS = ("energy", "joy", "focus", "affection")

# How each agent event nudges the pet's stats.
EVENT_DELTAS: dict[str, dict[str, int]] = {
    "success": {"joy": 14, "energy": 6, "focus": 4, "affection": 3},
    "failure": {"joy": -10, "energy": -4, "focus": 8, "affection": 2},
    "idle": {"joy": -3, "energy": -8, "focus": -5, "affection": -2},
    "praise": {"joy": 12, "energy": 4, "focus": 0, "affection": 10},
}

# Passive drift applied by tick(): pets slowly settle toward calm.
TICK_DRIFT = {"energy": -2, "joy": -1, "focus": -1, "affection": 0}


def _clamp(value: int) -> int:
    return max(0, min(100, value))


@dataclass
class MoodEngine:
    """Mutable mood state for one adopted pet."""

    energy: int = 60
    joy: int = 60
    focus: int = 60
    affection: int = 60
    history: list[str] = field(default_factory=list)

    @classmethod
    def from_base(cls, base_stats: dict[str, int]) -> "MoodEngine":
        missing = [stat for stat in STATS if stat not in base_stats]
        if missing:
            raise ValueError(f"base_stats is missing required stat(s): {', '.join(missing)}")
        return cls(**{stat: _clamp(int(base_stats[stat])) for stat in STATS})

    def snapshot(self) -> dict[str, int]:
        return {stat: getattr(self, stat) for stat in STATS}

    def apply(self, event: str) -> str:
        """Apply an event's deltas and return the resulting mood label."""
        if event not in EVENT_DELTAS:
            raise ValueError(f"unknown event kind: {event!r}")
        for stat, delta in EVENT_DELTAS[event].items():
            setattr(self, stat, _clamp(getattr(self, stat) + delta))
        mood = self.mood
        self.history.append(mood)
        return mood

    def apply_deltas(self, stats: dict[str, int], energy_cost: int = 0) -> str:
        """Apply arbitrary stat deltas (an action's effects); return mood."""
        for stat, delta in stats.items():
            if stat not in STATS:
                raise ValueError(f"unknown stat: {stat!r}")
            setattr(self, stat, _clamp(getattr(self, stat) + delta))
        if energy_cost:
            self.energy = _clamp(self.energy - energy_cost)
        mood = self.mood
        self.history.append(mood)
        return mood

    def tick(self) -> str:
        """Let time pass: stats drift gently downward (pets get sleepy)."""
        for stat, delta in TICK_DRIFT.items():
            setattr(self, stat, _clamp(getattr(self, stat) + delta))
        return self.mood

    @property
    def mood(self) -> str:
        """Derive a single mood label from the current stats."""
        if self.energy <= 20:
            return "sleepy"
        if self.joy >= 85 and self.energy >= 60:
            return "ecstatic"
        if self.joy >= 70:
            return "happy"
        if self.focus >= 80 and self.joy >= 45:
            return "focused"
        if self.affection >= 85:
            return "devoted"
        if self.joy <= 25:
            return "downcast"
        if self.joy <= 45 and self.energy <= 45:
            return "bored"
        return "content"
