# src/scipeerai/modules/institutional_conflict.py
#
# Module 24: Institutional Conflict Score
# Detects author institution patterns correlated with bias,
# undisclosed conflicts of interest, self-serving citation
# patterns, and funding-driven conclusion distortion.
#
# Score attribute: conflict_score (0.0 = clean, 1.0 = high conflict)
# Part of SciPeerAI Phase 6 — v2.3.0

from __future__ import annotations

import re
from dataclasses import dataclass
from collections import Counter


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ConflictFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class ConflictResult:
    institution_mentions:     int
    unique_institutions:      int
    funding_sources:          list
    conflict_disclosures:     int
    undisclosed_signals:      int
    self_serving_claims:      int
    industry_funding_signals: int
    conclusion_bias_score:    float
    conflict_score:           float
    risk_level:               str
    summary:                  str
    flags:                    list
    flags_count:              int


# ── Compiled patterns ─────────────────────────────────────────────────────────

_INSTITUTION_RE = re.compile(
    r'\b(university|institute|college|department|laboratory|lab|'
    r'school of|faculty of|division of|center for|centre for|'
    r'hospital|clinic|foundation|corporation|inc\.|ltd\.|llc|'
    r'pharmaceut\w+|biotech\w*|tech\w+\s+(?:corp|inc|ltd))\b',
    re.IGNORECASE,
)

_FUNDING_RE = re.compile(
    r'\b(funded by|supported by|grant from|sponsored by|'
    r'financial support|funding from|research grant|award from|'
    r'contract from|supported in part|partially funded|'
    r'this work was supported|this research was funded)\b',
    re.IGNORECASE,
)

_CONFLICT_DISCLOSURE_RE = re.compile(
    r'\b(conflict of interest|competing interest|declare no|'
    r'no conflict|no competing|disclose|disclosure|'
    r'authors declare|nothing to disclose|potential conflict)\b',
    re.IGNORECASE,
)

_UNDISCLOSED_SIGNAL_RE = re.compile(
    r'\b(consultant\w* (?:for|to)|advisor\w* (?:to|for)|'
    r'employee\w* of|employed by|stock\w*|equity|'
    r'patent\w*|license\w*|royalt\w*|honorar\w*|'
    r'speaker bureau|board member|scientific advisory)\b',
    re.IGNORECASE,
)

_INDUSTRY_FUNDING_RE = re.compile(
    r'\b(pharma\w*|biotech\w*|(?:medical|health\w*)\s+(?:corp|inc|ltd|company)|'
    r'industry (?:partner|fund|grant|support)|commercial\w* fund|'
    r'private (?:fund|grant|support)|corporate (?:fund|grant|sponsor))\b',
    re.IGNORECASE,
)

_SELF_SERVING_RE = re.compile(
    r'\b(our (?:previous|prior|earlier|recent) (?:work|study|research|findings|results)|'
    r'as we (?:showed|demonstrated|reported|found|showed previously)|'
    r'consistent with our|confirms our|validates our|'
    r'as reported by (?:us|our group|our lab|our team)|'
    r'building on our|extending our|in our (?:earlier|previous|prior))\b',
    re.IGNORECASE,
)

_CONCLUSION_BIAS_RE = re.compile(
    r'\b(clearly (?:demonstrate|show|prove|establish|confirm)|'
    r'conclusively (?:show|prove|establish|demonstrate)|'
    r'unequivocally|undeniably|without doubt|it is clear that|'
    r'definitively (?:show|prove|establish)|strong evidence|'
    r'compelling evidence|overwhelmingly|irrefutably|'
    r'leaves no doubt|beyond question)\b',
    re.IGNORECASE,
)

_INSTITUTION_NAME_RE = re.compile(
    r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,3}\s+'
    r'(?:University|Institute|College|Laboratory|Hospital|Foundation|Corporation))\b',
)


# ── Engine ────────────────────────────────────────────────────────────────────

