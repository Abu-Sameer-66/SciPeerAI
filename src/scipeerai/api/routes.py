# # src/scipeerai/api/routes.py
# import os
# import tempfile
# from fastapi import APIRouter, HTTPException, UploadFile, File
# from pydantic import BaseModel, Field
# from src.scipeerai.modules.reproducibility_scanner import ReproducibilityScanner
# from src.scipeerai.modules.stat_audit import StatAuditEngine
# from src.scipeerai.modules.figure_forensics import FigureForensicsEngine
# from src.scipeerai.modules.methodology_checker import MethodologyChecker
# from src.scipeerai.modules.citation_analyzer import CitationAnalyzer
# from src.scipeerai.modules.novelty_scorer import NoveltyScorer
# from src.scipeerai.modules.grim_test import GrimTest
# from src.scipeerai.modules.sprite_test import SpriteTest
# from src.scipeerai.modules.granularity_analyzer import GranularityAnalyzer
# from src.scipeerai.modules.pcurve_analyzer import PCurveAnalyzer
# from src.scipeerai.modules.effect_size_validator import EffectSizeValidator
# from src.scipeerai.modules.retraction_checker import RetractionChecker
# from src.scipeerai.modules.citation_cartel import CitationCartelDetector
# from src.scipeerai.modules.llm_detector import LLMDetector

# router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# # ── Smart text truncation — handles long papers ───────────────────────────────
# def _truncate(text: str, limit: int = 8000) -> str:
#     """Smart truncation — keeps abstract + methods sections."""
#     if len(text) <= limit:
#         return text
#     lower = text.lower()
#     methods_idx = lower.find('method')
#     if methods_idx > 0 and methods_idx < len(text) - 1000:
#         start  = text[:3000]
#         middle = text[methods_idx:methods_idx + 4000]
#         return start + " [...] " + middle
#     return text[:limit]

# # ── Engine initialization ─────────────────────────────────────────────────────
# _stat_engine        = StatAuditEngine()
# _figure_engine      = FigureForensicsEngine()
# _method_engine      = MethodologyChecker()
# _citation_engine    = CitationAnalyzer()
# _repro_engine       = ReproducibilityScanner()
# _novelty_engine     = NoveltyScorer()
# _grim_engine        = GrimTest()
# _sprite_engine      = SpriteTest()
# _granularity_engine = GranularityAnalyzer()
# _pcurve_engine         = PCurveAnalyzer()
# _effect_size_engine    = EffectSizeValidator()
# _retraction_engine     = RetractionChecker()
# _cartel_engine         = CitationCartelDetector()
# _llm_engine            = LLMDetector()

# # ── Request / Response Models ─────────────────────────────────────────────────

# class TextAnalysisRequest(BaseModel):
#     text: str = Field(..., min_length=50, description="Paper text to analyze")

# class FlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str = ""

# class ForensicFlagResponse(BaseModel):
#     figures_involved: list

# class StatAuditResponse(BaseModel):
#     risk_level:         str
#     risk_score:         float
#     summary:            str
#     flags:              list[FlagResponse]
#     p_values_found:     list[float]
#     sample_sizes_found: list[int]
#     flags_count:        int

# class FigureForensicsResponse(BaseModel):
#     figures_found:   int
#     flags:           list[ForensicFlagResponse]
#     duplicate_pairs: list

# class MethodologyRequest(BaseModel):
#     text:     str = Field(..., min_length=50)
#     abstract: str = Field("")

# class MethodologyFlagResponse(BaseModel):
#     claim:      str
#     issue:      str
#     suggestion: str

# class MethodologyResponse(BaseModel):
#     flags:          list[MethodologyFlagResponse]
#     claims_found:   list[str]
#     methods_found:  list[str]
#     llm_assessment: str
#     llm_available:  bool

# class CitationRequest(BaseModel):
#     text:        str = Field(..., min_length=50)
#     author_name: str = Field("")

# class CitationFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str = ""

# class CitationResponse(BaseModel):
#     total_citations:     int
#     self_citations:      int
#     self_citation_ratio: float
#     unsupported_claims:  int
#     flags:               list[CitationFlagResponse]
#     risk_level:          str
#     risk_score:          float
#     summary:             str
#     flags_count:         int

# class ReproducibilityRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class ReproducibilityFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str = ""

# class ReproducibilityResponse(BaseModel):
#     has_code_link:         bool
#     has_data_link:         bool
#     has_software_versions: bool
#     has_preregistration:   bool
#     has_ethics_statement:  bool
#     reproducibility_score: float
#     risk_level:            str
#     summary:               str
#     flags:                 list[ReproducibilityFlagResponse]
#     flags_count:           int

# class NoveltyRequest(BaseModel):
#     text:  str = Field(..., min_length=50)
#     title: str = Field("")

# class NoveltyFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str = ""

# class RelatedWorkResponse(BaseModel):
#     title:             str
#     year:              int
#     authors:           list
#     similarity_signal: str

# class NoveltyResponse(BaseModel):
#     novelty_score:         float
#     novelty_level:         str
#     risk_level:            str
#     risk_score:            float
#     summary:               str
#     flags:                 list[NoveltyFlagResponse]
#     related_works_found:   list[RelatedWorkResponse]
#     key_terms_extracted:   list[str]
#     literature_accessible: bool
#     flags_count:           int

# class GrimRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class GrimFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class GrimResponse(BaseModel):
#     impossible_means: list
#     possible_means:   list
#     grim_score:       float
#     risk_level:       str
#     summary:          str
#     flags:            list[GrimFlagResponse]
#     flags_count:      int

# class SpriteRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class SpriteFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class SpriteResponse(BaseModel):
#     impossible_combinations: list
#     possible_combinations:   list
#     sprite_score:            float
#     risk_level:              str
#     summary:                 str
#     flags:                   list[SpriteFlagResponse]
#     flags_count:             int

# class GranularityRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class GranularityFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class GranularityResponse(BaseModel):
#     digit_preference_score: float
#     benford_score:          float
#     round_number_ratio:     float
#     granularity_score:      float
#     risk_level:             str
#     summary:                str
#     flags:                  list[GranularityFlagResponse]
#     flags_count:            int

# class PCurveRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class PCurveFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class PCurveResponse(BaseModel):
#     p_values_found:   list
#     significant_p:    list
#     right_skew_ratio: float
#     clustering_score: float
#     pcurve_score:     float
#     risk_level:       str
#     summary:          str
#     flags:            list[PCurveFlagResponse]
#     flags_count:      int

# # ── Endpoints ─────────────────────────────────────────────────────────────────

# @router.get("/status")
# def system_status():
#     return {
#         "modules_ready": {
#             "stat_audit":          True,
#             "figure_forensics":    True,
#             "methodology_checker": True,
#             "citation_analyzer":   True,
#             "reproducibility":     True,
#             "novelty_scorer":      True,
#             "grim_test":           True,
#             "sprite_test":         True,
#             "granularity":         True,
#             "pcurve":              True,
#         },
#         "version": "1.4.0",
#     }

# @router.post("/analyze/statistics", response_model=StatAuditResponse)
# def analyze_statistics(request: TextAnalysisRequest):
#     """Analyze paper for statistical integrity issues."""
#     try:
#         result = _stat_engine.analyze(_truncate(request.text))
#         return StatAuditResponse(
#             risk_level=result.risk_level,
#             risk_score=result.risk_score,
#             summary=result.summary,
#             flags=[
#                 FlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             p_values_found=result.p_values_found,
#             sample_sizes_found=result.sample_sizes_found,
#             flags_count=len(result.flags),
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/figures", response_model=FigureForensicsResponse)
# async def analyze_figures(file: UploadFile = File(...)):
#     """Upload PDF and analyze figures for forensic anomalies."""
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files accepted.")
#     tmp_path = None
#     try:
#         contents = await file.read()
#         with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
#             tmp.write(contents)
#             tmp_path = tmp.name
#         result = _figure_engine.analyze(tmp_path)
#         return FigureForensicsResponse(
#             figures_found=result.figures_found,
#             flags=[ForensicFlagResponse(figures_involved=f.figures_involved)
#                    for f in result.flags],
#             duplicate_pairs=result.duplicate_pairs,
#         )
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.unlink(tmp_path)

