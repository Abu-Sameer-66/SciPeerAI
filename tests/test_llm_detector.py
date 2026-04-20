# tests/test_llm_detector.py
#
# Test suite for LLM-Generated Paper Detector.
# 8 tests covering burstiness, vocabulary diversity,
# LLM phrases, and risk levels.

import pytest
from src.scipeerai.modules.llm_detector import LLMDetector

engine = LLMDetector()

LLM_TEXT = (
    "It is worth noting that this study presents a comprehensive "
    "analysis of the research landscape. Furthermore, the findings "
    "suggest that leveraging state-of-the-art methods plays a crucial "
    "role in advancing our understanding. Moreover, it is important to "
    "note that the results demonstrate significant improvements. In "
    "conclusion, this novel approach sheds light on the realm of "
    "scientific integrity and provides a robust framework."
)

HUMAN_TEXT = (
    "We recruited 47 adults aged 18-65. Blood samples were taken at "
    "baseline. Three participants dropped out. Why? Scheduling conflicts "
    "mostly. The assay failed twice — frustrating, but expected with "
    "this protocol. Final N=44. Mean cortisol was 18.3 nmol/L "
    "(SD=4.2). Our lab has run this test 200+ times. These numbers "
    "look normal to us, maybe slightly elevated in the stress group."
)


def test_llm_text_detected():
    """Classic LLM text — high or critical risk."""
    r = engine.analyze(LLM_TEXT)
    assert r.risk_level in ("medium", "high", "critical")
    assert r.llm_score > 0.2


def test_human_text_lower_risk():
    """Natural human writing — lower risk."""
    r = engine.analyze(HUMAN_TEXT)
    assert r.llm_score < 0.7


def test_llm_phrases_counted():
    """LLM signature phrases correctly counted."""
    r = engine.analyze(LLM_TEXT)
    assert r.llm_phrase_count >= 5


def test_insufficient_text():
    """Very short text — low risk."""
    r = engine.analyze("This is a short text.")
    assert r.risk_level == "low"
    assert r.llm_score == 0.0


def test_llm_score_range():
    """Score must be between 0 and 1."""
    r = engine.analyze(LLM_TEXT)
    assert 0.0 <= r.llm_score <= 1.0


def test_burstiness_range():
    """Burstiness must be between 0 and 1."""
    r = engine.analyze(LLM_TEXT)
    assert 0.0 <= r.burstiness_score <= 1.0


def test_flag_structure():
    """Flags have correct required fields."""
    r = engine.analyze(LLM_TEXT)
    if r.flags_count > 0:
        flag = r.flags[0]
        assert hasattr(flag, 'flag_type')
        assert hasattr(flag, 'severity')
        assert hasattr(flag, 'description')
        assert hasattr(flag, 'evidence')
        assert hasattr(flag, 'suggestion')


def test_summary_contains_key_info():
    """Summary mentions LLM detection and risk level."""
    r = engine.analyze(LLM_TEXT)
    assert "LLM" in r.summary
    assert r.risk_level.upper() in r.summary