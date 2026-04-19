# src/scipeerai/api/routes.py
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
from src.scipeerai.modules.grim_test import GrimTest
from src.scipeerai.modules.sprite_test import SpriteTest
from src.scipeerai.modules.granularity_analyzer import GranularityAnalyzer
from src.scipeerai.modules.pcurve_analyzer import PCurveAnalyzer
from src.scipeerai.modules.effect_size_validator import EffectSizeValidator

router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# ── Smart text truncation — handles long papers ───────────────────────────────
def _truncate(text: str, limit: int = 8000) -> str:
    """Smart truncation — keeps abstract + methods sections."""
    if len(text) <= limit:
        return text
    lower = text.lower()
    methods_idx = lower.find('method')
    if methods_idx > 0 and methods_idx < len(text) - 1000:
        start  = text[:3000]
        middle = text[methods_idx:methods_idx + 4000]
        return start + " [...] " + middle
    return text[:limit]

# ── Engine initialization ─────────────────────────────────────────────────────
_stat_engine        = StatAuditEngine()
_figure_engine      = FigureForensicsEngine()
_method_engine      = MethodologyChecker()
_citation_engine    = CitationAnalyzer()
_repro_engine       = ReproducibilityScanner()
_novelty_engine     = NoveltyScorer()
_grim_engine        = GrimTest()
_sprite_engine      = SpriteTest()
_granularity_engine = GranularityAnalyzer()
_pcurve_engine         = PCurveAnalyzer()
_effect_size_engine    = EffectSizeValidator()

# ── Request / Response Models ─────────────────────────────────────────────────

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=50, description="Paper text to analyze")

class FlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str = ""

class ForensicFlagResponse(BaseModel):
    figures_involved: list

class StatAuditResponse(BaseModel):
    risk_level:         str
    risk_score:         float
    summary:            str
    flags:              list[FlagResponse]
    p_values_found:     list[float]
    sample_sizes_found: list[int]
    flags_count:        int

class FigureForensicsResponse(BaseModel):
    figures_found:   int
    flags:           list[ForensicFlagResponse]
    duplicate_pairs: list

class MethodologyRequest(BaseModel):
    text:     str = Field(..., min_length=50)
    abstract: str = Field("")

class MethodologyFlagResponse(BaseModel):
    claim:      str
    issue:      str
    suggestion: str

class MethodologyResponse(BaseModel):
    flags:          list[MethodologyFlagResponse]
    claims_found:   list[str]
    methods_found:  list[str]
    llm_assessment: str
    llm_available:  bool

class CitationRequest(BaseModel):
    text:        str = Field(..., min_length=50)
    author_name: str = Field("")

class CitationFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str = ""

class CitationResponse(BaseModel):
    total_citations:     int
    self_citations:      int
    self_citation_ratio: float
    unsupported_claims:  int
    flags:               list[CitationFlagResponse]
    risk_level:          str
    risk_score:          float
    summary:             str
    flags_count:         int

class ReproducibilityRequest(BaseModel):
    text: str = Field(..., min_length=50)

class ReproducibilityFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str = ""

class ReproducibilityResponse(BaseModel):
    has_code_link:         bool
    has_data_link:         bool
    has_software_versions: bool
    has_preregistration:   bool
    has_ethics_statement:  bool
    reproducibility_score: float
    risk_level:            str
    summary:               str
    flags:                 list[ReproducibilityFlagResponse]
    flags_count:           int

class NoveltyRequest(BaseModel):
    text:  str = Field(..., min_length=50)
    title: str = Field("")

class NoveltyFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str = ""

class RelatedWorkResponse(BaseModel):
    title:             str
    year:              int
    authors:           list
    similarity_signal: str

class NoveltyResponse(BaseModel):
    novelty_score:         float
    novelty_level:         str
    risk_level:            str
    risk_score:            float
    summary:               str
    flags:                 list[NoveltyFlagResponse]
    related_works_found:   list[RelatedWorkResponse]
    key_terms_extracted:   list[str]
    literature_accessible: bool
    flags_count:           int

class GrimRequest(BaseModel):
    text: str = Field(..., min_length=50)

class GrimFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class GrimResponse(BaseModel):
    impossible_means: list
    possible_means:   list
    grim_score:       float
    risk_level:       str
    summary:          str
    flags:            list[GrimFlagResponse]
    flags_count:      int

class SpriteRequest(BaseModel):
    text: str = Field(..., min_length=50)

class SpriteFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class SpriteResponse(BaseModel):
    impossible_combinations: list
    possible_combinations:   list
    sprite_score:            float
    risk_level:              str
    summary:                 str
    flags:                   list[SpriteFlagResponse]
    flags_count:             int

class GranularityRequest(BaseModel):
    text: str = Field(..., min_length=50)

class GranularityFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class GranularityResponse(BaseModel):
    digit_preference_score: float
    benford_score:          float
    round_number_ratio:     float
    granularity_score:      float
    risk_level:             str
    summary:                str
    flags:                  list[GranularityFlagResponse]
    flags_count:            int

class PCurveRequest(BaseModel):
    text: str = Field(..., min_length=50)

class PCurveFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class PCurveResponse(BaseModel):
    p_values_found:   list
    significant_p:    list
    right_skew_ratio: float
    clustering_score: float
    pcurve_score:     float
    risk_level:       str
    summary:          str
    flags:            list[PCurveFlagResponse]
    flags_count:      int

# ── Endpoints ─────────────────────────────────────────────────────────────────

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
            "grim_test":           True,
            "sprite_test":         True,
            "granularity":         True,
            "pcurve":              True,
        },
        "version": "1.4.0",
    }

