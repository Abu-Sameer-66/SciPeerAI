# tests/test_retraction_checker.py
import pytest
from src.scipeerai.modules.retraction_checker import RetractionChecker

engine = RetractionChecker()


def test_known_retracted_doi_detected():
    """STAP cell paper DOI — critical risk."""
    r = engine.analyze(
        "This study builds on STAP cell findings "
        "doi:10.1038/nature13187 by Obokata et al."
    )
    assert r.risk_level in ("high", "critical")


def test_lacour_retracted_detected():
    """LaCour political persuasion — known retracted."""
    r = engine.analyze(
        "Based on LaCour and Green doi:10.1126/science.1254166 "
        "we examine political persuasion effects in voters."
    )
    assert len(r.retracted_found) >= 1
    assert r.risk_level == "critical"


def test_clean_paper_no_dois():
    """No DOIs — low risk with informational flag."""
    r = engine.analyze(
        "This study examined the effect of cognitive "
        "behavioral therapy on anxiety disorders in "
        "adult patients over a period of twelve weeks."
    )
    assert r.risk_level == "low"
    flag_types = [f.flag_type for f in r.flags]
    assert "no_dois_found" in flag_types


def test_retraction_signal_detected():
    """Retraction language in text flagged."""
    r = engine.analyze(
        "Following the retraction of the original study "
        "we conducted a reanalysis of the withdrawn data "
        "with corrected methodology and sample sizes here."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "retraction_language_detected" in flag_types


def test_doi_extraction():
    """DOIs correctly extracted from text."""
    r = engine.analyze(
        "See Smith et al. doi:10.1038/nature13187 and "
        "Jones et al. doi.org/10.1097/00007632-200207150-00020 "
        "for background on the methodology used here."
    )
    assert len(r.dois_found) >= 1


def test_retraction_score_range():
    """Score must be between 0 and 1."""
    r = engine.analyze(
        "Based on LaCour doi:10.1126/science.1254166 "
        "we examine political persuasion in this study."
    )
    assert 0.0 <= r.retraction_score <= 1.0


def test_flag_structure():
    """Flags have correct required fields."""
    r = engine.analyze(
        "Based on LaCour doi:10.1126/science.1254166 "
        "we examine political persuasion effects here."
    )
    assert r.flags_count >= 1
    flag = r.flags[0]
    assert hasattr(flag, 'flag_type')
    assert hasattr(flag, 'severity')
    assert hasattr(flag, 'description')
    assert hasattr(flag, 'evidence')
    assert hasattr(flag, 'suggestion')


def test_summary_contains_key_info():
    """Summary mentions DOIs and risk level."""
    r = engine.analyze(
        "Based on LaCour doi:10.1126/science.1254166 "
        "we examine political persuasion effects here."
    )
    assert "Retraction" in r.summary
    assert r.risk_level.upper() in r.summary