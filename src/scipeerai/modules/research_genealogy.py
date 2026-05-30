# src/scipeerai/modules/research_genealogy.py
#
# Module 22: Research Genealogy Engine
# Traces citation ancestry, detects citation ring networks,
# measures lineage concentration, and checks for retracted ancestors
# via CrossRef API.
#
# Score attribute: genealogy_score (0.0 = clean, 1.0 = high risk)
# Part of SciPeerAI Phase 6 — v2.3.0

from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Optional

import requests


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class GenealogyFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class GenealogyResult:
    doi_count:               int
    unique_cited_authors:    int
    genealogy_concentration: float
    ring_detected:           bool
    ring_members:            list
    crossref_checked:        int
    retracted_ancestors:     int
    lineage_depth_score:     float
    genealogy_score:         float
    risk_level:              str
    summary:                 str
    flags:                   list
    flags_count:             int


# ── Compiled patterns ─────────────────────────────────────────────────────────

_DOI_RE = re.compile(
    r'\b(10\.\d{4,9}/[^\s\]\)\,\"\'<>\|]+)',
    re.IGNORECASE,
)

_AUTHOR_YEAR_RE = re.compile(
    r'\b([A-Z][a-zA-Z\-\']{2,})'
    r'(?:\s+et\s+al\.?)?'
    r'[,\s\(]+(?:19|20)(\d{2})[a-z]?\b',
)

_YEAR_RE = re.compile(r'\b((?:19|20)\d{2})\b')

_CROSSREF_BASE   = "https://api.crossref.org/works/"
_REQUEST_TIMEOUT = 3
_MAX_DOIS_TO_CHECK = 8


# ── Engine ────────────────────────────────────────────────────────────────────

