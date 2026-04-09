# src/scipeerai/modules/novelty_scorer.py
#
# Novelty Scorer
# --------------
# Science advances through genuinely new contributions.
# But with 4 million papers published per year, it is
# increasingly difficult to know if a contribution is
# truly novel or an incremental rehash of existing work.
#
# This module estimates novelty by:
# 1. Extracting key claims from the paper
# 2. Searching existing literature via Semantic Scholar
# 3. Analyzing title/abstract overlap patterns
# 4. Scoring novelty from 0.0 (not novel) to 1.0 (highly novel)

import re
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from dataclasses import dataclass


# ── data structures ───────────────────────────────────────────

@dataclass
class NoveltyFlag:
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


@dataclass
class RelatedWork:
    title: str
    year: int
    authors: list
    similarity_signal: str


@dataclass
class NoveltyResult:
    novelty_score: float          # 0.0 = not novel, 1.0 = highly novel
    novelty_level: str            # "low" / "moderate" / "high" / "very_high"
    related_works_found: list
    key_terms_extracted: list
    flags: list
    literature_accessible: bool   # was Semantic Scholar reachable?
    risk_level: str
    summary: str


# ── main class ────────────────────────────────────────────────

class NoveltyScorer:
    """
    Estimates paper novelty using two approaches:

    Approach 1 — Structural novelty signals (offline):
    Looks for language patterns that indicate genuine
    novelty vs incremental work. Fast, always available.

    Approach 2 — Literature search (online):
    Uses Semantic Scholar free API to find related papers.
    Graceful fallback if API unavailable.

    Final score combines both approaches.
    """

    # phrases that signal genuine novelty
    NOVELTY_SIGNALS = [
        "first study to", "first paper to", "novel approach",
        "we propose a new", "we introduce", "we present a new",
        "previously unexplored", "to our knowledge",
        "no prior work", "first time", "new framework",
        "new method", "we develop a novel", "first investigation",
        "pioneer", "groundbreaking", "unprecedented",
    ]

    # phrases that signal incremental / derivative work
    INCREMENTAL_SIGNALS = [
        "extending previous work", "building on",
        "similar to previous", "following the approach of",
        "replicating", "consistent with prior",
        "confirming previous findings", "in line with",
        "as shown previously", "extending the work of",
        "we replicate", "corroborating",
    ]

    # domain keywords for better search queries
    DOMAIN_KEYWORDS = [
        "machine learning", "deep learning", "neural network",
        "transformer", "language model", "computer vision",
        "natural language processing", "reinforcement learning",
        "clinical trial", "randomized controlled",
        "meta-analysis", "systematic review",
        "molecular", "genomics", "proteomics",
        "quantum", "photonic", "nanomaterial",
    ]

    def __init__(self):
        self._api_base = (
            "https://api.semanticscholar.org/graph/v1/paper/search"
        )

    # ── public method ─────────────────────────────────────────

    def analyze(self, text: str, title: str = "") -> NoveltyResult:
        """
        Full novelty analysis.
        Combines structural signals with optional literature search.
        """
        key_terms   = self._extract_key_terms(text, title)
        struct_score = self._structural_novelty_score(text)

        # try live literature search
        related_works = []
        api_ok        = False

        if key_terms:
            related_works, api_ok = self._search_literature(
                key_terms, title
            )

        # combine scores
        if api_ok and related_works:
            # literature found — factor in search results
            overlap_penalty = min(len(related_works) * 0.08, 0.4)
            final_score = max(struct_score - overlap_penalty, 0.1)
        else:
            # no API or no results — use structural only
            final_score = struct_score

        final_score   = round(final_score, 3)
        novelty_level = self._get_novelty_level(final_score)
        risk_level    = self._get_risk_level(final_score)

        flags = []
        flags.extend(self._check_novelty_flags(text, final_score))
        flags.extend(self._check_incremental_language(text))

        return NoveltyResult(
            novelty_score=final_score,
            novelty_level=novelty_level,
            related_works_found=related_works,
            key_terms_extracted=key_terms,
            flags=flags,
            literature_accessible=api_ok,
            risk_level=risk_level,
            summary=self._write_summary(
                final_score, novelty_level,
                related_works, api_ok, flags
            ),
        )

    # ── term extraction ───────────────────────────────────────

    def _extract_key_terms(self, text: str, title: str) -> list:
        """
        Extract the most meaningful terms for literature search.
        Priority: title terms > domain keywords > noun phrases.
        """
        terms = []

        # title words are most informative
        if title:
            words = re.findall(r'\b[A-Z][a-z]{3,}\b', title)
            terms.extend(words[:5])

        # domain keywords present in text
        t_lower = text.lower()
        for kw in self.DOMAIN_KEYWORDS:
            if kw in t_lower:
                terms.append(kw)
                if len(terms) >= 6:
                    break

        # fallback: capitalized noun phrases from text
        if len(terms) < 3:
            caps = re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)
            terms.extend(caps[:3])

        # deduplicate
        seen = set()
        unique = []
        for t in terms:
            if t.lower() not in seen:
                seen.add(t.lower())
                unique.append(t)

        return unique[:6]

    # ── structural scoring ────────────────────────────────────

    def _structural_novelty_score(self, text: str) -> float:
        """
        Score novelty from language patterns alone.
        Novelty signals push score up, incremental signals push down.
        Base score: 0.5 (neutral — unknown)
        """
        t_lower = text.lower()

        novelty_count = sum(
            1 for s in self.NOVELTY_SIGNALS if s in t_lower
        )
        incremental_count = sum(
            1 for s in self.INCREMENTAL_SIGNALS if s in t_lower
        )

        score = 0.50
        score += novelty_count     * 0.08   # each novelty signal +8%
        score -= incremental_count * 0.06   # each incremental signal -6%

        return round(min(max(score, 0.05), 0.95), 3)

    # ── literature search ─────────────────────────────────────

    def _search_literature(
        self, key_terms: list, title: str
    ) -> tuple:
        """
        Search Semantic Scholar for related papers.
        Returns (list of RelatedWork, success_bool).
        Free API — no key required for basic search.
        """
        query_parts = key_terms[:3]
        if title:
            # use first 5 words of title for precision
            title_words = title.split()[:5]
            query_parts = title_words + query_parts[:2]

        query = " ".join(query_parts)
        encoded = urllib.parse.quote(query)
        url = (
            f"{self._api_base}"
            f"?query={encoded}"
            f"&fields=title,year,authors"
            f"&limit=5"
        )

        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "SciPeerAI/0.1 (academic integrity tool)"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())

            papers = data.get("data", [])
            related = []

            for p in papers:
                if not p.get("title"):
                    continue
                authors = [
                    a.get("name", "")
                    for a in p.get("authors", [])[:3]
                ]
                # rough similarity — shared words between
                # search query and result title
                result_words = set(
                    p["title"].lower().split()
                )
                query_words  = set(query.lower().split())
                overlap = len(result_words & query_words)
                signal  = (
                    "high overlap" if overlap > 4
                    else "moderate overlap" if overlap > 2
                    else "low overlap"
                )

                related.append(RelatedWork(
                    title=p["title"],
                    year=p.get("year", 0),
                    authors=authors,
                    similarity_signal=signal,
                ))

            return related, True

        except Exception:
            # API unreachable — silent fallback
            return [], False

    # ── flag checks ───────────────────────────────────────────

    def _check_novelty_flags(
        self, text: str, score: float
    ) -> list:
        """Flag papers with suspiciously low novelty scores."""
        flags = []

        if score < 0.25:
            flags.append(NoveltyFlag(
                flag_type="low_novelty_score",
                severity="high",
                description=(
                    f"Novelty score of {round(score*100)}% suggests "
                    f"this work may be insufficiently differentiated "
                    f"from existing literature."
                ),
                evidence=f"Novelty score: {score}",
                suggestion=(
                    "Clearly articulate what is new in this work. "
                    "Add a dedicated section comparing to the most "
                    "closely related prior work."
                ),
            ))
        elif score < 0.45:
            flags.append(NoveltyFlag(
                flag_type="moderate_novelty_concern",
                severity="medium",
                description=(
                    f"Novelty score of {round(score*100)}% is moderate. "
                    f"The contribution may be incremental."
                ),
                evidence=f"Novelty score: {score}",
                suggestion=(
                    "Strengthen the novelty argument. Be specific about "
                    "what prior work did NOT do that this paper does."
                ),
            ))

        return flags

    def _check_incremental_language(self, text: str) -> list:
        """Flag papers that heavily signal incremental work."""
        flags = []
        t_lower = text.lower()

        found = [s for s in self.INCREMENTAL_SIGNALS if s in t_lower]

        if len(found) >= 3:
            flags.append(NoveltyFlag(
                flag_type="incremental_language_detected",
                severity="medium",
                description=(
                    f"Paper uses multiple phrases suggesting incremental "
                    f"rather than novel contribution: {found[:3]}"
                ),
                evidence=str(found[:3]),
                suggestion=(
                    "This is not inherently a problem — incremental work "
                    "is valuable. But if claiming novelty, revise language "
                    "to clearly articulate what is genuinely new."
                ),
            ))

        return flags

    # ── scoring ───────────────────────────────────────────────

    def _get_novelty_level(self, score: float) -> str:
        if score >= 0.75: return "very_high"
        elif score >= 0.55: return "high"
        elif score >= 0.35: return "moderate"
        return "low"

    def _get_risk_level(self, novelty_score: float) -> str:
        # low novelty = high risk of rejection / plagiarism concern
        if novelty_score < 0.25:   return "critical"
        elif novelty_score < 0.40: return "high"
        elif novelty_score < 0.60: return "medium"
        return "low"

    def _write_summary(
        self, score: float, level: str,
        related: list, api_ok: bool, flags: list
    ) -> str:
        pct = round(score * 100)
        base = f"Novelty score: {pct}% ({level.replace('_', ' ')})."

        if api_ok and related:
            base += f" {len(related)} related work(s) found in literature."
        elif not api_ok:
            base += " Literature search unavailable — score based on structural analysis only."

        if not flags:
            base += " No novelty concerns detected."
        else:
            high = sum(1 for f in flags if f.severity == "high")
            if high:
                base += f" {high} novelty concern(s) flagged."

        return base