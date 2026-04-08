# tests/test_reproducibility_scanner.py

import pytest
from src.scipeerai.modules.reproducibility_scanner import (
    ReproducibilityScanner,
    ReproducibilityResult,
)


@pytest.fixture
def scanner():
    return ReproducibilityScanner()


# ── code availability ─────────────────────────────────────────

def test_detects_github_link(scanner):
    text = "Code available at https://github.com/researcher/study-code"
    result = scanner.analyze(text)
    assert result.has_code_link is True


def test_flags_missing_code_in_computational_paper(scanner):
    text = (
        "We implemented a deep learning algorithm using neural networks. "
        "The model was trained on GPU hardware. "
        "No external repository is mentioned."
    )
    result = scanner.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "missing_code_availability" in types


# ── data availability ─────────────────────────────────────────

def test_detects_osf_data_link(scanner):
    text = "Dataset available at https://osf.io/abc123 for replication."
    result = scanner.analyze(text)
    assert result.has_data_link is True


def test_flags_data_on_request(scanner):
    text = (
        "We collected data from 150 participants. "
        "Data available upon request from the corresponding author."
    )
    result = scanner.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "data_available_on_request" in types


# ── software versions ─────────────────────────────────────────

def test_detects_r_version(scanner):
    text = "Statistical analysis was performed using R version 4.3.1."
    result = scanner.analyze(text)
    assert result.has_software_versions is True


def test_detects_python_version(scanner):
    text = "All models were trained using Python 3.10 with PyTorch 2.0."
    result = scanner.analyze(text)
    assert result.has_software_versions is True


# ── ethics ────────────────────────────────────────────────────

def test_detects_ethics_statement(scanner):
    text = (
        "This study was approved by the Institutional Review Board "
        "of the University. All participants provided informed consent."
    )
    result = scanner.analyze(text)
    assert result.has_ethics_statement is True


def test_flags_missing_ethics_for_human_study(scanner):
    text = (
        "We recruited 80 participants for this experiment. "
        "Subjects completed a series of cognitive tasks."
    )
    result = scanner.analyze(text)
    types = [f.flag_type for f in result.flags]
    assert "missing_ethics_statement" in types


# ── result structure ──────────────────────────────────────────

def test_result_structure(scanner):
    result = scanner.analyze("A simple paper with no details.")
    assert isinstance(result, ReproducibilityResult)
    assert 0.0 <= result.reproducibility_score <= 1.0
    assert result.risk_level in ("low", "medium", "high", "critical")

def test_highly_reproducible_paper_low_risk(scanner):
    text = """
    Code available at https://github.com/lab/study.
    Dataset deposited at https://osf.io/xyz123.
    Analysis performed using R version 4.3.1.
    Ethics approval obtained from University IRB protocol 2023-045.
    Informed consent was obtained from all participants.
    This study was preregistered on OSF (osf.io/prereg123).
    No conflict of interest declared.
    Power analysis indicated n=120 required for 80% power.
    """
    result = scanner.analyze(text)
    assert result.reproducibility_score >= 0.7
    assert result.risk_level in ("low", "medium")