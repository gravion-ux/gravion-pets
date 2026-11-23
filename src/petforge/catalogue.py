"""Catalogue loading: the pet roster lives in data/catalogue.json."""

from __future__ import annotations

import json
import random
from importlib import resources

from .models import CATEGORIES, Pet

_cache: list[Pet] | None = None


def load_catalogue() -> list[Pet]:
    """Load and validate every pet in the bundled JSON catalogue."""
    global _cache
    if _cache is None:
        raw = (
            resources.files("petforge.data")
            .joinpath("catalogue.json")
            .read_text(encoding="utf-8")
        )
        data = json.loads(raw)
        pets = [Pet.from_dict(entry) for entry in data["pets"]]
        ids = [pet.id for pet in pets]
        if len(ids) != len(set(ids)):
            raise ValueError("catalogue contains duplicate pet ids")
        _cache = pets
    return list(_cache)


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


def random_pet(rng: random.Random | None = None) -> Pet:
    return (rng or random).choice(load_catalogue())