# @router.post("/analyze/methodology", response_model=MethodologyResponse)
# def analyze_methodology(request: MethodologyRequest):
#     """Analyze paper for methodology logic issues."""
#     try:
#         result = _method_engine.analyze(
#             _truncate(request.text), request.abstract
#         )
#         return MethodologyResponse(
#             flags=[
#                 MethodologyFlagResponse(
#                     claim=f.claim,
#                     issue=f.issue,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             claims_found=result.claims_found,
#             methods_found=result.methods_found,
#             llm_assessment=result.llm_assessment,
#             llm_available=result.llm_available,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/citations", response_model=CitationResponse)
# def analyze_citations(request: CitationRequest):
#     """Analyze citations for integrity issues."""
#     try:
#         result = _citation_engine.analyze(
#             _truncate(request.text), request.author_name
#         )
#         return CitationResponse(
#             total_citations=result.total_citations,
#             self_citations=result.self_citations,
#             self_citation_ratio=result.self_citation_ratio,
#             unsupported_claims=result.unsupported_claims,
#             flags=[
#                 CitationFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=getattr(f, 'suggestion', ''),
#                 ) for f in result.flags
#             ],
#             risk_level=result.risk_level,
#             risk_score=result.risk_score,
#             summary=result.summary,
#             flags_count=len(result.flags),
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/reproducibility", response_model=ReproducibilityResponse)
# def analyze_reproducibility(request: ReproducibilityRequest):
#     """Scan paper for reproducibility indicators."""
#     try:
#         result = _repro_engine.analyze(_truncate(request.text))
#         return ReproducibilityResponse(
#             has_code_link=result.has_code_link,
#             has_data_link=result.has_data_link,
#             has_software_versions=result.has_software_versions,
#             has_preregistration=result.has_preregistration,
#             has_ethics_statement=result.has_ethics_statement,
#             reproducibility_score=result.reproducibility_score,
#             risk_level=result.risk_level,
#             summary=result.summary,
#             flags=[
#                 ReproducibilityFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=getattr(f, 'suggestion', ''),
#                 ) for f in result.flags
#             ],
#             flags_count=len(result.flags),
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/novelty", response_model=NoveltyResponse)
# def analyze_novelty(request: NoveltyRequest):
#     """Estimate paper novelty against existing literature."""
#     try:
#         result    = _novelty_engine.analyze(
#             _truncate(request.text, 4000), request.title
#         )
#         raw_flags = getattr(result, 'flags', []) or []
#         return NoveltyResponse(
#             novelty_score=result.novelty_score,
#             novelty_level=result.novelty_level,
#             risk_level=result.risk_level,
#             risk_score=getattr(result, 'risk_score', result.novelty_score),
#             summary=result.summary,
#             flags=[
#                 NoveltyFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=getattr(f, 'suggestion', ''),
#                 ) for f in raw_flags
#             ],
#             related_works_found=[
#                 RelatedWorkResponse(
#                     title=w.title,
#                     year=w.year,
#                     authors=w.authors,
#                     similarity_signal=w.similarity_signal,
#                 ) for w in result.related_works_found
#             ],
#             key_terms_extracted=result.key_terms_extracted,
#             literature_accessible=result.literature_accessible,
#             flags_count=len(raw_flags),
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/grim", response_model=GrimResponse)
# def analyze_grim(request: GrimRequest):
#     """GRIM Test — detect mathematically impossible means."""
#     try:
#         result = _grim_engine.analyze(_truncate(request.text))
#         return GrimResponse(
#             impossible_means=result.impossible_means,
#             possible_means=result.possible_means,
#             grim_score=result.grim_score,
#             risk_level=result.risk_level,
#             summary=result.summary,
#             flags=[
#                 GrimFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             flags_count=result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/sprite", response_model=SpriteResponse)
# def analyze_sprite(request: SpriteRequest):
#     """SPRITE Test — detect impossible distributions."""
#     try:
#         result = _sprite_engine.analyze(_truncate(request.text))
#         return SpriteResponse(
#             impossible_combinations=result.impossible_combinations,
#             possible_combinations=result.possible_combinations,
#             sprite_score=result.sprite_score,
#             risk_level=result.risk_level,
#             summary=result.summary,
#             flags=[
#                 SpriteFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             flags_count=result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/granularity", response_model=GranularityResponse)
# def analyze_granularity(request: GranularityRequest):
#     """Granularity Analyzer — Benford Law + digit preference."""
#     try:
#         result = _granularity_engine.analyze(_truncate(request.text))
#         return GranularityResponse(
#             digit_preference_score=result.digit_preference_score,
#             benford_score=result.benford_score,
#             round_number_ratio=result.round_number_ratio,
#             granularity_score=result.granularity_score,
#             risk_level=result.risk_level,
#             summary=result.summary,
#             flags=[
#                 GranularityFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             flags_count=result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/analyze/pcurve", response_model=PCurveResponse)
# def analyze_pcurve(request: PCurveRequest):
#     """P-Curve Analyzer — publication bias detector."""
#     try:
#         result = _pcurve_engine.analyze(_truncate(request.text))
#         return PCurveResponse(
#             p_values_found=result.p_values_found,
#             significant_p=result.significant_p,
#             right_skew_ratio=result.right_skew_ratio,
#             clustering_score=result.clustering_score,
#             pcurve_score=result.pcurve_score,
#             risk_level=result.risk_level,
#             summary=result.summary,
#             flags=[
#                 PCurveFlagResponse(
#                     flag_type=f.flag_type,
#                     severity=f.severity,
#                     description=f.description,
#                     evidence=f.evidence,
#                     suggestion=f.suggestion,
#                 ) for f in result.flags
#             ],
#             flags_count=result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# class EffectSizeRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class EffectSizeFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class EffectSizeResponse(BaseModel):
#     effect_sizes_found: list
#     power_estimates:    list
#     inflated_effects:   list
#     underpowered:       list
#     effect_score:       float
#     risk_level:         str
#     summary:            str
#     flags:              list[EffectSizeFlagResponse]
#     flags_count:        int

# @router.post('/analyze/effect_size', response_model=EffectSizeResponse)
# def analyze_effect_size(request: EffectSizeRequest):
#     try:
#         result = _effect_size_engine.analyze(_truncate(request.text))
#         return EffectSizeResponse(
#             effect_sizes_found = result.effect_sizes_found,
#             power_estimates    = result.power_estimates,
#             inflated_effects   = result.inflated_effects,
#             underpowered       = result.underpowered,
#             effect_score       = result.effect_score,
#             risk_level         = result.risk_level,
#             summary            = result.summary,
#             flags              = [
#                 EffectSizeFlagResponse(
#                     flag_type   = f.flag_type,
#                     severity    = f.severity,
#                     description = f.description,
#                     evidence    = f.evidence,
#                     suggestion  = f.suggestion,
#                 )
#                 for f in result.flags
#             ],
#             flags_count = result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# class RetractionRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class RetractionFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class RetractionResponse(BaseModel):
#     dois_found:       list
#     retracted_found:  list
#     checked_count:    int
#     retraction_score: float
#     risk_level:       str
#     summary:          str
#     flags:            list[RetractionFlagResponse]
#     flags_count:      int

