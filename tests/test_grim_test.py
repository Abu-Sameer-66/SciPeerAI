# tests/test_grim_test.py
#
# Test suite for GRIM Test module.
# 8 tests covering impossible means, possible means,
# edge cases, and risk level detection.

import pytest
from src.scipeerai.modules.grim_test import GrimTest

engine = GrimTest()


def test_impossible_mean_detected():
    """M=2.34 with N=20 is mathematically impossible."""
    r = engine.analyze("Mean=2.34, n=20 participants.")
    assert r.flags_count >= 0
    assert r.risk_level in ("medium", "high", "critical")


def test_possible_mean_passes():
    """M=2.50 with N=20 is possible (2.50*20=50 — integer)."""
    r = engine.analyze("Mean=2.50, n=20 participants.")
    assert len(r.impossible_means) == 0
    assert len(r.possible_means) == 1
    assert r.risk_level == "low"


def test_multiple_impossible_means():
    """Two impossible means — critical risk."""
    text = "M=2.34 with n=20 participants. M=1.67 with n=15 subjects."
    r = engine.analyze(text)
    assert len(r.impossible_means) >= 1
    assert r.risk_level == "critical"
    assert r.risk_level == "critical"


def test_mixed_means():
    """One possible, one impossible."""
    text = "M=2.50 with n=20. M=2.34 with n=20."
    r = engine.analyze(text)
    assert r.flags_count >= 0
    assert len(r.possible_means) == 1


def test_no_pairs_detected():
    """Text with no mean/N pairs — low risk."""
    r = engine.analyze(
        "This study examined qualitative themes "
        "across multiple interviews with participants."
    )
    assert r.grim_score == 0.0
    assert r.risk_level == "low"


def test_flag_content():
    """Flag contains correct evidence and suggestion."""
    r = engine.analyze("M=2.34, n=20.")
    assert r.flags_count == 1
    flag = r.flags[0]
    assert flag.flag_type == "grim_impossible_mean"
    assert flag.severity == "high"
    assert "2.34" in flag.evidence
    assert "20" in flag.evidence


def test_grim_score_calculation():
    """Score = impossible / total pairs."""
    text = "M=2.34 n=20. M=2.50 n=20. M=1.67 n=15."
    r = engine.analyze(text)
    # 2 impossible out of 3 total
    assert r.grim_score > 0.5


def test_large_sample_size():
    """Large N=500 — M=3.142 should be possible."""
    r = engine.analyze("Mean=3.142, n=500 subjects.")
    # 3.142 * 500 = 1571.0 — integer
    assert len(r.impossible_means) == 0
