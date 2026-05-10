# Temporal Anomaly Detection
# --------------------------
# Science has a timeline. Every discovery builds on what came before.
# A paper submitted in March 2022 cannot cite a paper published
# in September 2022. A dataset collected in 2019 cannot reference
# findings published in 2021 as the basis for its design.
#
# These are not typos. These are fabrication signals.
#
# This module reconstructs the timeline of a paper —
# when data was collected, when the study was designed,
# when it was written — and checks whether the citations
# respect that timeline.
#
# It also catches subtler anomalies:
# papers that claim recency but cite only old literature,
# studies that report emerging findings from a decade ago,
# and impossible sequences in the research narrative.

import re
from dataclasses import dataclass
from datetime import datetime


# ── constants ──────────────────────────────────────────────────────────────────

CURRENT_YEAR = datetime.now().year

COLLECTION_MARKERS = [
    r'data (?:were |was )?collected (?:in |during |between )?(\w+ \d{4}|\d{4})',
    r'study (?:was )?conducted (?:in |during )?(\w+ \d{4}|\d{4})',
    r'between (\w+ \d{4}) and (\w+ \d{4})',
    r'from (\w+ \d{4}) to (\w+ \d{4})',
    r'during (\d{4})[–\-](\d{4})',
    r'participants (?:were )?recruited (?:in |during )?(\w+ \d{4}|\d{4})',
    r'experiment(?:s)? (?:were |was )?run (?:in |during )?(\d{4})',
    r'survey(?:s)? (?:were |was )?administered (?:in |during )?(\d{4})',
]

RECENCY_MARKERS = [
    "recent studies", "recent research", "recent work",
    "recently published", "emerging evidence", "growing body of evidence",
    "latest findings", "current evidence", "new research",
    "newly developed", "state of the art", "cutting edge",
]

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "oct": 10, "nov": 11, "dec": 12,
}


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class TemporalFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class TemporalResult:
    collection_years:     list
    cited_years:          list
    future_citations:     list
    recency_claim_score:  float
    timeline_score:       float
    temporal_score:       float
    risk_level:           str
    summary:              str
    flags:                list
    flags_count:          int


# ── main class ────────────────────────────────────────────────────────────────

