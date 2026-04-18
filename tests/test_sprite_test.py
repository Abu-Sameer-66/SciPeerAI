# tests/test_sprite_test.py
#
# Test suite for SPRITE Test module.
# 8 tests covering impossible distributions, possible ones,
# edge cases, and risk level detection.

import pytest
from src.scipeerai.modules.sprite_test import SpriteTest

engine = SpriteTest()


def test_impossible_distribution_detected():
    """M=2.50, SD=1.20, N=8, Scale=1-5 is impossible."""
    r = engine.analyze("mean=2.50 sd=1.20 n=8 scale=1-5")
    assert len(r.impossible_combinations) == 1
    assert r.risk_level in ("high", "critical")


def test_possible_distribution_passes():
    """M=3.00, SD=0.00, N=5, Scale=1-5 — all values equal 3."""
    r = engine.analyze("mean=3.00 sd=0.00 n=5 scale=1-5")
    assert len(r.impossible_combinations) == 0
    assert r.risk_level == "low"


def test_no_groups_detected():
    """Text with no mean/SD/N — low risk."""
    r = engine.analyze(
        "This study examined qualitative themes "
        "across multiple interviews with participants "
        "using thematic analysis methods throughout."
    )
    assert r.sprite_score == 0.0
    assert r.risk_level == "low"


def test_flag_content():
    """Flag contains correct evidence and suggestion."""
    r = engine.analyze("mean=2.50 sd=1.20 n=8 scale=1-5")
    assert r.flags_count == 1
    flag = r.flags[0]
    assert flag.flag_type == "sprite_impossible_distribution"
    assert flag.severity == "high"
    assert "2.5" in flag.evidence
    assert "1.2" in flag.evidence


def test_sprite_score_calculation():
    """Score = impossible / total groups."""
    r = engine.analyze("mean=2.50 sd=1.20 n=8 scale=1-5")
    assert r.sprite_score == 1.0


def test_large_n_variance_bounds():
    """Large N=100 — variance bounds check runs."""
    r = engine.analyze("mean=3.00 sd=0.50 n=100 scale=1-5")
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_summary_contains_key_info():
    """Summary mentions analyzed groups and failure rate."""
    r = engine.analyze("mean=2.50 sd=1.20 n=8 scale=1-5")
    assert "SPRITE Test" in r.summary
    assert "1" in r.summary


def test_risk_level_critical_on_impossible():
    """Single impossible group gives high or critical."""
    r = engine.analyze("mean=2.50 sd=1.20 n=8 scale=1-5")
    assert r.risk_level in ("high", "critical")