import pytest

from petforge.bond import LEVEL_TITLES, LEVEL_XP, Bond


def test_starts_at_level_zero():
    bond = Bond()
    assert bond.level == 0
    assert bond.title == LEVEL_TITLES[0]
    assert bond.xp_to_next == LEVEL_XP[1]


def test_gain_returns_xp_and_level_flag():
    bond = Bond()
    gained, up = bond.gain("success")
    assert gained == 12 and up is False
    gained, up = bond.gain("success")  # 24 XP total -> level 1 at 20 XP
    assert gained == 12 and up is True
    assert bond.level == 1


def test_failure_earns_bond_too():
    bond = Bond()
    gained, _ = bond.gain("failure")
    assert gained == 9  # sticking around after failure counts


def test_level_thresholds():
    bond = Bond(xp=LEVEL_XP[3])
    assert bond.level == 3
    assert bond.xp_into_level == 0
    assert bond.xp_to_next == LEVEL_XP[4] - LEVEL_XP[3]


def test_max_level_has_no_next():
    bond = Bond(xp=LEVEL_XP[-1] + 500)
    assert bond.level == len(LEVEL_XP) - 1
    assert bond.title == "Soulbound"
    assert bond.xp_to_next is None


def test_unknown_event_rejected():
    with pytest.raises(ValueError):
        Bond().gain("dance-party")
