import pytest

from petforge import PetForge, culture_actions, get_pet, load_catalogue


def test_every_pet_has_valid_evolution_thresholds():
    for pet in load_catalogue():
        assert 0 < pet.stage2_xp < pet.stage3_xp, pet.id
        assert pet.stage_title(1) and pet.stage_title(2) and pet.stage_title(3)
        assert pet.stage_bonus(2) and pet.stage_bonus(3)


def test_evolution_stage_boundaries():
    pet = get_pet("mochi")
    assert pet.evolution_stage(0) == 1
    assert pet.evolution_stage(pet.stage2_xp - 1) == 1
    assert pet.evolution_stage(pet.stage2_xp) == 2
    assert pet.evolution_stage(pet.stage3_xp) == 3
    assert pet.xp_to_evolution(0) == pet.stage2_xp
    assert pet.xp_to_evolution(pet.stage3_xp) is None


def test_companion_starts_at_stage_one():
    buddy = PetForge(agent_name="tester").adopt("mochi")
    status = buddy.status()
    assert status["evolution_stage"] == 1
    assert status["stage_title"] == buddy.pet.stage_title(1)
    assert status["xp_to_evolution"] == buddy.pet.stage2_xp
    assert status["culture"] == buddy.pet.culture
    assert status["form_type"] == buddy.pet.form_type


def _evolve_to(buddy, stage):
    """Feed successes until the companion reaches ``stage``; return flags."""
    flags = []
    while buddy.evolution_stage < stage:
        flags.append(buddy.react("success")["evolved"])
    return flags


def test_using_a_pet_earns_xp_and_evolves_it():
    buddy = PetForge(agent_name="tester").adopt("mochi")
    flags = _evolve_to(buddy, 2)
    assert flags[-1] is True and flags.count(True) == 1
    status = buddy.status()
    assert status["evolution_stage"] == 2
    assert status["stage_title"] == buddy.pet.stage_title(2)
    assert status["stage_form"] == buddy.pet.stage_form(2)
    assert status["xp_to_evolution"] == buddy.pet.stage3_xp - status["bond_xp"]


def test_final_evolution_caps_at_stage_three():
    buddy = PetForge(agent_name="tester").adopt("glitch")
    _evolve_to(buddy, 3)
    status = buddy.status()
    assert status["evolution_stage"] == 3
    assert status["xp_to_evolution"] is None
    reaction = buddy.react("success")
    assert reaction["evolved"] is False
    assert reaction["evolution_stage"] == 3


def test_culture_moves_unlock_with_evolution():
    buddy = PetForge(agent_name="tester").adopt("mochi")  # japanese
    moves = culture_actions()[buddy.pet.culture]
    stage2_move = next(
        m for m in moves if buddy.pet.can(m) and m in
        {a.id for a in buddy.locked_actions()}
    )
    with pytest.raises(ValueError, match="unlocks at evolution stage"):
        buddy.act(stage2_move)
    _evolve_to(buddy, 2)
    result = buddy.act(stage2_move)
    assert result["action"] == stage2_move
    assert result["evolution_stage"] == 2


def test_act_reports_evolution_fields():
    buddy = PetForge(agent_name="tester").adopt("biscuit")
    result = buddy.act("dance")
    assert result["evolution_stage"] == 1
    assert result["evolved"] is False
    assert result["xp_to_evolution"] == buddy.pet.stage2_xp - result["bond_xp_gained"]
