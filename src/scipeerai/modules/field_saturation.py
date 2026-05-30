# src/scipeerai/modules/field_saturation.py
#
# Module 23: Field Saturation Detector
# Detects over-published research topics, measures novelty space,
# identifies redundant contribution patterns, and scores field
# crowding relative to claimed contributions.
#
# Score attribute: saturation_score (0.0 = fresh field, 1.0 = saturated)
# Part of SciPeerAI Phase 6 — v2.3.0

from __future__ import annotations

import re
import math
from collections import Counter
from dataclasses import dataclass


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class SaturationFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class SaturationResult:
    topic_keywords:          list
    keyword_density:         float
    redundancy_score:        float
    novelty_claim_score:     float
    contribution_vagueness:  float
    overcrowding_signals:    int
    saturation_score:        float
    risk_level:              str
    summary:                 str
    flags:                   list
    flags_count:             int


# ── Compiled patterns ─────────────────────────────────────────────────────────

_NOVELTY_CLAIMS = re.compile(
    r'\b(novel|innovative|first|pioneer|unique|original|breakthrough|'
    r'state.of.the.art|cutting.edge|unprecedented|revolutionar\w+|'
    r'new approach|new method|new framework|we propose|we present|'
    r'we introduce|we develop)\b',
    re.IGNORECASE,
)

_SATURATION_SIGNALS = re.compile(
    r'\b(many studies|numerous studies|extensive research|'
    r'widely studied|well.studied|well.known|well.established|'
    r'extensively investigated|much attention|growing body|'
    r'large body of|considerable research|substantial literature|'
    r'abundant literature|intensively studied|heavily researched|'
    r'significant amount of work|proliferation of|surge of interest)\b',
    re.IGNORECASE,
)

_VAGUE_CONTRIBUTION = re.compile(
    r'\b(improve\w*|enhanc\w*|better\w*|outperform\w*|superior\w*|'
    r'more efficient|more effective|more accurate|higher performance|'
    r'significant improvement|notable improvement|'
    r'promising results|competitive results)\b',
    re.IGNORECASE,
)

_KEYWORD_STOP = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
    'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
    'be', 'been', 'has', 'have', 'had', 'do', 'does', 'did', 'will',
    'would', 'could', 'should', 'may', 'might', 'this', 'that', 'these',
    'those', 'it', 'its', 'we', 'our', 'their', 'as', 'not', 'also',
    'can', 'which', 'such', 'than', 'other', 'into', 'used', 'using',
    'based', 'paper', 'study', 'research', 'method', 'approach', 'work',
    'show', 'shows', 'shown', 'propose', 'present', 'results', 'data',
}

_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
_WORD_RE        = re.compile(r'\b[a-zA-Z]{4,}\b')


# ── Engine ────────────────────────────────────────────────────────────────────

