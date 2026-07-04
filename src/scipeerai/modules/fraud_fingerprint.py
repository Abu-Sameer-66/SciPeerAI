import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ── Section markers ───────────────────────────────────────────────────────────

SECTION_MARKERS = [
    "abstract", "introduction", "background", "related work",
    "literature review", "methodology", "methods", "materials and methods",
    "experimental setup", "results", "findings", "discussion",
    "conclusion", "conclusions", "references", "acknowledgment",
    "acknowledgements",
]

EXPECTED_ORDER = [
    "abstract", "introduction", "background", "related work",
    "literature review", "methodology", "methods", "materials and methods",
    "results", "findings", "discussion", "conclusion", "conclusions",
    "references",
]

# ── Style signal patterns ─────────────────────────────────────────────────────

PASSIVE_PAT = re.compile(
    r'\b(?:was|were|is|are|been|being)\s+\w+ed\b',
    re.IGNORECASE,
)

HEDGE_WORDS = [
    "may", "might", "could", "possibly", "perhaps", "suggest",
    "appear", "seem", "likely", "probably", "approximately",
    "indicate", "potential", "tend to",
]

CITATION_PAT = re.compile(
    r'\[\d+\]|\(\w+,?\s*\d{4}\)|\b\w+\s+\d{4}\b',
)

JARGON_PAT = re.compile(
    r'\b(?:therefore|furthermore|moreover|however|nevertheless'
    r'|consequently|subsequently|notably|specifically|particularly'
    r'|importantly|significantly|substantially)\b',
    re.IGNORECASE,
)

AI_PHRASE_PAT = re.compile(
    r'\b(?:it is worth noting|in conclusion|furthermore|notably'
    r'|it should be noted|taken together|in summary|shed(?:s)? light'
    r'|delve|leverage|utilize|facilitate|groundbreaking|unprecedented'
    r'|robust|comprehensive|state-of-the-art|cutting-edge)\b',
    re.IGNORECASE,
)

AUTHORSHIP_SIGNALS = re.compile(
    r'\b(?:the author|the authors|we|our|I\b)',
    re.IGNORECASE,
)

TEMPLATE_PHRASES = [
    "this paper presents", "in this paper", "this study aims",
    "the main contribution", "to the best of our knowledge",
    "this work proposes", "we propose a novel", "extensive experiments",
    "state of the art", "outperforms existing", "superior performance",
    "promising results", "significantly better", "we demonstrate that",
    "our approach achieves", "our method achieves",
]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class FraudFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class FraudFingerprintResult:
    fingerprint_score:      float
    risk_level:             str
    summary:                str
    section_dna:            Dict[str, dict]
    anomalies:              List[dict]
    flags:                  List[FraudFlag] = field(default_factory=list)
    flags_count:            int = 0
    ai_phrase_count:        int = 0
    style_consistency:      float = 0.0
    authorship_consistency: float = 0.0
    section_order_correct:  bool = True
    template_score:         float = 0.0


# ── Main class ────────────────────────────────────────────────────────────────

