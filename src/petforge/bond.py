"""Bond / level system: shared work deepens the agent<->pet bond."""

from __future__ import annotations

from dataclasses import dataclass

# XP needed to *reach* each level (index = level).
LEVEL_XP = (0, 20, 55, 110, 190, 300, 450, 650)

LEVEL_TITLES = (
    "Newly Met",
    "Warming Up",
    "Trusted Sidekick",
    "Close Companion",
    "Best Friend",
    "Partner in Crime",
    "Family",
    "Soulbound",
)

# Bond XP earned per event kind: showing up counts, winning counts more,
# and sticking around after a failure counts most of all.
EVENT_XP = {"success": 12, "failure": 9, "praise": 7, "idle": 2}


@dataclass
class Bond:
    xp: int = 0

    @property
    def level(self) -> int:
        level = 0
        for idx, needed in enumerate(LEVEL_XP):
            if self.xp >= needed:
                level = idx
        return level

    @property
    def title(self) -> str:
        return LEVEL_TITLES[self.level]

    @property
    def xp_into_level(self) -> int:
        return self.xp - LEVEL_XP[self.level]

    @property
    def xp_to_next(self) -> int | None:
        """XP still needed for the next level, or None at max level."""
        if self.level >= len(LEVEL_XP) - 1:
            return None
        return LEVEL_XP[self.level + 1] - self.xp

    def gain(self, event: str) -> tuple[int, bool]:
        """Add XP for an event. Returns (xp_gained, levelled_up)."""
        if event not in EVENT_XP:
            raise ValueError(f"unknown event kind: {event!r}")
        return self.gain_amount(EVENT_XP[event])

    def gain_amount(self, amount: int) -> tuple[int, bool]:
        """Add an arbitrary XP amount (e.g. an action's bond_xp)."""
        if amount < 0:
            raise ValueError("bond XP gain cannot be negative")
        before = self.level
        self.xp += amount
        return amount, self.level > before