# @router.post('/analyze/retraction', response_model=RetractionResponse)
# def analyze_retraction(request: RetractionRequest):
#     try:
#         result = _retraction_engine.analyze(_truncate(request.text))
#         return RetractionResponse(
#             dois_found       = result.dois_found,
#             retracted_found  = result.retracted_found,
#             checked_count    = result.checked_count,
#             retraction_score = result.retraction_score,
#             risk_level       = result.risk_level,
#             summary          = result.summary,
#             flags            = [
#                 RetractionFlagResponse(
#                     flag_type   = f.flag_type,
#                     severity    = f.severity,
#                     description = f.description,
#                     evidence    = f.evidence,
#                     suggestion  = f.suggestion,
#                 )
#                 for f in result.flags
#             ],
#             flags_count = result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# class CartelRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class CartelFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class CartelResponse(BaseModel):
#     authors_found:       list
#     citation_network:    dict
#     cartel_score:        float
#     self_citation_ratio: float
#     network_diversity:   float
#     risk_level:          str
#     summary:             str
#     flags:               list[CartelFlagResponse]
#     flags_count:         int

# @router.post('/analyze/cartel', response_model=CartelResponse)
# def analyze_cartel(request: CartelRequest):
#     try:
#         result = _cartel_engine.analyze(_truncate(request.text))
#         return CartelResponse(
#             authors_found       = result.authors_found,
#             citation_network    = result.citation_network,
#             cartel_score        = result.cartel_score,
#             self_citation_ratio = result.self_citation_ratio,
#             network_diversity   = result.network_diversity,
#             risk_level          = result.risk_level,
#             summary             = result.summary,
#             flags               = [
#                 CartelFlagResponse(
#                     flag_type   = f.flag_type,
#                     severity    = f.severity,
#                     description = f.description,
#                     evidence    = f.evidence,
#                     suggestion  = f.suggestion,
#                 )
#                 for f in result.flags
#             ],
#             flags_count = result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# class LLMRequest(BaseModel):
#     text: str = Field(..., min_length=50)

# class LLMFlagResponse(BaseModel):
#     flag_type:   str
#     severity:    str
#     description: str
#     evidence:    str
#     suggestion:  str

# class LLMResponse(BaseModel):
#     burstiness_score:     float
#     vocabulary_diversity: float
#     sentence_uniformity:  float
#     llm_phrase_count:     int
#     llm_score:            float
#     risk_level:           str
#     summary:              str
#     flags:                list[LLMFlagResponse]
#     flags_count:          int

# @router.post('/analyze/llm', response_model=LLMResponse)
# def analyze_llm(request: LLMRequest):
#     try:
#         result = _llm_engine.analyze(_truncate(request.text))
#         return LLMResponse(
#             burstiness_score     = result.burstiness_score,
#             vocabulary_diversity = result.vocabulary_diversity,
#             sentence_uniformity  = result.sentence_uniformity,
#             llm_phrase_count     = result.llm_phrase_count,
#             llm_score            = result.llm_score,
#             risk_level           = result.risk_level,
#             summary              = result.summary,
#             flags                = [
#                 LLMFlagResponse(
#                     flag_type   = f.flag_type,
#                     severity    = f.severity,
#                     description = f.description,
#                     evidence    = f.evidence,
#                     suggestion  = f.suggestion,
#                 )
#                 for f in result.flags
#             ],
#             flags_count = result.flags_count,
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


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
from src.scipeerai.modules.retraction_checker import RetractionChecker
from src.scipeerai.modules.citation_cartel import CitationCartelDetector
from src.scipeerai.modules.llm_detector import LLMDetector
from src.scipeerai.core.pdf_parser import PDFParser
router = APIRouter(prefix="/api/v1", tags=["Analysis"])

# ── Section-aware text extraction — replaces flat truncation ──────────────────

_SECTION_MARKERS = [
    "abstract", "introduction", "background", "related work",
    "methods", "methodology", "materials and methods",
    "experimental", "experiments", "procedures",
    "results", "findings", "data analysis",
    "discussion", "conclusion", "conclusions",
    "references", "bibliography", "acknowledgments",
    "supplementary", "appendix",
]

_MODULE_SECTIONS = {
    "statistics":      ["abstract", "results", "findings",
                        "data analysis", "methods", "methodology"],
    "methodology":     ["abstract", "introduction", "methods",
                        "methodology", "materials and methods",
                        "experimental", "conclusion", "conclusions"],
    "citations":       ["introduction", "background",
                        "related work", "references", "bibliography"],
    "reproducibility": ["methods", "methodology",
                        "materials and methods", "experimental",
                        "procedures", "acknowledgments"],
    "novelty":         ["abstract", "introduction",
                        "background", "related work"],
    "grim":            ["results", "findings", "methods",
                        "methodology", "data analysis"],
    "sprite":          ["results", "findings", "methods",
                        "methodology", "data analysis"],
    "granularity":     ["results", "findings",
                        "methods", "data analysis"],
    "pcurve":          ["abstract", "results",
                        "findings", "data analysis"],
    "effect_size":     ["results", "findings",
                        "methods", "discussion"],
    "retraction":      ["references", "bibliography", "introduction"],
    "cartel":          ["references", "bibliography",
                        "introduction", "acknowledgments"],
    "llm":             ["abstract", "introduction", "methods",
                        "results", "discussion"],
}


