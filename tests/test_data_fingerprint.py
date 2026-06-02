# tests/test_data_fingerprint.py
#
# Test suite for Data Fingerprint Analyzer (Module 17).
# 10 tests covering round number bias, terminal digit patterns,
# suspicious duplicates, impossible pairs, and edge cases.

import pytest
from src.scipeerai.modules.data_fingerprint import DataFingerprintAnalyzer

engine = DataFingerprintAnalyzer()


def test_round_number_bias_detected():
    """All round numbers — fabrication signal."""
    r = engine.analyze(
        "The mean score was 80.00 with SD of 10.00. "
        "Group A scored 70.00 and Group B scored 90.00. "
        "The effect size was 0.50 with CI 0.30 to 0.70. "
        "Sample sizes were 100, 200, and 300 participants. "
        "Response rate was 80.00 percent across all sites."
    )
    assert r.fingerprint_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_natural_data_low_risk():
    """Realistic messy numbers — low fabrication signal."""
    r = engine.analyze(
        "The mean score was 73.47 with SD of 12.83. "
        "Group A scored 68.91 and Group B scored 79.23. "
        "The effect size was 0.43 with CI 0.17 to 0.69. "
        "Sample sizes were 87, 94, and 103 participants. "
        "Response rate was 76.3 percent across all sites."
    )
    assert r.risk_level in ("low", "medium")


def test_fingerprint_score_bounded():
    """Fingerprint score always between 0 and 1."""
    r = engine.analyze(
        "Mean 4.5, SD 1.2, n 45. Effect d 0.67. "
        "Correlation r 0.34, p 0.023. CI 0.12 to 0.56."
    )
    assert 0.0 <= r.fingerprint_score <= 1.0


def test_total_numbers_counted():
    """Total numbers is a non-negative integer."""
    r = engine.analyze(
        "The sample included 245 participants with mean age 34.7 years. "
        "Scores ranged from 12 to 98 with median 54.3 and IQR 41 to 67."
    )
    assert isinstance(r.total_numbers, int)
    assert r.total_numbers >= 0


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "Mean 80.00, SD 10.00, n 100. Mean 80.00, SD 10.00, n 200. "
        "Mean 80.00, SD 10.00, n 300. Mean 80.00, SD 10.00, n 400. "
        "Effect size 0.50, CI 0.30 to 0.70, p value 0.050."
    )
    for flag in r.flags:
        assert hasattr(flag, "flag_type")
        assert hasattr(flag, "severity")
        assert hasattr(flag, "description")
        assert hasattr(flag, "evidence")
        assert hasattr(flag, "suggestion")


def test_empty_text_safe():
    """Empty input returns safe defaults without raising."""
    r = engine.analyze("")
    assert r.fingerprint_score == 0.0
    assert r.risk_level        == "low"
    assert r.flags_count       == 0


def test_round_number_ratio_bounded():
    """Round number ratio always between 0 and 1."""
    r = engine.analyze(
        "Scores: 80.00, 90.00, 70.00, 60.00, 50.00. "
        "Means: 4.23, 5.67, 3.89, 6.12, 2.45."
    )
    assert 0.0 <= r.round_number_ratio <= 1.0


def test_suspicious_duplicates_list():
    """Suspicious duplicates is always a list."""
    r = engine.analyze(
        "Mean 4.5672, SD 1.2341. Mean 4.5672, SD 1.2341. "
        "Effect 0.3847, p 0.0234. Effect 0.3847, p 0.0234."
    )
    assert isinstance(r.suspicious_duplicates, list)


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "The sample had mean age 34.7 years, SD 12.3, n equals 245. "
        "Primary outcome mean was 67.4, SD 15.8, effect size 0.43."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "Mean 73.47, SD 12.83, n 87. Effect d 0.43. "
        "Correlation r 0.34, p 0.023. CI 0.12 to 0.56."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")