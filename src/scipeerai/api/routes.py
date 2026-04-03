# src/scipeerai/api/routes.py
#
# All API routes for SciPeerAI.
# Two types of endpoints here:
#   - Text-based  (stat audit  — user pastes paper text)
#   - File-based  (figure forensics — user uploads PDF)

import os
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from src.scipeerai.modules.stat_audit import StatAuditEngine
from src.scipeerai.modules.figure_forensics import FigureForensicsEngine


router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# initialize engines once — not on every request
_stat_engine   = StatAuditEngine()
_figure_engine = FigureForensicsEngine()


# ── request / response models ─────────────────────────────────────────────────

class TextAnalysisRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=50,
        description="Paper text to analyze for statistical issues",
        example=(
            "We recruited n=12 participants. "
            "Results were significant (p=0.048). "
            "Secondary outcome also significant (p=0.049)."
        )
    )


class FlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str = ""


class ForensicFlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    figures_involved: list


class StatAuditResponse(BaseModel):
    risk_level: str
    risk_score: float
    summary: str
    flags: list[FlagResponse]
    p_values_found: list[float]
    sample_sizes_found: list[int]
    flags_count: int


class FigureForensicsResponse(BaseModel):
    figures_found: int
    risk_level: str
    risk_score: float
    summary: str
    flags: list[ForensicFlagResponse]
    duplicate_pairs: list
    flags_count: int


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.get("/status")
def system_status():
    return {
        "modules_ready": {
            "stat_audit":          True,
            "figure_forensics":    True,
            "methodology_checker": False,
            "citation_analyzer":   False,
            "reproducibility":     False,
            "novelty_scorer":      False,
        },
        "version": "0.1.0",
    }


@router.post("/analyze/statistics", response_model=StatAuditResponse)
def analyze_statistics(request: TextAnalysisRequest):
    """
    Analyze paper text for statistical integrity issues.

    Detects p-hacking, underpowered studies, suspiciously
    round p-values, and missing statistical tests.
    Returns a risk score from 0.0 (clean) to 1.0 (critical).
    """
    try:
        result = _stat_engine.analyze(request.text)
        return StatAuditResponse(
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags=[
                FlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                )
                for f in result.flags
            ],
            p_values_found=result.p_values_found,
            sample_sizes_found=result.sample_sizes_found,
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/figures", response_model=FigureForensicsResponse)
async def analyze_figures(file: UploadFile = File(...)):
    """
    Upload a PDF and analyze all figures for forensic anomalies.

    Detects:
    - Duplicate/recycled figures across the paper
    - Digital editing artifacts (Error Level Analysis)
    - Unnatural brightness uniformity

    Returns forensic flags with evidence for each suspicious figure.
    """
    # validate file type before doing anything else
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted."
        )

    # write upload to a temp file — figure engine needs a real path
    # tempfile handles cleanup automatically when the block exits
    try:
        contents = await file.read()

        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        result = _figure_engine.analyze(tmp_path)

        return FigureForensicsResponse(
            figures_found=result.figures_found,
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags=[
                ForensicFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    figures_involved=f.figures_involved,
                )
                for f in result.flags
            ],
            duplicate_pairs=result.duplicate_pairs,
            flags_count=len(result.flags),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # always clean up temp file — even if analysis crashed
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)