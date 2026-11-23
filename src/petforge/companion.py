"""Agent-integration API: adopt a pet, feed it task outcomes, get reactions.

Typical use from any agent / subagent runtime::

    from petforge import PetForge

    forge = PetForge(agent_name="research-subagent-3")
    buddy = forge.adopt("glitch")
    print(buddy.react("success")["message"])
    print(buddy.status())
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .bond import Bond
from .catalogue import get_pet, random_pet
from .models import EVENT_KINDS, Pet
from .mood import MoodEngine


@dataclass
class Reaction:
    pet_id: str
    event: str
    message: str
    mood: str
    stats: dict[str, int]
    bond_xp_gained: int
    level: int
    level_title: str
    levelled_up: bool

    def to_dict(self) -> dict:
        return {
            "pet_id": self.pet_id,
            "event": self.event,
            "message": self.message,
            "mood": self.mood,
            "stats": dict(self.stats),
            "bond_xp_gained": self.bond_xp_gained,
            "level": self.level,
            "level_title": self.level_title,
            "levelled_up": self.levelled_up,
        }


@dataclass
class Companion:
    """A pet adopted by one agent: mood + bond + voice, all live state."""

    pet: Pet
    agent_name: str = "agent"
    seed: int | None = None
    _rng: random.Random = field(init=False, repr=False)
    _mood: MoodEngine = field(init=False, repr=False)
    _bond: Bond = field(init=False, repr=False)
    _seen: dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._mood = MoodEngine.from_base(self.pet.base_stats)
        self._bond = Bond()
        self._seen = {kind: 0 for kind in EVENT_KINDS}

    # -- the core API -----------------------------------------------------
    def react(self, event: str) -> dict:
        """React to a task outcome: 'success', 'failure', 'idle' or 'praise'.

        Returns a plain dict (JSON-friendly) so any agent framework can
        consume it without importing petforge types.
        """
        if event not in EVENT_KINDS:
            raise ValueError(f"unknown event kind: {event!r}")
        mood = self._mood.apply(event)
        gained, levelled_up = self._bond.gain(event)
        lines = self.pet.reactions[event]
        # Rotate through the pet's lines so repeats feel fresh, not random.
        line = lines[self._seen[event] % len(lines)]
        self._seen[event] += 1
        reaction = Reaction(
            pet_id=self.pet.id,
            event=event,
            message=line.format(agent=self.agent_name),
            mood=mood,
            stats=self._mood.snapshot(),
            bond_xp_gained=gained,
            level=self._bond.level,
            level_title=self._bond.title,
            levelled_up=levelled_up,
        )
        return reaction.to_dict()

    def tick(self) -> str:
        """Let time pass (call on a heartbeat); returns the current mood."""
        return self._mood.tick()

    @property
    def mood(self) -> str:
        return self._mood.mood

    @property
    def bond(self) -> Bond:
        return self._bond

    def status(self) -> dict:
        return {
            "pet_id": self.pet.id,
            "pet_name": self.pet.name,
            "category": self.pet.category,
            "agent": self.agent_name,
            "mood": self.mood,
            "stats": self._mood.snapshot(),
            "bond_xp": self._bond.xp,
            "level": self._bond.level,
            "level_title": self._bond.title,
            "xp_to_next": self._bond.xp_to_next,
        }

    def greeting(self) -> str:
        return (
            f"{self.pet.name} ({self.pet.form}) joins {self.agent_name}. "
            f"{self.pet.tagline}"
        )


class PetForge:
    """Entry point: one forge per agent runtime, many companions per forge."""

    def __init__(self, agent_name: str = "agent") -> None:
        self.agent_name = agent_name
        self._companions: dict[str, Companion] = {}

    def adopt(self, pet_id: str, *, seed: int | None = None) -> Companion:
        """Adopt a catalogue pet by id. Re-adopting returns the same buddy."""
        if pet_id not in self._companions:
            self._companions[pet_id] = Companion(
                pet=get_pet(pet_id), agent_name=self.agent_name, seed=seed
            )
        return self._companions[pet_id]

    def adopt_random(
        self, *, seed: int | None = None, rng_seed: int | None = None
    ) -> Companion:
        rng = random.Random(rng_seed)
        pet = random_pet(rng)
        return self.adopt(pet.id, seed=seed)

    def companions(self) -> list[Companion]:
        return list(self._companions.values())

    def broadcast(self, event: str) -> list[dict]:
        """Feed one event to every adopted pet (e.g. a team-wide deploy)."""
        return [companion.react(event) for companion in self.companions()]
