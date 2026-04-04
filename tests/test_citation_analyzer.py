# tests/test_citation_analyzer.py

import pytest
from src.scipeerai.modules.citation_analyzer import (
    CitationAnalyzer,
    CitationResult,
)


@pytest.fixture
def analyzer():
    return CitationAnalyzer()


# ── citation extraction ───────────────────────────────────────

def test_extracts_bracketed_citations(analyzer):
    text = "Previous work [1] showed this. Another study [2,3] confirmed."
    result = analyzer.analyze(text)
    assert result.total_citations >= 2


def test_extracts_author_year_citations(analyzer):
    text = "As shown by (Smith, 2020) and later (Jones et al., 2021)."
    result = analyzer.analyze(text)
    assert result.total_citations >= 1


# ── self citation ─────────────────────────────────────────────

def test_flags_excessive_self_citation(analyzer):
    text = """
    As we showed previously (Nadeem, 2022), this effect holds.
    Our earlier work (Nadeem, 2021) established the baseline.
    We demonstrated this in (Nadeem et al 2020) as well.
    Further evidence from (Nadeem, 2019) confirms [1][2][3].
    Independent study [4] also agrees with our framework.
    """
    result = analyzer.analyze(text, author_name="Sameer Nadeem")
    types = [f.flag_type for f in result.flags]
    assert (
        "excessive_self_citation" in types
        or "high_self_citation_ratio" in types
    )


# ── unsupported claims ────────────────────────────────────────

def test_flags_unsupported_claims(analyzer):
    text = """
    Studies show that exercise improves memory.
    It is well known that sleep affects performance.
    Research shows that diet impacts cognition.
    Evidence suggests that stress causes disease.
    """
    result = analyzer.analyze(text)
    assert result.unsupported_claims >= 2


def test_cited_claims_not_flagged(analyzer):
    text = (
        "As demonstrated by (Smith, 2020), exercise improves memory. "
        "Sleep affects performance [1]. Diet impacts cognition (Jones, 2019)."
    )
    result = analyzer.analyze(text)
    assert result.unsupported_claims == 0


# ── result structure ──────────────────────────────────────────

def test_result_structure(analyzer):
    result = analyzer.analyze("A simple paper with no citations.")
    assert isinstance(result, CitationResult)
    assert 0.0 <= result.risk_score <= 1.0
    assert result.risk_level in ("low", "medium", "high", "critical")
    assert result.self_citation_ratio >= 0.0


def test_empty_text_safe(analyzer):
    result = analyzer.analyze("")
    assert result.total_citations == 0
    assert result.risk_score == 0.0