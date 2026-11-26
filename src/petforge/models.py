"""Core data model for a petforge companion."""

from __future__ import annotations

from dataclasses import dataclass, field

CATEGORIES = (
    "anime", "animal", "human", "aquatic", "couples",
    "robot", "spirit", "plushie", "gods", "devils",
)
EVENT_KINDS = ("success", "failure", "idle", "praise")
STATS = ("energy", "joy", "focus", "affection")

# Mythology / culture families the catalogue draws from (schema v4).
CULTURES = (
    "greek", "roman", "norse", "egyptian", "mesopotamian", "persian",
    "arabian", "indian", "chinese", "japanese", "korean", "thai",
    "vietnamese", "filipino", "celtic", "slavic", "european-folklore",
    "aztec", "mayan", "native-american", "inuit", "african",
    "polynesian", "aboriginal-australian", "arthurian", "global-modern",
)

# Primary body plan of a pet (every pet also has an orb face form).
FORM_TYPES = ("orb", "humanoid", "anime", "creature", "plush", "robot", "duo")

EVOLUTION_STAGES = (1, 2, 3)


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
    culture: str | None = None  # set for culture signature moves
    unlock_stage: int = 1  # evolution stage needed to perform it
    stats: dict[str, int] = field(default_factory=dict)
    bond_xp: int = 0
    energy_cost: int = 0

    def __post_init__(self) -> None:
        if self.category is not None and self.category not in CATEGORIES:
            raise ValueError(f"unknown action category {self.category!r}")
        if self.culture is not None and self.culture not in CULTURES:
            raise ValueError(f"unknown action culture {self.culture!r}")
        if self.unlock_stage not in EVOLUTION_STAGES:
            raise ValueError(
                f"action {self.id!r} has bad unlock_stage {self.unlock_stage!r}"
            )
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
            culture=raw.get("culture"),
            unlock_stage=int(raw.get("unlock_stage", 1)),
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
            "culture": self.culture,
            "unlock_stage": self.unlock_stage,
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
    orb: dict = field(default_factory=dict)  # orb face spec: palette/face/glow/prompt
    culture: str = "global-modern"  # mythology family (schema v4)
    form_type: str = "creature"  # primary body plan (schema v4)
    evolution: dict = field(default_factory=dict)  # stage thresholds/titles (v4)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"unknown category {self.category!r} for pet {self.id!r}")
        if self.culture not in CULTURES:
            raise ValueError(f"unknown culture {self.culture!r} for pet {self.id!r}")
        if self.form_type not in FORM_TYPES:
            raise ValueError(
                f"unknown form_type {self.form_type!r} for pet {self.id!r}"
            )
        stage2_xp = int(self.evolution.get("stage2_xp", 150))
        stage3_xp = int(self.evolution.get("stage3_xp", 400))
        if not 0 < stage2_xp < stage3_xp:
            raise ValueError(f"pet {self.id!r} has bad evolution thresholds")
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
            orb=dict(raw.get("orb", {})),
            culture=raw.get("culture", "global-modern"),
            form_type=raw.get("form_type", "creature"),
            evolution=dict(raw.get("evolution", {})),
        )

    # -- evolution (schema v4) -------------------------------------------
    @property
    def stage2_xp(self) -> int:
        return int(self.evolution.get("stage2_xp", 150))

    @property
    def stage3_xp(self) -> int:
        return int(self.evolution.get("stage3_xp", 400))

    def evolution_stage(self, xp: int) -> int:
        """Stage 1/2/3 for a companion with ``xp`` bond XP."""
        if xp >= self.stage3_xp:
            return 3
        if xp >= self.stage2_xp:
            return 2
        return 1

    def stage_title(self, stage: int) -> str:
        return str(self.evolution.get(f"stage{stage}_title", f"Stage {stage}"))

    def stage_form(self, stage: int) -> str:
        """Form description for an evolution stage (stage 1 = base form)."""
        if stage == 1:
            return self.form
        return str(self.evolution.get(f"stage{stage}_form", self.form))

    def stage_bonus(self, stage: int) -> dict[str, int]:
        """One-off stat bonus granted when evolving into ``stage``."""
        return dict(self.evolution.get(f"stage{stage}_bonus", {}))

    def xp_to_evolution(self, xp: int) -> int | None:
        """XP still needed for the next stage, or None at stage 3."""
        stage = self.evolution_stage(xp)
        if stage == 1:
            return self.stage2_xp - xp
        if stage == 2:
            return self.stage3_xp - xp
        return None

    def image_prompt(self, extra: str = "") -> str:
        """Appearance descriptor as a self-contained image-gen prompt."""
        prompt = self.appearance
        return f"{prompt}. {extra}".strip() if extra else prompt

    def orb_prompt(self) -> str:
        """Image-gen prompt for this pet's floating orb form."""
        if self.orb.get("prompt"):
            return self.orb["prompt"]
        return f"floating orb companion version of {self.name}: glossy sphere, expressive face, tiny orbiting sparkles, clean game-art style"

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