class TemporalAnomalyDetector:
    """
    Reconstructs the implied timeline of a paper and checks it
    for internal contradictions.

    Three checks:
    1. Citation time paradox — cited papers newer than data collection
    2. False recency — claims recent but cites old literature only
    3. Impossible year references — citations beyond current year
    """

    def analyze(self, text: str) -> TemporalResult:
        collection_years = self._extract_collection_years(text)
        cited_years      = self._extract_cited_years(text)
        flags            = []

        future_citations = self._check_citation_paradox(
            text, collection_years, cited_years, flags
        )
        recency_score    = self._check_false_recency(text, cited_years, flags)
        timeline_score   = self._check_impossible_years(cited_years, flags)

        temporal_score   = self._compute_score(
            future_citations, recency_score, timeline_score, cited_years
        )
        risk_level       = self._get_risk_level(temporal_score)

        return TemporalResult(
            collection_years    = collection_years,
            cited_years         = cited_years,
            future_citations    = future_citations,
            recency_claim_score = round(recency_score,  3),
            timeline_score      = round(timeline_score, 3),
            temporal_score      = round(temporal_score, 3),
            risk_level          = risk_level,
            summary             = self._write_summary(flags, risk_level, cited_years),
            flags               = flags,
            flags_count         = len(flags),
        )

    # ── extraction ─────────────────────────────────────────────────────────────

    def _extract_collection_years(self, text: str) -> list:
        """
        Pull every year mentioned in the context of data collection.
        These define the earliest possible citation boundary.
        """
        years   = []
        text_lo = text.lower()

        for pattern in COLLECTION_MARKERS:
            for match in re.finditer(pattern, text_lo):
                for group in match.groups():
                    if not group:
                        continue
                    year = self._parse_year_safe(group)
                    if year:
                        years.append(year)

        return sorted(set(years))

    def _extract_cited_years(self, text: str) -> list:
        """
        Pull publication years from inline citations.
        Handles Smith (2018) and (Smith, 2018) styles.
        Any 4-digit year between 1900-2300 is captured —
        future years are kept because they are the anomalies.
        """
        years = []

        # style 1 — name outside brackets: Smith (2018), Jones et al. (2020)
        for match in re.finditer(
            r'[A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?\s+\((\d{4})\)',
            text
        ):
            year = self._to_int_year(match.group(1))
            if year:
                years.append(year)

        # style 2 — name inside brackets: (Smith, 2018), (Jones et al., 2020)
        for match in re.finditer(
            r'\([A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?,?\s*(\d{4})\)',
            text
        ):
            year = self._to_int_year(match.group(1))
            if year:
                years.append(year)

        # style 3 — bare years in reference list section
        ref_section = self._extract_references(text)
        if ref_section:
            for match in re.finditer(r'\b(\d{4})\b', ref_section):
                year = self._to_int_year(match.group(1))
                if year:
                    years.append(year)

        return sorted(set(years))

    def _to_int_year(self, raw: str) -> int:
        """
        Convert a raw 4-digit string to int.
        Accepts any year from 1900 onward — no upper cap,
        so future-year fabrications are preserved for flagging.
        """
        try:
            year = int(raw.strip())
            if year >= 1900:
                return year
        except (ValueError, AttributeError):
            pass
        return 0

    def _extract_references(self, text: str) -> str:
        text_lo = text.lower()
        for marker in ["references", "bibliography", "works cited"]:
            idx = text_lo.rfind(marker)
            if idx != -1:
                return text[idx:]
        return ""

    def _parse_year_safe(self, raw: str) -> int:
        """
        Parse a year from strings like '2022', 'March 2022'.
        Used for collection year extraction — stays within valid range.
        """
        if not raw:
            return 0
        raw = raw.strip().lower()
        for month in MONTH_MAP:
            raw = raw.replace(month, "").strip()
        match = re.search(r'\b(\d{4})\b', raw)
        if match:
            year = int(match.group(1))
            if 1900 <= year <= CURRENT_YEAR + 2:
                return year
        return 0

    # ── checks ─────────────────────────────────────────────────────────────────

    def _check_citation_paradox(
        self,
        text: str,
        collection_years: list,
        cited_years: list,
        flags: list,
    ) -> list:
        """
        If data was collected in year X, no citation from year > X
        should be presented as the theoretical basis for study design.
        """
        if not collection_years or not cited_years:
            return []

        earliest_collection = min(collection_years)
        future_refs = [
            y for y in cited_years
            if y > earliest_collection + 1
        ]

        if len(future_refs) >= 3:
            flags.append(TemporalFlag(
                flag_type   = "citation_time_paradox",
                severity    = "high",
                description = (
                    f"Data collection appears to predate several cited references. "
                    f"If data was collected around {earliest_collection}, "
                    f"then {len(future_refs)} citation(s) from later years "
                    f"could not have informed the study design."
                ),
                evidence    = (
                    f"Earliest data collection: {earliest_collection}. "
                    f"Later citations: "
                    f"{sorted(future_refs)[:5]}"
                    f"{'...' if len(future_refs) > 5 else ''}."
                ),
                suggestion  = (
                    "Verify that citations used to justify study design "
                    "predate data collection. Post-hoc additions are a "
                    "known manipulation pattern."
                ),
            ))

        return future_refs

    def _check_false_recency(
        self,
        text: str,
        cited_years: list,
        flags: list,
    ) -> float:
        """
        Papers claiming recent evidence but citing only old literature
        are either unaware of the field or deliberately misleading.
        """
        text_lo = text.lower()
        recency_claims = sum(
            1 for marker in RECENCY_MARKERS if marker in text_lo
        )

        if recency_claims == 0 or not cited_years:
            return 0.0

        valid_years = [y for y in cited_years if y <= CURRENT_YEAR]
        if not valid_years:
            return 0.0

        max_cited = max(valid_years)
        years_old = CURRENT_YEAR - max_cited

        if recency_claims >= 2 and years_old >= 5:
            flags.append(TemporalFlag(
                flag_type   = "false_recency_claim",
                severity    = "medium",
                description = (
                    f"The paper uses {recency_claims} recency phrase(s) "
                    f"but the most recent citation is from {max_cited} — "
                    f"{years_old} years ago."
                ),
                evidence    = (
                    f"Most recent citation: {max_cited}. "
                    f"Recency claims: {recency_claims}. "
                    f"Gap: {years_old} years."
                ),
                suggestion  = (
                    "Update literature review with citations from the "
                    "last 2-3 years, or remove recency language."
                ),
            ))
            return min(years_old / 10.0, 1.0)

        return 0.0

    def _check_impossible_years(
        self,
        cited_years: list,
        flags: list,
    ) -> float:
        """
        Citations with years beyond current year are impossible.
        """
        if not cited_years:
            return 0.0

        future  = [y for y in cited_years if y > CURRENT_YEAR]
        ancient = [y for y in cited_years if y < 1950]
        score   = 0.0

        if future:
            flags.append(TemporalFlag(
                flag_type   = "future_year_citation",
                severity    = "high",
                description = (
                    f"Citations reference years beyond {CURRENT_YEAR}. "
                    f"This indicates data entry error or fabricated references."
                ),
                evidence    = f"Future years in citations: {future}.",
                suggestion  = (
                    "Verify all citation years against original sources."
                ),
            ))
            score = max(score, 0.8)

        if len(ancient) > 2:
            flags.append(TemporalFlag(
                flag_type   = "excessive_ancient_citations",
                severity    = "low",
                description = (
                    f"{len(ancient)} citation(s) from before 1950 detected."
                ),
                evidence    = f"Pre-1950 years: {sorted(ancient)}.",
                suggestion  = (
                    "Confirm foundational citations are intentional."
                ),
            ))
            score = max(score, 0.2)

        return score

    # ── scoring ────────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        future_citations: list,
        recency_score: float,
        timeline_score: float,
        cited_years: list,
    ) -> float:
        paradox_score = min(len(future_citations) / 5.0, 1.0)
        score = (
            paradox_score  * 0.50 +
            recency_score  * 0.30 +
            timeline_score * 0.20
        )
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.20:   return "medium"
        return "low"

    def _write_summary(
        self,
        flags: list,
        risk_level: str,
        cited_years: list,
    ) -> str:
        year_range = ""
        if cited_years:
            valid = [y for y in cited_years if y <= CURRENT_YEAR]
            if valid:
                year_range = f" Citations span {min(valid)}–{max(valid)}."

        if not flags:
            return (
                f"Temporal Analysis: No timeline anomalies detected."
                f"{year_range} Citation chronology appears consistent "
                f"with reported study timeline. Risk level: {risk_level.upper()}."
            )

        high   = sum(1 for f in flags if f.severity == "high")
        medium = sum(1 for f in flags if f.severity == "medium")
        parts  = []
        if high:
            parts.append(
                f"{high} high-severity timeline violation"
                f"{'s' if high > 1 else ''}"
            )
        if medium:
            parts.append(
                f"{medium} recency inconsistenc"
                f"{'ies' if medium > 1 else 'y'}"
            )

        return (
            f"Temporal Analysis: {', '.join(parts)} detected."
            f"{year_range} Risk level: {risk_level.upper()}."
        )