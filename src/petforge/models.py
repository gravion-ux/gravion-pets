"""Core data model for a petforge companion."""

from __future__ import annotations

from dataclasses import dataclass, field

CATEGORIES = ("anime", "animal", "human", "aquatic", "couples", "robot", "spirit", "plushie")
EVENT_KINDS = ("success", "failure", "idle", "praise")


@dataclass(frozen=True)
class Pet:
    """One immutable catalogue entry: personality core + appearance + voice."""

    id: str
    name: str
    category: str
    form: str
    tagline: str
    traits: tuple[str, ...]
    speech_style: str
    quirks: tuple[str, ...]
    favourite: str
    appearance: str  # ready-to-use image-generation prompt
    base_stats: dict[str, int] = field(default_factory=dict)
    reactions: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"unknown category {self.category!r} for pet {self.id!r}")
        for kind in EVENT_KINDS:
            if kind not in self.reactions or not self.reactions[kind]:
                raise ValueError(f"pet {self.id!r} is missing reactions for {kind!r}")
        for stat in ("energy", "joy", "focus", "affection"):
            if stat not in self.base_stats:
                raise ValueError(f"pet {self.id!r} is missing base stat {stat!r}")

    @classmethod
    def from_dict(cls, raw: dict) -> "Pet":
        return cls(
            id=raw["id"],
            name=raw["name"],
            category=raw["category"],
            form=raw["form"],
            tagline=raw["tagline"],
            traits=tuple(raw["traits"]),
            speech_style=raw["speech_style"],
            quirks=tuple(raw["quirks"]),
            favourite=raw["favourite"],
            appearance=raw["appearance"],
            base_stats=dict(raw["base_stats"]),
            reactions={k: tuple(v) for k, v in raw["reactions"].items()},
        )

    def image_prompt(self, extra: str = "") -> str:
        """Appearance descriptor as a self-contained image-gen prompt."""
        prompt = self.appearance
        return f"{prompt}. {extra}".strip() if extra else prompt
