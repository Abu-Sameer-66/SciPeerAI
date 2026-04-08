# src/scipeerai/modules/reproducibility_scanner.py
#
# Reproducibility Scanner
# -----------------------
# The reproducibility crisis exists largely because
# researchers cannot access the code, data, and exact
# methods used in published papers.
#
# This module scans paper text for reproducibility
# signals — what is present and what is critically
# missing for independent replication.

import re
from dataclasses import dataclass, field


# ── data structures ───────────────────────────────────────────

@dataclass
class ReproducibilityFlag:
    flag_type: str
    severity: str
    description: str
    evidence: str
    suggestion: str


@dataclass
class ReproducibilityResult:
    # what was found
    has_code_link: bool
    has_data_link: bool
    has_software_versions: bool
    has_statistical_software: bool
    has_preregistration: bool
    has_ethics_statement: bool
    has_conflict_statement: bool
    has_sample_size_justification: bool

    # scoring
    reproducibility_score: float   # 0.0 = not reproducible, 1.0 = fully
    flags: list
    risk_level: str
    summary: str


# ── main class ────────────────────────────────────────────────

class ReproducibilityScanner:
    """
    Scans paper text for reproducibility indicators.

    Two layers:
    1. Presence checks — what good papers SHOULD have
    2. Absence flags — what is missing and how serious

    Scoring is inverted from other modules:
    HIGH reproducibility score = LOW risk.
    We report both for clarity.
    """

    # code/data sharing signals
    CODE_PATTERNS = [
        r'github\.com/\S+',
        r'gitlab\.com/\S+',
        r'bitbucket\.org/\S+',
        r'code.*available.*at',
        r'code.*provided.*at',
        r'source code.*available',
        r'scripts.*available',
        r'zenodo\.org/\S+',
        r'osf\.io/\S+',
        r'code ocean',
        r'figshare\.com/\S+',
    ]

    DATA_PATTERNS = [
        r'data.*available.*at',
        r'dataset.*available',
        r'data.*deposited',
        r'data.*repository',
        r'data.*doi',
        r'supplementary data',
        r'data.*provided',
        r'open data',
        r'zenodo\.org/\S+',
        r'osf\.io/\S+',
        r'dryad',
        r'figshare',
        r'harvard dataverse',
        r'data.*upon.*request',  # weaker — noted separately
    ]

    SOFTWARE_PATTERNS = [
        r'r\s+version\s+\d',
        r'python\s+\d+\.\d+',
        r'spss\s+version',
        r'stata\s+\d+',
        r'matlab\s+r\d+',
        r'sas\s+version',
        r'scipy\s+\d',
        r'numpy\s+\d',
        r'sklearn\s+\d',
        r'tensorflow\s+\d',
        r'pytorch\s+\d',
    ]

    STAT_SOFTWARE = [
        'r software', 'rstudio', 'spss', 'stata',
        'sas', 'matlab', 'python', 'excel', 'graphpad'
    ]

    PREREG_PATTERNS = [
        r'pre.?registered',
        r'preregistered',
        r'clinicaltrials\.gov',
        r'osf\.io',
        r'aspredicted\.org',
        r'registered report',
        r'trial registration',
        r'isrctn',
        r'anzctr',
    ]

    def __init__(self):
        self._code_re    = [re.compile(p, re.IGNORECASE) for p in self.CODE_PATTERNS]
        self._data_re    = [re.compile(p, re.IGNORECASE) for p in self.DATA_PATTERNS]
        self._sw_re      = [re.compile(p, re.IGNORECASE) for p in self.SOFTWARE_PATTERNS]
        self._prereg_re  = [re.compile(p, re.IGNORECASE) for p in self.PREREG_PATTERNS]

    # ── public method ─────────────────────────────────────────

    def analyze(self, text: str) -> ReproducibilityResult:
        """
        Full reproducibility scan.
        Returns what is present, what is missing, and risk level.
        """
        t = text.lower()

        # presence checks
        has_code       = self._check_patterns(text, self._code_re)
        has_data       = self._check_patterns(text, self._data_re)
        has_sw_version = self._check_patterns(text, self._sw_re)
        has_stat_sw    = any(sw in t for sw in self.STAT_SOFTWARE)
        has_prereg     = self._check_patterns(text, self._prereg_re)
        has_ethics     = self._has_ethics_statement(t)
        has_conflict   = self._has_conflict_statement(t)
        has_n_justify  = self._has_sample_size_justification(t)

        # build flags for what is missing
        flags = []
        flags.extend(self._flag_missing_code(has_code, t))
        flags.extend(self._flag_missing_data(has_data, t))
        flags.extend(self._flag_missing_software(has_sw_version, has_stat_sw, t))
        flags.extend(self._flag_missing_prereg(has_prereg, t))
        flags.extend(self._flag_missing_ethics(has_ethics, t))
        flags.extend(self._flag_data_on_request(text))

        # reproducibility score: percentage of key items present
        checklist = [
            has_code, has_data, has_sw_version,
            has_stat_sw, has_prereg, has_ethics,
            has_conflict, has_n_justify
        ]
        repro_score = sum(checklist) / len(checklist)

        # risk is inverse of reproducibility
        risk_score = round(1.0 - repro_score, 3)
        risk_level = self._get_risk_level(risk_score)

        return ReproducibilityResult(
            has_code_link=has_code,
            has_data_link=has_data,
            has_software_versions=has_sw_version,
            has_statistical_software=has_stat_sw,
            has_preregistration=has_prereg,
            has_ethics_statement=has_ethics,
            has_conflict_statement=has_conflict,
            has_sample_size_justification=has_n_justify,
            reproducibility_score=round(repro_score, 3),
            flags=flags,
            risk_level=risk_level,
            summary=self._write_summary(
                repro_score, risk_level, flags,
                has_code, has_data
            ),
        )

    # ── presence detectors ────────────────────────────────────

    def _check_patterns(self, text: str, patterns: list) -> bool:
        return any(p.search(text) for p in patterns)

    def _has_ethics_statement(self, text: str) -> bool:
        markers = [
            'ethics committee', 'institutional review board',
            'irb approval', 'ethics approval', 'ethical approval',
            'helsinki declaration', 'informed consent',
            'ethical clearance', 'ethics board'
        ]
        return any(m in text for m in markers)

    def _has_conflict_statement(self, text: str) -> bool:
        markers = [
            'conflict of interest', 'competing interest',
            'no conflict', 'declare no', 'disclose',
            'funding source', 'financial disclosure'
        ]
        return any(m in text for m in markers)

    def _has_sample_size_justification(self, text: str) -> bool:
        markers = [
            'power analysis', 'sample size calculation',
            'power calculation', 'statistical power',
            'a priori power', 'effect size calculation',
            'g*power', 'gpower'
        ]
        return any(m in text for m in markers)

    # ── flag generators ───────────────────────────────────────

    def _flag_missing_code(self, has_code: bool, text: str) -> list:
        """
        Code absence is critical for computational papers.
        We detect if the paper is computational first.
        """
        flags = []
        is_computational = any(w in text for w in [
            'algorithm', 'code', 'software', 'script',
            'simulation', 'model', 'neural network',
            'machine learning', 'deep learning'
        ])

        if is_computational and not has_code:
            flags.append(ReproducibilityFlag(
                flag_type="missing_code_availability",
                severity="high",
                description=(
                    "Computational study does not provide a link to "
                    "source code or analysis scripts. Independent "
                    "replication is not possible without this."
                ),
                evidence="Computational methods detected — no code link found",
                suggestion=(
                    "Deposit code on GitHub/GitLab/Zenodo and include "
                    "the URL in a 'Code Availability' section."
                ),
            ))
        return flags

    def _flag_missing_data(self, has_data: bool, text: str) -> list:
        flags = []
        has_empirical = any(w in text for w in [
            'dataset', 'data', 'sample', 'participants',
            'measurements', 'observations', 'collected'
        ])

        if has_empirical and not has_data:
            flags.append(ReproducibilityFlag(
                flag_type="missing_data_availability",
                severity="high",
                description=(
                    "Empirical study does not specify where raw data "
                    "can be accessed. Results cannot be independently verified."
                ),
                evidence="Empirical data detected — no data availability statement found",
                suggestion=(
                    "Deposit raw data in a repository (OSF, Zenodo, Dryad, "
                    "Harvard Dataverse) and include a Data Availability statement."
                ),
            ))
        return flags

    def _flag_missing_software(
        self, has_versions: bool, has_sw: bool, text: str
    ) -> list:
        flags = []
        is_quantitative = any(w in text for w in [
            'statistical', 'analysis', 'test', 'regression',
            'anova', 'correlation', 't-test', 'chi-square'
        ])

        if is_quantitative and not has_versions:
            flags.append(ReproducibilityFlag(
                flag_type="missing_software_versions",
                severity="medium",
                description=(
                    "Statistical analysis performed but software name and "
                    "version number not reported. Results may not replicate "
                    "across different software versions."
                ),
                evidence="Statistical analysis detected — no software version found",
                suggestion=(
                    "Specify the exact software and version used "
                    "(e.g., 'R version 4.3.1', 'Python 3.10.12 with "
                    "scikit-learn 1.3.0')."
                ),
            ))
        return flags

    def _flag_missing_prereg(self, has_prereg: bool, text: str) -> list:
        flags = []
        is_clinical_or_experimental = any(w in text for w in [
            'clinical trial', 'randomized', 'experiment',
            'intervention', 'treatment', 'placebo',
            'hypothesis', 'we predicted', 'we hypothesized'
        ])

        if is_clinical_or_experimental and not has_prereg:
            flags.append(ReproducibilityFlag(
                flag_type="missing_preregistration",
                severity="medium",
                description=(
                    "Experimental or clinical study with no preregistration "
                    "detected. Without preregistration, it is difficult to "
                    "distinguish confirmatory from exploratory analyses."
                ),
                evidence="Experimental design detected — no preregistration link",
                suggestion=(
                    "For future studies, preregister hypotheses on OSF "
                    "(osf.io) or ClinicalTrials.gov before data collection."
                ),
            ))
        return flags

    def _flag_missing_ethics(self, has_ethics: bool, text: str) -> list:
        flags = []
        involves_humans = any(w in text for w in [
            'participants', 'subjects', 'patients', 'volunteers',
            'respondents', 'human', 'children', 'adults'
        ])

        if involves_humans and not has_ethics:
            flags.append(ReproducibilityFlag(
                flag_type="missing_ethics_statement",
                severity="high",
                description=(
                    "Human participants study with no ethics approval "
                    "or IRB statement detected. This is required by "
                    "most journals and funding bodies."
                ),
                evidence="Human participants detected — no ethics statement found",
                suggestion=(
                    "Include an Ethics Statement specifying the approving "
                    "body, protocol number, and that informed consent was obtained."
                ),
            ))
        return flags

    def _flag_data_on_request(self, text: str) -> list:
        """
        'Data available upon request' is widely considered
        a reproducibility red flag — studies show that
        most such requests are never fulfilled.
        """
        flags = []
        if re.search(
            r'data.*available.*upon.*request|'
            r'data.*available.*on.*request|'
            r'available.*from.*corresponding.*author',
            text, re.IGNORECASE
        ):
            flags.append(ReproducibilityFlag(
                flag_type="data_available_on_request",
                severity="medium",
                description=(
                    "'Data available upon request' is a reproducibility "
                    "risk. Research shows that over 80% of such requests "
                    "go unfulfilled or receive no response."
                ),
                evidence="'Data available upon request' language detected",
                suggestion=(
                    "Deposit data in a public repository instead. "
                    "This increases citation rates and research trust."
                ),
            ))
        return flags

    # ── scoring ───────────────────────────────────────────────

    def _get_risk_level(self, risk_score: float) -> str:
        if risk_score >= 0.7:   return "critical"
        elif risk_score >= 0.4: return "high"
        elif risk_score >= 0.2: return "medium"
        return "low"

    def _write_summary(
        self,
        repro_score: float,
        risk_level: str,
        flags: list,
        has_code: bool,
        has_data: bool,
    ) -> str:
        pct = round(repro_score * 100)

        if not flags:
            return (
                f"Reproducibility score: {pct}%. "
                f"All key reproducibility indicators detected."
            )

        missing = []
        if not has_code: missing.append("code")
        if not has_data: missing.append("data")

        high = sum(1 for f in flags if f.severity == "high")
        med  = sum(1 for f in flags if f.severity == "medium")

        parts = []
        if high: parts.append(f"{high} critical gap{'s' if high > 1 else ''}")
        if med:  parts.append(f"{med} concern{'s' if med > 1 else ''}")

        return (
            f"Reproducibility score: {pct}%. "
            f"Flagged {', '.join(parts)}. "
            f"Risk level: {risk_level.upper()}."
        )