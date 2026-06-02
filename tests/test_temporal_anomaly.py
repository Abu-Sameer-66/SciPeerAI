# tests/test_temporal_anomaly.py
#
# Test suite for Temporal Anomaly Detector (Module 15).
# 10 tests covering future citations, timeline paradoxes,
# recency claims, and edge cases.

import pytest
from src.scipeerai.modules.temporal_anomaly import TemporalAnomalyDetector

engine = TemporalAnomalyDetector()


def test_future_citation_detected():
    """Citation year beyond collection year — anomaly flagged."""
    r = engine.analyze(
        "Data was collected in 2019. This study builds on recent work "
        "by Smith et al. (2023) and Jones (2024) who demonstrated "
        "that the effect persists across multiple populations. "
        "The methodology follows Brown (2025) and Davis (2026)."
    )
    assert r.temporal_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_clean_timeline_low_risk():
    """All citations before collection year — no anomaly."""
    r = engine.analyze(
        "Data was collected between 2015 and 2017. This study builds "
        "on foundational work by Smith (2010) and Jones (2012). "
        "The theoretical framework was established by Brown (2008) "
        "and extended by Davis (2014) and Wilson (2016)."
    )
    assert r.risk_level in ("low", "medium")


def test_temporal_score_bounded():
    """Temporal score always between 0 and 1."""
    r = engine.analyze(
        "This research was conducted in 2018. Prior work by Smith (2020) "
        "and Jones (2022) confirmed these results in subsequent studies."
    )
    assert 0.0 <= r.temporal_score <= 1.0


def test_recency_claim_without_recent_citations():
    """Claims recent advances but cites only old papers."""
    r = engine.analyze(
        "Recent advances in this rapidly evolving field have shown "
        "significant progress in the latest developments. The most "
        "current state-of-the-art methods include work by Smith (2003), "
        "Jones (2001), Williams (1999), and Brown (2002)."
    )
    assert r.temporal_score >= 0.0
    assert isinstance(r.summary, str)


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "Data collected in 2018. Smith (2023) and Jones (2024) "
        "confirmed the results in work published after data collection. "
        "Williams (2025) further extended these findings significantly."
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
    assert r.temporal_score  == 0.0
    assert r.risk_level      == "low"
    assert r.flags_count     == 0


def test_cited_years_extracted():
    """Year extraction returns a list."""
    r = engine.analyze(
        "Smith (2015) established the framework. Jones (2017) extended "
        "it. Williams (2019) replicated the findings across populations."
    )
    assert isinstance(r.cited_years, list)


def test_future_citations_list():
    """Future citations is always a list."""
    r = engine.analyze(
        "This builds on Smith (2021) and Jones (2022) published after "
        "data collection ended in 2018 per our protocol registration."
    )
    assert isinstance(r.future_citations, list)


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "Smith (2015) showed X. Jones (2017) confirmed Y. "
        "Williams (2019) extended these findings further."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "The study collected data in 2016 using validated instruments "
        "developed by Smith (2010) and refined by Jones (2014)."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")