# Citation DNA Analysis
# ---------------------
# Every researcher leaves a citation fingerprint.
# The journals they trust. The authors they follow.
# The countries they draw from. The decade they anchor to.
#
# Two genuinely independent papers on the same topic
# will share some citations — but not 80% of them.
# When citation overlap is that high, the papers are not
# independent. They are the same work in a different coat.
#
# This module extracts the citation DNA of a paper:
# the network of who is cited, how often, from where,
# and how diverse that network is.
# Then it measures the health of that network.
#
# A manipulated reference list has patterns:
# too concentrated in one journal, one author, one year,
# one institution — or suspiciously identical to another
# paper the same group published six months earlier.

import re
import math
from dataclasses import dataclass, field
from collections import Counter


# ── constants ──────────────────────────────────────────────────────────────────

# major journal name fragments — used to detect journal concentration
KNOWN_JOURNALS = [
    "nature", "science", "cell", "lancet", "jama", "nejm",
    "plos", "pnas", "ieee", "acm", "springer", "elsevier",
    "wiley", "oxford", "cambridge", "frontiers", "mdpi",
    "journal of", "proceedings of", "transactions on",
    "review of", "annals of", "advances in",
]

# country/region markers found in author affiliations and addresses
COUNTRY_MARKERS = [
    "usa", "united states", "uk", "united kingdom", "china",
    "germany", "france", "japan", "india", "australia",
    "canada", "italy", "spain", "netherlands", "sweden",
    "switzerland", "brazil", "south korea", "russia", "iran",
]


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class CitationNode:
    author:  str
    year:    int
    journal: str
    raw:     str


@dataclass
class DNAFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class CitationDNAResult:
    total_citations:      int
    unique_authors:       int
    year_distribution:    dict
    journal_distribution: dict
    author_concentration: float
    journal_concentration: float
    decade_concentration: float
    geographic_diversity: float
    dna_diversity_score:  float
    dna_risk_score:       float
    risk_level:           str
    summary:              str
    flags:                list
    flags_count:          int


# ── main class ────────────────────────────────────────────────────────────────