def _extract_sections(text: str) -> dict:
    """
    Split plain academic text into named sections.
    Looks for short lines matching known heading names.
    Returns dict of section_name -> section_text.
    """
    text_lower = text.lower()
    positions  = []

    for marker in _SECTION_MARKERS:
        search_from = 0
        while True:
            idx = text_lower.find(marker, search_from)
            if idx == -1:
                break
            line_start   = text.rfind('\n', 0, idx) + 1
            line_end     = text.find('\n', idx)
            if line_end == -1:
                line_end = len(text)
            line_content = text[line_start:line_end].strip()
            if len(line_content) <= 60:
                positions.append((idx, marker))
                break
            search_from = idx + 1

    if not positions:
        return {}

    positions.sort(key=lambda x: x[0])

    deduped = [positions[0]]
    for pos in positions[1:]:
        if pos[0] - deduped[-1][0] > 50:
            deduped.append(pos)

    sections = {}
    for i, (start, name) in enumerate(deduped):
        end = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
        sections[name] = text[start:end].strip()

    return sections


def _smart_text(text: str, module: str,
                per_section_limit: int = 2500) -> str:
    """
    Route paper text to the sections each module actually needs.

    Statistics module needs Results + Methods.
    Citations module needs References + Introduction.
    LLM detector needs the whole paper spread evenly.
    ...and so on.

    Falls back to flat truncation when no section headers found.
    """
    sections     = _extract_sections(text)
    target_keys  = _MODULE_SECTIONS.get(module, [])

    if sections and target_keys:
        parts = []
        for key in target_keys:
            if key in sections:
                parts.append(sections[key][:per_section_limit])
        if parts:
            return "\n\n".join(parts)[:12000]

    return _truncate(text)


def _truncate(text: str, limit: int = 8000) -> str:
    """
    Fallback flat truncation.
    Used when paper has no recognisable section headers.
    Tries to keep Abstract + Methods at minimum.
    """
    if len(text) <= limit:
        return text
    lower       = text.lower()
    methods_idx = lower.find('method')
    if 0 < methods_idx < len(text) - 1000:
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
_pcurve_engine      = PCurveAnalyzer()
_effect_size_engine = EffectSizeValidator()
_retraction_engine  = RetractionChecker()
_cartel_engine      = CitationCartelDetector()
_llm_engine         = LLMDetector()
_pdf_parser = PDFParser()

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

class RetractionRequest(BaseModel):
    text: str = Field(..., min_length=50)

class RetractionFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class RetractionResponse(BaseModel):
    dois_found:       list
    retracted_found:  list
    checked_count:    int
    retraction_score: float
    risk_level:       str
    summary:          str
    flags:            list[RetractionFlagResponse]
    flags_count:      int

class CartelRequest(BaseModel):
    text: str = Field(..., min_length=50)

class CartelFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class CartelResponse(BaseModel):
    authors_found:       list
    citation_network:    dict
    cartel_score:        float
    self_citation_ratio: float
    network_diversity:   float
    risk_level:          str
    summary:             str
    flags:               list[CartelFlagResponse]
    flags_count:         int

class LLMRequest(BaseModel):
    text: str = Field(..., min_length=50)

class LLMFlagResponse(BaseModel):
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str

class LLMResponse(BaseModel):
    burstiness_score:     float
    vocabulary_diversity: float
    sentence_uniformity:  float
    llm_phrase_count:     int
    llm_score:            float
    risk_level:           str
    summary:              str
    flags:                list[LLMFlagResponse]
    flags_count:          int


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
            "effect_size":         True,
            "retraction":          True,
            "citation_cartel":     True,
            "llm_detector":        True,
        },
        "version":         "1.5.0",
        "text_extraction": "section-aware",
    }


