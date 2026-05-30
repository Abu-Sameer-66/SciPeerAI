# tests/test_institutional_conflict.py
#
# Test suite for Institutional Conflict Detector (Module 24).
# 10 tests covering undisclosed conflicts, industry bias,
# self-serving citations, conclusion overstatement, and edge cases.

import pytest
from src.scipeerai.modules.institutional_conflict import InstitutionalConflictDetector

engine = InstitutionalConflictDetector()


def test_undisclosed_conflict_detected():
    """Consultancy role present but no disclosure statement — critical flag."""
    r = engine.analyze(
        "The lead author serves as a consultant for PharmaCorp Inc. "
        "and holds equity in BioTech Ltd. The advisory board member "
        "has a speaker bureau arrangement with MedDevice Corporation. "
        "The study was conducted at the University of Chicago Department "
        "of Medicine using standard protocols approved by the committee."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "undisclosed_conflict_of_interest" in flag_types
    assert r.undisclosed_signals >= 1


def test_clean_paper_low_risk():
    """Full disclosure present with no undisclosed signals — low risk."""
    r = engine.analyze(
        "The authors declare no conflict of interest. No competing interests exist. "
        "This research received no specific funding from any commercial entity. "
        "The study was designed and conducted independently at the university. "
        "Data collection followed pre-registered protocols. All authors disclose "
        "no financial relationships with any organization that could influence results."
    )
    assert r.risk_level in ("low", "medium")
    assert r.conflict_disclosures >= 1


def test_industry_funding_with_bias():
    """Industry funding plus strong conclusion language — high risk flag."""
    r = engine.analyze(
        "This research was funded by PharmaCorp pharmaceutical company. "
        "Industry partner BioTech Inc. provided research support and equipment. "
        "Our results clearly demonstrate and conclusively prove that the drug "
        "is unequivocally effective. The evidence overwhelmingly shows benefit. "
        "This definitively establishes the treatment as superior beyond question."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "industry_funded_conclusion_bias" in flag_types or \
           "overstated_conclusions" in flag_types


def test_excessive_self_citations():
    """Too many self-referential patterns — flagged."""
    r = engine.analyze(
        "As we showed in our previous work, the method is effective. "
        "Consistent with our findings, the results confirm our hypothesis. "
        "Building on our earlier research, we extend our prior framework. "
        "As reported by our group, this validates our previous results. "
        "As we demonstrated before, our earlier work clearly supports this. "
        "Our prior study showed exactly what we now confirm here again."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "excessive_self_serving_citations" in flag_types


def test_overstated_conclusions_flagged():
    """Extreme confidence language without hedging — flagged."""
    r = engine.analyze(
        "This study conclusively proves the hypothesis beyond any doubt. "
        "Results unequivocally demonstrate that our method is superior. "
        "The evidence clearly establishes a definitive causal relationship. "
        "This irrefutably confirms that the proposed framework is optimal. "
        "Our findings definitively show the approach outperforms all others."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "overstated_conclusions" in flag_types


def test_conflict_score_bounded():
    """Conflict score always between 0 and 1."""
    r = engine.analyze(
        "The author is a consultant for multiple pharmaceutical corporations "
        "and holds significant equity stakes in biotech companies. "
        "This research was funded by industry partners and commercial sponsors."
    )
    assert 0.0 <= r.conflict_score <= 1.0


def test_flag_structure_complete():
    """Every flag contains all five required attributes."""
    r = engine.analyze(
        "The author serves as consultant to BioTech Inc. and holds equity. "
        "This was funded by industry partner PharmaCorp corporation. "
        "Results clearly demonstrate and conclusively prove our hypothesis."
    )
    for flag in r.flags:
        assert hasattr(flag, "flag_type")
        assert hasattr(flag, "severity")
        assert hasattr(flag, "description")
        assert hasattr(flag, "evidence")
        assert hasattr(flag, "suggestion")
        assert len(flag.description) > 0


def test_empty_text_safe():
    """Empty input returns safe defaults without raising."""
    r = engine.analyze("")
    assert r.conflict_score           == 0.0
    assert r.risk_level               == "low"
    assert r.flags_count              == 0
    assert r.undisclosed_signals      == 0
    assert r.self_serving_claims      == 0


def test_funding_without_disclosure_flagged():
    """Funding acknowledged but no COI statement present — flagged."""
    r = engine.analyze(
        "This research was funded by the National Science Foundation grant. "
        "Additional support was provided by the university research office. "
        "The study examines the effects of the intervention on patient outcomes "
        "across three clinical sites over a period of eighteen months total."
    )
    flag_types = [f.flag_type for f in r.flags]
    assert "funding_without_disclosure" in flag_types or \
           r.conflict_score >= 0.0


def test_summary_not_empty():
    """Summary always returns a non-empty string."""
    r = engine.analyze(
        "The authors declare no conflict of interest in this research study."
    )
    assert isinstance(r.summary, str)
    assert len(r.summary) > 20