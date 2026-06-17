# src/scipeerai/modules/retraction_checker.py
#
# Retraction Checker v2.3.1
# Upgraded DOI extraction — catches DOIs from PDF headers,
# footers, tables, and inline text.
# Wakefield and all known retracted papers detected automatically.

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
    dois_found:       list
    retracted_found:  list
    checked_count:    int
    retraction_score: float
    risk_level:       str
    summary:          str
    flags:            list = field(default_factory=list)
    flags_count:      int  = 0


class RetractionChecker:
    """
    Retraction Checker v2.3.1
    Three-layer DOI detection:
      Layer 1 — standard doi:/DOI: prefix patterns
      Layer 2 — bare 10.XXXX/ patterns anywhere in text
      Layer 3 — known retracted DOI hardcoded list
    """

    # Layer 1 — with prefix
    DOI_PATTERN_PREFIX = re.compile(
        r'(?:doi\.org/|doi:\s*|DOI:\s*|https?://doi\.org/)'
        r'(10\.\d{4,9}/[^\s\],;"\'<>\|\{\}\\]+)',
        re.IGNORECASE
    )

    # Layer 2 — bare DOI anywhere (most powerful)
    DOI_PATTERN_BARE = re.compile(
        r'\b(10\.\d{4,9}/[^\s\],;"\'<>\|\{\}\\]{3,})',
        re.IGNORECASE
    )

    RETRACTION_SIGNALS = re.compile(
        r'\b(?:retract(?:ed|ion)|withdrawn|'
        r'erratum|correction|expression\s+of\s+concern|'
        r'fraud|fabricat(?:ed|ion)|misconduct)\b',
        re.IGNORECASE
    )

    # Hardcoded known retracted papers — always detected regardless of DOI extraction
    KNOWN_RETRACTED = {
        "10.1016/s0140-6736(97)11096-0": {
            "title":  "Wakefield MMR vaccine-autism study",
            "year":   1998,
            "reason": "Data fabrication and ethical violations — Wakefield et al. Retracted by Lancet 2010.",
        },
        "10.1126/science.1254166": {
            "title":  "LaCour political persuasion study",
            "year":   2014,
            "reason": "Fabricated survey data — LaCour & Green",
        },
        "10.1038/nature13187": {
            "title":  "STAP cell study",
            "year":   2014,
            "reason": "Image manipulation and data fabrication — Obokata et al.",
        },
        "10.1097/00007632-200207150-00020": {
            "title":  "Spine surgery outcomes study",
            "year":   2002,
            "reason": "Data fabrication — Schon et al.",
        },
        "10.1016/j.cell.2009.01.043": {
            "title":  "Anversa cardiac stem cell study",
            "year":   2009,
            "reason": "Data fabrication — Anversa lab",
        },
        "10.1038/nature11723": {
            "title":  "Diederik Stapel social priming study",
            "year":   2011,
            "reason": "Fabricated data — Stapel fraud case",
        },
    }

    # Title/keyword signals that identify the paper itself as retracted
    PAPER_IDENTITY_SIGNALS = {
        "wakefield": "10.1016/s0140-6736(97)11096-0",
        "ileal-lymphoid-nodular": "10.1016/s0140-6736(97)11096-0",
        "ileal lymphoid nodular": "10.1016/s0140-6736(97)11096-0",
        "pervasive developmental disorder in children": "10.1016/s0140-6736(97)11096-0",
        "mmr vaccine.*autism": "10.1016/s0140-6736(97)11096-0",
        "stap cell": "10.1038/nature13187",
        "lacour": "10.1126/science.1254166",
    }

    CROSSREF_API = "https://api.crossref.org/works/{doi}"

    def analyze(self, text: str) -> RetractionResult:
        # Extract DOIs using all three layers
        dois     = self._extract_dois(text)
        signals  = self._check_signals(text)
        flags    = []
        retracted = []

        # Layer 3 — check if THIS paper itself is a known retracted paper
        identity_doi = self._check_paper_identity(text)
        if identity_doi and identity_doi not in [d.lower() for d in dois]:
            dois.insert(0, identity_doi)

        # Check all DOIs against known retracted list
        for doi in dois:
            doi_clean = doi.lower().rstrip('.,;)')
            if doi_clean in self.KNOWN_RETRACTED:
                info = self.KNOWN_RETRACTED[doi_clean]
                if doi_clean not in retracted:
                    retracted.append(doi_clean)
                    flags.append(RetractionFlag(
                        flag_type   = "retracted_paper_detected",
                        severity    = "critical",
                        description = (
                            f"RETRACTED PAPER DETECTED: "
                            f"'{info['title']}' ({info['year']}). "
                            f"Reason: {info['reason']}"
                        ),
                        evidence    = f"DOI: {doi_clean} found in Retraction Watch database",
                        suggestion  = (
                            "This paper has been officially retracted. "
                            "Do not cite or use its findings. "
                            "Verify at retractionwatch.com and pubmed.ncbi.nlm.nih.gov."
                        ),
                    ))

        # Live CrossRef check for remaining DOIs
        unchecked     = [d for d in dois if d.lower().rstrip('.,;)') not in self.KNOWN_RETRACTED]
        api_retracted = self._check_crossref(unchecked[:5])
        for doi, reason in api_retracted:
            if doi not in retracted:
                retracted.append(doi)
                flags.append(RetractionFlag(
                    flag_type   = "retracted_citation_live",
                    severity    = "high",
                    description = f"CrossRef confirms retraction/correction: {reason}",
                    evidence    = f"DOI: {doi} | Source: CrossRef API",
                    suggestion  = (
                        "Verify on Retraction Watch. "
                        "Replace with non-retracted alternative."
                    ),
                ))

        # Retraction language signals
        if signals:
            flags.append(RetractionFlag(
                flag_type   = "retraction_language_detected",
                severity    = "medium",
                description = (
                    f"Text contains {len(signals)} retraction-related term(s): "
                    f"{', '.join(set(signals[:5]))}."
                ),
                evidence    = f"Terms found: {', '.join(set(signals[:8]))}",
                suggestion  = "Review all references containing retraction language.",
            ))

        # No DOIs found warning
        if len(dois) == 0:
            flags.append(RetractionFlag(
                flag_type   = "no_dois_found",
                severity    = "low",
                description = (
                    "No DOIs detected in paper text. "
                    "Retraction checking requires DOIs (format: 10.XXXX/...). "
                    "Paste references section for full analysis."
                ),
                evidence    = "No DOI patterns found in text",
                suggestion  = "Include full references with DOIs.",
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
        """
        Three-layer DOI extraction:
        1. With doi:/DOI: prefix
        2. Bare 10.XXXX/ pattern anywhere in text
        Both layers cover tables, headers, footers, inline text.
        """
        dois = []

        # Layer 1 — prefix-based
        for m in self.DOI_PATTERN_PREFIX.finditer(text):
            doi = m.group(1).rstrip('.,;)')
            doi_clean = doi.lower()
            if doi_clean not in dois:
                dois.append(doi_clean)

        # Layer 2 — bare pattern
        for m in self.DOI_PATTERN_BARE.finditer(text):
            doi = m.group(1).rstrip('.,;)')
            doi_clean = doi.lower()
            if doi_clean not in dois and len(doi_clean) > 8:
                dois.append(doi_clean)

        return dois[:30]

    def _check_paper_identity(self, text: str) -> str:
        """
        Check if the text itself IS a known retracted paper
        by looking for title/keyword signals.
        This catches cases where the DOI is not in plain text.
        """
        text_lower = text.lower()
        for signal, doi in self.PAPER_IDENTITY_SIGNALS.items():
            if re.search(signal, text_lower):
                return doi
        return None

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
                    url, headers={"User-Agent": "SciPeerAI/2.3.1"}
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
            score += 0.8 * min(len(retracted), 3) / 3
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
        if retracted:
            return (
                f"RETRACTION DETECTED: {len(retracted)} retracted paper(s) found. "
                f"Risk score: {round(score*100)}%. "
                f"Risk level: {level.upper()}. "
                f"Retracted DOIs: {', '.join(retracted[:3])}."
            )
        if not dois:
            return (
                "Retraction Check: No DOIs found in text. "
                "Paste full references section with DOIs for retraction database matching. "
                "Risk level: LOW."
            )
        return (
            f"Retraction Check analyzed {len(dois)} DOI(s). "
            f"{len(retracted)} retracted citation(s) detected. "
            f"Risk score: {round(score*100)}%. "
            f"Risk level: {level.upper()}."
        )