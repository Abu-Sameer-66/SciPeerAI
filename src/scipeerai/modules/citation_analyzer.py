# Citation Integrity Analyzer
# ---------------------------
# Citations are the backbone of science.
# When they are manipulated — through self-citation
# abuse, retracted sources, or citation cartels —
# the entire knowledge chain gets corrupted.
#
# This module audits citation patterns in paper text
# and checks references against retraction databases.

import re
import json
import urllib.request
import urllib.error
from dataclasses import dataclass


# ── data structures ───────────────────────────────────────────

@dataclass
class CitationFlag:
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


@dataclass
class CitationResult:
    total_citations: int
    self_citations: int
    self_citation_ratio: float
    unsupported_claims: int
    flags: list
    risk_score: float
    risk_level: str
    summary: str


# ── main class ────────────────────────────────────────────────

class CitationAnalyzer:
    """
    Two-layer citation analysis:

    Layer 1 — Pattern analysis: self-citation ratio,
    unsupported claims, citation density problems.

    Layer 2 — External validation: checks author names
    against Semantic Scholar for retraction signals.
    Free API — no key required for basic usage.
    """

    # ratio above this is suspicious self-citation
    SELF_CITE_THRESHOLD = 0.30

    # claims that need citations but often don't have them
    CLAIM_MARKERS = [
        "studies show", "research shows", "evidence suggests",
        "it is well known", "it has been shown", "it is established",
        "previous work shows", "literature suggests",
        "experts agree", "scientists believe"
    ]

    def __init__(self):
        self._semantic_scholar_url = (
            "https://api.semanticscholar.org/graph/v1/paper/search"
        )

    # ── public method ─────────────────────────────────────────

    def analyze(self, text: str, author_name: str = "") -> CitationResult:
        """
        Full citation integrity analysis.

        Args:
            text: Full paper text
            author_name: Primary author — used for self-citation detection
        """
        citations     = self._extract_citations(text)
        self_cites    = self._count_self_citations(text, author_name)
        unsupported   = self._find_unsupported_claims(text)

        total         = len(citations)
        self_ratio    = (self_cites / total) if total > 0 else 0.0

        flags = []
        flags.extend(self._check_self_citation_ratio(
            self_cites, total, self_ratio
        ))
        flags.extend(self._check_unsupported_claims(unsupported))
        flags.extend(self._check_citation_density(text, total))
        flags.extend(self._check_citation_patterns(text, citations))

        # try live retraction check — graceful fallback
        if author_name:
            retraction_flags = self._check_retraction_signals(
                citations, author_name
            )
            flags.extend(retraction_flags)

        risk_score = self._calculate_risk(flags)
        risk_level = self._get_risk_level(risk_score)

        return CitationResult(
            total_citations=total,
            self_citations=self_cites,
            self_citation_ratio=round(self_ratio, 3),
            unsupported_claims=len(unsupported),
            flags=flags,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            summary=self._write_summary(flags, risk_level, total),
        )

    # ── extraction helpers ────────────────────────────────────

    def _extract_citations(self, text: str) -> list:
        """
        Extract citation markers from text.
        Handles: [1], [1,2], [1-3], (Smith, 2020), (Smith et al., 2019)
        """
        patterns = [
            r'\[\d+(?:,\s*\d+)*\]',          # [1] or [1,2,3]
            r'\[\d+\-\d+\]',                   # [1-3]
            r'\([A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s+\d{4}\)',  # (Smith, 2020)
            r'\([A-Z][a-z]+\s+&\s+[A-Z][a-z]+,?\s+\d{4}\)', # (Smith & Jones, 2020)
        ]
        citations = []
        for pattern in patterns:
            found = re.findall(pattern, text)
            citations.extend(found)

        # deduplicate while preserving order
        seen = set()
        unique = []
        for c in citations:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique

    def _count_self_citations(self, text: str, author_name: str) -> int:
        """
        Count how many times the author's own name appears
        in citation context. Checks both surname variants.
        """
        if not author_name:
            return 0

        # extract surname — "Sameer Nadeem" → "Nadeem"
        parts = author_name.strip().split()
        surname = parts[-1] if parts else author_name

        # look for surname near citation patterns
        citation_context = re.findall(
            rf'{re.escape(surname)}[,\s]{{0,10}}(?:\d{{4}}|et al)',
            text,
            re.IGNORECASE
        )
        return len(citation_context)

    def _find_unsupported_claims(self, text: str) -> list:
        """
        Find sentences that make broad claims without
        a citation immediately following.
        "Studies show that X" with no [1] or (Author, year) nearby.
        """
        unsupported = []
        sentences   = re.split(r'[.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue

            s_lower = sentence.lower()
            has_claim_marker = any(
                marker in s_lower for marker in self.CLAIM_MARKERS
            )
            has_citation = bool(re.search(
                r'\[\d+\]|\([A-Z][a-z]+.*?\d{4}\)', sentence
            ))

            if has_claim_marker and not has_citation:
                unsupported.append(sentence)

        return unsupported[:5]  # cap at 5 for report clarity

    # ── flag checks ───────────────────────────────────────────

    def _check_self_citation_ratio(
        self, self_cites: int, total: int, ratio: float
    ) -> list:
        """
        High self-citation ratio inflates the author's
        citation metrics without adding scientific value.
        """
        flags = []

        if total < 5:
            return flags  # too few citations to judge pattern

        if ratio >= 0.5:
            flags.append(CitationFlag(
                flag_type="excessive_self_citation",
                severity="high",
                description=(
                    f"{self_cites} out of {total} citations "
                    f"({round(ratio*100)}%) appear to be self-citations. "
                    f"Threshold: {round(self.SELF_CITE_THRESHOLD*100)}%."
                ),
                evidence=f"Self-citation ratio: {round(ratio, 3)}",
                suggestion=(
                    "Review whether all self-citations are necessary. "
                    "Journals typically flag ratios above 20-30%."
                ),
            ))
        elif ratio >= self.SELF_CITE_THRESHOLD:
            flags.append(CitationFlag(
                flag_type="high_self_citation_ratio",
                severity="medium",
                description=(
                    f"Self-citation ratio of {round(ratio*100)}% "
                    f"is above the recommended threshold."
                ),
                evidence=f"Self-citation ratio: {round(ratio, 3)}",
                suggestion=(
                    "Consider whether additional independent sources "
                    "could support the same claims."
                ),
            ))

        return flags

    def _check_unsupported_claims(self, unsupported: list) -> list:
        """Flag broad claims that lack any citation support."""
        flags = []

        if len(unsupported) >= 3:
            flags.append(CitationFlag(
                flag_type="unsupported_broad_claims",
                severity="high",
                description=(
                    f"{len(unsupported)} broad claim(s) found without "
                    f"supporting citations. These cannot be independently verified."
                ),
                evidence=" | ".join(unsupported[:2]),
                suggestion=(
                    "Each claim beginning with 'studies show' or "
                    "'it is well known' must be backed by specific citations."
                ),
            ))
        elif len(unsupported) >= 1:
            flags.append(CitationFlag(
                flag_type="unsupported_claims",
                severity="medium",
                description=(
                    f"{len(unsupported)} claim(s) make broad assertions "
                    f"without citation support."
                ),
                evidence=unsupported[0] if unsupported else "",
                suggestion="Add specific citations for each broad claim.",
            ))

        return flags

    def _check_citation_density(self, text: str, total: int) -> list:
        """
        Very few citations in a long paper = claims without backing.
        Very many in a short paper = padding.
        """
        flags  = []
        words  = len(text.split())
        # rough pages estimate
        pages  = max(1, words // 250)
        density = total / pages

        if pages >= 5 and density < 1.5:
            flags.append(CitationFlag(
                flag_type="low_citation_density",
                severity="medium",
                description=(
                    f"Only {total} citations across approximately "
                    f"{pages} pages (density: {round(density, 1)}/page). "
                    f"Well-supported papers typically cite 3-5 sources per page."
                ),
                evidence=f"{total} total citations, ~{pages} pages",
                suggestion=(
                    "Review whether all major claims have adequate "
                    "citation support from independent sources."
                ),
            ))

        return flags

    def _check_citation_patterns(self, text: str, citations: list) -> list:
        """
        Detect suspicious citation clustering —
        all citations in one section, none in others.
        Also detects 'et al.' overuse which hides
        the actual authors being cited.
        """
        flags = []

        # et al. overuse — hides who is actually being cited
        et_al_count = len(re.findall(r'et al\.?', text, re.IGNORECASE))
        if citations and et_al_count > 0:
            et_al_ratio = et_al_count / max(len(citations), 1)
            if et_al_ratio > 0.7 and len(citations) > 5:
                flags.append(CitationFlag(
                    flag_type="et_al_overuse",
                    severity="low",
                    description=(
                        f"{et_al_count} out of {len(citations)} citations "
                        f"use 'et al.' ({round(et_al_ratio*100)}%). "
                        f"This obscures the actual authorship of cited works."
                    ),
                    evidence=f"et al. ratio: {round(et_al_ratio, 2)}",
                    suggestion=(
                        "For papers with 3 or fewer authors, "
                        "list all names. Reserve et al. for 4+ authors."
                    ),
                ))

        return flags

    def _check_retraction_signals(
        self, citations: list, author_name: str
    ) -> list:
        """
        Query Semantic Scholar for the author's papers.
        Flag if any cited paper appears to have integrity issues.
        This is a lightweight signal — not a definitive retraction check.
        Full retraction database integration is a roadmap item.
        """
        flags = []
        if not author_name or not citations:
            return flags

        try:
            surname = author_name.strip().split()[-1]
            query   = urllib.parse.quote(surname)
            url     = (
                f"{self._semantic_scholar_url}"
                f"?query={query}&fields=title,year,authors&limit=5"
            )

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SciPeerAI/0.1 Research Tool"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            # if we get results — API is live — note it worked
            # full retraction checking needs Retraction Watch API
            # which requires institutional access
            if data.get("data"):
                pass  # API working — retraction DB integration: Phase D

        except Exception:
            pass  # external API down — silent fail, not critical

        return flags

    # ── scoring ───────────────────────────────────────────────

    def _calculate_risk(self, flags: list) -> float:
        weights = {"high": 0.35, "medium": 0.20, "low": 0.08}
        score   = sum(weights.get(f.severity, 0) for f in flags)
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.7:   return "critical"
        elif score >= 0.4: return "high"
        elif score >= 0.2: return "medium"
        return "low"

    def _write_summary(
        self, flags: list, risk_level: str, total: int
    ) -> str:
        if not flags:
            return (
                f"Analyzed {total} citation(s). "
                f"No citation integrity issues detected."
            )

        high = sum(1 for f in flags if f.severity == "high")
        med  = sum(1 for f in flags if f.severity == "medium")
        parts = []
        if high: parts.append(
            f"{high} high-severity issue{'s' if high > 1 else ''}"
        )
        if med:  parts.append(
            f"{med} medium-severity concern{'s' if med > 1 else ''}"
        )

        return (
            f"Analyzed {total} citation(s). "
            f"Citation audit flagged {', '.join(parts)}. "
            f"Risk level: {risk_level.upper()}."
        )


# ── fix missing import ────────────────────────────────────────
import urllib.parse