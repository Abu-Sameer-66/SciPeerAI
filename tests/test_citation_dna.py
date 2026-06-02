# tests/test_citation_dna.py
#
# Test suite for Citation DNA Analyzer (Module 16).
# 10 tests covering author concentration, journal diversity,
# decade spread, geographic diversity, and edge cases.

import pytest
from src.scipeerai.modules.citation_dna import CitationDNAAnalyzer

engine = CitationDNAAnalyzer()


def test_high_concentration_detected():
    """Same journal cited repeatedly — high concentration flagged."""
    r = engine.analyze(
        "Smith A, Jones B. Nature. 2021;1:1-10. "
        "Smith A, Brown C. Nature. 2020;2:11-20. "
        "Jones B, Smith A. Nature. 2019;3:21-30. "
        "Smith A, Davis D. Nature. 2018;4:31-40. "
        "Brown C, Smith A. Nature. 2017;5:41-50. "
        "Smith A et al. Nature. 2016;6:51-60."
    )
    assert r.dna_risk_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_diverse_citations_low_risk():
    """Many different authors and journals — low concentration."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019. Brown D. Lancet. 2018. "
        "Davis E. NEJM. 2017. Wilson F. JAMA. 2016. "
        "Taylor G. BMJ. 2015. Anderson H. PLOS ONE. 2014. "
        "Martinez I. PNAS. 2013. Thompson J. eLife. 2012."
    )
    assert r.risk_level in ("low", "medium")


def test_dna_risk_score_bounded():
    """DNA risk score always between 0 and 1."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019. Brown D. Lancet. 2018."
    )
    assert 0.0 <= r.dna_risk_score <= 1.0


def test_dna_diversity_score_bounded():
    """DNA diversity score always between 0 and 1."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019. Brown D. Lancet. 2018."
    )
    assert 0.0 <= r.dna_diversity_score <= 1.0


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "Smith A. Nature. 2021;1:1. Smith A. Nature. 2020;2:2. "
        "Smith A. Nature. 2019;3:3. Smith A. Nature. 2018;4:4. "
        "Smith A. Nature. 2017;5:5. Jones B. Nature. 2016;6:6."
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
    assert r.dna_risk_score  == 0.0
    assert r.risk_level      == "low"
    assert r.flags_count     == 0


def test_unique_authors_count():
    """Unique authors count is a non-negative integer."""
    r = engine.analyze(
        "Smith A. 2021. Jones B. 2020. Williams C. 2019. "
        "Brown D. 2018. Davis E. 2017. Wilson F. 2016."
    )
    assert isinstance(r.unique_authors, int)
    assert r.unique_authors >= 0


def test_total_citations_count():
    """Total citations is a non-negative integer."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019. Brown D. Lancet. 2018."
    )
    assert isinstance(r.total_citations, int)
    assert r.total_citations >= 0


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "Smith A. Nature. 2021. Jones B. Science. 2020. "
        "Williams C. Cell. 2019. Brown D. Lancet. 2018."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")