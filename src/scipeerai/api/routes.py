# API routes for SciPeerAI
# Each route connects an HTTP endpoint to an analysis module.
# Keeping routes separate from app factory — clean separation of concerns.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.scipeerai.modules.stat_audit import StatAuditEngine


# one router for all analysis endpoints — we'll add more modules here later
router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# initialize once at module level — no need to rebuild on every request
_stat_engine = StatAuditEngine()


# ── request / response models ─────────────────────────────────────────────────

class TextAnalysisRequest(BaseModel):
    """
    What the client sends us.
    Using Pydantic model — automatic validation, automatic docs.
    If someone sends an empty string, FastAPI rejects it before
    it even reaches our code.
    """
    text: str = Field(
        ...,
        min_length=50,
        description="The paper text to analyze — paste abstract or full text",
        example=(
            "We recruited n=12 participants for this study. "
            "Results showed significant improvement (p=0.048). "
            "Secondary outcomes were also significant (p=0.049)."
        )
    )


class FlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


class StatAuditResponse(BaseModel):
    """
    What we send back.
    Clean, typed, documented — this shows up automatically in /docs.
    """
    risk_level: str
    risk_score: float
    summary: str
    flags: list[FlagResponse]
    p_values_found: list[float]
    sample_sizes_found: list[int]
    flags_count: int


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/status")
def system_status():
    return {
        "modules": [
            "stat_audit",
            "figure_forensics",
            "methodology_checker",
            "citation_analyzer",
            "reproducibility",
            "novelty_scorer"
        ],
        "modules_ready": {
            "stat_audit": True,
            "figure_forensics": False,
            "methodology_checker": False,
            "citation_analyzer": False,
            "reproducibility": False,
            "novelty_scorer": False,
        },
        "version": "0.1.0"
    }


@router.post("/analyze/statistics", response_model=StatAuditResponse)
def analyze_statistics(request: TextAnalysisRequest):
    """
    Analyze paper text for statistical integrity issues.

    Detects:
    - p-hacking (suspicious clustering near 0.05)
    - Underpowered sample sizes
    - Suspiciously round p-values
    - Missing statistical tests despite significance claims

    Returns a risk score from 0.0 (clean) to 1.0 (critical).
    """
    try:
        result = _stat_engine.analyze(request.text)

        flags_out = [
            FlagResponse(
                flag_type=f.flag_type,
                severity=f.severity,
                description=f.description,
                evidence=f.evidence,
                suggestion=f.suggestion,
            )
            for f in result.flags
        ]

        return StatAuditResponse(
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags=flags_out,
            p_values_found=result.p_values_found,
            sample_sizes_found=result.sample_sizes_found,
            flags_count=len(result.flags),
        )

    except Exception as e:
        # never expose raw exception to client — log it, return clean error
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )