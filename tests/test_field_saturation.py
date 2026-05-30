# tests/test_field_saturation.py
#
# Test suite for Field Saturation Detector (Module 23).
# 10 tests covering saturation detection, redundancy,
# novelty claims, vagueness, and edge cases.

import pytest
from src.scipeerai.modules.field_saturation import FieldSaturationDetector

engine = FieldSaturationDetector()


def test_saturated_field_detected():
    """Paper acknowledges crowded field yet claims novelty — high risk."""
    r = engine.analyze(
        "Many studies have investigated deep learning for image classification. "
        "Extensive research has been conducted in this well-studied area. "
        "Numerous studies confirm the effectiveness of CNNs. There is a large body "
        "of literature on this topic. Despite this considerable research, we propose "
        "a novel innovative breakthrough framework that significantly improves and "
        "enhances performance with unprecedented results outperforming all baselines."
    )
    assert r.saturation_score > 0.30
    assert r.overcrowding_signals >= 2


def test_fresh_field_low_risk():
    """Specific technical contribution in narrow domain — low saturation."""
    r = engine.analyze(
        "We introduce a cross-modal alignment mechanism for protein folding "
        "prediction under thermal stress conditions at 340K. The binding affinity "
        "predictor uses torsion angle constraints derived from molecular dynamics "
        "simulations. Validation on 847 crystal structures shows RMSD of 1.2 angstroms. "
        "No prior work has addressed thermal-stress folding at this resolution."
    )
    assert r.risk_level in ("low", "medium")


def test_vague_contribution_flagged():
    """Generic improvement language without specifics — flagged."""
    r = engine.analyze(
        "Our method improves performance significantly. The proposed approach "
        "enhances accuracy and achieves better results than existing methods. "
        "We outperform competitive baselines with superior efficiency. "
        "The framework achieves higher performance with more effective optimization. "
        "Results demonstrate significant improvement over state-of-the-art approaches."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "vague_contribution_language" in flag_types


def test_overclaimed_novelty_flagged():
    """Too many novelty buzzwords — overclaimed novelty flag."""
    r = engine.analyze(
        "We present a novel innovative first-of-its-kind breakthrough approach. "
        "This pioneering unique original method is unprecedented in the literature. "
        "Our revolutionary cutting-edge state-of-the-art framework is truly novel. "
        "We introduce a new method that is innovative and original in every way. "
        "This first-ever unique approach represents a significant breakthrough."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "overclaimed_novelty" in flag_types


def test_saturation_score_bounded():
    """Score always between 0 and 1."""
    r = engine.analyze(
        "Many studies have explored this well-studied area extensively. "
        "We propose a novel innovative unique breakthrough method that improves "
        "performance significantly and outperforms all prior approaches."
    )
    assert 0.0 <= r.saturation_score <= 1.0


def test_flag_structure_complete():
    """Every flag has all five required fields."""
    r = engine.analyze(
        "Many studies have investigated this. Extensive research exists. "
        "We propose a novel innovative approach that improves performance. "
        "Our method enhances results and outperforms existing techniques significantly."
    )
    for flag in r.flags:
        assert hasattr(flag, "flag_type")
        assert hasattr(flag, "severity")
        assert hasattr(flag, "description")
        assert hasattr(flag, "evidence")
        assert hasattr(flag, "suggestion")
        assert len(flag.description) > 0


def test_empty_text_safe():
    """Empty input returns safe defaults without crashing."""
    r = engine.analyze("")
    assert r.saturation_score  == 0.0
    assert r.risk_level        == "low"
    assert r.flags_count       == 0
    assert r.overcrowding_signals == 0


def test_keywords_extracted():
    """Topic keywords extracted from content-rich text."""
    r = engine.analyze(
        "Deep learning neural networks convolutional architecture transformer "
        "attention mechanism classification detection segmentation benchmark "
        "dataset evaluation training optimization gradient descent loss function."
    )
    assert isinstance(r.topic_keywords, list)
    assert r.keyword_density >= 0.0


def test_redundancy_detected():
    """Highly repetitive text gets high redundancy score."""
    r = engine.analyze(
        "The proposed method achieves better results on the benchmark dataset. "
        "Our approach achieves better results using the proposed method on dataset. "
        "Results show our method achieves better performance on the benchmark. "
        "The benchmark dataset shows better results for the proposed approach. "
        "Our proposed method achieves better benchmark dataset results overall."
    )
    assert r.redundancy_score > 0.0


def test_summary_not_empty():
    """Summary is always a non-empty string."""
    r = engine.analyze(
        "We investigate deep learning methods for natural language processing tasks."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 20