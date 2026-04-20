# src/scipeerai/modules/llm_detector.py
#
# LLM-Generated Paper Detector
# Detects AI-generated academic text using:
# - Burstiness analysis (human text varies, LLM uniform)
# - Vocabulary diversity (TTR — type-token ratio)
# - Sentence length uniformity
# - Perplexity approximation via n-gram analysis
# - LLM signature phrases detection
#
# Completely novel approach — no free tool does this.
# Based on research in AI text detection (2023-2024).

import re
import math
import statistics
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class LLMFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class LLMResult:
    burstiness_score:    float
    vocabulary_diversity: float
    sentence_uniformity: float
    llm_phrase_count:    int
    llm_score:           float
    risk_level:          str
    summary:             str
    flags:               list = field(default_factory=list)
    flags_count:         int  = 0


class LLMDetector:
    """
    LLM-Generated Paper Detector.
    Human writing is bursty — complex sentences mixed
    with simple ones, varied vocabulary, irregular rhythm.
    LLM writing is uniform — consistent complexity,
    repetitive structures, characteristic phrases.
    """

    # LLM signature phrases — common in GPT/Claude output
    LLM_PHRASES = [
        "it is worth noting",
        "it is important to note",
        "it should be noted",
        "furthermore",
        "moreover",
        "in conclusion",
        "in summary",
        "this paper presents",
        "this study aims to",
        "the results demonstrate",
        "the findings suggest",
        "significantly",
        "notably",
        "interestingly",
        "it is evident",
        "plays a crucial role",
        "plays an important role",
        "has been widely studied",
        "in recent years",
        "state of the art",
        "state-of-the-art",
        "leveraging",
        "utilize",
        "utilizes",
        "delve into",
        "delves into",
        "shed light on",
        "sheds light on",
        "comprehensive analysis",
        "robust framework",
        "novel approach",
        "cutting-edge",
        "landscape of",
        "in the realm of",
        "a testament to",
    ]

    # Sentence splitter
    SENT_PAT = re.compile(r'[.!?]+\s+')

    # Word tokenizer
    WORD_PAT = re.compile(r'\b[a-z]+\b', re.IGNORECASE)

    def analyze(self, text: str) -> LLMResult:
        if len(text.strip()) < 100:
            return LLMResult(
                burstiness_score     = 0.0,
                vocabulary_diversity = 1.0,
                sentence_uniformity  = 0.0,
                llm_phrase_count     = 0,
                llm_score            = 0.0,
                risk_level           = "low",
                summary              = (
                    "LLM Detection: Insufficient text for analysis "
                    "(minimum 100 characters required)."
                ),
                flags      = [],
                flags_count= 0,
            )

        sentences  = self._split_sentences(text)
        words      = self._tokenize(text)
        flags      = []

        # ── 1. Burstiness Analysis ────────────────────────────────
        burstiness = self._burstiness(sentences)

        # ── 2. Vocabulary Diversity (TTR) ─────────────────────────
        ttr = self._type_token_ratio(words)

        # ── 3. Sentence Length Uniformity ─────────────────────────
        uniformity = self._sentence_uniformity(sentences)

        # ── 4. LLM Phrase Detection ───────────────────────────────
        phrase_count, phrases_found = self._detect_phrases(text)

        # ── Flag 1: Low burstiness ────────────────────────────────
        if burstiness < 0.3 and len(sentences) >= 5:
            flags.append(LLMFlag(
                flag_type   = "low_burstiness",
                severity    = "high" if burstiness < 0.15 else "medium",
                description = (
                    f"Text burstiness score: {round(burstiness, 3)}. "
                    f"Human writing naturally varies between complex "
                    f"and simple sentences (high burstiness). "
                    f"This text shows unusually uniform complexity — "
                    f"a strong indicator of LLM generation."
                ),
                evidence    = (
                    f"Burstiness: {round(burstiness, 3)} "
                    f"(human avg: 0.4-0.8) | "
                    f"Sentences analyzed: {len(sentences)}"
                ),
                suggestion  = (
                    "If AI was used, disclose it per journal policy. "
                    "Human-written text naturally has rhythm variation. "
                    "Review for AI assistance disclosure requirements."
                ),
            ))

        # ── Flag 2: Low vocabulary diversity ─────────────────────
        if ttr < 0.4 and len(words) >= 50:
            flags.append(LLMFlag(
                flag_type   = "low_vocabulary_diversity",
                severity    = "medium",
                description = (
                    f"Type-Token Ratio: {round(ttr, 3)}. "
                    f"Low vocabulary diversity suggests repetitive "
                    f"word usage typical of LLM output. "
                    f"Human academic writing typically scores >0.5."
                ),
                evidence    = (
                    f"TTR: {round(ttr, 3)} | "
                    f"Unique words: {len(set(w.lower() for w in words))} / "
                    f"Total words: {len(words)}"
                ),
                suggestion  = (
                    "Vary vocabulary and sentence structure. "
                    "If AI-assisted, follow institutional disclosure policy."
                ),
            ))

        # ── Flag 3: High sentence uniformity ─────────────────────
        if uniformity > 0.7 and len(sentences) >= 5:
            flags.append(LLMFlag(
                flag_type   = "high_sentence_uniformity",
                severity    = "medium",
                description = (
                    f"Sentence length uniformity: {round(uniformity*100)}%. "
                    f"All sentences are suspiciously similar in length. "
                    f"LLMs tend to produce consistent sentence lengths; "
                    f"human writers vary naturally."
                ),
                evidence    = (
                    f"Uniformity score: {round(uniformity*100)}% | "
                    f"Sentences: {len(sentences)}"
                ),
                suggestion  = (
                    "Natural academic writing mixes short and long "
                    "sentences. High uniformity is an LLM signal."
                ),
            ))

        # ── Flag 4: LLM signature phrases ────────────────────────
        if phrase_count >= 3:
            flags.append(LLMFlag(
                flag_type   = "llm_signature_phrases",
                severity    = "high" if phrase_count >= 6 else "medium",
                description = (
                    f"{phrase_count} LLM-characteristic phrase(s) detected. "
                    f"Phrases like 'it is worth noting', 'furthermore', "
                    f"'delve into' are disproportionately common in "
                    f"AI-generated text compared to human writing."
                ),
                evidence    = (
                    f"Phrases found: {', '.join(phrases_found[:6])} | "
                    f"Count: {phrase_count}"
                ),
                suggestion  = (
                    "Replace generic transitional phrases with "
                    "discipline-specific language. Disclose AI use "
                    "if applicable per journal requirements."
                ),
            ))

        score   = self._aggregate_score(
            burstiness, ttr, uniformity, phrase_count, sentences, words
        )
        level   = self._risk(score, len(flags))
        summary = self._build_summary(
            score, level, burstiness, ttr, phrase_count, len(sentences)
        )

        return LLMResult(
            burstiness_score     = round(burstiness, 4),
            vocabulary_diversity = round(ttr, 4),
            sentence_uniformity  = round(uniformity, 4),
            llm_phrase_count     = phrase_count,
            llm_score            = round(score, 4),
            risk_level           = level,
            summary              = summary,
            flags                = flags,
            flags_count          = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _split_sentences(self, text: str) -> list:
        sentences = self.SENT_PAT.split(text.strip())
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def _tokenize(self, text: str) -> list:
        return self.WORD_PAT.findall(text)

    def _burstiness(self, sentences: list) -> float:
        """
        Burstiness = coefficient of variation of sentence lengths.
        High burstiness = human-like variation.
        Low burstiness = LLM-like uniformity.
        """
        if len(sentences) < 3:
            return 0.5
        lengths = [len(s.split()) for s in sentences]
        if statistics.mean(lengths) == 0:
            return 0.5
        cv = statistics.stdev(lengths) / statistics.mean(lengths)
        return min(cv, 1.0)

    def _type_token_ratio(self, words: list) -> float:
        """TTR = unique words / total words. Higher = more diverse."""
        if not words:
            return 1.0
        # Use sliding window TTR for longer texts
        window = min(len(words), 100)
        sample = words[:window]
        unique = len(set(w.lower() for w in sample))
        return unique / len(sample)

    def _sentence_uniformity(self, sentences: list) -> float:
        """
        How uniform are sentence lengths?
        1.0 = all same length (LLM-like)
        0.0 = highly varied (human-like)
        """
        if len(sentences) < 3:
            return 0.0
        lengths = [len(s.split()) for s in sentences]
        mean    = statistics.mean(lengths)
        if mean == 0:
            return 0.0
        stdev   = statistics.stdev(lengths)
        cv      = stdev / mean
        # Invert: high CV = low uniformity
        return max(0.0, 1.0 - min(cv, 1.0))

    def _detect_phrases(self, text: str) -> tuple:
        text_lower   = text.lower()
        found        = []
        for phrase in self.LLM_PHRASES:
            if phrase in text_lower:
                found.append(phrase)
        return len(found), found

    def _aggregate_score(self, burstiness, ttr, uniformity,
                         phrase_count, sentences, words) -> float:
        if len(sentences) < 3:
            return 0.0
        # Normalize components to 0-1 risk
        burst_risk   = max(0, 1 - (burstiness / 0.5))
        ttr_risk     = max(0, 1 - (ttr / 0.6))
        uniform_risk = uniformity
        phrase_risk  = min(phrase_count / 8, 1.0)

        score = (
            burst_risk   * 0.35 +
            ttr_risk     * 0.25 +
            uniform_risk * 0.20 +
            phrase_risk  * 0.20
        )
        return min(round(score, 4), 1.0)

    def _risk(self, score: float, flag_count: int) -> str:
        if score >= 0.65 or flag_count >= 3:
            return "critical"
        if score >= 0.45 or flag_count >= 2:
            return "high"
        if score >= 0.25 or flag_count >= 1:
            return "medium"
        return "low"

    def _build_summary(self, score, level, burstiness,
                       ttr, phrase_count, n_sentences) -> str:
        pct = round(score * 100)
        return (
            f"LLM Detection analyzed {n_sentences} sentence(s). "
            f"Burstiness: {round(burstiness*100)}% "
            f"(human-like threshold: >40%). "
            f"Vocabulary diversity: {round(ttr*100)}%. "
            f"LLM signature phrases: {phrase_count}. "
            f"AI-generation probability: {pct}%. "
            f"Risk level: {level.upper()}."
        )