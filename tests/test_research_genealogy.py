# tests/test_research_genealogy.py
#
# Test suite for Research Genealogy Engine (Module 22).
# 10 tests covering ring detection, concentration, DOI extraction,
# depth scoring, flag structure, and edge cases.

import pytest
from src.scipeerai.modules.research_genealogy import ResearchGenealogyEngine

engine = ResearchGenealogyEngine()


def test_citation_ring_detected():
    """Small author group dominates references — ring flagged."""
    r = engine.analyze(
        "Smith (2021) originally proposed this framework which Smith et al. (2020) "
        "confirmed. Smith (2019) and Smith (2018) laid the groundwork that Jones (2021) "
        "and Jones (2020) extended. Jones (2019) replicated Smith (2017) findings and "
        "Smith et al. (2022) further validated the results across multiple contexts."
    )
    assert r.ring_detected is True
    flag_types = [f.flag_type for f in r.flags]
    assert "citation_ring_detected" in flag_types


def test_diverse_citations_low_risk():
    """Ten different authors — concentration low, no ring."""
    r = engine.analyze(
        "Smith (2021) proposed the model. Jones (2018) independently verified it. "
        "Williams (2016) introduced the methodology. Brown (2020) extended the scope. "
        "Davis (2019) critiqued the original approach. Wilson (2017) replicated key "
        "findings. Taylor (2021) provided a systematic review. Anderson (2015) laid "
        "the historical groundwork. Martinez (2022) updated the framework parameters. "
        "Thompson (2014) first described the core phenomenon in clinical settings."
    )
    assert r.risk_level in ("low", "medium")
    assert r.genealogy_concentration < 0.80


def test_doi_extraction_count():
    """DOIs correctly extracted and counted."""
    r = engine.analyze(
        "Previous work (10.1038/nature12345) established the baseline. Smith (2020) "
        "using methods from 10.1016/j.cell.2019.01.001 and Jones et al. (2021) "
        "citing 10.1126/science.abc1234 confirmed our approach. Williams (2019) "
        "also referenced doi: 10.1093/bioinformatics/btz001 in related work."
    )
    assert r.doi_count >= 3


def test_score_bounded():
    """Genealogy score always between 0 and 1."""
    r = engine.analyze(
        "Smith (2021), Smith (2020), Smith (2019), Jones (2020), Jones (2019), "
        "Jones (2018), Williams (2022), Williams (2021), Brown (2020), Davis (2021)."
    )
    assert 0.0 <= r.genealogy_score <= 1.0


def test_concentration_bounded():
    """Concentration index always between 0 and 1."""
    r = engine.analyze(
        "Smith (2021) and Jones (2020) provided foundations. "
        "Williams (2019), Brown (2018), Davis (2017) all confirmed."
    )
    assert 0.0 <= r.genealogy_concentration <= 1.0


def test_flag_structure_complete():
    """Every flag has all five required attributes."""
    r = engine.analyze(
        "Smith (2021) showed that Smith et al. (2020) confirmed what Smith (2019) "
        "proposed. Smith (2018) and Jones (2021) and Jones (2020) dominate the "
        "literature. Smith (2022) also verified these conclusions in a follow-up."
    )
    for flag in r.flags:
        assert hasattr(flag, "flag_type"),   "flag missing flag_type"
        assert hasattr(flag, "severity"),    "flag missing severity"
        assert hasattr(flag, "description"), "flag missing description"
        assert hasattr(flag, "evidence"),    "flag missing evidence"
        assert hasattr(flag, "suggestion"),  "flag missing suggestion"
        assert isinstance(flag.flag_type,   str)
        assert isinstance(flag.description, str)
        assert len(flag.description) > 0


def test_empty_text_safe():
    """Empty string returns safe zero-risk defaults without raising."""
    r = engine.analyze("")
    assert r.genealogy_score  == 0.0
    assert r.risk_level       == "low"
    assert r.flags_count      == 0
    assert r.ring_detected    is False
    assert r.doi_count        == 0


def test_no_citations_flag():
    """Text with no citations at all gets no_citations_detected flag."""
    r = engine.analyze(
        "This study examines the impact of climate change on agricultural output "
        "across sub-Saharan Africa using remote sensing data collected over ten years "
        "from multiple satellite platforms operating in low Earth orbit."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "no_citations_detected" in flag_types


def test_summary_not_empty():
    """Summary is a non-empty string for any valid input."""
    r = engine.analyze(
        "Smith (2021) showed X. Jones (2020) confirmed Y. Williams (2019) found Z."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 20


def test_ring_members_list():
    """Ring members is always a list and never crashes."""
    r = engine.analyze(
        "Smith (2020), Jones (2019), Williams (2021), Brown (2018), Davis (2022)."
    )
    assert isinstance(r.ring_members, list)
    assert r.unique_cited_authors >= 0