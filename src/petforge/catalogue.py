"""Catalogue loading: the pet roster lives in data/catalogue.json."""

from __future__ import annotations

import json
import random
from importlib import resources

from .models import CATEGORIES, CULTURES, Action, Pet

_cache: list[Pet] | None = None
_raw_cache: dict | None = None
_actions_cache: dict[str, Action] | None = None


def _raw() -> dict:
    global _raw_cache
    if _raw_cache is None:
        text = (
            resources.files("petforge.data")
            .joinpath("catalogue.json")
            .read_text(encoding="utf-8")
        )
        _raw_cache = json.loads(text)
    return _raw_cache


def load_catalogue() -> list[Pet]:
    """Load and validate every pet in the bundled JSON catalogue."""
    global _cache
    if _cache is None:
        pets = [Pet.from_dict(entry) for entry in _raw()["pets"]]
        ids = [pet.id for pet in pets]
        if len(ids) != len(set(ids)):
            raise ValueError("catalogue contains duplicate pet ids")
        _cache = pets
    return list(_cache)


def load_actions() -> dict[str, Action]:
    """The shared action library: action id -> Action."""
    global _actions_cache
    if _actions_cache is None:
        actions = [Action.from_dict(entry) for entry in _raw().get("actions", [])]
        ids = [action.id for action in actions]
        if len(ids) != len(set(ids)):
            raise ValueError("catalogue contains duplicate action ids")
        _actions_cache = {action.id: action for action in actions}
    return dict(_actions_cache)


def get_action(action_id: str) -> Action:
    actions = load_actions()
    if action_id not in actions:
        raise KeyError(f"no action with id {action_id!r}")
    return actions[action_id]


def category_actions() -> dict[str, list[str]]:
    """Category -> ids of that category's flavoured library actions."""
    return {cat: list(ids) for cat, ids in _raw().get("category_actions", {}).items()}


def culture_actions() -> dict[str, list[str]]:
    """Culture -> ids of that culture's signature library moves."""
    return {cul: list(ids) for cul, ids in _raw().get("culture_actions", {}).items()}


def pet_action(pet: Pet, action_id: str) -> Action:
    """Resolve an action a pet can perform (library entry or signature)."""
    if pet.signature_move is not None and action_id == pet.signature_move.id:
        return pet.signature_move
    if action_id in pet.actions:
        return get_action(action_id)
    raise ValueError(f"pet {pet.id!r} cannot perform action {action_id!r}")


def get_pet(pet_id: str) -> Pet:
    for pet in load_catalogue():
        if pet.id == pet_id:
            return pet
    raise KeyError(f"no pet with id {pet_id!r}")


def by_category(category: str) -> list[Pet]:
    if category not in CATEGORIES:
        raise ValueError(f"unknown category: {category!r}")
    return [pet for pet in load_catalogue() if pet.category == category]


def categories() -> dict[str, int]:
    """Category -> number of pets, for every category."""
    counts = {category: 0 for category in CATEGORIES}
    for pet in load_catalogue():
        counts[pet.category] += 1
    return counts


def by_culture(culture: str) -> list[Pet]:
    if culture not in CULTURES:
        raise ValueError(f"unknown culture: {culture!r}")
    return [pet for pet in load_catalogue() if pet.culture == culture]


def cultures() -> dict[str, int]:
    """Culture -> number of pets, for every culture with at least one pet."""
    counts: dict[str, int] = {}
    for pet in load_catalogue():
        counts[pet.culture] = counts.get(pet.culture, 0) + 1
    return dict(sorted(counts.items()))


def random_pet(rng: random.Random | None = None) -> Pet:
    return (rng or random).choice(load_catalogue())
