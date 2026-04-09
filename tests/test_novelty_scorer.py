# tests/test_novelty_scorer.py

import pytest
from src.scipeerai.modules.novelty_scorer import (
    NoveltyScorer,
    NoveltyResult,
)


@pytest.fixture
def scorer():
    return NoveltyScorer()


# ── structural novelty ─────────────────────────────────────────

def test_novelty_signals_increase_score(scorer):
    text = (
        "To our knowledge, this is the first study to propose "
        "a novel framework. We introduce a new method that has "
        "never been explored before."
    )
    result = scorer.analyze(text)
    assert result.novelty_score >= 0.6


def test_incremental_signals_decrease_score(scorer):
    text = (
        "Building on previous work, we extend the approach of "
        "Smith et al. Consistent with prior findings, our results "
        "confirm and corroborate the existing literature. "
        "Following the approach of Jones, we replicate the study."
    )
    result = scorer.analyze(text)
    assert result.novelty_score <= 0.5


def test_neutral_text_gets_middle_score(scorer):
    text = (
        "We conducted a study examining the relationship between "
        "exercise and cognitive performance in adult populations."
    )
    result = scorer.analyze(text)
    assert 0.3 <= result.novelty_score <= 0.7


# ── flags ──────────────────────────────────────────────────────

def test_flags_low_novelty(scorer):
    text = (
        "Building on previous work, extending prior studies, "
        "confirming previous findings, consistent with prior "
        "literature, following the approach of earlier papers."
    )
    result = scorer.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert (
        "low_novelty_score" in types
        or "incremental_language_detected" in types
    )


def test_no_flags_for_novel_paper(scorer):
    text = (
        "To our knowledge, this is the first paper to introduce "
        "this novel approach. No prior work has investigated this. "
        "We present a new framework that is previously unexplored."
    )
    result = scorer.analyze(text)
    high_flags = [f for f in result.flags if f.severity == "high"]
    assert len(high_flags) == 0


# ── result structure ───────────────────────────────────────────

def test_result_structure(scorer):
    result = scorer.analyze("A paper about science.")
    assert isinstance(result, NoveltyResult)
    assert 0.0 <= result.novelty_score <= 1.0
    assert result.novelty_level in (
        "low", "moderate", "high", "very_high"
    )
    assert result.risk_level in (
        "low", "medium", "high", "critical"
    )
    assert isinstance(result.literature_accessible, bool)


def test_empty_text_safe(scorer):
    result = scorer.analyze("")
    assert result.novelty_score >= 0.0
    assert result.risk_level is not None


def test_title_improves_extraction(scorer):
    result = scorer.analyze(
        "We propose a novel deep learning architecture.",
        title="Novel Transformer Architecture for Medical Imaging"
    )
    assert len(result.key_terms_extracted) >= 1