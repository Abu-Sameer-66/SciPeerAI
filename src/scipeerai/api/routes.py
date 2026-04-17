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
from src.scipeerai.modules.reproducibility_scanner import ReproducibilityScanner
from src.scipeerai.modules.stat_audit import StatAuditEngine
from src.scipeerai.modules.figure_forensics import FigureForensicsEngine
from src.scipeerai.modules.methodology_checker import MethodologyChecker
from src.scipeerai.modules.citation_analyzer import CitationAnalyzer
from src.scipeerai.modules.novelty_scorer import NoveltyScorer
router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# initialize engines once — not on every request
_stat_engine   = StatAuditEngine()
_figure_engine = FigureForensicsEngine()
_method_engine = MethodologyChecker()
_citation_engine = CitationAnalyzer()
_repro_engine    = ReproducibilityScanner()
_novelty_engine  = NoveltyScorer()
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
            "methodology_checker": True,
            "citation_analyzer":   True,
            "reproducibility":     True,
            "novelty_scorer":      True,
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
            
            
class MethodologyRequest(BaseModel):
    text: str = Field(..., min_length=50,
                      description="Full paper text for methodology analysis")
    abstract: str = Field("", description="Abstract separately (optional but recommended)")


class MethodologyFlagResponse(BaseModel):
    flag_type: str
    severity: str
    claim: str
    issue: str
    evidence: str
    suggestion: str


class MethodologyResponse(BaseModel):
    risk_level: str
    risk_score: float
    summary: str
    flags: list[MethodologyFlagResponse]
    claims_found: list[str]
    methods_found: list[str]
    llm_assessment: str
    llm_available: bool
    flags_count: int


@router.post("/analyze/methodology", response_model=MethodologyResponse)
def analyze_methodology(request: MethodologyRequest):
    """
    Analyze paper text for methodology logic issues.

    Detects: causation claims without RCT, missing control groups,
    timeframe mismatches, weak design with strong claims,
    overgeneralization. Includes LLM reasoning if HF token configured.
    """
    try:
        result = _method_engine.analyze(request.text, request.abstract)
        return MethodologyResponse(
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags=[
                MethodologyFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    claim=f.claim,
                    issue=f.issue,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                )
                for f in result.flags
            ],
            claims_found=result.claims_found,
            methods_found=result.methods_found,
            llm_assessment=result.llm_assessment,
            llm_available=result.llm_available,
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class CitationRequest(BaseModel):
    text: str = Field(..., min_length=50,
                      description="Full paper text for citation analysis")
    author_name: str = Field("",
                             description="Primary author name for self-citation detection")


class CitationFlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


class CitationResponse(BaseModel):
    total_citations: int
    self_citations: int
    self_citation_ratio: float
    unsupported_claims: int
    risk_level: str
    risk_score: float
    summary: str
    flags: list[CitationFlagResponse]
    flags_count: int


@router.post("/analyze/citations", response_model=CitationResponse)
def analyze_citations(request: CitationRequest):
    """
    Analyze paper citations for integrity issues.

    Detects: excessive self-citation, unsupported broad claims,
    low citation density, et al. overuse.
    Optionally checks author name for self-citation patterns.
    """
    try:
        result = _citation_engine.analyze(
            request.text, request.author_name
        )
        return CitationResponse(
            total_citations=result.total_citations,
            self_citations=result.self_citations,
            self_citation_ratio=result.self_citation_ratio,
            unsupported_claims=result.unsupported_claims,
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags=[
                CitationFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                )
                for f in result.flags
            ],
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
class ReproducibilityRequest(BaseModel):
    text: str = Field(..., min_length=50,
                      description="Full paper text for reproducibility analysis")


class ReproducibilityFlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


class ReproducibilityResponse(BaseModel):
    has_code_link: bool
    has_data_link: bool
    has_software_versions: bool
    has_preregistration: bool
    has_ethics_statement: bool
    reproducibility_score: float
    risk_level: str
    summary: str
    flags: list[ReproducibilityFlagResponse]
    flags_count: int


@router.post("/analyze/reproducibility", response_model=ReproducibilityResponse)
def analyze_reproducibility(request: ReproducibilityRequest):
    """
    Scan paper for reproducibility indicators.

    Checks: code availability, data availability,
    software versions, preregistration, ethics statements.
    Returns a reproducibility score (0-1) and missing items.
    """
    try:
        result = _repro_engine.analyze(request.text)
        return ReproducibilityResponse(
            has_code_link=result.has_code_link,
            has_data_link=result.has_data_link,
            has_software_versions=result.has_software_versions,
            has_preregistration=result.has_preregistration,
            has_ethics_statement=result.has_ethics_statement,
            reproducibility_score=result.reproducibility_score,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                ReproducibilityFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                )
                for f in result.flags
            ],
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
_novelty_engine = NoveltyScorer()
class NoveltyRequest(BaseModel):
    text: str = Field(..., min_length=50,
                      description="Full paper text for novelty analysis")
    title: str = Field("", description="Paper title for better search accuracy")


class NoveltyFlagResponse(BaseModel):
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


class RelatedWorkResponse(BaseModel):
    title: str
    year: int
    authors: list
    similarity_signal: str


class NoveltyResponse(BaseModel):
    novelty_score: float
    novelty_level: str
    risk_level: str
    summary: str
    flags: list[NoveltyFlagResponse]
    related_works_found: list[RelatedWorkResponse]
    key_terms_extracted: list[str]
    literature_accessible: bool
    flags_count: int


@router.post("/analyze/novelty", response_model=NoveltyResponse)
def analyze_novelty(request: NoveltyRequest):
    """
    Estimate paper novelty against existing literature.

    Uses structural language analysis + Semantic Scholar API
    to estimate how novel the contribution is.
    Returns novelty score 0.0 (not novel) to 1.0 (highly novel).
    """
    try:
        result = _novelty_engine.analyze(request.text, request.title)
        return NoveltyResponse(
            novelty_score=result.novelty_score,
            novelty_level=result.novelty_level,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                NoveltyFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                )
                for f in result.flags
            ],
            related_works_found=[
                RelatedWorkResponse(
                    title=w.title,
                    year=w.year,
                    authors=w.authors,
                    similarity_signal=w.similarity_signal,
                )
                for w in result.related_works_found
            ],
            key_terms_extracted=result.key_terms_extracted,
            literature_accessible=result.literature_accessible,
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
