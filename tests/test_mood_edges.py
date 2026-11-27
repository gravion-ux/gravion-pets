import pytest
from petforge.mood import MoodEngine


def test_from_base_reports_missing_stat():
    with pytest.raises(ValueError, match="missing required stat"):
        MoodEngine.from_base({"energy": 50})


def test_from_base_clamps_out_of_range():
    engine = MoodEngine.from_base({"energy": 999, "joy": -5, "focus": 50, "affection": 50})
    assert engine.snapshot() == {"energy": 100, "joy": 0, "focus": 50, "affection": 50}
