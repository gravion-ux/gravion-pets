"""Core data model for a petforge companion."""

from __future__ import annotations

from dataclasses import dataclass, field

CATEGORIES = (
    "anime", "animal", "human", "aquatic", "couples",
    "robot", "spirit", "plushie", "gods", "devils",
)
EVENT_KINDS = ("success", "failure", "idle", "praise")
STATS = ("energy", "joy", "focus", "affection")


@dataclass(frozen=True)
class Action:
    """One thing a pet can DO: description + animation prompt + effects.

    ``animation`` is an image-to-video style motion prompt (what moves,
    how, and whether it loops) so a pet can later be animated into video.
    ``effects`` carries stat deltas under ``stats``, a ``bond_xp`` gain
    and an ``energy_cost`` that is spent on top of the stat deltas.
    """

    id: str
    name: str
    description: str
    animation: str
    loop: bool = False
    category: str | None = None  # None = shared by every pet
    stats: dict[str, int] = field(default_factory=dict)
    bond_xp: int = 0
    energy_cost: int = 0

    def __post_init__(self) -> None:
        if self.category is not None and self.category not in CATEGORIES:
            raise ValueError(f"unknown action category {self.category!r}")
        for stat in self.stats:
            if stat not in STATS:
                raise ValueError(f"action {self.id!r} touches unknown stat {stat!r}")
        if self.energy_cost < 0 or self.bond_xp < 0:
            raise ValueError(f"action {self.id!r} has negative bond_xp/energy_cost")

    @classmethod
    def from_dict(cls, raw: dict) -> "Action":
        effects = raw.get("effects", {})
        return cls(
            id=raw["id"],
            name=raw["name"],
            description=raw["description"],
            animation=raw["animation"],
            loop=bool(raw.get("loop", False)),
            category=raw.get("category"),
            stats=dict(effects.get("stats", {})),
            bond_xp=int(effects.get("bond_xp", 0)),
            energy_cost=int(effects.get("energy_cost", 0)),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "animation": self.animation,
            "loop": self.loop,
            "effects": {
                "stats": dict(self.stats),
                "bond_xp": self.bond_xp,
                "energy_cost": self.energy_cost,
            },
        }


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
    actions: tuple[str, ...] = ()  # ids into the shared action library
    signature_move: Action | None = None  # this pet's one unique action

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"unknown category {self.category!r} for pet {self.id!r}")
        for kind in EVENT_KINDS:
            if kind not in self.reactions or not self.reactions[kind]:
                raise ValueError(f"pet {self.id!r} is missing reactions for {kind!r}")
        for stat in STATS:
            if stat not in self.base_stats:
                raise ValueError(f"pet {self.id!r} is missing base stat {stat!r}")
        if self.signature_move is not None and self.signature_move.id in self.actions:
            raise ValueError(
                f"pet {self.id!r} lists its signature move in its library actions"
            )

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
            actions=tuple(raw.get("actions", ())),
            signature_move=(
                Action.from_dict(raw["signature_move"])
                if raw.get("signature_move")
                else None
            ),
        )

    def image_prompt(self, extra: str = "") -> str:
        """Appearance descriptor as a self-contained image-gen prompt."""
        prompt = self.appearance
        return f"{prompt}. {extra}".strip() if extra else prompt

    def can(self, action_id: str) -> bool:
        """True if ``action_id`` is in this pet's repertoire."""
        if self.signature_move is not None and action_id == self.signature_move.id:
            return True
        return action_id in self.actions

    def repertoire_ids(self) -> tuple[str, ...]:
        """Every performable action id: library actions + signature move."""
        ids = list(self.actions)
        if self.signature_move is not None:
            ids.append(self.signature_move.id)
        return tuple(ids)
