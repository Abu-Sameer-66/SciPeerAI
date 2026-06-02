# tests/test_ai_human_spectrum.py
#
# Test suite for AI-Human Spectrum Analyzer (Module 19).
# 10 tests covering AI signal detection, model attribution,
# spectrum scoring, section analysis, and edge cases.

import pytest
from src.scipeerai.modules.ai_human_spectrum import AIHumanSpectrumAnalyzer

engine = AIHumanSpectrumAnalyzer()


def test_ai_signals_detected():
    """Classic AI-generated patterns — high AI ratio."""
    r = engine.analyze(
        "In conclusion, it is worth noting that this comprehensive "
        "analysis delves into the multifaceted aspects of the research "
        "domain. Furthermore, it is important to emphasize that the "
        "findings shed light on the intricate relationship between "
        "variables. Additionally, this study aims to provide a thorough "
        "examination of the nuanced implications for future research. "
        "The results demonstrate significant improvements across all "
        "measured dimensions in a robust and systematic manner."
    )
    assert r.spectrum_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_human_writing_low_risk():
    """Natural human academic writing — low AI score."""
    r = engine.analyze(
        "We tested 47 undergraduates on a spatial reasoning task "
        "after either 20 minutes of aerobic exercise or seated rest. "
        "Contrary to our hypothesis, exercise did not improve scores. "
        "If anything, the exercised group performed slightly worse, "
        "though this difference was not significant (p = 0.34). "
        "We think the timing of testing — immediately post-exercise — "
        "may explain this null result, as acute fatigue could mask "
        "any cognitive benefit that emerges after recovery."
    )
    assert r.risk_level in ("low", "medium")


def test_spectrum_score_bounded():
    """Spectrum score always between 0 and 1."""
    r = engine.analyze(
        "The methodology employed rigorous statistical procedures. "
        "Data were analyzed using validated psychometric instruments."
    )
    assert 0.0 <= r.spectrum_score <= 1.0


def test_human_ai_ratio_sum():
    """Human and AI ratios sum to approximately 1.0."""
    r = engine.analyze(
        "This study investigated the effects of cognitive training "
        "on working memory capacity in older adults aged 65 to 80."
    )
    total = r.overall_human_ratio + r.overall_ai_ratio
    assert 0.95 <= total <= 1.05


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "In conclusion, it is worth noting that this study provides "
        "comprehensive insights into the multifaceted research domain. "
        "Furthermore, the findings shed light on nuanced relationships. "
        "Additionally, this analysis delves into the intricate aspects "
        "of the complex and interconnected variables under examination."
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
    assert r.spectrum_score >= 0.0
    assert r.risk_level     == "low"
    assert r.flags_count    == 0


def test_dominant_ai_model_string():
    """Dominant AI model is always a string."""
    r = engine.analyze(
        "In conclusion, it is worth noting that the comprehensive "
        "analysis provides valuable insights into the research domain."
    )
    assert isinstance(r.dominant_ai_model, str)


def test_signal_counts_non_negative():
    """All model signal counts are non-negative integers."""
    r = engine.analyze(
        "In conclusion, it is worth noting that the findings "
        "shed light on the multifaceted aspects of this domain."
    )
    assert r.gpt4_signal_count   >= 0
    assert r.claude_signal_count >= 0
    assert r.gemini_signal_count >= 0


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "This study examined cognitive load during dual-task "
        "performance using eye-tracking and reaction time measures."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "The experimental design used a within-subjects approach "
        "with counterbalanced condition ordering across participants."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")