class FieldSaturationDetector:
    """
    Field Saturation Detector — Module 23.

    Analyses paper text to detect:
    - Over-saturated research topics with redundant contributions
    - Vague novelty claims unsupported by specific advances
    - Crowding signals indicating field congestion
    - Mismatch between claimed novelty and acknowledged saturation
    """

    def analyze(self, text: str) -> SaturationResult:
        text = (text or "").strip()
        if not text:
            return self._empty_result("No text provided for saturation analysis.")

        keywords             = self._extract_topic_keywords(text)
        keyword_density      = self._compute_keyword_density(text, keywords)
        redundancy_score     = self._compute_redundancy(text)
        novelty_claim_score  = self._compute_novelty_claims(text)
        contribution_vague   = self._compute_contribution_vagueness(text)
        overcrowding_signals = self._count_overcrowding_signals(text)

        saturation_score = self._compute_score(
            keyword_density,
            redundancy_score,
            novelty_claim_score,
            contribution_vague,
            overcrowding_signals,
        )

        risk_level = (
            "critical" if saturation_score >= 0.75 else
            "high"     if saturation_score >= 0.55 else
            "medium"   if saturation_score >= 0.30 else
            "low"
        )

        flags   = self._build_flags(
            keywords, keyword_density, redundancy_score,
            novelty_claim_score, contribution_vague,
            overcrowding_signals, saturation_score,
        )

        summary = self._build_summary(
            keywords, overcrowding_signals,
            redundancy_score, saturation_score, risk_level,
        )

        return SaturationResult(
            topic_keywords         = keywords[:15],
            keyword_density        = round(keyword_density, 4),
            redundancy_score       = round(redundancy_score, 4),
            novelty_claim_score    = round(novelty_claim_score, 4),
            contribution_vagueness = round(contribution_vague, 4),
            overcrowding_signals   = overcrowding_signals,
            saturation_score       = round(saturation_score, 4),
            risk_level             = risk_level,
            summary                = summary,
            flags                  = flags,
            flags_count            = len(flags),
        )

    # ── Extraction ────────────────────────────────────────────────────────────

    def _extract_topic_keywords(self, text: str) -> list:
        words   = _WORD_RE.findall(text.lower())
        cleaned = [w for w in words if w not in _KEYWORD_STOP and len(w) >= 4]
        counter = Counter(cleaned)
        return [w for w, _ in counter.most_common(30) if counter[w] >= 2]

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _compute_keyword_density(self, text: str, keywords: list) -> float:
        if not keywords:
            return 0.0
        words       = _WORD_RE.findall(text.lower())
        total_words = max(len(words), 1)
        kw_set      = set(keywords[:10])
        kw_count    = sum(1 for w in words if w in kw_set)
        raw_density = kw_count / total_words
        return round(min(1.0, raw_density * 8), 4)

    def _compute_redundancy(self, text: str) -> float:
        sentences = _SENTENCE_SPLIT.split(text.strip())
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        if len(sentences) < 4:
            return 0.0

        word_sets = []
        for s in sentences:
            words = set(_WORD_RE.findall(s.lower())) - _KEYWORD_STOP
            if words:
                word_sets.append(words)

        if len(word_sets) < 4:
            return 0.0

        overlap_count = 0
        total_pairs   = 0
        for i in range(len(word_sets)):
            for j in range(i + 1, min(i + 6, len(word_sets))):
                a, b        = word_sets[i], word_sets[j]
                union       = a | b
                intersection = a & b
                if union:
                    jaccard = len(intersection) / len(union)
                    if jaccard > 0.35:
                        overlap_count += 1
                total_pairs += 1

        if total_pairs == 0:
            return 0.0
        return round(min(1.0, overlap_count / total_pairs * 2.5), 4)

    def _compute_novelty_claims(self, text: str) -> float:
        words        = _WORD_RE.findall(text)
        total_words  = max(len(words), 1)
        claim_count  = len(_NOVELTY_CLAIMS.findall(text))
        claim_ratio  = claim_count / total_words

        sat_count    = len(_SATURATION_SIGNALS.findall(text))

        if sat_count > 0 and claim_count > 0:
            mismatch = min(1.0, (claim_count / max(sat_count, 1)) * 0.25)
        else:
            mismatch = 0.0

        base = min(1.0, claim_ratio * 60)
        return round(min(1.0, base * 0.5 + mismatch * 0.5), 4)

    def _compute_contribution_vagueness(self, text: str) -> float:
        words       = _WORD_RE.findall(text)
        total_words = max(len(words), 1)
        vague_count = len(_VAGUE_CONTRIBUTION.findall(text))
        return round(min(1.0, (vague_count / total_words) * 80), 4)

    def _count_overcrowding_signals(self, text: str) -> int:
        return len(_SATURATION_SIGNALS.findall(text))

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        keyword_density:     float,
        redundancy_score:    float,
        novelty_claim_score: float,
        contribution_vague:  float,
        overcrowding:        int,
    ) -> float:
        score  = 0.0
        score += keyword_density     * 0.15
        score += redundancy_score    * 0.30
        score += novelty_claim_score * 0.25
        score += contribution_vague  * 0.20
        score += min(overcrowding * 0.05, 0.20)
        return round(min(1.0, score), 4)

    # ── Flags ─────────────────────────────────────────────────────────────────

    def _build_flags(
        self,
        keywords:            list,
        keyword_density:     float,
        redundancy_score:    float,
        novelty_claim_score: float,
        contribution_vague:  float,
        overcrowding:        int,
        saturation_score:    float,
    ) -> list:
        flags = []

        if overcrowding >= 3:
            flags.append(SaturationFlag(
                flag_type   = "field_overcrowding_acknowledged",
                severity    = "high",
                description = (
                    f"Paper acknowledges {overcrowding} field saturation signals, "
                    f"yet still claims novel contribution — a credibility mismatch."
                ),
                evidence    = (
                    f"{overcrowding} saturation phrases detected: "
                    f"'many studies', 'well-studied', 'extensive research', etc. "
                    f"Field is crowded by the paper's own admission."
                ),
                suggestion  = (
                    "Clearly articulate what specific gap this paper fills that "
                    "prior work has not. Vague novelty in saturated fields is a "
                    "major rejection signal for top journals."
                ),
            ))

        if redundancy_score >= 0.45:
            flags.append(SaturationFlag(
                flag_type   = "high_content_redundancy",
                severity    = "medium",
                description = (
                    "High sentence-level content redundancy detected — paper "
                    "repeats concepts across sections without adding new information."
                ),
                evidence    = (
                    f"Jaccard similarity analysis across sentence windows "
                    f"returned redundancy score of {redundancy_score:.2f} "
                    f"(threshold: 0.45). Significant content overlap present."
                ),
                suggestion  = (
                    "Restructure paper to eliminate repetitive content. "
                    "Each section should introduce new information, not restate previous points."
                ),
            ))

        if novelty_claim_score >= 0.45:
            flags.append(SaturationFlag(
                flag_type   = "overclaimed_novelty",
                severity    = "high",
                description = (
                    "Paper makes disproportionately high novelty claims relative "
                    "to the specificity of its actual contributions."
                ),
                evidence    = (
                    f"Novelty claim density score: {novelty_claim_score:.2f}. "
                    f"High frequency of terms like 'novel', 'first', 'innovative', "
                    f"'breakthrough' without commensurate technical specificity."
                ),
                suggestion  = (
                    "Replace broad novelty claims with precise technical statements. "
                    "Quantify what makes the contribution different, not just that it is different."
                ),
            ))

        if contribution_vague >= 0.40:
            flags.append(SaturationFlag(
                flag_type   = "vague_contribution_language",
                severity    = "medium",
                description = (
                    "Contribution language is vague and non-specific — paper "
                    "relies on generic improvement claims rather than measurable advances."
                ),
                evidence    = (
                    f"Vagueness score: {contribution_vague:.2f}. Overuse of "
                    f"'improve', 'enhance', 'better', 'outperform' without "
                    f"quantified baselines or specific metrics."
                ),
                suggestion  = (
                    "State contributions with exact numbers: 'X% improvement on Y benchmark "
                    "over Z baseline' instead of 'improved performance'."
                ),
            ))

        if keyword_density >= 0.55 and len(keywords) >= 5:
            flags.append(SaturationFlag(
                flag_type   = "topic_keyword_saturation",
                severity    = "low",
                description = (
                    "Topic keyword density is high — a small set of terms "
                    "dominates the entire paper, suggesting narrow scope."
                ),
                evidence    = (
                    f"Keyword density index: {keyword_density:.2f}. "
                    f"Top terms: {', '.join(keywords[:6])}. "
                    f"Repeated heavily throughout without broadening context."
                ),
                suggestion  = (
                    "Contextualize the work within broader research themes. "
                    "Narrow keyword scope can signal incremental rather than transformative contribution."
                ),
            ))

        if not flags:
            flags.append(SaturationFlag(
                flag_type   = "field_saturation_acceptable",
                severity    = "low",
                description = "No significant field saturation indicators detected.",
                evidence    = (
                    f"Saturation score: {saturation_score:.2f}. "
                    f"Contribution language is sufficiently specific. "
                    f"Field crowding signals are within acceptable range."
                ),
                suggestion  = "Continue ensuring each section adds incremental specificity.",
            ))

        return flags

    # ── Summary ───────────────────────────────────────────────────────────────

    def _build_summary(
        self,
        keywords:         list,
        overcrowding:     int,
        redundancy_score: float,
        saturation_score: float,
        risk_level:       str,
    ) -> str:
        top_kw = ', '.join(keywords[:5]) if keywords else 'none detected'
        return (
            f"Field saturation analysis complete. "
            f"Top topic keywords: {top_kw}. "
            f"{overcrowding} field crowding signal(s) detected in text. "
            f"Content redundancy score: {redundancy_score:.2f}. "
            f"Overall saturation risk: {risk_level.upper()}."
        )

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _empty_result(self, msg: str) -> SaturationResult:
        return SaturationResult(
            topic_keywords         = [],
            keyword_density        = 0.0,
            redundancy_score       = 0.0,
            novelty_claim_score    = 0.0,
            contribution_vagueness = 0.0,
            overcrowding_signals   = 0,
            saturation_score       = 0.0,
            risk_level             = "low",
            summary                = msg,
            flags                  = [],
            flags_count            = 0,
        )