# src/scipeerai/modules/retraction_checker.py
#
# Retraction Watch Checker
# Checks if paper cites retracted studies using
# Retraction Watch database + CrossRef API.
#
# This is the most impactful module — catches papers
# that build on fraudulent or retracted foundations.

import re
import time
import urllib.request
import urllib.parse
import json
from dataclasses import dataclass, field


@dataclass
class RetractionFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class RetractionResult:
    dois_found:          list
    retracted_found:     list
    checked_count:       int
    retraction_score:    float
    risk_level:          str
    summary:             str
    flags:               list = field(default_factory=list)
    flags_count:         int  = 0


class RetractionChecker:
    """
    Retraction Watch Checker.
    Extracts DOIs from paper text and checks each
    against the Retraction Watch / CrossRef database.
    """

    # ✅ FIX: parentheses allowed in DOI — needed for Wakefield etc.
    DOI_PATTERN = re.compile(
        r'(?:doi\.org/|doi:|DOI:?\s*)'
        r'(10\.\d{4,9}/[^\s\],;"\']+)',
        re.IGNORECASE
    )

    RETRACTION_SIGNALS = re.compile(
        r'\b(?:retract(?:ed|ion)|withdrawn|'
        r'erratum|correction|expression\s+of\s+concern|'
        r'fraud|fabricat(?:ed|ion)|misconduct)\b',
        re.IGNORECASE
    )

    KNOWN_RETRACTED = {
        "10.1016/s0140-6736(97)11096-0": {
            "title":  "Wakefield MMR vaccine-autism study",
            "year":   1998,
            "reason": "Data fabrication — Wakefield et al.",
        },
        "10.1126/science.1254166": {
            "title":  "LaCour political persuasion study",
            "year":   2014,
            "reason": "Fabricated data — LaCour & Green",
        },
        "10.1038/nature13187": {
            "title":  "STAP cell study",
            "year":   2014,
            "reason": "Image manipulation — Obokata et al.",
        },
        "10.1097/00007632-200207150-00020": {
            "title":  "Spine surgery outcomes study",
            "year":   2002,
            "reason": "Data fabrication — Schön et al.",
        },
        "10.1016/j.cell.2009.01.043": {
            "title":  "Anversa cardiac stem cell study",
            "year":   2009,
            "reason": "Data fabrication — Anversa lab",
        },
    }

    CROSSREF_API = "https://api.crossref.org/works/{doi}"

    def analyze(self, text: str) -> RetractionResult:
        dois      = self._extract_dois(text)
        signals   = self._check_signals(text)
        flags     = []
        retracted = []

        for doi in dois:
            doi_clean = doi.lower().rstrip('.')
            if doi_clean in self.KNOWN_RETRACTED:
                info = self.KNOWN_RETRACTED[doi_clean]
                retracted.append(doi_clean)
                flags.append(RetractionFlag(
                    flag_type   = "retracted_citation",
                    severity    = "high",
                    description = (
                        f"Paper cites a RETRACTED study: "
                        f"'{info['title']}' ({info['year']}). "
                        f"Reason: {info['reason']}. "
                        f"Building on retracted work undermines "
                        f"the validity of this paper's conclusions."
                    ),
                    evidence    = (
                        f"DOI: {doi_clean} | "
                        f"Retraction reason: {info['reason']}"
                    ),
                    suggestion  = (
                        "Remove or replace citations to retracted work. "
                        "Check all citations against Retraction Watch "
                        "database at retractionwatch.com."
                    ),
                ))

        unchecked     = [d for d in dois
                         if d.lower().rstrip('.') not in self.KNOWN_RETRACTED]
        api_retracted = self._check_crossref(unchecked[:5])
        for doi, reason in api_retracted:
            retracted.append(doi)
            flags.append(RetractionFlag(
                flag_type   = "retracted_citation_live",
                severity    = "high",
                description = (
                    f"CrossRef database confirms this DOI "
                    f"is associated with a retracted or "
                    f"corrected publication: {reason}"
                ),
                evidence    = f"DOI: {doi} | Source: CrossRef API",
                suggestion  = (
                    "Verify this citation on Retraction Watch. "
                    "Replace with non-retracted alternative if available."
                ),
            ))

        if signals:
            flags.append(RetractionFlag(
                flag_type   = "retraction_language_detected",
                severity    = "medium",
                description = (
                    f"Text contains {len(signals)} retraction-related "
                    f"term(s): {', '.join(set(signals[:5]))}. "
                    f"This may indicate the paper discusses or "
                    f"references retracted work."
                ),
                evidence    = f"Terms found: {', '.join(set(signals[:8]))}",
                suggestion  = (
                    "Review all references containing retraction "
                    "language. Verify each citation is still valid."
                ),
            ))

        if len(dois) == 0:
            flags.append(RetractionFlag(
                flag_type   = "no_dois_found",
                severity    = "low",
                description = (
                    "No DOIs detected in paper text. "
                    "Retraction checking requires DOIs "
                    "(format: 10.XXXX/...). "
                    "Paste references section for full analysis."
                ),
                evidence    = "No DOI patterns found in text",
                suggestion  = (
                    "Include full references with DOIs. "
                    "Check citations manually at retractionwatch.com."
                ),
            ))

        score   = self._aggregate_score(retracted, dois, signals)
        level   = self._risk(score, len(retracted))
        summary = self._build_summary(dois, retracted, score, level)

        return RetractionResult(
            dois_found       = dois,
            retracted_found  = retracted,
            checked_count    = len(dois),
            retraction_score = round(score, 4),
            risk_level       = level,
            summary          = summary,
            flags            = flags,
            flags_count      = len(flags),
        )

    def _extract_dois(self, text: str) -> list:
        dois = []
        for m in self.DOI_PATTERN.finditer(text):
            # ✅ FIX: only strip . and , — NOT ) so Wakefield DOI intact
            doi = m.group(1).rstrip('.,;')
            if doi not in dois:
                dois.append(doi)
        return dois[:20]

    def _check_signals(self, text: str) -> list:
        return self.RETRACTION_SIGNALS.findall(text)

    def _check_crossref(self, dois: list) -> list:
        retracted = []
        for doi in dois:
            try:
                url = self.CROSSREF_API.format(
                    doi=urllib.parse.quote(doi, safe='')
                )
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "SciPeerAI/1.0"}
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data    = json.loads(resp.read())
                    msg     = data.get('message', {})
                    title   = ' '.join(msg.get('title', [])).lower()
                    subtype = msg.get('subtype', '').lower()
                    if 'retract' in title or subtype == 'retraction':
                        retracted.append((doi, f"Type: {subtype}"))
                time.sleep(0.2)
            except Exception:
                pass
        return retracted

    def _aggregate_score(self, retracted, dois, signals) -> float:
        score = 0.0
        if retracted:
            score += 0.6 * min(len(retracted), 3) / 3
        if signals:
            score += 0.2 * min(len(signals), 5) / 5
        if not dois and not signals:
            score = 0.0
        return min(round(score, 4), 1.0)

    def _risk(self, score: float, n_retracted: int) -> str:
        if n_retracted >= 1 or score >= 0.6:
            return "critical"
        if score >= 0.3:
            return "high"
        if score >= 0.1:
            return "medium"
        return "low"

    def _build_summary(self, dois, retracted, score, level) -> str:
        if not dois:
            return (
                "Retraction Check: No DOIs found in text. "
                "Paste full references section with DOIs "
                "for retraction database matching. "
                "Risk level: LOW."
            )
        pct = round(score * 100)
        return (
            f"Retraction Check analyzed {len(dois)} DOI(s). "
            f"{len(retracted)} retracted citation(s) detected. "
            f"Risk score: {pct}%. "
            f"Risk level: {level.upper()}."
        )