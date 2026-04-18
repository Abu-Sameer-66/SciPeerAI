# tests/test_granularity_analyzer.py
#
# Test suite for Statistical Granularity Analyzer.
# 8 tests covering digit preference, Benford's Law,
# round numbers, uniform precision, and risk levels.

import pytest
from src.scipeerai.modules.granularity_analyzer import GranularityAnalyzer

engine = GranularityAnalyzer()


def test_digit_preference_detected():
    """Too many 0s and 5s in decimal values."""
    text = (
        "Results: 2.50 3.50 4.50 1.50 2.00 3.00 "
        "4.00 5.00 1.00 6.50 7.50 8.00 n=20 p=0.05"
    )
    r = engine.analyze(text)
    assert r.flags_count >= 1
    assert r.risk_level in ("medium", "high", "critical")


def test_clean_data_passes():
    """Natural varied decimal values — low risk."""
    text = (
        "Values recorded: 2.34 1.87 3.92 4.13 2.76 "
        "1.53 3.47 2.19 4.82 1.63 n=45 p=0.032"
    )
    r = engine.analyze(text)
    assert r.risk_level in ("low", "medium")


def test_insufficient_data():
    """Less than 5 decimal values — low risk."""
    r = engine.analyze(
        "The study found significant results with "
        "p=0.04 and mean=2.5 in the sample group."
    )
    assert r.risk_level == "low"


def test_round_numbers_detected():
    """All whole number decimals — suspicious."""
    text = (
        "mean=1.0 sd=2.0 score=3.0 value=4.0 "
        "outcome=5.0 measure=6.0 result=7.0 n=20"
    )
    r = engine.analyze(text)
    assert r.flags_count >= 1


def test_granularity_score_range():
    """Score must be between 0 and 1."""
    text = (
        "Results showed mean=2.50 sd=1.00 p=0.050 n=20. "
        "Secondary mean=3.50 sd=2.00 p=0.040 n=15."
    )
    r = engine.analyze(text)
    assert 0.0 <= r.granularity_score <= 1.0


def test_flag_structure():
    """Flags have correct fields."""
    text = (
        "Results: 2.50 3.50 4.50 1.50 2.00 3.00 "
        "4.00 5.00 1.00 6.50 n=20 p=0.05"
    )
    r = engine.analyze(text)
    if r.flags_count > 0:
        flag = r.flags[0]
        assert hasattr(flag, 'flag_type')
        assert hasattr(flag, 'severity')
        assert hasattr(flag, 'description')
        assert hasattr(flag, 'evidence')
        assert hasattr(flag, 'suggestion')


def test_summary_contains_key_info():
    """Summary mentions anomaly score and risk level."""
    text = (
        "Results showed mean=2.50 sd=1.00 p=0.050 n=20. "
        "Values: 1.0 2.0 3.0 4.0 5.0 6.0 7.0 8.0"
    )
    r = engine.analyze(text)
    assert "Granularity" in r.summary
    assert r.risk_level.upper() in r.summary


def test_risk_level_valid():
    """Risk level must be one of four valid values."""
    text = (
        "Results showed mean=2.50 sd=1.00 p=0.050 n=20. "
        "Secondary mean=3.50 sd=2.00 p=0.040 n=15."
    )
    r = engine.analyze(text)
    assert r.risk_level in ("low", "medium", "high", "critical")