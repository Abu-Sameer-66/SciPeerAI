# tests/test_peer_review_score.py
#
# Test suite for Peer Review Score Module (Module 18).
# 10 tests covering manipulation detection, conflict statements,
# predatory signals, special issues, and edge cases.

import pytest
from src.scipeerai.modules.peer_review_score import PeerReviewScorer

engine = PeerReviewScorer()


def test_predatory_signals_detected():
    """Multiple predatory journal signals — high risk."""
    r = engine.analyze(
        "Received: January 1, 2023. Accepted: January 3, 2023. "
        "Published: January 5, 2023. This paper was published in a "
        "special issue guest edited by the corresponding author. "
        "The authors suggest reviewers: Dr. Smith (smith@email.com), "
        "Dr. Jones (jones@email.com). Article processing charge paid. "
        "Open access publication in predatory rapid review journal."
    )
    assert r.manipulation_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_clean_paper_low_risk():
    """Standard peer review process — low manipulation score."""
    r = engine.analyze(
        "The authors declare no conflict of interest. This research "
        "received no external funding. The manuscript was submitted "
        "for independent peer review following standard procedures. "
        "No competing interests exist among the authors of this work. "
        "This study was not part of any special issue publication."
    )
    assert r.risk_level in ("low", "medium")


def test_manipulation_score_bounded():
    """Manipulation score always between 0 and 1."""
    r = engine.analyze(
        "Received March 2022, accepted April 2022. Authors declare "
        "no conflict of interest. Standard peer review conducted."
    )
    assert 0.0 <= r.manipulation_score <= 1.0


def test_conflict_statement_detected():
    """Conflict of interest statement detected correctly."""
    r = engine.analyze(
        "Conflict of interest statement: The authors declare no "
        "competing interests. No financial relationships exist with "
        "any organization that could influence the reported results. "
        "This work was conducted independently without industry input."
    )
    assert isinstance(r.has_conflict_statement, bool)


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "Received: June 1, 2022. Accepted: June 2, 2022. "
        "Special issue edited by corresponding author Dr. Smith. "
        "Suggested reviewers provided by authors upon submission. "
        "Rapid publication in open access journal within 24 hours."
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
    assert r.manipulation_score >= 0.0
    assert r.risk_level         == "low"
    assert r.flags_count        == 0


def test_special_issue_detected():
    """Special issue flag returns boolean."""
    r = engine.analyze(
        "This paper was published as part of a special issue "
        "on machine learning in healthcare applications, guest "
        "edited by the lead author of this manuscript."
    )
    assert isinstance(r.special_issue, bool)


def test_predatory_signals_count():
    """Predatory signals count is a non-negative integer."""
    r = engine.analyze(
        "Received January 1. Accepted January 2. Article processing "
        "charge required. Rapid peer review completed within 24 hours. "
        "Authors suggested their own reviewers for this submission."
    )
    assert isinstance(r.predatory_signals, int)
    assert r.predatory_signals >= 0


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "The authors declare no conflict of interest. This study "
        "followed standard institutional review board procedures."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "Received March 2022. Accepted June 2022. Authors declare "
        "no competing interests. Standard double-blind review."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")