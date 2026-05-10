# Scientific Fraud Fingerprinting
# --------------------------------
# The idea is simple but the execution is rare:
# every researcher leaves traces — in how they round numbers,
# which words they repeat, how long their sentences run,
# how they structure a paragraph.
#
# This module reads those traces.
# It does not need a database to compare against.
# It finds the inconsistencies within a single paper —
# the places where the writing DNA suddenly changes.
#
# A sudden style shift in section 3.
# Numbers rounded to 2 decimal places everywhere except one table.
# Vocabulary that jumps from undergraduate level to post-doctoral
# in the space of a paragraph.
#
# These are the fingerprints of fraud.

import re
import math
from dataclasses import dataclass, field
from collections import Counter


# ── constants ─────────────────────────────────────────────────────────────────

# function words are style-neutral — they reveal writing habit, not topic
FUNCTION_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "by", "from", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "shall", "must",
    "that", "which", "who", "this", "these", "those", "it", "its",
    "we", "our", "they", "their", "as", "if", "when", "than", "so"
}

# academic hedge words — overuse signals LLM or copy-paste from reviews
HEDGE_WORDS = [
    "however", "therefore", "furthermore", "moreover", "nevertheless",
    "consequently", "subsequently", "additionally", "notably", "importantly",
    "significantly", "essentially", "fundamentally", "specifically",
    "particularly", "generally", "typically", "usually", "often"
]

# section headers used to split the paper into zones
SECTION_HEADERS = [
    "abstract", "introduction", "background", "related work",
    "methods", "methodology", "materials", "experimental",
    "results", "findings", "discussion", "conclusion",
    "references", "acknowledgment"
]


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class StyleZone:
    name: str
    text: str
    avg_sentence_length: float
    vocabulary_richness: float
    function_word_density: float
    hedge_word_density: float
    number_precision: float   # average decimal places used


@dataclass
class FingerprintFlag:
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


@dataclass
class FingerprintResult:
    style_zones: list
    style_shift_score: float
    precision_inconsistency: float
    vocabulary_mixing_score: float
    hedge_overuse_score: float
    fingerprint_score: float
    risk_level: str
    summary: str
    flags: list
    flags_count: int


# ── main class ────────────────────────────────────────────────────────────────

