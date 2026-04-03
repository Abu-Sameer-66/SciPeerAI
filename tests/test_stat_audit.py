# tests/test_stat_audit.py
#
# Tests for the statistical audit engine.
# We test with synthetic text that mimics
# real paper patterns — both clean and problematic ones.

import pytest
from src.scipeerai.modules.stat_audit import StatAuditEngine, StatAuditResult


@pytest.fixture
def engine():
    return StatAuditEngine()


# ── p-hacking tests ──────────────────────────────────────────

def test_flags_suspicious_p_clustering(engine):
    # three p-values all hugging 0.05 — should trigger high severity
    text = """
    The intervention showed significant improvement (p=0.048).
    Secondary outcome also significant (p=0.049).
    Tertiary measure borderline significant (p=0.046).
    """
    result = engine.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "p_hacking_suspected" in types or "borderline_p_values" in types


def test_clean_paper_passes(engine):
    # well-spaced p-values, decent sample, no red flags
    text = """
    Participants (n=120) completed the protocol.
    Group A showed significant improvement (p=0.002).
    No effect on secondary measure (p=0.41).
    """
    result = engine.analyze(text)
    assert result.risk_level in ("low", "medium")
    assert result.risk_score < 0.5


# ── sample size tests ────────────────────────────────────────

def test_flags_tiny_sample(engine):
    text = "We recruited n=8 participants. Results were significant (p=0.03)."
    result = engine.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "small_sample_size" in types


def test_acceptable_sample_passes(engine):
    text = "Study enrolled n=95 subjects across three sites."
    result = engine.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "small_sample_size" not in types


# ── round numbers ────────────────────────────────────────────

def test_flags_exact_p_value(engine):
    text = "The result was statistically significant (p=0.05)."
    result = engine.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "suspiciously_round_p_values" in types


# ── result structure tests ───────────────────────────────────

def test_result_is_correct_type(engine):
    result = engine.analyze("A simple paper with no statistics.")
    assert isinstance(result, StatAuditResult)
    assert 0.0 <= result.risk_score <= 1.0
    assert result.risk_level in ("low", "medium", "high", "critical")


def test_empty_text_doesnt_crash(engine):
    result = engine.analyze("")
    assert result.risk_score == 0.0
    assert result.risk_level == "low"