class ResearchGenealogyEngine:
    """
    Research Genealogy Engine — Module 22.

    Analyses the citation structure of a paper to detect:
    - Tight citation rings (small author groups dominating references)
    - Concentrated lineage (top-heavy citation trees)
    - Retracted ancestor papers (via CrossRef API, optional)
    - Temporally shallow citation ancestry
    """

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "SciPeerAI/2.3.0 (mailto:sameerdataanalyst66@gmail.com)",
        })

    # ── Public interface ──────────────────────────────────────────────────────

    def analyze(self, text: str) -> GenealogyResult:
        text = (text or "").strip()
        if not text:
            return self._empty_result("No text provided for genealogy analysis.")

        dois           = self._extract_dois(text)
        author_net     = self._build_author_network(text)
        concentration  = self._compute_concentration(author_net)
        ring, ring_mbr = self._detect_ring(author_net)
        depth_score    = self._lineage_depth_score(text)
        retracted      = self._check_retractions(dois[:_MAX_DOIS_TO_CHECK])

        flags = self._build_flags(
            dois, author_net, concentration,
            ring, ring_mbr, retracted, depth_score,
        )

        genealogy_score = self._compute_score(
            concentration, ring, retracted, depth_score, len(dois),
        )

        risk_level = (
            "critical" if genealogy_score >= 0.75 else
            "high"     if genealogy_score >= 0.55 else
            "medium"   if genealogy_score >= 0.30 else
            "low"
        )

        summary = self._build_summary(
            len(dois), len(author_net), concentration,
            ring, ring_mbr, retracted, risk_level,
        )

        return GenealogyResult(
            doi_count               = len(dois),
            unique_cited_authors    = len(author_net),
            genealogy_concentration = round(concentration, 4),
            ring_detected           = ring,
            ring_members            = ring_mbr[:10],
            crossref_checked        = min(len(dois), _MAX_DOIS_TO_CHECK),
            retracted_ancestors     = retracted,
            lineage_depth_score     = round(depth_score, 4),
            genealogy_score         = round(genealogy_score, 4),
            risk_level              = risk_level,
            summary                 = summary,
            flags                   = flags,
            flags_count             = len(flags),
        )

    # ── Extraction ────────────────────────────────────────────────────────────

    def _extract_dois(self, text: str) -> list:
        raw  = _DOI_RE.findall(text)
        seen = set()
        out  = []
        for doi in raw:
            doi = doi.rstrip(".,;)")
            if doi not in seen:
                seen.add(doi)
                out.append(doi)
        return out

    def _build_author_network(self, text: str) -> dict:
        matches = _AUTHOR_YEAR_RE.findall(text)
        counter = Counter()
        for name, _ in matches:
            if len(name) >= 3:
                counter[name] += 1
        return dict(counter)

    # ── Analysis ──────────────────────────────────────────────────────────────

    def _compute_concentration(self, network: dict) -> float:
        if not network:
            return 0.0
        total = sum(network.values())
        if total == 0:
            return 0.0

        sorted_counts = sorted(network.values(), reverse=True)
        top3_share    = sum(sorted_counts[:3]) / total

        shares = [v / total for v in network.values()]
        hhi    = sum(s * s for s in shares)

        return round(min(1.0, top3_share * 0.55 + hhi * 0.45), 4)

    def _detect_ring(self, network: dict) -> tuple:
        if len(network) < 2:
            return False, []
        total = sum(network.values())
        if total < 5:
            return False, []

        sorted_authors = sorted(network.items(), key=lambda x: x[1], reverse=True)
        top_candidates = [(name, cnt) for name, cnt in sorted_authors[:6] if cnt >= 3]

        if not top_candidates:
            return False, []

        top_share = sum(cnt for _, cnt in top_candidates) / total
        if top_share >= 0.65 and len(top_candidates) >= 2:
            return True, [name for name, _ in top_candidates]
        return False, []

    def _lineage_depth_score(self, text: str) -> float:
        year_matches = _YEAR_RE.findall(text)
        years = [int(y) for y in year_matches if 1970 <= int(y) <= 2025]

        if len(years) < 3:
            return 0.1

        year_range   = max(years) - min(years)
        unique_years = len(set(years))
        total_years  = len(years)

        if year_range < 5:
            range_risk = 0.80
        elif year_range < 10:
            range_risk = 0.55
        elif year_range < 15:
            range_risk = 0.35
        elif year_range < 25:
            range_risk = 0.15
        else:
            range_risk = 0.05

        diversity_ratio   = unique_years / max(total_years, 1)
        diversity_penalty = max(0.0, (0.5 - diversity_ratio) * 0.3)

        return round(min(1.0, range_risk + diversity_penalty), 4)

    def _check_retractions(self, dois: list) -> int:
        retracted = 0
        for doi in dois:
            try:
                resp = self._session.get(
                    f"{_CROSSREF_BASE}{doi}",
                    timeout=_REQUEST_TIMEOUT,
                )
                if resp.status_code != 200:
                    continue
                data       = resp.json().get("message", {})
                paper_type = data.get("type", "").lower()
                titles     = " ".join(data.get("title", [])).lower()
                if "retract" in paper_type or "retract" in titles:
                    retracted += 1
            except Exception:
                pass
            time.sleep(0.08)
        return retracted

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        concentration: float,
        ring_detected: bool,
        retracted:     int,
        depth_score:   float,
        doi_count:     int,
    ) -> float:
        score  = 0.0
        score += concentration             * 0.35
        score += (0.38 if ring_detected else 0.0)
        score += min(retracted * 0.20,       0.40)
        score += depth_score               * 0.15
        if doi_count == 0:
            score += 0.04
        return round(min(1.0, score), 4)

    # ── Flags ─────────────────────────────────────────────────────────────────

    def _build_flags(
        self,
        dois:          list,
        network:       dict,
        concentration: float,
        ring:          bool,
        ring_mbr:      list,
        retracted:     int,
        depth_score:   float,
    ) -> list:
        flags = []

        if ring and ring_mbr:
            flags.append(GenealogyFlag(
                flag_type   = "citation_ring_detected",
                severity    = "critical",
                description = (
                    f"Citation ring detected: {len(ring_mbr)} authors "
                    f"collectively account for over 65% of all citations."
                ),
                evidence    = (
                    f"Dominant citation group: {', '.join(ring_mbr[:5])}. "
                    f"These authors appear repeatedly in a mutually-reinforcing pattern."
                ),
                suggestion  = (
                    "Diversify citations beyond this cluster. Incorporate independent "
                    "literature from unaffiliated research groups to strengthen credibility."
                ),
            ))

        if concentration >= 0.60 and not ring:
            top3 = sorted(network.items(), key=lambda x: x[1], reverse=True)[:3]
            flags.append(GenealogyFlag(
                flag_type   = "concentrated_lineage",
                severity    = "high",
                description = (
                    "Citation lineage is heavily concentrated — a small number of "
                    "authors dominate the reference list."
                ),
                evidence    = (
                    f"Top 3 cited groups: {', '.join(n for n, _ in top3)}. "
                    f"Concentration index: {concentration:.2f} (threshold: 0.60)."
                ),
                suggestion  = (
                    "Broaden the citation scope to include diverse research groups, "
                    "institutions, and geographic regions."
                ),
            ))

        if retracted > 0:
            flags.append(GenealogyFlag(
                flag_type   = "retracted_ancestor",
                severity    = "critical",
                description = (
                    f"{retracted} retracted paper(s) found among cited DOIs "
                    f"via CrossRef live verification."
                ),
                evidence    = (
                    f"CrossRef DOI check identified {retracted} retraction(s) "
                    f"among {min(len(dois), _MAX_DOIS_TO_CHECK)} DOIs examined."
                ),
                suggestion  = (
                    "Replace or remove citations to retracted papers immediately. "
                    "Building on retracted work critically undermines scientific validity."
                ),
            ))

        if depth_score >= 0.65:
            flags.append(GenealogyFlag(
                flag_type   = "shallow_citation_ancestry",
                severity    = "medium",
                description = (
                    "Citation ancestry is temporally shallow — most references "
                    "cluster within a narrow time window, indicating incomplete "
                    "literature coverage."
                ),
                evidence    = (
                    f"Year-span diversity analysis returned depth risk score of "
                    f"{depth_score:.2f} (threshold: 0.65)."
                ),
                suggestion  = (
                    "Include foundational papers (10+ years old) alongside recent work. "
                    "A healthy genealogy spans multiple decades of scholarship."
                ),
            ))

        if len(dois) == 0 and len(network) >= 4:
            flags.append(GenealogyFlag(
                flag_type   = "no_dois_present",
                severity    = "low",
                description = (
                    "No machine-readable DOIs found despite multiple "
                    "citation references in the text."
                ),
                evidence    = (
                    f"Text contains {len(network)} cited author mentions "
                    f"but zero extractable DOIs for provenance verification."
                ),
                suggestion  = (
                    "Include DOIs for all references to enable automated "
                    "retraction checking and genealogy tracing."
                ),
            ))

        if not network:
            flags.append(GenealogyFlag(
                flag_type   = "no_citations_detected",
                severity    = "low",
                description = "No citation references detected in the submitted text.",
                evidence    = "Author-year pattern extraction returned zero citation matches.",
                suggestion  = (
                    "Ensure the full paper text including the references section "
                    "is submitted for complete genealogy analysis."
                ),
            ))

        return flags

    # ── Summary ───────────────────────────────────────────────────────────────

    def _build_summary(
        self,
        doi_count:     int,
        author_count:  int,
        concentration: float,
        ring:          bool,
        ring_mbr:      list,
        retracted:     int,
        risk_level:    str,
    ) -> str:
        parts = [
            f"Research genealogy analysis complete: {doi_count} DOIs extracted, "
            f"{author_count} unique cited author groups identified.",
            f"Lineage concentration index: {concentration:.2f}.",
        ]
        if ring:
            parts.append(
                f"Citation ring detected among {len(ring_mbr)} authors "
                f"({', '.join(ring_mbr[:3])})."
            )
        if retracted > 0:
            parts.append(
                f"{retracted} retracted ancestor(s) identified via CrossRef."
            )
        parts.append(f"Overall genealogy risk: {risk_level.upper()}.")
        return " ".join(parts)

    # ── Fallback ──────────────────────────────────────────────────────────────

    def _empty_result(self, msg: str) -> GenealogyResult:
        return GenealogyResult(
            doi_count               = 0,
            unique_cited_authors    = 0,
            genealogy_concentration = 0.0,
            ring_detected           = False,
            ring_members            = [],
            crossref_checked        = 0,
            retracted_ancestors     = 0,
            lineage_depth_score     = 0.0,
            genealogy_score         = 0.0,
            risk_level              = "low",
            summary                 = msg,
            flags                   = [],
            flags_count             = 0,
        )