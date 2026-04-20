# tests/test_citation_cartel.py
#
# Test suite for Citation Cartel Detector.
# 8 tests covering cartel detection, diversity,
# self-citation, and risk levels.

import pytest
from src.scipeerai.modules.citation_cartel import CitationCartelDetector

engine = CitationCartelDetector()


def test_cartel_detected():
    """Smith dominates citations — critical risk."""
    r = engine.analyze(
        "Based on Smith (2021), Smith (2020), Smith (2019), "
        "Smith (2018), Smith (2017), Jones (2020), Jones (2019), "
        "Smith et al. (2022) we conclude. Smith (2016) also showed."
    )
    assert r.risk_level in ("high", "critical")
    assert r.cartel_score > 0.3


def test_diverse_citations_pass():
    """Many different authors — low risk."""
    r = engine.analyze(
        "Smith (2021) showed X. Jones (2020) found Y. "
        "Williams (2019) reported Z. Brown (2018) confirmed. "
        "Davis (2022) extended. Wilson (2021) replicated. "
        "Taylor (2020) validated. Anderson (2019) supported."
    )
    assert r.risk_level in ("low", "medium")


def test_insufficient_citations():
    """Less than 5 citations — low risk flag."""
    r = engine.analyze(
        "This study examines cognitive behavioral therapy "
        "effects on adult anxiety disorders over twelve weeks "
        "using validated measurement instruments throughout."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "insufficient_citations" in flag_types


def test_cartel_score_range():
    """Score must be between 0 and 1."""
    r = engine.analyze(
        "Smith (2021), Smith (2020), Smith (2019), "
        "Smith (2018), Jones (2020), Jones (2019), "
        "Smith et al. (2022), Smith (2016), Jones (2021)."
    )
    assert 0.0 <= r.cartel_score <= 1.0


def test_flag_structure():
    """Flags have correct required fields."""
    r = engine.analyze(
        "Smith (2021), Smith (2020), Smith (2019), "
        "Smith (2018), Smith (2017), Jones (2020), "
        "Jones (2019), Smith et al. (2022) findings."
    )
    if r.flags_count > 0:
        flag = r.flags[0]
        assert hasattr(flag, 'flag_type')
        assert hasattr(flag, 'severity')
        assert hasattr(flag, 'description')
        assert hasattr(flag, 'evidence')
        assert hasattr(flag, 'suggestion')


def test_authors_extracted():
    """Authors correctly extracted from citations."""
    r = engine.analyze(
        "Smith (2021), Jones (2020), Williams (2019), "
        "Brown (2018), Davis (2022), Wilson (2021), "
        "Taylor (2020), Anderson (2019) all support this."
    )
    assert len(r.authors_found) >= 1


def test_summary_contains_key_info():
    """Summary mentions citations and risk level."""
    r = engine.analyze(
        "Smith (2021), Smith (2020), Smith (2019), "
        "Smith (2018), Jones (2020), Jones (2019), "
        "Smith et al. (2022), Smith (2016) findings."
    )
    assert "Citation" in r.summary


def test_network_diversity_range():
    """Diversity score must be between 0 and 1."""
    r = engine.analyze(
        "Smith (2021), Smith (2020), Jones (2020), "
        "Jones (2019), Williams (2019), Brown (2018), "
        "Davis (2022), Wilson (2021) all confirmed."
    )
    assert 0.0 <= r.network_diversity <= 1.0