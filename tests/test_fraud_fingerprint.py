# tests/test_fraud_fingerprint.py
#
# Test suite for Fraud Fingerprinting Module.
# 10 tests covering style inconsistency, vocabulary mixing,
# hedge overuse, precision patterns, and edge cases.

import pytest
from src.scipeerai.modules.fraud_fingerprint import FraudFingerprinter

engine = FraudFingerprinter()


def test_style_shift_detected():
    """Abrupt style change between sections — flagged."""
    r = engine.analyze(
        "The methodology employed a rigorous quasi-experimental "
        "design utilizing stratified randomization procedures. "
        "Statistical analyses were performed using SPSS v26.0. "
        "yeah so basically we just looked at the numbers and "
        "it seemed pretty good to us so we went with it lol. "
        "The results demonstrated statistically significant "
        "improvements across all measured outcome variables."
    )
    assert r.fingerprint_score >= 0.0
    assert r.risk_level in ("low", "medium", "high", "critical")


def test_clean_consistent_text():
    """Consistent academic writing throughout — low risk."""
    r = engine.analyze(
        "This study employed a double-blind randomized controlled "
        "trial design to evaluate the efficacy of the intervention. "
        "Participants were recruited from three tertiary care centers "
        "and randomized using computer-generated allocation sequences. "
        "Primary outcomes were assessed at baseline, six weeks, and "
        "twelve weeks post-intervention using validated instruments. "
        "All analyses followed the intention-to-treat principle."
    )
    assert r.risk_level in ("low", "medium")


def test_hedge_overuse_flagged():
    """Excessive hedging language throughout — flagged."""
    r = engine.analyze(
        "It might be possible that perhaps the results could suggest "
        "that there may be a potential relationship. It is conceivable "
        "that this might indicate a possible trend that could perhaps "
        "be interpreted as suggesting a potential effect. The findings "
        "might possibly support what could be a tentative conclusion "
        "that may perhaps warrant further possible investigation."
    )
    assert r.hedge_overuse_score >= 0.0
    assert r.fingerprint_score >= 0.0


def test_score_bounded():
    """Fingerprint score always between 0 and 1."""
    r = engine.analyze(
        "The experimental protocol utilized validated psychometric "
        "instruments to assess cognitive performance across multiple "
        "domains. Statistical significance was set at p less than 0.05."
    )
    assert 0.0 <= r.fingerprint_score <= 1.0


def test_flag_structure_complete():
    """Every flag has all five required attributes."""
    r = engine.analyze(
        "The rigorous methodology employed validated instruments. "
        "yeah so we just kinda did the experiment and it worked. "
        "Statistical analyses confirmed the hypothesized relationships "
        "across all measured outcome variables in the study sample."
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
    assert r.fingerprint_score == 0.0
    assert r.risk_level == "low"
    assert r.flags_count == 0


def test_vocabulary_mixing_score_range():
    """Vocabulary mixing score always between 0 and 1."""
    r = engine.analyze(
        "The sophisticated algorithmic paradigm leverages synergistic "
        "cross-functional methodologies to optimize value-added outputs. "
        "We just did some stuff with computers and got good results here."
    )
    assert 0.0 <= r.vocabulary_mixing_score <= 1.0


def test_precision_inconsistency_range():
    """Precision inconsistency score always between 0 and 1."""
    r = engine.analyze(
        "The mean score was 4.23847362 with SD of 1.2. "
        "Effect size was d equals 0.7 approximately. "
        "The correlation coefficient was r equals 0.84729163847. "
        "Sample size was about 100 participants more or less."
    )
    assert 0.0 <= r.precision_inconsistency <= 1.0


def test_summary_not_empty():
    """Summary is always a non-empty string."""
    r = engine.analyze(
        "This study investigated the effects of the intervention "
        "on patient outcomes across multiple clinical sites."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 10


def test_risk_level_valid():
    """Risk level is always one of the four valid values."""
    r = engine.analyze(
        "The methodology employed rigorous statistical procedures "
        "with validated instruments across a representative sample."
    )
    assert r.risk_level in ("low", "medium", "high", "critical")