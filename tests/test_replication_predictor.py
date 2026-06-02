# tests/test_replication_predictor.py
#
# Test suite for Replication Predictor (Module 21).
# 10 tests covering ensemble ML prediction, probability bounds,
# verdict generation, flag structure, and edge cases.
# Note: rf_v2.pkl is local-only — tests handle UNKNOWN fallback.

import pytest
from src.scipeerai.modules.replication_predictor import analyze

_VALID_RISK = ("low", "medium", "high", "critical", "UNKNOWN")


def _make_scores(val=0.0):
    return {
        "score_stat":        val,
        "score_method":      val,
        "score_citation":    val,
        "score_repro":       val,
        "score_novelty":     val,
        "score_grim":        val,
        "score_sprite":      val,
        "score_granularity": val,
        "score_pcurve":      val,
        "score_effect":      val,
        "score_retraction":  val,
        "score_cartel":      val,
        "score_llm":         val,
        "score_fraud":       val,
        "score_temporal":    val,
        "score_dna":         val,
        "score_dataprint":   val,
        "score_peerreview":  val,
        "score_spectrum":    val,
    }


def test_high_risk_scores_run():
    """High risk scores — module runs without raising."""
    scores = _make_scores(0.9)
    r = analyze(scores, text="High risk paper with many fraud signals detected.")
    assert r.replication_probability >= 0.0
    assert r.fraud_probability >= 0.0


def test_low_risk_scores_run():
    """All clean scores — module runs without raising."""
    scores = _make_scores(0.0)
    r = analyze(scores, text="Clean paper with no fraud signals detected.")
    assert r.replication_probability >= 0.0
    assert r.risk_level in _VALID_RISK


def test_replication_probability_bounded():
    """Replication probability always between 0 and 1."""
    scores = _make_scores(0.5)
    r = analyze(scores, text="Mixed signals paper with moderate risk scores.")
    assert 0.0 <= r.replication_probability <= 1.0


def test_fraud_probability_bounded():
    """Fraud probability always between 0 and 1."""
    scores = _make_scores(0.5)
    r = analyze(scores, text="Mixed signals paper with moderate risk scores.")
    assert 0.0 <= r.fraud_probability <= 1.0


def test_probabilities_non_negative():
    """Both probabilities are non-negative in all cases."""
    scores = _make_scores(0.3)
    r = analyze(scores, text="Paper with moderate statistical risk signals.")
    assert r.replication_probability >= 0.0
    assert r.fraud_probability >= 0.0


def test_verdict_is_string():
    """Verdict is always a string regardless of model state."""
    scores = _make_scores(0.4)
    r = analyze(scores, text="Paper under evaluation for replication risk.")
    assert isinstance(r.verdict, str)


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    scores = _make_scores(0.8)
    r = analyze(scores, text="Very high risk paper with extreme fraud signals.")
    for flag in r.flags:
        assert "flag_type"   in flag
        assert "severity"    in flag
        assert "description" in flag
        assert "evidence"    in flag
        assert "suggestion"  in flag


def test_model_version_string():
    """Model version is always a non-empty string."""
    scores = _make_scores(0.2)
    r = analyze(scores, text="Paper with low risk scores across all modules.")
    assert isinstance(r.model_version, str)
    assert len(r.model_version) > 0


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    scores = _make_scores(0.3)
    r = analyze(scores, text="Paper being evaluated for scientific integrity.")
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the valid values including UNKNOWN."""
    scores = _make_scores(0.5)
    r = analyze(scores, text="Paper with mixed integrity signals throughout.")
    assert r.risk_level in _VALID_RISK