class FraudFingerprinter:
    """
    Extracts the writing DNA of a paper and searches for breaks in it.

    A genuine single-author paper has a consistent style throughout —
    the same sentence rhythms, the same vocabulary level, the same
    number precision. Breaks in these patterns are anomalies worth flagging.

    Three layers of analysis:
    1. Style consistency across paper sections
    2. Number precision consistency across tables and text
    3. Vocabulary level mixing (sudden register shifts)
    """

    def analyze(self, text: str) -> FingerprintResult:
        zones  = self._build_style_zones(text)
        flags  = []

        style_shift        = self._measure_style_shift(zones, flags)
        precision_gap      = self._measure_precision_inconsistency(text, flags)
        vocab_mix          = self._measure_vocabulary_mixing(text, flags)
        hedge_score        = self._measure_hedge_overuse(text, flags)

        fingerprint_score  = self._compute_score(
            style_shift, precision_gap, vocab_mix, hedge_score
        )
        risk_level         = self._get_risk_level(fingerprint_score)

        return FingerprintResult(
            style_zones               = zones,
            style_shift_score         = round(style_shift,   3),
            precision_inconsistency   = round(precision_gap, 3),
            vocabulary_mixing_score   = round(vocab_mix,     3),
            hedge_overuse_score       = round(hedge_score,   3),
            fingerprint_score         = round(fingerprint_score, 3),
            risk_level                = risk_level,
            summary                   = self._write_summary(flags, risk_level),
            flags                     = flags,
            flags_count               = len(flags),
        )

    # ── zone building ──────────────────────────────────────────────────────────

    def _build_style_zones(self, text: str) -> list:
        """
        Divide the paper into named sections and compute style
        metrics for each zone independently.
        A single paper should look like one person wrote it.
        """
        raw_sections = self._split_sections(text)

        # need at least 2 zones to compare — fall back to halves
        if len(raw_sections) < 2:
            mid  = len(text) // 2
            raw_sections = {
                "first_half":  text[:mid],
                "second_half": text[mid:],
            }

        zones = []
        for name, section_text in raw_sections.items():
            if len(section_text.strip()) < 80:
                continue
            zones.append(StyleZone(
                name                  = name,
                text                  = section_text,
                avg_sentence_length   = self._avg_sentence_length(section_text),
                vocabulary_richness   = self._vocabulary_richness(section_text),
                function_word_density = self._function_word_density(section_text),
                hedge_word_density    = self._hedge_density(section_text),
                number_precision      = self._avg_number_precision(section_text),
            ))
        return zones

    def _split_sections(self, text: str) -> dict:
        text_lower = text.lower()
        positions  = []

        for header in SECTION_HEADERS:
            idx = text_lower.find(header)
            if idx == -1:
                continue
            line_start   = text.rfind("\n", 0, idx) + 1
            line_end     = text.find("\n", idx)
            if line_end == -1:
                line_end = len(text)
            line_content = text[line_start:line_end].strip()
            if len(line_content) <= 50:
                positions.append((idx, header))

        if not positions:
            return {}

        positions.sort(key=lambda x: x[0])

        # deduplicate close headers
        clean = [positions[0]]
        for pos in positions[1:]:
            if pos[0] - clean[-1][0] > 30:
                clean.append(pos)

        sections = {}
        for i, (start, name) in enumerate(clean):
            end              = clean[i + 1][0] if i + 1 < len(clean) else len(text)
            sections[name]   = text[start:end]

        return sections

    # ── style shift detection ──────────────────────────────────────────────────

    def _measure_style_shift(self, zones: list, flags: list) -> float:
        if len(zones) < 2:
            return 0.0

        # collect per-zone metrics into vectors
        sent_lengths  = [z.avg_sentence_length   for z in zones]
        vocab_levels  = [z.vocabulary_richness    for z in zones]
        func_densities = [z.function_word_density for z in zones]

        # coefficient of variation tells us how inconsistent values are
        cv_sent  = self._coeff_of_variation(sent_lengths)
        cv_vocab = self._coeff_of_variation(vocab_levels)
        cv_func  = self._coeff_of_variation(func_densities)

        shift_score = (cv_sent * 0.40) + (cv_vocab * 0.35) + (cv_func * 0.25)
        shift_score = min(shift_score, 1.0)

        if shift_score >= 0.55:
            # find the zone that deviates most
            mean_sent = sum(sent_lengths) / len(sent_lengths)
            worst_zone = max(
                zones,
                key=lambda z: abs(z.avg_sentence_length - mean_sent)
            )
            flags.append(FingerprintFlag(
                flag_type   = "style_shift_detected",
                severity    = "high" if shift_score >= 0.7 else "medium",
                description = (
                    f"Writing style shifts significantly across paper sections. "
                    f"Coefficient of variation in sentence length: "
                    f"{round(cv_sent * 100, 1)}%. "
                    f"This pattern suggests multiple authors, ghost-writing, "
                    f"or sections copied from different sources."
                ),
                evidence    = (
                    f"Most divergent section: '{worst_zone.name}' — "
                    f"avg sentence length {round(worst_zone.avg_sentence_length, 1)} words "
                    f"vs paper mean {round(mean_sent, 1)} words."
                ),
                suggestion  = (
                    "Review sections for authorship consistency. "
                    "High style variation in a single-author paper is unusual."
                ),
            ))

        return shift_score

    # ── number precision consistency ───────────────────────────────────────────

    def _measure_precision_inconsistency(self, text: str, flags: list) -> float:
        """
        Real data reported by one person tends to use consistent decimal precision.
        Mixing 4-decimal and 0-decimal reporting in the same paper is a signal.
        """
        numbers = re.findall(r'\b\d+(\.\d+)?\b', text)
        decimals = []
        for match in re.finditer(r'\b\d+\.(\d+)\b', text):
            decimals.append(len(match.group(1)))

        if len(decimals) < 5:
            return 0.0

        counter     = Counter(decimals)
        total       = len(decimals)
        dominant    = counter.most_common(1)[0][1] / total
        inconsistency = 1.0 - dominant

        if inconsistency >= 0.55:
            precision_counts = ", ".join(
                f"{k} decimal ({v}x)" for k, v in counter.most_common(4)
            )
            flags.append(FingerprintFlag(
                flag_type   = "precision_inconsistency",
                severity    = "medium",
                description = (
                    f"Number reporting precision is inconsistent across the paper. "
                    f"{round(inconsistency * 100, 1)}% of numbers deviate from "
                    f"the dominant precision level."
                ),
                evidence    = f"Decimal place distribution: {precision_counts}.",
                suggestion  = (
                    "Verify that all numerical results originate from the same "
                    "analysis pipeline. Mixed precision often signals data from "
                    "different sources being merged without harmonization."
                ),
            ))

        return round(min(inconsistency, 1.0), 3)

    # ── vocabulary register mixing ─────────────────────────────────────────────

    def _measure_vocabulary_mixing(self, text: str, flags: list) -> float:
        """
        Splits the paper into paragraphs and measures vocabulary level
        per paragraph. A sudden jump from simple to complex vocabulary
        within a few paragraphs is a ghost-writing or copy-paste signal.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]

        if len(paragraphs) < 4:
            return 0.0

        richness_per_para = [
            self._vocabulary_richness(p) for p in paragraphs
        ]

        cv = self._coeff_of_variation(richness_per_para)

        if cv >= 0.30:
            worst_idx = richness_per_para.index(max(richness_per_para))
            flags.append(FingerprintFlag(
                flag_type   = "vocabulary_register_shift",
                severity    = "medium",
                description = (
                    f"Vocabulary complexity shifts abruptly across paragraphs. "
                    f"CV of vocabulary richness across {len(paragraphs)} paragraphs: "
                    f"{round(cv * 100, 1)}%. "
                    f"Genuine single-author writing maintains a more consistent register."
                ),
                evidence    = (
                    f"Paragraph {worst_idx + 1} has the highest vocabulary richness "
                    f"({round(richness_per_para[worst_idx], 3)}), "
                    f"diverging from the paper average "
                    f"({round(sum(richness_per_para)/len(richness_per_para), 3)})."
                ),
                suggestion  = (
                    "Review high-divergence paragraphs for possible copy-paste "
                    "from other sources. Consider running targeted plagiarism checks."
                ),
            ))

        return round(min(cv, 1.0), 3)

    # ── hedge word overuse ─────────────────────────────────────────────────────

    def _measure_hedge_overuse(self, text: str, flags: list) -> float:
        """
        Hedge words are the verbal filler of academic writing.
        LLM-generated and hastily assembled papers massively overuse them.
        A clean research paper uses them sparingly.
        """
        words       = re.findall(r'\b[a-z]+\b', text.lower())
        total_words = len(words)

        if total_words < 100:
            return 0.0

        hedge_count = sum(1 for w in words if w in HEDGE_WORDS)
        density     = hedge_count / total_words

        # above 2.5% hedge density is unusual in genuine academic writing
        score = min(density / 0.025, 1.0)

        if score >= 0.7:
            flags.append(FingerprintFlag(
                flag_type   = "hedge_word_overuse",
                severity    = "low",
                description = (
                    f"Hedge and transition word density is elevated: "
                    f"{hedge_count} hedge words in {total_words} total words "
                    f"({round(density * 100, 2)}%). "
                    f"Typical genuine academic papers stay below 2.5%."
                ),
                evidence    = (
                    f"Hedge density {round(density * 100, 2)}% vs "
                    f"normal threshold 2.5%."
                ),
                suggestion  = (
                    "Elevated hedge density alone is not conclusive, "
                    "but combined with other flags it strengthens the case "
                    "for LLM-assisted writing or assembled-from-fragments authorship."
                ),
            ))

        return round(score, 3)

    # ── low-level metrics ──────────────────────────────────────────────────────

    def _avg_sentence_length(self, text: str) -> float:
        sentences = re.split(r'[.!?]+', text)
        lengths   = [
            len(s.split()) for s in sentences
            if len(s.split()) > 2
        ]
        if not lengths:
            return 0.0
        return sum(lengths) / len(lengths)

    def _vocabulary_richness(self, text: str) -> float:
        """Type-token ratio on first 200 words — standard measure."""
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())[:200]
        if len(words) < 20:
            return 0.0
        return len(set(words)) / len(words)

    def _function_word_density(self, text: str) -> float:
        words = re.findall(r'\b[a-z]+\b', text.lower())
        if not words:
            return 0.0
        count = sum(1 for w in words if w in FUNCTION_WORDS)
        return count / len(words)

    def _hedge_density(self, text: str) -> float:
        words = re.findall(r'\b[a-z]+\b', text.lower())
        if not words:
            return 0.0
        count = sum(1 for w in words if w in HEDGE_WORDS)
        return count / len(words)

    def _avg_number_precision(self, text: str) -> float:
        decimals = [
            len(m.group(1))
            for m in re.finditer(r'\b\d+\.(\d+)\b', text)
        ]
        if not decimals:
            return 0.0
        return sum(decimals) / len(decimals)

    def _coeff_of_variation(self, values: list) -> float:
        """Standard deviation / mean — measures relative spread."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance) / mean

    # ── scoring ────────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        style_shift: float,
        precision_gap: float,
        vocab_mix: float,
        hedge_score: float,
    ) -> float:
        score = (
            style_shift   * 0.40 +
            precision_gap * 0.25 +
            vocab_mix     * 0.25 +
            hedge_score   * 0.10
        )
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:
            return "critical"
        if score >= 0.45:
            return "high"
        if score >= 0.25:
            return "medium"
        return "low"

    def _write_summary(self, flags: list, risk_level: str) -> str:
        if not flags:
            return (
                "Fraud Fingerprint Analysis: Writing DNA appears consistent "
                "throughout the paper. No authorship anomalies detected. "
                f"Risk level: {risk_level.upper()}."
            )

        high   = sum(1 for f in flags if f.severity == "high")
        medium = sum(1 for f in flags if f.severity == "medium")
        low    = sum(1 for f in flags if f.severity == "low")

        parts  = []
        if high:
            parts.append(f"{high} high-severity authorship anomal{'y' if high == 1 else 'ies'}")
        if medium:
            parts.append(f"{medium} medium-severity inconsistenc{'y' if medium == 1 else 'ies'}")
        if low:
            parts.append(f"{low} low-severity signal{'s' if low > 1 else ''}")

        return (
            f"Fraud Fingerprint Analysis: {', '.join(parts)} detected. "
            f"Risk level: {risk_level.upper()}."
        )