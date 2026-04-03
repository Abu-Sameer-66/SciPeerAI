# tests/test_methodology_checker.py

import pytest
from src.scipeerai.modules.methodology_checker import (
    MethodologyChecker,
    MethodologyResult,
)


@pytest.fixture
def checker():
    return MethodologyChecker()


# ── causation tests ───────────────────────────────────────────

def test_flags_causation_without_rct(checker):
    text = """
    We conducted a survey of 45 participants.
    Our results demonstrate that social media causes
    increased anxiety in teenagers.
    Participants self-reported their usage patterns.
    """
    result = checker.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "causation_without_rct" in types


def test_rct_does_not_flag_causation(checker):
    text = """
    We conducted a randomized controlled trial with placebo.
    The control group received standard care.
    Results demonstrate that the drug causes reduction in symptoms.
    """
    result = checker.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "causation_without_rct" not in types


# ── control group tests ────────────────────────────────────────

def test_flags_missing_control_group(checker):
    text = """
    Participants underwent a 4-week training intervention.
    Results showed significant improvement in performance.
    The treatment was highly effective.
    """
    result = checker.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "missing_control_group" in types


def test_no_flag_when_control_present(checker):
    text = """
    The treatment group and control group both completed assessments.
    The control condition received standard protocol.
    Results showed improvement in the treatment group.
    """
    result = checker.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "missing_control_group" not in types


# ── timeframe tests ────────────────────────────────────────────

def test_flags_timeframe_mismatch(checker):
    text = """
    This two-week preliminary study examined exercise habits.
    Results demonstrate long-term chronic health benefits
    of daily walking on sustained cardiovascular outcomes.
    """
    result = checker.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "timeframe_mismatch" in types


# ── result structure ───────────────────────────────────────────

def test_result_structure(checker):
    result = checker.analyze("A simple paper about science.")
    assert isinstance(result, MethodologyResult)
    assert 0.0 <= result.risk_score <= 1.0
    assert result.risk_level in ("low", "medium", "high", "critical")
    assert isinstance(result.llm_available, bool)


def test_empty_text_safe(checker):
    result = checker.analyze("")
    assert result.risk_score == 0.0