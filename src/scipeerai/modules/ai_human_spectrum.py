# AI-Human Collaboration Spectrum
# --------------------------------
# The question is no longer "was this written by AI?"
# That binary is already obsolete.
#
# The real question is: how much of this paper is human,
# how much is AI, which sections crossed the line,
# and — critically — which AI system left its fingerprints?
#
# GPT-4 writes differently from Claude.
# Claude writes differently from Gemini.
# Each system has signature phrase patterns, sentence
# rhythm preferences, and structural habits that persist
# even when users try to disguise them.
#
# This module does not just score AI probability.
# It maps the collaboration: section by section,
# model by model, returning a spectrum rather than
# a verdict. A paper that is 30% AI-assisted in the
# discussion section is a different integrity question
# than one that is 90% AI in the methods section.
#
# The spectrum is the signal.

import re
import math
from dataclasses import dataclass, field
from collections import Counter


# ── model signature phrases ────────────────────────────────────────────────────
# These are characteristic patterns each model uses at elevated frequency.
# Compiled from large-scale analysis of known model outputs.

GPT4_SIGNATURES = [
    "it is worth noting", "it is important to note",
    "in the context of", "with respect to",
    "it should be noted that", "as mentioned earlier",
    "in this regard", "to this end",
    "plays a crucial role", "serves as a foundation",
    "a comprehensive understanding", "shed light on",
    "this is particularly important", "in recent years",
    "has been widely studied", "it is well established",
]

CLAUDE_SIGNATURES = [
    "let me", "i should note", "it's worth",
    "to be clear", "more specifically",
    "at the same time", "in other words",
    "this suggests that", "one important",
    "the key insight", "fundamentally",
    "carefully consider", "nuanced understanding",
    "there are several", "it's important to",
]

GEMINI_SIGNATURES = [
    "based on the above", "in summary",
    "to summarize", "the following",
    "as shown in", "it can be seen",
    "the results show", "figure shows",
    "table shows", "as indicated",
    "considering the", "taking into account",
    "in light of", "with this in mind",
    "building upon", "drawing from",
]

# universal AI writing patterns — present across all models
UNIVERSAL_AI_PATTERNS = [
    "delve into", "it is crucial", "it is essential",
    "comprehensive overview", "multifaceted",
    "in conclusion", "in summary", "to summarize",
    "furthermore", "moreover", "additionally",
    "it is noteworthy", "it is evident",
    "underscore the importance", "highlight the need",
    "pave the way", "open new avenues",
    "robust framework", "holistic approach",
    "seamlessly integrate", "leverage the power",
    "transformative potential", "groundbreaking",
    "paradigm shift", "cutting-edge",
]

# human academic writing patterns — signal genuine authorship
HUMAN_ACADEMIC_PATTERNS = [
    "we observed", "we note that", "we found",
    "surprisingly", "unexpectedly", "contrary to",
    "we were unable to", "failed to",
    "this is consistent with", "in contrast to our expectation",
    "personal communication", "unpublished data",
    "in our experience", "we speculate",
    "one limitation", "a key limitation",
    "we cannot rule out", "remains unclear",
]

SECTION_HEADERS = [
    "abstract", "introduction", "background",
    "methods", "methodology", "materials",
    "results", "findings", "discussion",
    "conclusion", "references",
]


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class SectionSpectrum:
    section:         str
    human_score:     float
    ai_score:        float
    dominant_model:  str
    confidence:      float


@dataclass
class SpectrumFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class AIHumanSpectrumResult:
    overall_human_ratio:   float
    overall_ai_ratio:      float
    dominant_ai_model:     str
    model_confidence:      float
    section_breakdown:     list
    ai_sections:           list
    human_sections:        list
    universal_ai_count:    int
    gpt4_signal_count:     int
    claude_signal_count:   int
    gemini_signal_count:   int
    human_signal_count:    int
    spectrum_score:        float
    risk_level:            str
    summary:               str
    flags:                 list
    flags_count:           int


# ── main class ────────────────────────────────────────────────────────────────

