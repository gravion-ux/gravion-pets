import pytest

from petforge import PetForge, category_actions, get_action, load_actions, load_catalogue
from petforge.models import CATEGORIES

SHARED_IDS = {
    "idle-breathe", "walk", "run", "jump", "dance", "spin", "wave",
    "bow", "sleep", "eat", "play", "celebrate", "hide", "peek",
}


def test_action_library_loads_complete():
    library = load_actions()
    assert SHARED_IDS <= set(library)
    for action in library.values():
        assert action.name and action.description
        assert len(action.animation) >= 40  # a real motion prompt, not a stub
        assert isinstance(action.loop, bool)
        assert action.energy_cost >= 0 and action.bond_xp >= 0
        for stat in action.stats:
            assert stat in ("energy", "joy", "focus", "affection")


def test_shared_actions_have_no_category_and_category_actions_do():
    for action_id in SHARED_IDS:
        assert get_action(action_id).category is None
    for category, ids in category_actions().items():
        assert category in CATEGORIES
        for action_id in ids:
            assert get_action(action_id).category == category


def test_every_pet_has_a_repertoire():
    library = load_actions()
    for pet in load_catalogue():
        assert pet.actions, f"{pet.id} has no library actions"
        for action_id in pet.actions:
            assert action_id in library, f"{pet.id} lists unknown action {action_id}"
        # every pet can do (nearly) all the shared basics
        assert len(SHARED_IDS & set(pet.actions)) >= len(SHARED_IDS) - 2


def test_category_actions_stay_in_their_category():
    flavours = category_actions()
    for pet in load_catalogue():
        for action_id in pet.actions:
            owner = get_action(action_id).category
            assert owner is None or owner == pet.category
        # and the pet actually gets its own category's flavours
        for action_id in flavours.get(pet.category, []):
            assert action_id in pet.actions


def test_every_pet_has_a_unique_signature_move():
    signatures = []
    for pet in load_catalogue():
        move = pet.signature_move
        assert move is not None, f"{pet.id} has no signature move"
        assert move.id == f"{pet.id}-signature"
        assert move.name and move.description and len(move.animation) >= 40
        assert not move.loop  # signature moves are one-shot performances
        signatures.append(move.id)
    assert len(signatures) == len(set(signatures))
    library = load_actions()
    for signature_id in signatures:
        assert signature_id not in library  # unique to the pet, not shared


def test_gods_and_devils_repertoires():
    forge = PetForge(agent_name="tester")
    vaelion = forge.adopt("vaelion")
    assert {"levitate", "bless", "thunder-gesture"} <= set(vaelion.pet.actions)
    pimwick = forge.adopt("pimwick")
    assert {"cackle", "smoke-vanish", "tail-flick"} <= set(pimwick.pet.actions)


def test_act_applies_effects():
    forge = PetForge(agent_name="tester")
    buddy = forge.adopt("glitch")
    before = buddy.status()
    result = buddy.act("dance")
    dance = get_action("dance")
    assert result["action"] == "dance"
    assert result["description"].startswith("Glitch:")
    assert result["animation"] == dance.animation
    assert result["bond_xp_gained"] == dance.bond_xp
    after = buddy.status()
    assert after["bond_xp"] == before["bond_xp"] + dance.bond_xp
    assert after["stats"]["joy"] == min(100, before["stats"]["joy"] + dance.stats["joy"])
    assert after["stats"]["energy"] == before["stats"]["energy"] - dance.energy_cost


def test_act_signature_move():
    forge = PetForge(agent_name="tester")
    buddy = forge.adopt("vaelion")
    result = buddy.act("vaelion-signature")
    assert result["signature"] is True
    assert result["name"] == "Forecast: Glory"
    assert result["bond_xp_gained"] == buddy.pet.signature_move.bond_xp


def test_act_restores_energy_when_sleeping():
    forge = PetForge(agent_name="tester")
    buddy = forge.adopt("mochi")
    buddy.act("run")
    buddy.act("run")
    drained = buddy.status()["stats"]["energy"]
    result = buddy.act("sleep")
    assert result["energy_cost"] == 0
    assert buddy.status()["stats"]["energy"] > drained


def test_act_rejects_actions_outside_repertoire():
    forge = PetForge(agent_name="tester")
    buddy = forge.adopt("glitch")  # a robot: cannot swim, cannot bless
    with pytest.raises(ValueError):
        buddy.act("swim")
    with pytest.raises(ValueError):
        buddy.act("bless")
    with pytest.raises(ValueError):
        buddy.act("not-a-real-action")


def test_available_actions_includes_signature_last():
    forge = PetForge(agent_name="tester")
    buddy = forge.adopt("squish")
    actions = buddy.available_actions()
    assert actions[-1].id == "squish-signature"
    # Stage-1 view: everything unlocked, nothing stage-gated (v4 evolution).
    unlocked = {
        a.id for a in actions
    }
    assert unlocked == {
        action_id
        for action_id in buddy.pet.repertoire_ids()
        if action_id == "squish-signature"
        or get_action(action_id).unlock_stage <= buddy.evolution_stage
    }
    assert {a.id for a in buddy.locked_actions()} == (
        set(buddy.pet.repertoire_ids()) - unlocked
    )
    assert "swim" in buddy.pet.actions  # an aquatic pet swims