@router.post("/analyze/statistics", response_model=StatAuditResponse)
def analyze_statistics(request: TextAnalysisRequest):
    """Analyze paper for statistical integrity issues."""
    try:
        result = _stat_engine.analyze(_truncate(request.text))
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
                ) for f in result.flags
            ],
            p_values_found=result.p_values_found,
            sample_sizes_found=result.sample_sizes_found,
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/figures", response_model=FigureForensicsResponse)
async def analyze_figures(file: UploadFile = File(...)):
    """Upload PDF and analyze figures for forensic anomalies."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted.")
    tmp_path = None
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        result = _figure_engine.analyze(tmp_path)
        return FigureForensicsResponse(
            figures_found=result.figures_found,
            flags=[ForensicFlagResponse(figures_involved=f.figures_involved)
                   for f in result.flags],
            duplicate_pairs=result.duplicate_pairs,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

@router.post("/analyze/methodology", response_model=MethodologyResponse)
def analyze_methodology(request: MethodologyRequest):
    """Analyze paper for methodology logic issues."""
    try:
        result = _method_engine.analyze(
            _truncate(request.text), request.abstract
        )
        return MethodologyResponse(
            flags=[
                MethodologyFlagResponse(
                    claim=f.claim,
                    issue=f.issue,
                    suggestion=f.suggestion,
                ) for f in result.flags
            ],
            claims_found=result.claims_found,
            methods_found=result.methods_found,
            llm_assessment=result.llm_assessment,
            llm_available=result.llm_available,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/citations", response_model=CitationResponse)
def analyze_citations(request: CitationRequest):
    """Analyze citations for integrity issues."""
    try:
        result = _citation_engine.analyze(
            _truncate(request.text), request.author_name
        )
        return CitationResponse(
            total_citations=result.total_citations,
            self_citations=result.self_citations,
            self_citation_ratio=result.self_citation_ratio,
            unsupported_claims=result.unsupported_claims,
            flags=[
                CitationFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=getattr(f, 'suggestion', ''),
                ) for f in result.flags
            ],
            risk_level=result.risk_level,
            risk_score=result.risk_score,
            summary=result.summary,
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/reproducibility", response_model=ReproducibilityResponse)
def analyze_reproducibility(request: ReproducibilityRequest):
    """Scan paper for reproducibility indicators."""
    try:
        result = _repro_engine.analyze(_truncate(request.text))
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
                    suggestion=getattr(f, 'suggestion', ''),
                ) for f in result.flags
            ],
            flags_count=len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/novelty", response_model=NoveltyResponse)
def analyze_novelty(request: NoveltyRequest):
    """Estimate paper novelty against existing literature."""
    try:
        result    = _novelty_engine.analyze(
            _truncate(request.text, 4000), request.title
        )
        raw_flags = getattr(result, 'flags', []) or []
        return NoveltyResponse(
            novelty_score=result.novelty_score,
            novelty_level=result.novelty_level,
            risk_level=result.risk_level,
            risk_score=getattr(result, 'risk_score', result.novelty_score),
            summary=result.summary,
            flags=[
                NoveltyFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=getattr(f, 'suggestion', ''),
                ) for f in raw_flags
            ],
            related_works_found=[
                RelatedWorkResponse(
                    title=w.title,
                    year=w.year,
                    authors=w.authors,
                    similarity_signal=w.similarity_signal,
                ) for w in result.related_works_found
            ],
            key_terms_extracted=result.key_terms_extracted,
            literature_accessible=result.literature_accessible,
            flags_count=len(raw_flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/grim", response_model=GrimResponse)
def analyze_grim(request: GrimRequest):
    """GRIM Test — detect mathematically impossible means."""
    try:
        result = _grim_engine.analyze(_truncate(request.text))
        return GrimResponse(
            impossible_means=result.impossible_means,
            possible_means=result.possible_means,
            grim_score=result.grim_score,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                GrimFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                ) for f in result.flags
            ],
            flags_count=result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/sprite", response_model=SpriteResponse)
def analyze_sprite(request: SpriteRequest):
    """SPRITE Test — detect impossible distributions."""
    try:
        result = _sprite_engine.analyze(_truncate(request.text))
        return SpriteResponse(
            impossible_combinations=result.impossible_combinations,
            possible_combinations=result.possible_combinations,
            sprite_score=result.sprite_score,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                SpriteFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                ) for f in result.flags
            ],
            flags_count=result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/granularity", response_model=GranularityResponse)
def analyze_granularity(request: GranularityRequest):
    """Granularity Analyzer — Benford Law + digit preference."""
    try:
        result = _granularity_engine.analyze(_truncate(request.text))
        return GranularityResponse(
            digit_preference_score=result.digit_preference_score,
            benford_score=result.benford_score,
            round_number_ratio=result.round_number_ratio,
            granularity_score=result.granularity_score,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                GranularityFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                ) for f in result.flags
            ],
            flags_count=result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze/pcurve", response_model=PCurveResponse)
def analyze_pcurve(request: PCurveRequest):
    """P-Curve Analyzer — publication bias detector."""
    try:
        result = _pcurve_engine.analyze(_truncate(request.text))
        return PCurveResponse(
            p_values_found=result.p_values_found,
            significant_p=result.significant_p,
            right_skew_ratio=result.right_skew_ratio,
            clustering_score=result.clustering_score,
            pcurve_score=result.pcurve_score,
            risk_level=result.risk_level,
            summary=result.summary,
            flags=[
                PCurveFlagResponse(
                    flag_type=f.flag_type,
                    severity=f.severity,
                    description=f.description,
                    evidence=f.evidence,
                    suggestion=f.suggestion,
                ) for f in result.flags
            ],
            flags_count=result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EffectSizeRequest(BaseModel):
    text: str = Field(..., min_length=50)

class EffectSizeFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class EffectSizeResponse(BaseModel):
    effect_sizes_found: list
    power_estimates:    list
    inflated_effects:   list
    underpowered:       list
    effect_score:       float
    risk_level:         str
    summary:            str
    flags:              list[EffectSizeFlagResponse]
    flags_count:        int

@router.post('/analyze/effect_size', response_model=EffectSizeResponse)
def analyze_effect_size(request: EffectSizeRequest):
    try:
        result = _effect_size_engine.analyze(_truncate(request.text))
        return EffectSizeResponse(
            effect_sizes_found = result.effect_sizes_found,
            power_estimates    = result.power_estimates,
            inflated_effects   = result.inflated_effects,
            underpowered       = result.underpowered,
            effect_score       = result.effect_score,
            risk_level         = result.risk_level,
            summary            = result.summary,
            flags              = [
                EffectSizeFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                )
                for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
