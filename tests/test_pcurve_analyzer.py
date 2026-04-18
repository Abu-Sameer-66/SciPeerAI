# tests/test_pcurve_analyzer.py
#
# Test suite for P-Curve Analyzer.
# 8 tests covering clustering, right skew,
# exact threshold reporting, and risk levels.

import pytest
from src.scipeerai.modules.pcurve_analyzer import PCurveAnalyzer

engine = PCurveAnalyzer()


def test_phacking_detected():
    """All p-values near 0.05 — critical risk."""
    text = (
        "Results showed p=0.049, p=0.048, p=0.047, "
        "p=0.044, p=0.043 suggesting significant effects."
    )
    r = engine.analyze(text)
    assert r.risk_level in ("high", "critical")
    assert r.clustering_score > 0.5


def test_clean_pvalues_pass():
    """P-values spread across range — low risk."""
    text = (
        "Results: p=0.001, p=0.003, p=0.008, "
        "p=0.012, p=0.019, p=0.021 all significant."
    )
    r = engine.analyze(text)
    assert r.right_skew_ratio > 0.5
    assert r.risk_level in ("low", "medium")


def test_insufficient_pvalues():
    """Less than 3 significant p-values — low risk."""
    r = engine.analyze(
        "The study found p=0.049 for primary outcome "
        "suggesting a marginally significant effect."
    )
    assert r.risk_level == "low"
    assert r.pcurve_score == 0.0


def test_exact_threshold_flagged():
    """Multiple p=0.05 exact values flagged."""
    text = (
        "Outcome 1: p=0.05, outcome 2: p=0.05, "
        "outcome 3: p=0.049, outcome 4: p=0.048, "
        "outcome 5: p=0.047 all significant results."
    )
    r = engine.analyze(text)
    assert r.flags_count >= 1


def test_pcurve_score_range():
    """Score must be between 0 and 1."""
    text = (
        "p=0.049, p=0.048, p=0.047, p=0.044, "
        "p=0.043 all significant effects found."
    )
    r = engine.analyze(text)
    assert 0.0 <= r.pcurve_score <= 1.0


def test_flag_structure():
    """Flags have correct required fields."""
    text = (
        "Results: p=0.049, p=0.048, p=0.047, "
        "p=0.044, p=0.043 significant effects."
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
    """Summary mentions p-values and risk level."""
    text = (
        "p=0.049, p=0.048, p=0.047, p=0.044, "
        "p=0.043 all significant effects found."
    )
    r = engine.analyze(text)
    assert "P-Curve" in r.summary
    assert r.risk_level.upper() in r.summary


def test_right_skew_real_effect():
    """Strong right skew = real effect = low risk."""
    text = (
        "Primary: p=0.001, secondary: p=0.003, "
        "tertiary: p=0.002, exploratory: p=0.004, "
        "confirmatory: p=0.001 all highly significant."
    )
    r = engine.analyze(text)
    assert r.right_skew_ratio >= 0.8
    assert r.risk_level in ("low", "medium")