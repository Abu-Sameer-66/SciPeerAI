import re
from dataclasses import dataclass
from datetime import datetime

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
    r'(?:this|our|the) (\d{4}) study',
    r'(?:we |the researchers )?collected (?:data )?in (\d{4})',
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


class TemporalAnomalyDetector:
    """
    Temporal Anomaly Detector v2.3.1
    Upgraded citation year extraction:
      - Brackets format: Smith (2018), (Smith, 2018)
      - Plain format: Smith 2018, Jones et al. 2020
      - Bare year in text near author names
      - Reference section year extraction
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

    def _extract_collection_years(self, text: str) -> list:
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
        v2.3.1 — Four-layer year extraction:
        Layer 1: Smith (2018), Jones et al. (2020) — brackets outside
        Layer 2: (Smith, 2018), (Jones et al., 2020) — brackets inside
        Layer 3: Smith 2018, Jones 2024 — plain Author Year format (NEW)
        Layer 4: Reference section bare years
        """
        years = set()

        # Layer 1 — name outside brackets: Smith (2018)
        for match in re.finditer(
            r'[A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?\s+\((\d{4})\)',
            text
        ):
            year = self._to_int_year(match.group(1))
            if year:
                years.add(year)

        # Layer 2 — name inside brackets: (Smith, 2018)
        for match in re.finditer(
            r'\([A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?,?\s*(\d{4})\)',
            text
        ):
            year = self._to_int_year(match.group(1))
            if year:
                years.add(year)

        # Layer 3 — plain Author Year format: Smith 2018, Jones 2024
        # This is the critical missing layer
        for match in re.finditer(
            r'(?:^|[\s,;])([A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?)\s+(\d{4})(?:\b)',
            text,
            re.MULTILINE
        ):
            year = self._to_int_year(match.group(2))
            if year:
                years.add(year)

        # Layer 4 — reference section bare years
        ref_section = self._extract_references(text)
        if ref_section:
            for match in re.finditer(r'\b(\d{4})\b', ref_section):
                year = self._to_int_year(match.group(1))
                if year:
                    years.add(year)

        return sorted(years)

    def _to_int_year(self, raw: str) -> int:
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

    def _check_citation_paradox(
        self, text, collection_years, cited_years, flags
    ) -> list:
        if not collection_years or not cited_years:
            return []

        earliest_collection = min(collection_years)
        future_refs = [
            y for y in cited_years
            if y > earliest_collection + 1
        ]

        if len(future_refs) >= 2:
            flags.append(TemporalFlag(
                flag_type   = "citation_time_paradox",
                severity    = "high",
                description = (
                    f"Data collection appears to predate cited references. "
                    f"If data was collected around {earliest_collection}, "
                    f"then {len(future_refs)} citation(s) from later years "
                    f"could not have informed the study design."
                ),
                evidence    = (
                    f"Earliest data collection: {earliest_collection}. "
                    f"Later citations: {sorted(future_refs)[:5]}"
                    f"{'...' if len(future_refs) > 5 else ''}."
                ),
                suggestion  = (
                    "Verify that citations used to justify study design "
                    "predate data collection. Post-hoc additions are a "
                    "known manipulation pattern."
                ),
            ))

        return future_refs

    def _check_false_recency(self, text, cited_years, flags) -> float:
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

    def _check_impossible_years(self, cited_years, flags) -> float:
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
                    f"Citations reference years beyond {CURRENT_YEAR}: "
                    f"{future}. "
                    f"This indicates fabricated references or impossible timeline."
                ),
                evidence    = f"Future years detected: {future}.",
                suggestion  = (
                    "Verify all citation years against original sources. "
                    "Future-year citations are a strong fabrication signal."
                ),
            ))
            score = max(score, 0.9)

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

    def _compute_score(
        self, future_citations, recency_score, timeline_score, cited_years
    ) -> float:
        paradox_score = min(len(future_citations) / 3.0, 1.0)
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

    def _write_summary(self, flags, risk_level, cited_years) -> str:
        year_range = ""
        if cited_years:
            valid = [y for y in cited_years if y <= CURRENT_YEAR]
            if valid:
                year_range = f" Citations span {min(valid)}-{max(valid)}."

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
            parts.append(f"{high} high-severity timeline violation{'s' if high > 1 else ''}")
        if medium:
            parts.append(f"{medium} recency inconsistenc{'ies' if medium > 1 else 'y'}")

        return (
            f"Temporal Analysis: {', '.join(parts)} detected."
            f"{year_range} Risk level: {risk_level.upper()}."
        )