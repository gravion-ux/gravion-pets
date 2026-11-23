import pytest

from petforge.mood import MoodEngine


def base(**overrides):
    stats = {"energy": 60, "joy": 60, "focus": 60, "affection": 60}
    stats.update(overrides)
    return stats


def test_from_base_clamps_values():
    engine = MoodEngine.from_base(base(energy=250, joy=-5))
    assert engine.energy == 100
    assert engine.joy == 0


def test_success_raises_joy():
    engine = MoodEngine.from_base(base())
    engine.apply("success")
    assert engine.joy == 74
    assert engine.affection == 63


def test_failure_drops_joy_but_raises_focus():
    engine = MoodEngine.from_base(base())
    engine.apply("failure")
    assert engine.joy == 50
    assert engine.focus == 68


def test_stats_never_leave_bounds():
    engine = MoodEngine.from_base(base(joy=98, energy=98))
    for _ in range(10):
        engine.apply("success")
    assert engine.joy == 100
    engine2 = MoodEngine.from_base(base(joy=2, energy=2))
    for _ in range(10):
        engine2.apply("failure")
        engine2.apply("idle")
    assert engine2.joy >= 0 and engine2.energy >= 0


def test_unknown_event_rejected():
    engine = MoodEngine.from_base(base())
    with pytest.raises(ValueError):
        engine.apply("explosion")


def test_mood_ecstatic():
    engine = MoodEngine.from_base(base(joy=90, energy=80))
    assert engine.mood == "ecstatic"


def test_mood_sleepy_wins_over_everything():
    engine = MoodEngine.from_base(base(joy=95, energy=10))
    assert engine.mood == "sleepy"


def test_mood_downcast():
    engine = MoodEngine.from_base(base(joy=10, energy=60))
    assert engine.mood == "downcast"


def test_mood_focused():
    engine = MoodEngine.from_base(base(joy=50, focus=90, energy=60))
    assert engine.mood == "focused"


def test_tick_makes_pets_sleepier():
    engine = MoodEngine.from_base(base())
    for _ in range(30):
        engine.tick()
    assert engine.mood == "sleepy"
    assert engine.energy == 0


def test_history_records_moods():
    engine = MoodEngine.from_base(base())
    engine.apply("success")
    engine.apply("failure")
    assert len(engine.history) == 2
