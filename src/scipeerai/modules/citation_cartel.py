# src/scipeerai/modules/citation_cartel.py
#
# Citation Cartel Detector
# Detects suspicious citation network patterns:
# - Authors citing only each other (cartels)
# - Excessive self-citation clusters
# - Citation ring patterns
# - Suspiciously narrow citation networks
#
# Based on network analysis techniques used in
# Nature/Science level integrity research.
# Nobody implements this freely.

import re
import math
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class CartelFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class CartelResult:
    authors_found:        list
    citation_network:     dict
    cartel_score:         float
    self_citation_ratio:  float
    network_diversity:    float
    risk_level:           str
    summary:              str
    flags:                list = field(default_factory=list)
    flags_count:          int  = 0


class CitationCartelDetector:
    """
    Citation Cartel Detector.
    Analyzes citation patterns to detect cartels —
    groups of authors who exclusively cite each other
    to artificially inflate impact metrics.

    Key signals:
    - High ratio of citations to same small group
    - Same author names appearing repeatedly
    - Narrow institutional citation network
    - Reciprocal citation patterns
    """

    # Author name patterns in references
    AUTHOR_PAT = re.compile(
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]*\.?)+)',
    )
    
    CITE_PAT = re.compile(
        r'([A-Z][a-z]+(?:\s+et\s+al\.?)?)\s*[\(\[,]?\s*(\d{4})[\)\]]',
        re.IGNORECASE
    )
    

    # Et al pattern
    ETAL_PAT = re.compile(
        r'([A-Z][a-z]+)\s+et\s+al\.?\s*[\(\[,]?\s*(\d{4})',
        re.IGNORECASE
    )

    # Reference section markers
    REF_MARKERS = re.compile(
        r'\b(?:references|bibliography|works\s+cited)\b',
        re.IGNORECASE
    )

    def analyze(self, text: str) -> CartelResult:
        citations    = self._extract_citations(text)
        authors      = self._extract_authors(citations)
        network      = self._build_network(citations)
        flags        = []

        # ── Analysis ──────────────────────────────────────────────
        self_cite_ratio  = self._self_citation_ratio(citations, text)
        diversity        = self._network_diversity(network, citations)
        concentration    = self._concentration_score(network, citations)
        reciprocal       = self._detect_reciprocal(network)

        # ── Flag 1: High concentration ────────────────────────────
        if concentration > 0.5 and len(citations) >= 5:
            top_author = max(network, key=lambda a: network[a],
                           default=None)
            top_count  = network.get(top_author, 0)
            flags.append(CartelFlag(
                flag_type   = "citation_concentration",
                severity    = "high" if concentration > 0.7 else "medium",
                description = (
                    f"Citation network is highly concentrated — "
                    f"{round(concentration*100)}% of citations point "
                    f"to a small group of authors. This pattern "
                    f"suggests a citation cartel or echo chamber "
                    f"rather than broad scholarly engagement."
                ),
                evidence    = (
                    f"Top cited author: '{top_author}' "
                    f"({top_count} citations) | "
                    f"Concentration score: {round(concentration*100)}% | "
                    f"Total citations analyzed: {len(citations)}"
                ),
                suggestion  = (
                    "Broaden citation network to include diverse "
                    "sources. Avoid citing only colleagues or "
                    "institutional partners. Aim for <30% citations "
                    "from any single research group."
                ),
            ))

        # ── Flag 2: Low network diversity ─────────────────────────
        if diversity < 0.3 and len(citations) >= 8:
            flags.append(CartelFlag(
                flag_type   = "low_citation_diversity",
                severity    = "medium",
                description = (
                    f"Citation network diversity score: "
                    f"{round(diversity*100)}%. "
                    f"Paper draws from a very narrow pool of authors. "
                    f"Genuine scholarship typically cites a broad "
                    f"range of researchers across institutions."
                ),
                evidence    = (
                    f"Unique authors cited: {len(network)} | "
                    f"Total citations: {len(citations)} | "
                    f"Diversity score: {round(diversity*100)}%"
                ),
                suggestion  = (
                    "Include citations from diverse research groups, "
                    "institutions, and geographic regions. "
                    "Review recent literature more broadly."
                ),
            ))

        # ── Flag 3: Excessive self-citation ───────────────────────
        if self_cite_ratio > 0.3 and len(citations) >= 5:
            flags.append(CartelFlag(
                flag_type   = "excessive_self_citation",
                severity    = "high" if self_cite_ratio > 0.5 else "medium",
                description = (
                    f"Self-citation ratio: {round(self_cite_ratio*100)}%. "
                    f"Paper cites the same author(s) excessively — "
                    f"threshold for concern is >30%. This inflates "
                    f"citation metrics artificially."
                ),
                evidence    = (
                    f"Self-citation rate: {round(self_cite_ratio*100)}% "
                    f"(acceptable: <20%) | "
                    f"Citations analyzed: {len(citations)}"
                ),
                suggestion  = (
                    "Limit self-citations to genuinely necessary "
                    "references. Most journals recommend <20% "
                    "self-citation rate."
                ),
            ))

        # ── Flag 4: Reciprocal citation pattern ───────────────────
        if reciprocal:
            flags.append(CartelFlag(
                flag_type   = "reciprocal_citation_pattern",
                severity    = "medium",
                description = (
                    f"Potential reciprocal citation pattern detected. "
                    f"Authors: {', '.join(reciprocal[:3])} appear "
                    f"multiple times in concentrated citation clusters. "
                    f"This may indicate coordinated citation exchange."
                ),
                evidence    = (
                    f"Repeated author clusters: "
                    f"{', '.join(reciprocal[:5])}"
                ),
                suggestion  = (
                    "Ensure citations reflect genuine intellectual "
                    "debt rather than reciprocal agreements. "
                    "Disclose any collaborative relationships."
                ),
            ))

        # ── Flag 5: Too few citations ──────────────────────────────
        if len(citations) < 5:
            flags.append(CartelFlag(
                flag_type   = "insufficient_citations",
                severity    = "low",
                description = (
                    f"Only {len(citations)} citation(s) detected. "
                    f"Citation cartel analysis requires at least "
                    f"5 citations. Paste full references section "
                    f"for complete network analysis."
                ),
                evidence    = f"{len(citations)} citations found",
                suggestion  = (
                    "Include full references section for "
                    "complete citation network analysis."
                ),
            ))

        score   = self._aggregate_score(
            concentration, diversity, self_cite_ratio, citations
        )
        level   = self._risk(score, len(flags))
        summary = self._build_summary(
            citations, network, score, level,
            concentration, diversity
        )

        return CartelResult(
            authors_found       = list(network.keys())[:10],
            citation_network    = dict(network),
            cartel_score        = round(score, 4),
            self_citation_ratio = round(self_cite_ratio, 4),
            network_diversity   = round(diversity, 4),
            risk_level          = level,
            summary             = summary,
            flags               = flags,
            flags_count         = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _extract_citations(self, text: str) -> list:
        citations = []
        for m in self.CITE_PAT.finditer(text):
            citations.append((m.group(1).strip(), m.group(2)))
        for m in self.ETAL_PAT.finditer(text):
            citations.append((m.group(1).strip(), m.group(2)))
        return citations

    def _extract_authors(self, citations: list) -> list:
        return list(set(c[0] for c in citations))

    def _build_network(self, citations: list) -> dict:
        network = defaultdict(int)
        for author, _ in citations:
            network[author] += 1
        return dict(network)

    def _self_citation_ratio(self, citations: list,
                             text: str) -> float:
        if not citations:
            return 0.0
        # Find most frequent author
        network = self._build_network(citations)
        if not network:
            return 0.0
        top_count = max(network.values())
        return min(top_count / len(citations), 1.0)

    def _network_diversity(self, network: dict,
                           citations: list) -> float:
        if not citations:
            return 1.0
        unique_authors = len(network)
        total_cites    = len(citations)
        if total_cites == 0:
            return 1.0
        # Shannon entropy normalized
        entropy = 0.0
        for count in network.values():
            p = count / total_cites
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(max(unique_authors, 1))
        return (entropy / max_entropy) if max_entropy > 0 else 1.0

    def _concentration_score(self, network: dict,
                             citations: list) -> float:
        if not citations or not network:
            return 0.0
        total = len(citations)
        # Top 3 authors' share
        top3  = sorted(network.values(), reverse=True)[:3]
        return sum(top3) / total

    def _detect_reciprocal(self, network: dict) -> list:
        if not network:
            return []
        avg = sum(network.values()) / len(network)
        return [a for a, c in network.items() if c >= avg * 2]

    def _aggregate_score(self, concentration: float,
                         diversity: float,
                         self_cite: float,
                         citations: list) -> float:
        if len(citations) < 3:
            return 0.0
        score = (
            concentration * 0.4 +
            (1 - diversity) * 0.3 +
            self_cite * 0.3
        )
        return min(round(score, 4), 1.0)

    def _risk(self, score: float, flag_count: int) -> str:
        if score >= 0.6 or flag_count >= 3:
            return "critical"
        if score >= 0.4 or flag_count >= 2:
            return "high"
        if score >= 0.2 or flag_count >= 1:
            return "medium"
        return "low"

    def _build_summary(self, citations, network, score,
                       level, concentration, diversity) -> str:
        if len(citations) < 3:
            return (
                "Citation Cartel Analysis: Insufficient citations "
                "detected. Paste full references section for "
                "network analysis. Risk level: LOW."
            )
        pct = round(score * 100)
        return (
            f"Citation network analyzed: {len(citations)} citations, "
            f"{len(network)} unique authors. "
            f"Concentration: {round(concentration*100)}%, "
            f"Diversity: {round(diversity*100)}%. "
            f"Cartel risk score: {pct}%. "
            f"Risk level: {level.upper()}."
        )