class AIHumanSpectrumAnalyzer:
    """
    Maps the AI-human collaboration spectrum of a paper.

    Unlike binary AI detectors, this module produces a gradient:
    - Overall human vs AI ratio
    - Section-by-section breakdown
    - Which AI model's signatures dominate
    - Confidence level of model attribution

    The output answers: not just "is this AI?" but
    "where, how much, and which system?"
    """

    def analyze(self, text: str) -> AIHumanSpectrumResult:
        if not text or len(text.strip()) < 50:
            return self._empty_result()

        flags            = []
        sections         = self._split_sections(text)
        section_spectra  = [
            self._analyze_section(name, content)
            for name, content in sections.items()
        ]

        universal_ai     = self._count_patterns(text, UNIVERSAL_AI_PATTERNS)
        gpt4_count       = self._count_patterns(text, GPT4_SIGNATURES)
        claude_count     = self._count_patterns(text, CLAUDE_SIGNATURES)
        gemini_count     = self._count_patterns(text, GEMINI_SIGNATURES)
        human_count      = self._count_patterns(text, HUMAN_ACADEMIC_PATTERNS)

        dominant_model, model_conf = self._identify_dominant_model(
            gpt4_count, claude_count, gemini_count, universal_ai
        )

        overall_ai    = self._compute_overall_ai_ratio(
            universal_ai, gpt4_count, claude_count,
            gemini_count, human_count, text
        )
        overall_human = round(1.0 - overall_ai, 3)

        ai_sections    = [
            s.section for s in section_spectra if s.ai_score >= 0.55
        ]
        human_sections = [
            s.section for s in section_spectra if s.human_score >= 0.60
        ]

        spectrum_score = overall_ai
        risk_level     = self._get_risk_level(spectrum_score)

        self._generate_flags(
            overall_ai, ai_sections, dominant_model,
            model_conf, universal_ai, flags
        )

        return AIHumanSpectrumResult(
            overall_human_ratio  = overall_human,
            overall_ai_ratio     = round(overall_ai,   3),
            dominant_ai_model    = dominant_model,
            model_confidence     = round(model_conf,   3),
            section_breakdown    = section_spectra,
            ai_sections          = ai_sections,
            human_sections       = human_sections,
            universal_ai_count   = universal_ai,
            gpt4_signal_count    = gpt4_count,
            claude_signal_count  = claude_count,
            gemini_signal_count  = gemini_count,
            human_signal_count   = human_count,
            spectrum_score       = round(spectrum_score, 3),
            risk_level           = risk_level,
            summary              = self._write_summary(
                overall_ai, dominant_model, model_conf,
                ai_sections, flags, risk_level
            ),
            flags                = flags,
            flags_count          = len(flags),
        )

    # ── section analysis ───────────────────────────────────────────────────────

    def _split_sections(self, text: str) -> dict:
        """Split paper into named sections for per-section analysis."""
        text_lo   = text.lower()
        positions = []

        for header in SECTION_HEADERS:
            idx = text_lo.find(header)
            if idx == -1:
                continue
            line_start = text.rfind("\n", 0, idx) + 1
            line_end   = text.find("\n", idx)
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end].strip()
            if len(line) <= 40:
                positions.append((idx, header))

        if not positions:
            return {"full_text": text}

        positions.sort(key=lambda x: x[0])
        deduped = [positions[0]]
        for pos in positions[1:]:
            if pos[0] - deduped[-1][0] > 30:
                deduped.append(pos)

        sections = {}
        for i, (start, name) in enumerate(deduped):
            end            = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
            sections[name] = text[start:end]

        return sections

    def _analyze_section(self, name: str, text: str) -> SectionSpectrum:
        """Compute AI vs human score for a single section."""
        if len(text.strip()) < 40:
            return SectionSpectrum(
                section        = name,
                human_score    = 0.5,
                ai_score       = 0.5,
                dominant_model = "unknown",
                confidence     = 0.0,
            )

        ai_hits    = self._count_patterns(text, UNIVERSAL_AI_PATTERNS)
        human_hits = self._count_patterns(text, HUMAN_ACADEMIC_PATTERNS)
        words      = max(len(text.split()), 1)

        ai_density    = ai_hits    / (words / 100)
        human_density = human_hits / (words / 100)
        total_density = ai_density + human_density

        if total_density == 0:
            ai_score    = 0.3
            human_score = 0.7
        else:
            ai_score    = round(ai_density    / total_density, 3)
            human_score = round(human_density / total_density, 3)

        gpt4   = self._count_patterns(text, GPT4_SIGNATURES)
        claude = self._count_patterns(text, CLAUDE_SIGNATURES)
        gemini = self._count_patterns(text, GEMINI_SIGNATURES)

        model, conf = self._identify_dominant_model(gpt4, claude, gemini, ai_hits)

        return SectionSpectrum(
            section        = name,
            human_score    = human_score,
            ai_score       = ai_score,
            dominant_model = model,
            confidence     = round(conf, 3),
        )

    # ── model identification ───────────────────────────────────────────────────

    def _identify_dominant_model(
        self,
        gpt4:      int,
        claude:    int,
        gemini:    int,
        universal: int,
    ) -> tuple:
        """
        Identify which AI model's signatures dominate the text.
        Returns (model_name, confidence_score).
        Confidence is low when signals are weak or mixed.
        """
        total = gpt4 + claude + gemini
        if total == 0:
            return ("none", 0.0)

        scores = {"GPT-4": gpt4, "Claude": claude, "Gemini": gemini}
        dominant = max(scores, key=scores.get)
        top_score = scores[dominant]
        confidence = top_score / total

        # boost confidence when universal AI patterns also present
        if universal >= 3:
            confidence = min(confidence * 1.2, 1.0)

        # low confidence when signals are evenly distributed
        if confidence < 0.45:
            dominant = "mixed"

        return (dominant, round(confidence, 3))

    # ── ratio computation ──────────────────────────────────────────────────────

    def _compute_overall_ai_ratio(
        self,
        universal: int,
        gpt4:      int,
        claude:    int,
        gemini:    int,
        human:     int,
        text:      str,
    ) -> float:
        """
        Compute the overall probability that the paper is AI-generated.
        Blends multiple signals: phrase patterns, sentence uniformity,
        and vocabulary burstiness.
        """
        words    = max(len(text.split()), 1)
        ai_total = universal + gpt4 + claude + gemini

        phrase_ratio = min(ai_total / (words / 50), 1.0)

        burstiness   = self._compute_burstiness(text)
        # AI text has lower burstiness — more uniform sentence lengths
        uniformity   = 1.0 - min(burstiness, 1.0)

        ttr = self._compute_ttr(text)
        # AI text has slightly lower type-token ratio
        ai_ttr_signal = max(0.0, 0.75 - ttr)

        human_signal = min(human / max(words / 100, 1), 1.0)

        raw = (
            phrase_ratio    * 0.45 +
            uniformity      * 0.25 +
            ai_ttr_signal   * 0.15 +
            (1.0 - min(human_signal * 3, 1.0)) * 0.15
        )

        return round(min(max(raw, 0.0), 1.0), 3)

    def _compute_burstiness(self, text: str) -> float:
        """
        Burstiness measures sentence length variance.
        Human writing bursts — short then long then medium.
        AI writing is smoother, more uniform.
        """
        sentences = re.split(r'[.!?]+', text)
        lengths   = [len(s.split()) for s in sentences if len(s.split()) > 2]

        if len(lengths) < 5:
            return 0.5

        mean = sum(lengths) / len(lengths)
        if mean == 0:
            return 0.0

        variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
        cv       = math.sqrt(variance) / mean

        return round(min(cv, 1.0), 3)

    def _compute_ttr(self, text: str) -> float:
        """Type-token ratio on first 300 words — vocabulary diversity."""
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())[:300]
        if len(words) < 20:
            return 0.7
        return round(len(set(words)) / len(words), 3)

    # ── pattern counting ───────────────────────────────────────────────────────

    def _count_patterns(self, text: str, patterns: list) -> int:
        text_lo = text.lower()
        return sum(1 for p in patterns if p in text_lo)

    # ── flags ──────────────────────────────────────────────────────────────────

    def _generate_flags(
        self,
        overall_ai:    float,
        ai_sections:   list,
        dominant_model: str,
        model_conf:    float,
        universal_ai:  int,
        flags:         list,
    ) -> None:

        if overall_ai >= 0.70:
            flags.append(SpectrumFlag(
                flag_type   = "high_ai_generation_probability",
                severity    = "high",
                description = (
                    f"Overall AI generation probability: "
                    f"{round(overall_ai * 100, 1)}%. "
                    f"The paper's writing patterns are strongly consistent "
                    f"with AI-generated text rather than human academic writing."
                ),
                evidence    = (
                    f"AI ratio: {round(overall_ai * 100, 1)}%. "
                    f"Universal AI patterns detected: {universal_ai}. "
                    f"Dominant model signature: {dominant_model} "
                    f"(confidence: {round(model_conf * 100, 1)}%)."
                ),
                suggestion  = (
                    "If AI tools were used in writing, disclose this per "
                    "journal policy. Substantial AI generation without "
                    "disclosure violates most journal ethics guidelines."
                ),
            ))
        elif overall_ai >= 0.45:
            flags.append(SpectrumFlag(
                flag_type   = "moderate_ai_assistance_detected",
                severity    = "medium",
                description = (
                    f"Moderate AI writing assistance detected: "
                    f"{round(overall_ai * 100, 1)}% AI signal. "
                    f"This level suggests significant AI drafting or editing "
                    f"beyond light grammar assistance."
                ),
                evidence    = (
                    f"AI probability: {round(overall_ai * 100, 1)}%. "
                    f"Sections with AI patterns: {ai_sections if ai_sections else 'distributed'}."
                ),
                suggestion  = (
                    "Disclose AI tool usage per applicable journal policy."
                ),
            ))

        if dominant_model not in ("none", "mixed", "unknown") and model_conf >= 0.55:
            flags.append(SpectrumFlag(
                flag_type   = "model_signature_detected",
                severity    = "low",
                description = (
                    f"Writing signatures consistent with {dominant_model} "
                    f"detected with {round(model_conf * 100, 1)}% confidence. "
                    f"Characteristic phrase patterns of this system appear "
                    f"at elevated frequency."
                ),
                evidence    = (
                    f"Dominant model: {dominant_model}. "
                    f"Attribution confidence: {round(model_conf * 100, 1)}%."
                ),
                suggestion  = (
                    f"If {dominant_model} was used, disclose this in the "
                    f"methods or acknowledgments section."
                ),
            ))

        if len(ai_sections) >= 2:
            flags.append(SpectrumFlag(
                flag_type   = "multiple_sections_ai_generated",
                severity    = "medium",
                description = (
                    f"{len(ai_sections)} paper section(s) show elevated "
                    f"AI writing patterns: {ai_sections}. "
                    f"Concentrated AI generation in core sections "
                    f"raises disclosure concerns."
                ),
                evidence    = f"AI-pattern sections: {ai_sections}.",
                suggestion  = (
                    "Review each flagged section for undisclosed AI generation. "
                    "Methods and Results sections require particular scrutiny."
                ),
            ))

    # ── scoring ────────────────────────────────────────────────────────────────

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.25:   return "medium"
        return "low"

    def _write_summary(
        self,
        overall_ai:    float,
        dominant_model: str,
        model_conf:    float,
        ai_sections:   list,
        flags:         list,
        risk_level:    str,
    ) -> str:
        human_pct = round((1.0 - overall_ai) * 100, 1)
        ai_pct    = round(overall_ai * 100, 1)

        model_str = ""
        if dominant_model not in ("none", "mixed", "unknown") and model_conf >= 0.45:
            model_str = (
                f" Dominant AI model signature: {dominant_model} "
                f"({round(model_conf * 100, 1)}% confidence)."
            )

        section_str = ""
        if ai_sections:
            section_str = f" AI-dominant sections: {ai_sections}."

        return (
            f"AI-Human Spectrum Analysis: "
            f"{human_pct}% human / {ai_pct}% AI estimated."
            f"{model_str}{section_str} "
            f"Risk level: {risk_level.upper()}."
        )

    def _empty_result(self) -> AIHumanSpectrumResult:
        return AIHumanSpectrumResult(
            overall_human_ratio  = 1.0,
            overall_ai_ratio     = 0.0,
            dominant_ai_model    = "none",
            model_confidence     = 0.0,
            section_breakdown    = [],
            ai_sections          = [],
            human_sections       = [],
            universal_ai_count   = 0,
            gpt4_signal_count    = 0,
            claude_signal_count  = 0,
            gemini_signal_count  = 0,
            human_signal_count   = 0,
            spectrum_score       = 0.0,
            risk_level           = "low",
            summary              = (
                "AI-Human Spectrum Analysis: Insufficient text for analysis. "
                "Risk level: LOW."
            ),
            flags                = [],
            flags_count          = 0,
        )