class InstitutionalConflictDetector:
    """
    Institutional Conflict Score — Module 24.

    Detects:
    - Undisclosed conflicts of interest
    - Industry funding with biased conclusions
    - Excessive self-citation and self-serving claims
    - Conclusion language inflated beyond evidence
    - Missing or inadequate conflict disclosure statements
    """

    def analyze(self, text: str) -> ConflictResult:
        text = (text or "").strip()
        if not text:
            return self._empty_result("No text provided for conflict analysis.")

        institution_mentions  = len(_INSTITUTION_RE.findall(text))
        unique_institutions   = self._count_unique_institutions(text)
        funding_sources       = self._extract_funding_sources(text)
        conflict_disclosures  = len(_CONFLICT_DISCLOSURE_RE.findall(text))
        undisclosed_signals   = len(_UNDISCLOSED_SIGNAL_RE.findall(text))
        self_serving_claims   = len(_SELF_SERVING_RE.findall(text))
        industry_signals      = len(_INDUSTRY_FUNDING_RE.findall(text))
        conclusion_bias       = self._compute_conclusion_bias(text)

        conflict_score = self._compute_score(
            conflict_disclosures,
            undisclosed_signals,
            self_serving_claims,
            industry_signals,
            conclusion_bias,
            len(funding_sources),
        )

        risk_level = (
            "critical" if conflict_score >= 0.75 else
            "high"     if conflict_score >= 0.55 else
            "medium"   if conflict_score >= 0.30 else
            "low"
        )

        flags = self._build_flags(
            conflict_disclosures,
            undisclosed_signals,
            self_serving_claims,
            industry_signals,
            conclusion_bias,
            funding_sources,
            conflict_score,
        )

        summary = self._build_summary(
            institution_mentions,
            unique_institutions,
            undisclosed_signals,
            self_serving_claims,
            conflict_score,
            risk_level,
        )

        return ConflictResult(
            institution_mentions     = institution_mentions,
            unique_institutions      = unique_institutions,
            funding_sources          = funding_sources[:10],
            conflict_disclosures     = conflict_disclosures,
            undisclosed_signals      = undisclosed_signals,
            self_serving_claims      = self_serving_claims,
            industry_funding_signals = industry_signals,
            conclusion_bias_score    = round(conclusion_bias, 4),
            conflict_score           = round(conflict_score, 4),
            risk_level               = risk_level,
            summary                  = summary,
            flags                    = flags,
            flags_count              = len(flags),
        )

    # ── Extraction ────────────────────────────────────────────────────────────

    def _count_unique_institutions(self, text: str) -> int:
        matches = _INSTITUTION_NAME_RE.findall(text)
        return len(set(m.strip().lower() for m in matches))

    def _extract_funding_sources(self, text: str) -> list:
        funding_hits = _FUNDING_RE.findall(text)
        lines        = text.split('\n')
        sources      = []
        for line in lines:
            if any(kw.lower() in line.lower() for kw in ['funded', 'supported', 'grant', 'sponsored']):
                stripped = line.strip()
                if 10 < len(stripped) < 300:
                    sources.append(stripped[:150])
        return sources[:8] if sources else funding_hits[:8]

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _compute_conclusion_bias(self, text: str) -> float:
        words       = text.split()
        total_words = max(len(words), 1)
        bias_count  = len(_CONCLUSION_BIAS_RE.findall(text))
        return round(min(1.0, (bias_count / total_words) * 80), 4)

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        disclosures:      int,
        undisclosed:      int,
        self_serving:     int,
        industry:         int,
        conclusion_bias:  float,
        funding_count:    int,
    ) -> float:
        score = 0.0

        if undisclosed > 0 and disclosures == 0:
            score += min(undisclosed * 0.18, 0.45)
        elif undisclosed > 0 and disclosures > 0:
            score += min(undisclosed * 0.08, 0.20)

        score += min(self_serving * 0.06,  0.25)
        score += min(industry     * 0.08,  0.25)
        score += conclusion_bias           * 0.25

        if funding_count > 0 and disclosures == 0:
            score += 0.10

        return round(min(1.0, score), 4)

    # ── Flags ─────────────────────────────────────────────────────────────────

    def _build_flags(
        self,
        disclosures:     int,
        undisclosed:     int,
        self_serving:    int,
        industry:        int,
        conclusion_bias: float,
        funding_sources: list,
        conflict_score:  float,
    ) -> list:
        flags = []

        if undisclosed > 0 and disclosures == 0:
            flags.append(ConflictFlag(
                flag_type   = "undisclosed_conflict_of_interest",
                severity    = "critical",
                description = (
                    f"{undisclosed} potential conflict signal(s) detected "
                    f"with no corresponding conflict disclosure statement."
                ),
                evidence    = (
                    f"Text contains references to consultancy, advisory roles, "
                    f"equity, patents, or speaker bureaus ({undisclosed} signals) "
                    f"but no 'conflict of interest' or 'competing interests' declaration."
                ),
                suggestion  = (
                    "Add an explicit conflict of interest statement. "
                    "All financial relationships, consultancy roles, and equity "
                    "positions must be declared per journal ethics requirements."
                ),
            ))

        if industry > 0 and conclusion_bias >= 0.25:
            flags.append(ConflictFlag(
                flag_type   = "industry_funded_conclusion_bias",
                severity    = "high",
                description = (
                    "Industry funding signals combined with inflated conclusion "
                    "language suggest potential sponsor-driven result presentation."
                ),
                evidence    = (
                    f"{industry} industry funding reference(s) detected alongside "
                    f"conclusion bias score of {conclusion_bias:.2f}. "
                    f"Overly confident conclusion language in industry-funded work "
                    f"is a known integrity risk factor."
                ),
                suggestion  = (
                    "Moderate conclusion language to match the actual strength of "
                    "evidence. Avoid absolute claims ('clearly proves', 'definitively "
                    "establishes') especially in industry-funded studies."
                ),
            ))

        if self_serving >= 4:
            flags.append(ConflictFlag(
                flag_type   = "excessive_self_serving_citations",
                severity    = "medium",
                description = (
                    f"{self_serving} self-serving reference pattern(s) detected — "
                    f"paper disproportionately builds on and validates the authors' own prior work."
                ),
                evidence    = (
                    f"Phrases like 'as we showed', 'consistent with our findings', "
                    f"'our previous work', 'building on our' appear {self_serving} times. "
                    f"This pattern can indicate citation padding or circular validation."
                ),
                suggestion  = (
                    "Ensure self-citations are genuinely necessary and not inflating "
                    "the authors' citation count. Include independent replications "
                    "that confirm the findings."
                ),
            ))

        if conclusion_bias >= 0.40:
            flags.append(ConflictFlag(
                flag_type   = "overstated_conclusions",
                severity    = "high",
                description = (
                    "Conclusion language significantly overstates the strength "
                    "of evidence — claims exceed what the data can support."
                ),
                evidence    = (
                    f"Conclusion bias score: {conclusion_bias:.2f} (threshold: 0.40). "
                    f"Terms like 'conclusively proves', 'unequivocally demonstrates', "
                    f"'leaves no doubt' detected. These exceed standard scientific hedging."
                ),
                suggestion  = (
                    "Use appropriately hedged language: 'our results suggest', "
                    "'findings are consistent with', 'evidence supports'. "
                    "Reserve definitive language for replicated, high-powered results."
                ),
            ))

        if len(funding_sources) > 0 and disclosures == 0:
            flags.append(ConflictFlag(
                flag_type   = "funding_without_disclosure",
                severity    = "medium",
                description = (
                    "Funding acknowledgment found but no conflict of interest "
                    "disclosure statement present."
                ),
                evidence    = (
                    f"{len(funding_sources)} funding source reference(s) detected. "
                    f"Zero conflict disclosure statements found. "
                    f"Most journals require explicit COI statements alongside funding."
                ),
                suggestion  = (
                    "Add a dedicated 'Conflicts of Interest' section. "
                    "Even 'no competing interests' must be explicitly stated per "
                    "ICMJE and most journal editorial policies."
                ),
            ))

        if not flags:
            flags.append(ConflictFlag(
                flag_type   = "no_conflict_detected",
                severity    = "low",
                description = "No significant institutional conflict indicators detected.",
                evidence    = (
                    f"Conflict score: {conflict_score:.2f}. "
                    f"Disclosure language present or no undisclosed signals found. "
                    f"Conclusion language within acceptable bounds."
                ),
                suggestion  = (
                    "Maintain transparency by including explicit COI and "
                    "funding statements in all future submissions."
                ),
            ))

        return flags

    # ── Summary ───────────────────────────────────────────────────────────────

    def _build_summary(
        self,
        institution_mentions: int,
        unique_institutions:  int,
        undisclosed:          int,
        self_serving:         int,
        conflict_score:       float,
        risk_level:           str,
    ) -> str:
        return (
            f"Institutional conflict analysis complete. "
            f"{institution_mentions} institution reference(s) found "
            f"({unique_institutions} unique). "
            f"{undisclosed} undisclosed conflict signal(s) detected. "
            f"{self_serving} self-serving citation pattern(s) found. "
            f"Overall conflict risk: {risk_level.upper()}."
        )

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _empty_result(self, msg: str) -> ConflictResult:
        return ConflictResult(
            institution_mentions     = 0,
            unique_institutions      = 0,
            funding_sources          = [],
            conflict_disclosures     = 0,
            undisclosed_signals      = 0,
            self_serving_claims      = 0,
            industry_funding_signals = 0,
            conclusion_bias_score    = 0.0,
            conflict_score           = 0.0,
            risk_level               = "low",
            summary                  = msg,
            flags                    = [],
            flags_count              = 0,
        )