class FraudFingerprinter:
    """
    Fraud Fingerprinting v2.3.4

    Detects writing style inconsistencies across paper sections.
    Ghost-writing, multi-author style mixing, and AI-generated
    section substitution all produce detectable fingerprint anomalies.

    v2.3.4 upgrades:
    - 8 style DNA features (was 5)
    - Coefficient of variation scoring — works on short text too
    - Z-score per-section outlier detection
    - AI phrase density integrated into fingerprint score
    - _extract_authorship_signals preserved
    - _check_section_order preserved
    - _detect_template_writing preserved
    """

    def analyze(self, text: str, sections: Optional[dict] = None) -> FraudFingerprintResult:
        # Split into sections if not pre-split
        if not sections:
            sections = self._split_sections(text)

        # Fallback — treat whole text as one section
        if not sections:
            sections = {"full_text": text}

        # Compute style DNA per section
        dna_map = {}
        for sec_name, sec_text in sections.items():
            if sec_text and len(sec_text.strip()) > 20:
                dna_map[sec_name] = self._compute_style_dna(sec_text)

        # Compare sections for inconsistency
        inconsistency_score, anomalies = self._compare_sections(dna_map)

        # Authorship signals
        authorship_score = self._extract_authorship_signals(text, sections)

        # Section order check
        order_correct, order_flags = self._check_section_order(sections)

        # Template writing detection
        template_score, template_phrases_found = self._detect_template_writing(text)

        # AI phrase analysis on full text
        ai_count   = len(AI_PHRASE_PAT.findall(text))
        words      = text.split()
        n_words    = max(len(words), 1)
        ai_density = ai_count / n_words

        # Combined fingerprint score
        ai_component      = min(ai_density * 12, 0.40)
        template_comp     = min(template_score * 0.15, 0.15)
        fingerprint_score = min(
            inconsistency_score * 0.55
            + ai_component      * 0.25
            + template_comp     * 0.10
            + (0.10 if not order_correct else 0.0),
            1.0
        )

        # Flags
        flags: List[FraudFlag] = []

        if inconsistency_score >= 0.45:
            flags.append(FraudFlag(
                flag_type   = "style_inconsistency",
                severity    = "high" if inconsistency_score >= 0.65 else "medium",
                description = (
                    f"Writing style varies significantly across sections "
                    f"(inconsistency score: {round(inconsistency_score * 100)}%). "
                    f"This pattern is consistent with ghost-writing, "
                    f"multi-author section contributions without harmonization, "
                    f"or AI-generated section substitution."
                ),
                evidence    = (
                    f"{len(anomalies)} section-level anomalies detected: "
                    + (", ".join(
                        f"{a['section']}.{a['feature']} (CV={a['cv']})"
                        for a in anomalies[:3]
                    ) if anomalies else "style drift across sections")
                ),
                suggestion  = (
                    "Review sections for stylistic consistency. "
                    "Large vocabulary or sentence-length differences between "
                    "sections may indicate undisclosed multiple authors or "
                    "AI-assisted writing."
                ),
            ))

        if ai_count >= 5:
            flags.append(FraudFlag(
                flag_type   = "ai_phrase_density",
                severity    = "high" if ai_count >= 10 else "medium",
                description = (
                    f"High density of AI-typical phrases detected "
                    f"({ai_count} phrases). "
                    f"Pattern consistent with LLM-generated or heavily "
                    f"LLM-edited content."
                ),
                evidence    = (
                    f"AI phrase count: {ai_count} | "
                    f"Density: {round(ai_density * 1000, 1)} per 1000 words"
                ),
                suggestion  = (
                    "Review for AI-generated content. Journals increasingly "
                    "require disclosure of AI writing assistance."
                ),
            ))

        if not order_correct and order_flags:
            flags.append(FraudFlag(
                flag_type   = "section_order_anomaly",
                severity    = "low",
                description = (
                    "Paper sections appear in non-standard order. "
                    "This may indicate copy-paste assembly or structural manipulation."
                ),
                evidence    = "; ".join(order_flags[:3]),
                suggestion  = (
                    "Verify that sections follow standard academic structure: "
                    "Abstract → Introduction → Methods → Results → Discussion → Conclusion."
                ),
            ))

        if template_score >= 0.30:
            flags.append(FraudFlag(
                flag_type   = "template_writing_detected",
                severity    = "medium" if template_score >= 0.50 else "low",
                description = (
                    f"High density of template/boilerplate phrases detected "
                    f"(score: {round(template_score * 100)}%). "
                    f"Pattern associated with paper mills and AI-assisted writing."
                ),
                evidence    = (
                    f"Template phrases found: "
                    f"{', '.join(template_phrases_found[:5])}"
                ),
                suggestion  = (
                    "Replace generic template phrases with specific, "
                    "original descriptions of your methodology and findings."
                ),
            ))

        if anomalies:
            high_anom = [a for a in anomalies if a.get("severity") == "high"]
            if high_anom:
                flags.append(FraudFlag(
                    flag_type   = "section_outlier",
                    severity    = "medium",
                    description = (
                        f"{len(high_anom)} section(s) show extreme style deviation "
                        f"from the rest of the paper."
                    ),
                    evidence    = (
                        "; ".join(
                            f"Section '{a['section']}' has {a['feature']}="
                            f"{a['value']} vs paper mean {a['mean']}"
                            for a in high_anom[:2]
                        )
                    ),
                    suggestion  = (
                        "Inspect flagged sections for authorship consistency. "
                        "Outlier sections may have been written by a different person "
                        "or generated by AI."
                    ),
                ))

        # Risk level
        risk_level = self._get_risk_level(fingerprint_score)

        # Summary
        summary = self._build_summary(
            fingerprint_score, risk_level,
            len(anomalies), ai_count, flags
        )

        return FraudFingerprintResult(
            fingerprint_score      = round(fingerprint_score, 4),
            risk_level             = risk_level,
            summary                = summary,
            section_dna            = dna_map,
            anomalies              = anomalies,
            flags                  = flags,
            flags_count            = len(flags),
            ai_phrase_count        = ai_count,
            style_consistency      = round(1.0 - inconsistency_score, 4),
            authorship_consistency = round(authorship_score, 4),
            section_order_correct  = order_correct,
            template_score         = round(template_score, 4),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _split_sections(self, text: str) -> dict:
        """Split paper text into named sections."""
        sections   = {}
        text_lower = text.lower()

        for i, marker in enumerate(SECTION_MARKERS):
            start = text_lower.find(marker)
            if start == -1:
                continue
            end = len(text)
            for next_marker in SECTION_MARKERS[i + 1:]:
                next_idx = text_lower.find(next_marker, start + len(marker))
                if next_idx != -1:
                    end = next_idx
                    break
            section_text = text[start:end].strip()
            if len(section_text) > 30:
                sections[marker] = section_text

        return sections

    def _compute_style_dna(self, text: str) -> dict:
        """
        v2.3.4 — 8-feature style DNA.
        Works on both short and long text sections.
        """
        if not text or len(text.strip()) < 10:
            return {}

        words     = text.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 5]
        n_words   = max(len(words), 1)
        n_sents   = max(len(sentences), 1)

        avg_sent_len     = n_words / n_sents
        vocab_diversity  = len(set(w.lower() for w in words)) / n_words
        passive_count    = len(PASSIVE_PAT.findall(text))
        passive_ratio    = passive_count / n_sents
        hedge_count      = sum(1 for w in HEDGE_WORDS if w in text.lower())
        hedge_ratio      = hedge_count / n_words
        cite_count       = len(CITATION_PAT.findall(text))
        citation_density = cite_count / n_words
        jargon_count     = len(JARGON_PAT.findall(text))
        jargon_ratio     = jargon_count / n_words
        question_ratio   = text.count('?') / n_sents
        numbers          = re.findall(r'\b\d+\.?\d*\b', text)
        number_density   = len(numbers) / n_words

        return {
            "avg_sentence_len": round(avg_sent_len,    3),
            "vocab_diversity":  round(vocab_diversity,  3),
            "passive_ratio":    round(passive_ratio,    3),
            "hedge_ratio":      round(hedge_ratio,      4),
            "citation_density": round(citation_density, 4),
            "jargon_ratio":     round(jargon_ratio,     4),
            "question_ratio":   round(question_ratio,   4),
            "number_density":   round(number_density,   4),
        }

    def _compare_sections(self, dna_map: dict) -> tuple:
        """
        v2.3.4 — Coefficient of variation scoring.
        Works on both short and long sections.
        """
        sections = {k: v for k, v in dna_map.items() if v}
        if len(sections) < 2:
            return 0.0, []

        features = [
            "avg_sentence_len", "vocab_diversity", "passive_ratio",
            "hedge_ratio", "citation_density", "jargon_ratio",
            "number_density",
        ]

        anomalies      = []
        feature_scores = []

        for feat in features:
            vals = [
                dna[feat] for dna in sections.values()
                if feat in dna and dna[feat] is not None
            ]
            if len(vals) < 2:
                continue

            mean_val = sum(vals) / len(vals)
            if mean_val == 0:
                continue

            std_val = (sum((v - mean_val) ** 2 for v in vals) / len(vals)) ** 0.5
            cv      = std_val / (mean_val + 1e-9)
            feature_scores.append(min(cv, 1.0))

            if cv > 0.35:
                for sec_name, dna in sections.items():
                    if feat not in dna:
                        continue
                    val      = dna[feat]
                    z_approx = abs(val - mean_val) / (std_val + 1e-9)
                    if z_approx > 1.5:
                        anomalies.append({
                            "section":  sec_name,
                            "feature":  feat,
                            "value":    round(val, 4),
                            "mean":     round(mean_val, 4),
                            "cv":       round(cv, 3),
                            "severity": "high" if cv > 0.60 else "medium",
                        })

        if not feature_scores:
            return 0.0, []

        high_cv_count = sum(1 for s in feature_scores if s > 0.60)
        med_cv_count  = sum(1 for s in feature_scores if 0.35 < s <= 0.60)
        base_score    = sum(feature_scores) / len(feature_scores)
        bonus         = high_cv_count * 0.12 + med_cv_count * 0.05
        final_score   = min(base_score + bonus, 1.0)

        return round(final_score, 4), anomalies

    def _extract_authorship_signals(self, text: str, sections: dict) -> float:
        """
        Detect authorship inconsistencies across sections.
        Shifts in first-person vs third-person usage suggest
        different authors wrote different sections.
        """
        if not sections or len(sections) < 2:
            return 1.0

        section_scores = {}
        for sec_name, sec_text in sections.items():
            if not sec_text:
                continue
            words     = sec_text.split()
            n_words   = max(len(words), 1)
            we_count  = len(re.findall(r'\bwe\b|\bour\b', sec_text, re.IGNORECASE))
            i_count   = len(re.findall(r'\bI\b', sec_text))
            the_author = len(re.findall(r'\bthe\s+authors?\b', sec_text, re.IGNORECASE))
            first_person  = (we_count + i_count) / n_words
            third_person  = the_author / n_words
            section_scores[sec_name] = {
                "first_person": first_person,
                "third_person": third_person,
            }

        if len(section_scores) < 2:
            return 1.0

        fp_vals = [v["first_person"] for v in section_scores.values()]
        mean_fp = sum(fp_vals) / len(fp_vals)
        if mean_fp == 0:
            return 1.0

        std_fp = (sum((v - mean_fp) ** 2 for v in fp_vals) / len(fp_vals)) ** 0.5
        cv_fp  = std_fp / (mean_fp + 1e-9)

        # High CV = inconsistent authorship voice
        return round(max(0.0, 1.0 - min(cv_fp, 1.0)), 4)

    def _check_section_order(self, sections: dict) -> tuple:
        """
        Verify that sections appear in the expected academic order.
        Out-of-order sections may indicate copy-paste assembly.
        """
        if not sections:
            return True, []

        found_order = [
            marker for marker in EXPECTED_ORDER
            if marker in sections
        ]

        if len(found_order) < 2:
            return True, []

        flags      = []
        correct    = True
        prev_index = -1

        for sec in found_order:
            curr_index = EXPECTED_ORDER.index(sec)
            if curr_index < prev_index:
                correct = False
                flags.append(
                    f"'{sec}' appears after section(s) that should follow it"
                )
            prev_index = curr_index

        return correct, flags

    def _detect_template_writing(self, text: str) -> tuple:
        """
        Detect boilerplate / paper-mill template phrases.
        High density of template phrases is associated with
        AI-generated papers and paper mills.
        """
        text_lower  = text.lower()
        found       = [p for p in TEMPLATE_PHRASES if p in text_lower]
        words       = text.split()
        n_words     = max(len(words), 1)

        # Normalize by text length
        raw_score   = len(found) / max(len(TEMPLATE_PHRASES), 1)
        density_pen = min(len(found) / (n_words / 100), 0.5)
        score       = min(raw_score * 0.6 + density_pen * 0.4, 1.0)

        return round(score, 4), found

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.20:   return "medium"
        return "low"

    def _build_summary(
        self, score: float, risk: str,
        n_anomalies: int, ai_count: int, flags: list
    ) -> str:
        parts = []
        if n_anomalies:
            parts.append(f"{n_anomalies} style anomaly/anomalies detected")
        if ai_count >= 5:
            parts.append(f"{ai_count} AI-typical phrases found")
        if not parts:
            parts.append("No significant style inconsistencies detected")

        return (
            f"Fraud Fingerprint analysis: {', '.join(parts)}. "
            f"Fingerprint score: {round(score * 100)}%. "
            f"Risk level: {risk.upper()}."
        )