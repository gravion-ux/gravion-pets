import pytest

from petforge import PetForge


def test_adopt_returns_companion_with_greeting():
    forge = PetForge(agent_name="scout-1")
    buddy = forge.adopt("biscuit")
    greeting = buddy.greeting()
    assert "Biscuit" in greeting and "scout-1" in greeting


def test_adopt_unknown_pet_raises():
    with pytest.raises(KeyError):
        PetForge().adopt("missingno")


def test_readopting_returns_same_companion():
    forge = PetForge()
    assert forge.adopt("wisp") is forge.adopt("wisp")


def test_react_success_shape():
    buddy = PetForge(agent_name="tester").adopt("glitch")
    reaction = buddy.react("success")
    assert reaction["pet_id"] == "glitch"
    assert reaction["event"] == "success"
    assert "tester" in reaction["message"]
    assert reaction["mood"] in {
        "ecstatic", "happy", "focused", "devoted", "content",
        "bored", "downcast", "sleepy",
    }
    assert reaction["bond_xp_gained"] == 12
    assert set(reaction["stats"]) == {"energy", "joy", "focus", "affection"}


def test_reaction_lines_rotate_instead_of_repeating():
    buddy = PetForge().adopt("mochi")
    first = buddy.react("success")["message"]
    second = buddy.react("success")["message"]
    third = buddy.react("success")["message"]
    assert first != second
    assert third == first  # two lines in the catalogue, so it wraps


def test_failure_then_success_moves_mood_and_bond():
    buddy = PetForge(agent_name="fixer").adopt("unit-7")
    start_joy = buddy.status()["stats"]["joy"]
    buddy.react("failure")
    after_fail = buddy.status()
    assert after_fail["stats"]["joy"] < start_joy
    assert after_fail["bond_xp"] == 9
    buddy.react("success")
    after_fix = buddy.status()
    assert after_fix["stats"]["joy"] > after_fail["stats"]["joy"]
    assert after_fix["bond_xp"] == 21


def test_level_up_is_reported():
    buddy = PetForge().adopt("pudding")
    flags = [buddy.react("success")["levelled_up"] for _ in range(3)]
    assert flags == [False, True, False]  # 12, 24 (Lv1), 36 XP
    assert buddy.status()["level"] == 1
    assert buddy.status()["level_title"] == "Warming Up"


def test_unknown_event_rejected():
    buddy = PetForge().adopt("squish")
    with pytest.raises(ValueError):
        buddy.react("nap-attack")


def test_adopt_random_is_deterministic_with_seed():
    a = PetForge().adopt_random(rng_seed=42)
    b = PetForge().adopt_random(rng_seed=42)
    assert a.pet.id == b.pet.id


def test_broadcast_reaches_every_companion():
    forge = PetForge(agent_name="team")
    forge.adopt("bubbles")
    forge.adopt("djinn-tonic")
    reactions = forge.broadcast("praise")
    assert len(reactions) == 2
    assert {r["pet_id"] for r in reactions} == {"bubbles", "djinn-tonic"}


def test_status_reports_bond_progress():
    buddy = PetForge(agent_name="ops").adopt("auntie-aurora")
    status = buddy.status()
    assert status["pet_name"] == "Auntie Aurora"
    assert status["category"] == "spirit"
    assert status["bond_xp"] == 0
    assert status["xp_to_next"] == 20


def test_tick_eventually_makes_pet_sleepy():
    buddy = PetForge().adopt("coach-dario")
    for _ in range(40):
        mood = buddy.tick()
    assert mood == "sleepy"