class CitationDNAAnalyzer:
    """
    Extracts and evaluates the citation network of a paper.

    Four dimensions of analysis:
    1. Author concentration — too many citations to one person
    2. Journal concentration — too many citations from one outlet
    3. Temporal concentration — all citations from one decade
    4. Geographic diversity — single-country citation network

    A healthy reference list is diverse across all four dimensions.
    Concentration in any dimension is a manipulation signal.
    """

    def analyze(self, text: str) -> CitationDNAResult:
        nodes   = self._extract_citation_nodes(text)
        flags   = []
        if not nodes:
            return CitationDNAResult(
                total_citations       = 0,
                unique_authors        = 0,
                year_distribution     = {},
                journal_distribution  = {},
                author_concentration  = 0.0,
                journal_concentration = 0.0,
                decade_concentration  = 0.0,
                geographic_diversity  = 0.0,
                dna_diversity_score   = 1.0,
                dna_risk_score        = 0.0,
                risk_level            = "low",
                summary               = (
                    "Citation DNA Analysis: No citations extracted. "
                    "Paste the full references section for complete "
                    "network analysis. Risk level: LOW."
                ),
                flags                 = [],
                flags_count           = 0,
            )
        author_conc  = self._measure_author_concentration(nodes, flags)
        journal_conc = self._measure_journal_concentration(nodes, flags)
        decade_conc  = self._measure_decade_concentration(nodes, flags)
        geo_div      = self._measure_geographic_diversity(text, flags)

        year_dist    = self._year_distribution(nodes)
        journal_dist = self._journal_distribution(nodes)

        diversity    = self._compute_diversity(
            author_conc, journal_conc, decade_conc, geo_div
        )
        risk_score   = 1.0 - diversity
        risk_level   = self._get_risk_level(risk_score)

        return CitationDNAResult(
            total_citations       = len(nodes),
            unique_authors        = len({n.author for n in nodes if n.author}),
            year_distribution     = year_dist,
            journal_distribution  = journal_dist,
            author_concentration  = round(author_conc,  3),
            journal_concentration = round(journal_conc, 3),
            decade_concentration  = round(decade_conc,  3),
            geographic_diversity  = round(geo_div,      3),
            dna_diversity_score   = round(diversity,    3),
            dna_risk_score        = round(risk_score,   3),
            risk_level            = risk_level,
            summary               = self._write_summary(
                nodes, flags, risk_level, diversity
            ),
            flags                 = flags,
            flags_count           = len(flags),
        )

    # ── citation extraction ────────────────────────────────────────────────────

    def _extract_citation_nodes(self, text: str) -> list:
        """
        Parse individual citations from the paper text.
        Handles author-year inline style and numbered reference lists.
        Each node carries author name, year, and guessed journal.
        """
        nodes = []

        # inline style: Smith (2018), Jones et al. (2020)
        for match in re.finditer(
            r'([A-Z][a-zA-Z\-]+)(?:\s+et\s+al\.?)?\s+\((\d{4})\)',
            text
        ):
            author = match.group(1).lower()
            year   = self._safe_year(match.group(2))
            if year:
                nodes.append(CitationNode(
                    author  = author,
                    year    = year,
                    journal = self._guess_journal(text, match.start()),
                    raw     = match.group(0),
                ))

        # if no inline citations found, try reference list parsing
        if not nodes:
            ref_section = self._get_ref_section(text)
            if ref_section:
                nodes = self._parse_reference_list(ref_section)

        return nodes

    def _parse_reference_list(self, ref_text: str) -> list:
        """
        Extract structured nodes from a formatted reference list.
        Works on numbered lists like [1] Author, A. (Year). Title. Journal.
        """
        nodes  = []
        lines  = ref_text.split("\n")

        for line in lines:
            line = line.strip()
            if len(line) < 20:
                continue
            year_match = re.search(r'\((\d{4})\)', line)
            if not year_match:
                year_match = re.search(r'\b(19[5-9]\d|20[0-2]\d)\b', line)
            if not year_match:
                continue

            year = self._safe_year(year_match.group(1))
            if not year:
                continue

            # first capitalized word as author proxy
            author_match = re.search(r'[A-Z][a-z]+', line)
            author = author_match.group(0).lower() if author_match else "unknown"

            journal = ""
            for known in KNOWN_JOURNALS:
                if known in line.lower():
                    journal = known
                    break

            nodes.append(CitationNode(
                author  = author,
                year    = year,
                journal = journal,
                raw     = line[:80],
            ))

        return nodes

    def _guess_journal(self, text: str, position: int) -> str:
        """
        Look in a window around the citation for a known journal name.
        Used for inline citations that do not have full reference data.
        """
        window = text[max(0, position - 100): position + 200].lower()
        for journal in KNOWN_JOURNALS:
            if journal in window:
                return journal
        return ""

    def _get_ref_section(self, text: str) -> str:
        text_lo = text.lower()
        for marker in ["references", "bibliography", "works cited"]:
            idx = text_lo.rfind(marker)
            if idx != -1:
                return text[idx:]
        return ""

    def _safe_year(self, raw: str) -> int:
        try:
            year = int(raw.strip())
            if 1900 <= year <= 2100:
                return year
        except (ValueError, AttributeError):
            pass
        return 0

    # ── concentration measures ─────────────────────────────────────────────────

    def _measure_author_concentration(
        self, nodes: list, flags: list
    ) -> float:
        """
        Herfindahl-Hirschman Index on cited authors.
        HHI near 1.0 means one author dominates the reference list.
        A genuine literature review draws from many different voices.
        """
        if not nodes:
            return 0.0

        authors = [n.author for n in nodes if n.author]
        if not authors:
            return 0.0

        hhi = self._hhi(authors)

        if hhi >= 0.25:
            counter   = Counter(authors)
            top_name, top_count = counter.most_common(1)[0]
            ratio     = top_count / len(authors)
            flags.append(DNAFlag(
                flag_type   = "author_concentration",
                severity    = "high" if hhi >= 0.40 else "medium",
                description = (
                    f"Citation network is concentrated around a small number "
                    f"of authors. HHI concentration index: {round(hhi, 3)}. "
                    f"Diverse literature reviews have HHI below 0.10."
                ),
                evidence    = (
                    f"Most cited author: '{top_name}' appears in "
                    f"{top_count}/{len(authors)} citations "
                    f"({round(ratio * 100, 1)}%)."
                ),
                suggestion  = (
                    "Broaden the reference list to include a wider range "
                    "of authors. High author concentration may indicate "
                    "citation cartel behavior or incomplete literature review."
                ),
            ))

        return hhi

    def _measure_journal_concentration(
        self, nodes: list, flags: list
    ) -> float:
        """
        Measures how many citations come from a single journal or publisher.
        A paper citing 80% of its sources from one journal is suspicious.
        """
        if not nodes:
            return 0.0

        journals = [n.journal for n in nodes if n.journal]
        if len(journals) < 3:
            return 0.0

        hhi = self._hhi(journals)

        if hhi >= 0.30:
            counter          = Counter(journals)
            top_j, top_count = counter.most_common(1)[0]
            flags.append(DNAFlag(
                flag_type   = "journal_concentration",
                severity    = "medium",
                description = (
                    f"Citations are heavily concentrated in one journal "
                    f"or publisher. Journal concentration HHI: {round(hhi, 3)}."
                ),
                evidence    = (
                    f"Most cited outlet: '{top_j}' accounts for "
                    f"{top_count}/{len(journals)} identified journal citations."
                ),
                suggestion  = (
                    "A balanced reference list draws from multiple journals "
                    "across different publishers. Single-outlet concentration "
                    "may reflect editorial bias or citation ring behavior."
                ),
            ))

        return hhi

    def _measure_decade_concentration(
        self, nodes: list, flags: list
    ) -> float:
        """
        Maps citations to decades and measures concentration.
        A paper claiming to survey a field but citing only one decade
        is presenting an incomplete — possibly cherry-picked — picture.
        """
        if not nodes:
            return 0.0

        decades = [
            f"{(n.year // 10) * 10}s"
            for n in nodes if n.year
        ]
        if not decades:
            return 0.0

        hhi = self._hhi(decades)

        if hhi >= 0.60:
            counter          = Counter(decades)
            top_d, top_count = counter.most_common(1)[0]
            flags.append(DNAFlag(
                flag_type   = "temporal_concentration",
                severity    = "medium",
                description = (
                    f"Citations cluster heavily in one decade. "
                    f"Temporal concentration HHI: {round(hhi, 3)}. "
                    f"A thorough literature review spans multiple decades."
                ),
                evidence    = (
                    f"Dominant decade: {top_d} — "
                    f"{top_count}/{len(decades)} citations "
                    f"({round(top_count/len(decades)*100, 1)}%)."
                ),
                suggestion  = (
                    "Include foundational older works and recent advances "
                    "to demonstrate comprehensive literature coverage."
                ),
            ))

        return hhi

    def _measure_geographic_diversity(
        self, text: str, flags: list
    ) -> float:
        """
        Scans the text for country/region markers to estimate how
        internationally diverse the cited work is.
        Single-country citation networks are a known bias signal.
        """
        text_lo  = text.lower()
        found    = [c for c in COUNTRY_MARKERS if c in text_lo]
        unique   = len(set(found))

        # diversity score: 0 countries = 0.0, 5+ countries = 1.0
        diversity = min(unique / 5.0, 1.0)

        if diversity < 0.20 and unique <= 1:
            flags.append(DNAFlag(
                flag_type   = "low_geographic_diversity",
                severity    = "low",
                description = (
                    f"Citation network shows low geographic diversity. "
                    f"Only {unique} country/region marker(s) detected. "
                    f"International research should draw from global literature."
                ),
                evidence    = (
                    f"Countries/regions detected: "
                    f"{found if found else 'none identified'}."
                ),
                suggestion  = (
                    "Consider including research from institutions in "
                    "different countries to strengthen international validity."
                ),
            ))

        return diversity

    # ── distributions ──────────────────────────────────────────────────────────

    def _year_distribution(self, nodes: list) -> dict:
        years = [n.year for n in nodes if n.year]
        return dict(sorted(Counter(years).items()))

    def _journal_distribution(self, nodes: list) -> dict:
        journals = [n.journal for n in nodes if n.journal]
        return dict(Counter(journals).most_common(10))

    # ── hhi index ─────────────────────────────────────────────────────────────

    def _hhi(self, items: list) -> float:
        """
        Herfindahl-Hirschman Index — standard economics concentration measure.
        Sum of squared market shares. Range: 1/n (perfect diversity) to 1.0 (monopoly).
        We normalize to 0-1 for consistent interpretation.
        """
        if not items:
            return 0.0
        total   = len(items)
        counter = Counter(items)
        raw_hhi = sum((count / total) ** 2 for count in counter.values())
        min_hhi = 1.0 / len(counter) if counter else 0.0
        if min_hhi >= 1.0:
            return 1.0
        normalized = (raw_hhi - min_hhi) / (1.0 - min_hhi)
        return round(min(max(normalized, 0.0), 1.0), 4)

    # ── scoring ────────────────────────────────────────────────────────────────

    def _compute_diversity(
        self,
        author_conc:  float,
        journal_conc: float,
        decade_conc:  float,
        geo_div:      float,
    ) -> float:
        """
        Diversity is the inverse of concentration across all dimensions.
        Geographic diversity adds to the score rather than subtracting.
        """
        concentration = (
            author_conc  * 0.35 +
            journal_conc * 0.30 +
            decade_conc  * 0.20
        )
        diversity = (1.0 - concentration) * 0.75 + geo_div * 0.25
        return round(min(max(diversity, 0.0), 1.0), 3)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.25:   return "medium"
        return "low"

    def _write_summary(
        self,
        nodes: list,
        flags: list,
        risk_level: str,
        diversity: float,
    ) -> str:
        n = len(nodes)
        if n == 0:
            return (
                "Citation DNA Analysis: No citations extracted. "
                "Paste the full references section for complete network analysis. "
                f"Risk level: {risk_level.upper()}."
            )

        if not flags:
            return (
                f"Citation DNA Analysis: {n} citation(s) analyzed. "
                f"Network diversity score: {round(diversity * 100, 1)}%. "
                f"Citation network appears healthy and diverse. "
                f"Risk level: {risk_level.upper()}."
            )

        high   = sum(1 for f in flags if f.severity == "high")
        medium = sum(1 for f in flags if f.severity == "medium")
        parts  = []
        if high:
            parts.append(f"{high} high-severity concentration issue{'s' if high > 1 else ''}")
        if medium:
            parts.append(f"{medium} medium-severity pattern{'s' if medium > 1 else ''}")

        return (
            f"Citation DNA Analysis: {n} citation(s) analyzed. "
            f"Network diversity: {round(diversity * 100, 1)}%. "
            f"{', '.join(parts)} detected. "
            f"Risk level: {risk_level.upper()}."
        )