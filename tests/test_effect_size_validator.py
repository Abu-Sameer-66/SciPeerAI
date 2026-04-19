# tests/test_effect_size_validator.py
#
# Test suite for Effect Size Validator.
# 8 tests covering inflated effects, underpowered studies,
# missing effect sizes, impossible r values, and risk levels.

import pytest
from src.scipeerai.modules.effect_size_validator import EffectSizeValidator

engine = EffectSizeValidator()


def test_inflated_effect_detected():
    """Cohen d=3.2 with N=12 — critical risk."""
    r = engine.analyze(
        "Cohen d = 3.2 with n=12 participants. "
        "Results were significant p=0.049."
    )
    assert len(r.inflated_effects) >= 1
    assert r.risk_level == "critical"


def test_reasonable_effect_passes():
    """Cohen d=0.5 with N=80 — low risk."""
    r = engine.analyze(
        "Cohen d = 0.50 with n=80 participants. "
        "Results showed significant improvement p=0.032."
    )
    assert len(r.inflated_effects) == 0
    assert r.risk_level in ("low", "medium")


def test_missing_effect_sizes_flagged():
    """No effect sizes reported — medium risk."""
    r = engine.analyze(
        "This study examined the effect of treatment "
        "on outcomes in n=45 participants. Results "
        "showed significant improvement with p=0.03."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "missing_effect_sizes" in flag_types


def test_underpowered_study_detected():
    """Small d with small N — underpowered."""
    r = engine.analyze(
        "Cohen d = 0.30 with n=15 participants. "
        "Significant result found p=0.048."
    )
    assert r.flags_count >= 1


def test_effect_score_range():
    """Score must be between 0 and 1."""
    r = engine.analyze(
        "Cohen d = 3.2 with n=12 participants "
        "showing significant effects p=0.049."
    )
    assert 0.0 <= r.effect_score <= 1.0


def test_flag_structure():
    """Flags have correct required fields."""
    r = engine.analyze(
        "Cohen d = 3.2 with n=12 participants. "
        "Results were significant p=0.049."
    )
    assert r.flags_count >= 1
    flag = r.flags[0]
    assert hasattr(flag, 'flag_type')
    assert hasattr(flag, 'severity')
    assert hasattr(flag, 'description')
    assert hasattr(flag, 'evidence')
    assert hasattr(flag, 'suggestion')


def test_summary_contains_key_info():
    """Summary mentions effect sizes and risk level."""
    r = engine.analyze(
        "Cohen d = 3.2 with n=12 participants. "
        "Results were significant p=0.049."
    )
    assert "Effect Size" in r.summary
    assert r.risk_level.upper() in r.summary


def test_power_estimation_calculated():
    """Power estimates calculated for Cohen d."""
    r = engine.analyze(
        "Cohen d = 0.50 with n=20 participants. "
        "Significant improvement found p=0.035."
    )
    assert len(r.power_estimates) >= 1
    assert "power" in r.power_estimates[0]