import pytest

from petforge import by_culture, culture_actions, cultures, get_action, load_catalogue
from petforge.models import CULTURES, FORM_TYPES


def test_catalogue_has_over_800_pets():
    assert len(load_catalogue()) >= 800


def test_culture_counts_cover_every_pet():
    counts = cultures()
    assert sum(counts.values()) == len(load_catalogue())
    for culture in ("greek", "japanese", "indian"):
        assert counts[culture] >= 40, culture
    assert len(counts) >= 20  # a genuinely global roster


def test_every_pet_has_valid_culture_and_form_type():
    for pet in load_catalogue():
        assert pet.culture in CULTURES, pet.id
        assert pet.form_type in FORM_TYPES, pet.id


def test_form_type_coverage():
    from collections import Counter

    counts = Counter(pet.form_type for pet in load_catalogue())
    assert counts["humanoid"] >= 100
    assert counts["creature"] >= 100
    assert counts["orb"] >= 50
    assert counts["anime"] >= 10


def test_by_culture_filters_and_rejects_unknown():
    greek = by_culture("greek")
    assert greek and all(pet.culture == "greek" for pet in greek)
    with pytest.raises(ValueError):
        by_culture("atlantis")


def test_every_culture_has_stage_gated_moves():
    moves = culture_actions()
    for culture, ids in moves.items():
        assert culture in CULTURES
        assert len(ids) >= 2, culture
        stages = {get_action(action_id).unlock_stage for action_id in ids}
        assert stages == {1, 2, 3}, culture
        for action_id in ids:
            assert get_action(action_id).culture == culture


def test_every_pet_can_do_its_culture_moves():
    moves = culture_actions()
    for pet in load_catalogue():
        for action_id in moves.get(pet.culture, []):
            assert pet.can(action_id), f"{pet.id} missing {action_id}"


def test_culture_moves_stay_in_their_culture():
    for pet in load_catalogue():
        for action_id in pet.actions:
            owner = get_action(action_id).culture
            assert owner is None or owner == pet.culture, (
                f"{pet.id} ({pet.culture}) lists {action_id} ({owner})"
            )
