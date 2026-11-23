import pytest

from petforge import by_category, categories, get_pet, load_catalogue
from petforge.models import CATEGORIES, EVENT_KINDS


def test_catalogue_loads_and_is_not_empty():
    pets = load_catalogue()
    assert len(pets) >= 18


def test_every_category_has_several_pets():
    counts = categories()
    assert set(counts) == set(CATEGORIES)
    for category, count in counts.items():
        assert count >= 3, f"category {category} has only {count} pets"


def test_ids_are_unique():
    ids = [pet.id for pet in load_catalogue()]
    assert len(ids) == len(set(ids))


def test_every_pet_is_complete():
    for pet in load_catalogue():
        assert pet.name and pet.form and pet.tagline
        assert len(pet.traits) >= 3
        assert pet.speech_style
        assert len(pet.quirks) >= 2
        assert pet.favourite
        assert len(pet.appearance) >= 80  # a real prompt, not a stub
        for kind in EVENT_KINDS:
            assert pet.reactions[kind], f"{pet.id} missing {kind} reactions"
        for stat in ("energy", "joy", "focus", "affection"):
            assert 0 <= pet.base_stats[stat] <= 100


def test_get_pet_roundtrip():
    pet = get_pet("glitch")
    assert pet.name == "Glitch"
    assert pet.category == "robot"


def test_get_pet_unknown_id():
    with pytest.raises(KeyError):
        get_pet("no-such-pet")


def test_by_category_filters():
    anime = by_category("anime")
    assert anime and all(pet.category == "anime" for pet in anime)


def test_by_category_rejects_unknown():
    with pytest.raises(ValueError):
        by_category("dragons")


def test_couples_are_paired_duos():
    for pet in by_category("couples"):
        assert "paired duo" in pet.form


def test_image_prompt_is_appearance_based():
    pet = get_pet("mochi")
    assert pet.image_prompt() == pet.appearance
    assert "front view" in pet.image_prompt("front view")