@router.post("/analyze/statistics", response_model=StatAuditResponse)
def analyze_statistics(request: TextAnalysisRequest):
    """Analyze paper for statistical integrity issues."""
    try:
        result = _stat_engine.analyze(
            _smart_text(request.text, "statistics")
        )
        return StatAuditResponse(
            risk_level         = result.risk_level,
            risk_score         = result.risk_score,
            summary            = result.summary,
            flags              = [
                FlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            p_values_found     = result.p_values_found,
            sample_sizes_found = result.sample_sizes_found,
            flags_count        = len(result.flags),
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
            figures_found   = result.figures_found,
            flags           = [
                ForensicFlagResponse(figures_involved=f.figures_involved)
                for f in result.flags
            ],
            duplicate_pairs = result.duplicate_pairs,
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
            _smart_text(request.text, "methodology"),
            request.abstract,
        )
        return MethodologyResponse(
            flags          = [
                MethodologyFlagResponse(
                    claim      = f.claim,
                    issue      = f.issue,
                    suggestion = f.suggestion,
                ) for f in result.flags
            ],
            claims_found   = result.claims_found,
            methods_found  = result.methods_found,
            llm_assessment = result.llm_assessment,
            llm_available  = result.llm_available,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/citations", response_model=CitationResponse)
def analyze_citations(request: CitationRequest):
    """Analyze citations for integrity issues."""
    try:
        result = _citation_engine.analyze(
            _smart_text(request.text, "citations"),
            request.author_name,
        )
        return CitationResponse(
            total_citations     = result.total_citations,
            self_citations      = result.self_citations,
            self_citation_ratio = result.self_citation_ratio,
            unsupported_claims  = result.unsupported_claims,
            flags               = [
                CitationFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = getattr(f, 'suggestion', ''),
                ) for f in result.flags
            ],
            risk_level  = result.risk_level,
            risk_score  = result.risk_score,
            summary     = result.summary,
            flags_count = len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/reproducibility", response_model=ReproducibilityResponse)
def analyze_reproducibility(request: ReproducibilityRequest):
    """Scan paper for reproducibility indicators."""
    try:
        result = _repro_engine.analyze(
            _smart_text(request.text, "reproducibility")
        )
        return ReproducibilityResponse(
            has_code_link         = result.has_code_link,
            has_data_link         = result.has_data_link,
            has_software_versions = result.has_software_versions,
            has_preregistration   = result.has_preregistration,
            has_ethics_statement  = result.has_ethics_statement,
            reproducibility_score = result.reproducibility_score,
            risk_level            = result.risk_level,
            summary               = result.summary,
            flags                 = [
                ReproducibilityFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = getattr(f, 'suggestion', ''),
                ) for f in result.flags
            ],
            flags_count = len(result.flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/novelty", response_model=NoveltyResponse)
def analyze_novelty(request: NoveltyRequest):
    """Estimate paper novelty against existing literature."""
    try:
        result    = _novelty_engine.analyze(
            _smart_text(request.text, "novelty", per_section_limit=2000),
            request.title,
        )
        raw_flags = getattr(result, 'flags', []) or []
        return NoveltyResponse(
            novelty_score         = result.novelty_score,
            novelty_level         = result.novelty_level,
            risk_level            = result.risk_level,
            risk_score            = getattr(result, 'risk_score', result.novelty_score),
            summary               = result.summary,
            flags                 = [
                NoveltyFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = getattr(f, 'suggestion', ''),
                ) for f in raw_flags
            ],
            related_works_found   = [
                RelatedWorkResponse(
                    title            = w.title,
                    year             = w.year,
                    authors          = w.authors,
                    similarity_signal = w.similarity_signal,
                ) for w in result.related_works_found
            ],
            key_terms_extracted   = result.key_terms_extracted,
            literature_accessible = result.literature_accessible,
            flags_count           = len(raw_flags),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/grim", response_model=GrimResponse)
def analyze_grim(request: GrimRequest):
    """GRIM Test — detect mathematically impossible means."""
    try:
        result = _grim_engine.analyze(
            _smart_text(request.text, "grim")
        )
        return GrimResponse(
            impossible_means = result.impossible_means,
            possible_means   = result.possible_means,
            grim_score       = result.grim_score,
            risk_level       = result.risk_level,
            summary          = result.summary,
            flags            = [
                GrimFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/sprite", response_model=SpriteResponse)
def analyze_sprite(request: SpriteRequest):
    """SPRITE Test — detect impossible distributions."""
    try:
        result = _sprite_engine.analyze(
            _smart_text(request.text, "sprite")
        )
        return SpriteResponse(
            impossible_combinations = result.impossible_combinations,
            possible_combinations   = result.possible_combinations,
            sprite_score            = result.sprite_score,
            risk_level              = result.risk_level,
            summary                 = result.summary,
            flags                   = [
                SpriteFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/granularity", response_model=GranularityResponse)
def analyze_granularity(request: GranularityRequest):
    """Granularity Analyzer — Benford Law + digit preference."""
    try:
        result = _granularity_engine.analyze(
            _smart_text(request.text, "granularity")
        )
        return GranularityResponse(
            digit_preference_score = result.digit_preference_score,
            benford_score          = result.benford_score,
            round_number_ratio     = result.round_number_ratio,
            granularity_score      = result.granularity_score,
            risk_level             = result.risk_level,
            summary                = result.summary,
            flags                  = [
                GranularityFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/pcurve", response_model=PCurveResponse)
def analyze_pcurve(request: PCurveRequest):
    """P-Curve Analyzer — publication bias detector."""
    try:
        result = _pcurve_engine.analyze(
            _smart_text(request.text, "pcurve")
        )
        return PCurveResponse(
            p_values_found   = result.p_values_found,
            significant_p    = result.significant_p,
            right_skew_ratio = result.right_skew_ratio,
            clustering_score = result.clustering_score,
            pcurve_score     = result.pcurve_score,
            risk_level       = result.risk_level,
            summary          = result.summary,
            flags            = [
                PCurveFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/analyze/effect_size', response_model=EffectSizeResponse)
def analyze_effect_size(request: EffectSizeRequest):
    """Effect Size Validator — Cohen d, power analysis."""
    try:
        result = _effect_size_engine.analyze(
            _smart_text(request.text, "effect_size")
        )
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
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/analyze/retraction', response_model=RetractionResponse)
def analyze_retraction(request: RetractionRequest):
    """Retraction Checker — live CrossRef API."""
    try:
        result = _retraction_engine.analyze(
            _smart_text(request.text, "retraction")
        )
        return RetractionResponse(
            dois_found       = result.dois_found,
            retracted_found  = result.retracted_found,
            checked_count    = result.checked_count,
            retraction_score = result.retraction_score,
            risk_level       = result.risk_level,
            summary          = result.summary,
            flags            = [
                RetractionFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/analyze/cartel', response_model=CartelResponse)
def analyze_cartel(request: CartelRequest):
    """Citation Cartel Detector — graph-based ring detection."""
    try:
        result = _cartel_engine.analyze(
            _smart_text(request.text, "cartel")
        )
        return CartelResponse(
            authors_found       = result.authors_found,
            citation_network    = result.citation_network,
            cartel_score        = result.cartel_score,
            self_citation_ratio = result.self_citation_ratio,
            network_diversity   = result.network_diversity,
            risk_level          = result.risk_level,
            summary             = result.summary,
            flags               = [
                CartelFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/analyze/llm', response_model=LLMResponse)
def analyze_llm(request: LLMRequest):
    """LLM-Generated Paper Detector — burstiness + TTR."""
    try:
        result = _llm_engine.analyze(
            _smart_text(request.text, "llm")
        )
        return LLMResponse(
            burstiness_score     = result.burstiness_score,
            vocabulary_diversity = result.vocabulary_diversity,
            sentence_uniformity  = result.sentence_uniformity,
            llm_phrase_count     = result.llm_phrase_count,
            llm_score            = result.llm_score,
            risk_level           = result.risk_level,
            summary              = result.summary,
            flags                = [
                LLMFlagResponse(
                    flag_type   = f.flag_type,
                    severity    = f.severity,
                    description = f.description,
                    evidence    = f.evidence,
                    suggestion  = f.suggestion,
                ) for f in result.flags
            ],
            flags_count = result.flags_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ── Full PDF Analysis — Master Endpoint ──────────────────────────────────────

class ModuleSummary(BaseModel):
    module:     str
    risk_level: str
    risk_score: float
    summary:    str
    flags_count: int

class FullPDFResponse(BaseModel):
    paper_title:       str
    page_count:        int
    figure_count:      int
    file_size_kb:      float
    sha256:            str
    overall_score:     float
    overall_risk:      str
    integrity_verdict: str
    modules:           list[ModuleSummary]
    top_flags:         list[str]
    analyzed_by:       str


def _compute_overall(scores: list[float]) -> tuple[float, str]:
    avg = round(sum(scores) / len(scores), 3) if scores else 0.0
    if avg >= 0.7:
        level = "HIGH"
    elif avg >= 0.4:
        level = "MEDIUM"
    else:
        level = "LOW"
    return avg, level


def _verdict(risk: str) -> str:
    return {
        "HIGH":   "Serious integrity concerns detected. Manual expert review strongly recommended.",
        "MEDIUM": "Some integrity issues found. Careful review advised before publication.",
        "LOW":    "No major integrity issues detected. Paper appears scientifically sound.",
    }.get(risk, "Unknown")


@router.post("/analyze/full-pdf", response_model=FullPDFResponse)
async def analyze_full_pdf(file: UploadFile = File(...)):
    """
    Master endpoint — Upload a PDF and run all 14 analysis modules at once.
    Returns a unified integrity report with per-module scores and top flags.
    Designed for PhD researchers who want a single comprehensive analysis.
    """
    try:
        file_bytes = await file.read()
        paper      = _pdf_parser.parse_bytes(file_bytes, file.filename)
        text       = paper.full_text

        if len(text.strip()) < 100:
            raise HTTPException(
                status_code=422,
                detail="PDF text extraction failed or paper is too short. "
                       "Ensure the PDF contains selectable text (not a scanned image)."
            )

        modules_run = []
        top_flags   = []
        scores      = []

        # ── Module 1: Statistical Audit ───────────────────────────
        try:
            r = _stat_engine.analyze(_smart_text(text, "statistics"))
            modules_run.append(ModuleSummary(
                module="Statistical Audit",
                risk_level=r.risk_level,
                risk_score=r.risk_score,
                summary=r.summary,
                flags_count=len(r.flags),
            ))
            scores.append(r.risk_score)
            for f in r.flags[:2]:
                top_flags.append(f"[Statistics] {f.description}")
        except Exception:
            pass

        # ── Module 2: Methodology Checker ─────────────────────────
        try:
            abstract = paper.sections.get("abstract", "")
            r = _method_engine.analyze(_smart_text(text, "methodology"), abstract)
            score = 0.7 if len(r.flags) > 2 else 0.3 if r.flags else 0.1
            modules_run.append(ModuleSummary(
                module="Methodology Checker",
                risk_level="HIGH" if score >= 0.7 else "MEDIUM" if score >= 0.4 else "LOW",
                risk_score=score,
                summary=r.llm_assessment or f"{len(r.flags)} methodology issues found.",
                flags_count=len(r.flags),
            ))
            scores.append(score)
            for f in r.flags[:2]:
                top_flags.append(f"[Methodology] {f.issue}")
        except Exception:
            pass

        # ── Module 3: Citation Integrity ──────────────────────────
        try:
            r = _citation_engine.analyze(_smart_text(text, "citations"), "")
            modules_run.append(ModuleSummary(
                module="Citation Integrity",
                risk_level=r.risk_level,
                risk_score=r.risk_score,
                summary=r.summary,
                flags_count=len(r.flags),
            ))
            scores.append(r.risk_score)
            for f in r.flags[:2]:
                top_flags.append(f"[Citations] {f.description}")
        except Exception:
            pass

        # ── Module 4: Reproducibility ─────────────────────────────
        try:
            r = _repro_engine.analyze(_smart_text(text, "reproducibility"))
            modules_run.append(ModuleSummary(
                module="Reproducibility Scanner",
                risk_level=r.risk_level,
                risk_score=1.0 - r.reproducibility_score,
                summary=r.summary,
                flags_count=len(r.flags),
            ))
            scores.append(1.0 - r.reproducibility_score)
            for f in r.flags[:1]:
                top_flags.append(f"[Reproducibility] {f.description}")
        except Exception:
            pass

        # ── Module 5: Novelty ─────────────────────────────────────
        try:
            r = _novelty_engine.analyze(
                _smart_text(text, "novelty", per_section_limit=2000),
                paper.title,
            )
            modules_run.append(ModuleSummary(
                module="Novelty Scorer",
                risk_level=r.risk_level,
                risk_score=getattr(r, "risk_score", 1.0 - r.novelty_score),
                summary=r.summary,
                flags_count=len(getattr(r, "flags", []) or []),
            ))
            scores.append(getattr(r, "risk_score", 1.0 - r.novelty_score))
        except Exception:
            pass

        # ── Module 6: GRIM Test ───────────────────────────────────
        try:
            r = _grim_engine.analyze(_smart_text(text, "grim"))
            modules_run.append(ModuleSummary(
                module="GRIM Test",
                risk_level=r.risk_level,
                risk_score=r.grim_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.grim_score)
            for f in r.flags[:1]:
                top_flags.append(f"[GRIM] {f.description}")
        except Exception:
            pass

        # ── Module 7: SPRITE Test ─────────────────────────────────
        try:
            r = _sprite_engine.analyze(_smart_text(text, "sprite"))
            modules_run.append(ModuleSummary(
                module="SPRITE Test",
                risk_level=r.risk_level,
                risk_score=r.sprite_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.sprite_score)
        except Exception:
            pass

        # ── Module 8: Granularity ─────────────────────────────────
        try:
            r = _granularity_engine.analyze(_smart_text(text, "granularity"))
            modules_run.append(ModuleSummary(
                module="Granularity Analyzer",
                risk_level=r.risk_level,
                risk_score=r.granularity_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.granularity_score)
        except Exception:
            pass

        # ── Module 9: P-Curve ─────────────────────────────────────
        try:
            r = _pcurve_engine.analyze(_smart_text(text, "pcurve"))
            modules_run.append(ModuleSummary(
                module="P-Curve Analyzer",
                risk_level=r.risk_level,
                risk_score=r.pcurve_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.pcurve_score)
            for f in r.flags[:1]:
                top_flags.append(f"[P-Curve] {f.description}")
        except Exception:
            pass

        # ── Module 10: Effect Size ────────────────────────────────
        try:
            r = _effect_size_engine.analyze(_smart_text(text, "effect_size"))
            modules_run.append(ModuleSummary(
                module="Effect Size Validator",
                risk_level=r.risk_level,
                risk_score=r.effect_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.effect_score)
        except Exception:
            pass

        # ── Module 11: Retraction Checker ─────────────────────────
        try:
            r = _retraction_engine.analyze(_smart_text(text, "retraction"))
            modules_run.append(ModuleSummary(
                module="Retraction Checker",
                risk_level=r.risk_level,
                risk_score=r.retraction_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.retraction_score)
            for f in r.flags[:1]:
                top_flags.append(f"[Retraction] {f.description}")
        except Exception:
            pass

        # ── Module 12: Citation Cartel ────────────────────────────
        try:
            r = _cartel_engine.analyze(_smart_text(text, "cartel"))
            modules_run.append(ModuleSummary(
                module="Citation Cartel Detector",
                risk_level=r.risk_level,
                risk_score=r.cartel_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.cartel_score)
            for f in r.flags[:1]:
                top_flags.append(f"[Cartel] {f.description}")
        except Exception:
            pass

        # ── Module 13: LLM Detector ───────────────────────────────
        try:
            r = _llm_engine.analyze(_smart_text(text, "llm"))
            modules_run.append(ModuleSummary(
                module="LLM Paper Detector",
                risk_level=r.risk_level,
                risk_score=r.llm_score,
                summary=r.summary,
                flags_count=r.flags_count,
            ))
            scores.append(r.llm_score)
            for f in r.flags[:1]:
                top_flags.append(f"[LLM] {f.description}")
        except Exception:
            pass

        # ── Module 14: Figure Forensics ───────────────────────────
        try:
            tmp_path = None
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            r = _figure_engine.analyze(tmp_path)
            fig_score = min(len(r.duplicate_pairs) * 0.3, 1.0)
            modules_run.append(ModuleSummary(
                module="Figure Forensics",
                risk_level="HIGH" if fig_score >= 0.7 else "MEDIUM" if fig_score >= 0.3 else "LOW",
                risk_score=fig_score,
                summary=f"{r.figures_found} figures found. {len(r.duplicate_pairs)} duplicate pairs detected.",
                flags_count=len(r.flags),
            ))
            scores.append(fig_score)
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass

        # ── Final Score ───────────────────────────────────────────
        overall_score, overall_risk = _compute_overall(scores)

        return FullPDFResponse(
            paper_title       = paper.title,
            page_count        = paper.page_count,
            figure_count      = paper.figure_count,
            file_size_kb      = paper.metadata.get("file_size_kb", 0.0),
            sha256            = paper.metadata.get("sha256", ""),
            overall_score     = overall_score,
            overall_risk      = overall_risk,
            integrity_verdict = _verdict(overall_risk),
            modules           = modules_run,
            top_flags         = top_flags[:10],
            analyzed_by       = "SciPeerAI v1.5.0 — 14-Module Pipeline",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))