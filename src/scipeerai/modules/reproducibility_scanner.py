import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Patterns ──────────────────────────────────────────────────────────────────

CODE_PAT = re.compile(
    r'github\.com|gitlab\.com|bitbucket\.org'
    r'|zenodo\.org|figshare\.com|osf\.io'
    r'|code\s+(?:is\s+)?(?:publicly\s+)?available\s+at'
    r'|source\s+code\s+(?:is\s+)?available\s+at'
    r'|implementation\s+(?:is\s+)?available\s+at'
    r'|scripts?\s+(?:are\s+)?(?:publicly\s+)?available\s+at'
    r'|software\s+(?:is\s+)?available\s+at',
    re.IGNORECASE,
)

DATA_PAT = re.compile(
    r'data\s+(?:are\s+|is\s+)?(?:publicly\s+)?available\s+at'
    r'|dataset\s+(?:is\s+)?available\s+at'
    r'|data\s+(?:are\s+)?(?:deposited|archived|hosted)\s+(?:at|in|on)'
    r'|zenodo\.org|figshare\.com|osf\.io|dryad|dataverse'
    r'|open\s+data|data\s+availability\s+statement'
    r'|raw\s+data\s+(?:are\s+)?available\s+at',
    re.IGNORECASE,
)

# v2.3.2 — NEW: "available upon request" is NOT real availability
REQUEST_ONLY_PAT = re.compile(
    r'available\s+(?:upon|on)\s+request'
    r'|upon\s+(?:reasonable\s+)?request'
    r'|on\s+reasonable\s+request'
    r'|request\s+from\s+(?:the\s+)?(?:corresponding\s+)?author'
    r'|contact\s+(?:the\s+)?(?:corresponding\s+)?author\s+for'
    r'|will\s+not\s+be\s+(?:publicly\s+)?(?:released|shared|available)'
    r'|cannot\s+be\s+shared'
    r'|proprietary\s+and\s+(?:will\s+not|cannot)'
    r'|not\s+(?:publicly\s+)?available'
    r'|data\s+(?:are\s+)?not\s+available',
    re.IGNORECASE,
)

PREPRINT_PAT = re.compile(
    r'pre-?registered|pre\s+registered'
    r'|registration\s+(?:at|on|in)'
    r'|osf\.io|aspredicted\.org|clinicaltrials\.gov'
    r'|registered\s+(?:at|on|in|with)'
    r'|registration\s+number',
    re.IGNORECASE,
)

SOFTWARE_PAT = re.compile(
    r'\b(?:R\s+version|python\s+\d|spss\s+v|stata\s+v|matlab\s+r'
    r'|version\s+\d+\.\d+|v\d+\.\d+|release\s+\d)',
    re.IGNORECASE,
)

ETHICS_PAT = re.compile(
    r'ethics\s+(?:committee|board|approval|statement|review)'
    r'|institutional\s+review\s+board|irb\s+(?:approval|protocol)'
    r'|ethical\s+approval|helsinki|informed\s+consent'
    r'|ethics\s+approval\s+(?:was\s+)?(?:obtained|granted)',
    re.IGNORECASE,
)

COMPUTATIONAL_SIGNALS = re.compile(
    r'\b(?:algorithm|code|script|simulation|model|neural|train(?:ed|ing)'
    r'|dataset|pipeline|framework|implementation|repository|github'
    r'|python|pytorch|tensorflow|keras|sklearn|numpy|pandas)\b',
    re.IGNORECASE,
)

EMPIRICAL_SIGNALS = re.compile(
    r'\b(?:participants?|subjects?|patients?|sample|survey|interview'
    r'|experiment(?:al)?|randomized|control(?:led)?|cohort|trial'
    r'|questionnaire|observation|measurement|data\s+collect)\b',
    re.IGNORECASE,
)

OPEN_SCIENCE_BADGES = re.compile(
    r'open\s+(?:science|data|materials|access)'
    r'|badges?\s+(?:awarded|received|earned)'
    r'|transparency\s+(?:statement|checklist)',
    re.IGNORECASE,
)

CONFLICT_PAT = re.compile(
    r'no\s+conflict|conflicts?\s+of\s+interest'
    r'|competing\s+interest|author\s+declaration',
    re.IGNORECASE,
)

FUNDING_PAT = re.compile(
    r'fund(?:ed|ing)|grant|support(?:ed)?\s+by'
    r'|acknowledge|sponsor',
    re.IGNORECASE,
)

LIMITATION_PAT = re.compile(
    r'limitation|caveat|shortcoming|weakness'
    r'|future\s+(?:work|research|study|studies)',
    re.IGNORECASE,
)

RAW_DATA_PAT = re.compile(
    r'raw\s+data|anonymi[sz]ed\s+data|de-?identified'
    r'|participant\s+data|individual.{0,20}data',
    re.IGNORECASE,
)

REPLICATION_PAT = re.compile(
    r'replicated|replication|reproduced|reproducib'
    r'|independent\s+(?:lab|group|team|replication)',
    re.IGNORECASE,
)


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ReproducibilityFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class ReproducibilityResult:
    has_code_link:          bool
    has_data_link:          bool
    has_software_versions:  bool
    has_preregistration:    bool
    has_ethics_statement:   bool
    reproducibility_score:  float
    risk_level:             str
    summary:                str
    flags:                  List[ReproducibilityFlag] = field(default_factory=list)
    flags_count:            int = 0
    open_science_score:     float = 0.0
    has_conflict_statement: bool = False
    has_funding_statement:  bool = False
    has_limitations:        bool = False
    has_raw_data:           bool = False
    has_replication:        bool = False


# ── Main class ────────────────────────────────────────────────────────────────

class ReproducibilityScanner:
    """
    Reproducibility Scanner v2.3.2

    Scores papers across 10 reproducibility dimensions:
      1. Code availability       (real link, not "upon request")
      2. Data availability       (real link, not "upon request")
      3. Pre-registration
      4. Software versions
      5. Ethics statement
      6. Conflict of interest
      7. Funding disclosure
      8. Limitations section
      9. Raw data sharing
     10. Independent replication

    v2.3.2 upgrade: "available upon request" explicitly detected and
    flagged as insufficient — real repository links required.
    """

    def analyze(self, text: str) -> ReproducibilityResult:
        tl = text.lower()
        flags: List[ReproducibilityFlag] = []

        # ── v2.3.2: negation detection ────────────────────────────────────────
        # "available upon request" is NOT a real availability statement
        request_only = bool(REQUEST_ONLY_PAT.search(tl))

        # ── Core checks ───────────────────────────────────────────────────────
        is_computational = bool(COMPUTATIONAL_SIGNALS.search(tl))
        is_empirical     = bool(EMPIRICAL_SIGNALS.search(tl))

        # Real availability requires actual links AND no request-only language
        has_code = bool(CODE_PAT.search(tl)) and not request_only
        has_data = bool(DATA_PAT.search(tl)) and not request_only
        has_pre  = bool(PREPRINT_PAT.search(tl))
        has_sw   = bool(SOFTWARE_PAT.search(tl))
        has_eth  = bool(ETHICS_PAT.search(tl))

        # ── Extended checks ───────────────────────────────────────────────────
        has_conflict  = bool(CONFLICT_PAT.search(tl))
        has_funding   = bool(FUNDING_PAT.search(tl))
        has_limit     = bool(LIMITATION_PAT.search(tl))
        has_raw       = bool(RAW_DATA_PAT.search(tl))
        has_repl      = bool(REPLICATION_PAT.search(tl))
        has_os_badge  = bool(OPEN_SCIENCE_BADGES.search(tl))

        # ── Flag generation ───────────────────────────────────────────────────

        # Code availability
        if not has_code and is_computational:
            evidence = (
                "Code stated as 'available upon request' — "
                "this is not a verifiable availability statement."
                if request_only else
                "No repository link, GitHub URL, or code availability statement found."
            )
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_code_availability",
                severity    = "high",
                description = (
                    "Computational study does not provide a link to source code "
                    "or analysis scripts. Independent replication is not possible "
                    "without this."
                    + (" 'Available upon request' does not meet open science standards."
                       if request_only else "")
                ),
                evidence    = evidence,
                suggestion  = (
                    "Deposit code on GitHub/GitLab/Zenodo and include the URL "
                    "in a 'Code Availability' section."
                ),
            ))

        # Data availability
        if not has_data and is_empirical:
            evidence = (
                "Data stated as 'available upon request' — "
                "this is not a verifiable data access statement."
                if request_only else
                "Empirical data detected — no data availability statement found."
            )
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_data_availability",
                severity    = "high",
                description = (
                    "Empirical study does not specify where raw data can be accessed. "
                    "Results cannot be independently verified."
                    + (" Journals increasingly reject 'available upon request' "
                       "as insufficient." if request_only else "")
                ),
                evidence    = evidence,
                suggestion  = (
                    "Deposit raw data in a repository (OSF, Zenodo, Dryad, "
                    "Harvard Dataverse) and include a Data Availability statement."
                ),
            ))

        # Pre-registration
        if not has_pre and is_empirical:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_preregistration",
                severity    = "medium",
                description = (
                    "No pre-registration found. Pre-registration prevents "
                    "HARKing (Hypothesizing After Results are Known) and "
                    "strengthens causal claims."
                ),
                evidence    = "No OSF, AsPredicted, or ClinicalTrials registration found.",
                suggestion  = (
                    "Pre-register future studies on OSF (osf.io) or "
                    "AsPredicted (aspredicted.org) before data collection."
                ),
            ))

        # Software versions
        if not has_sw and is_computational:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_software_versions",
                severity    = "medium",
                description = (
                    "Software versions not reported. Results may differ "
                    "across package versions, making exact replication impossible."
                ),
                evidence    = "No version numbers found for statistical software or packages.",
                suggestion  = (
                    "Report exact version numbers for all software and packages used "
                    "(e.g. Python 3.10.4, scikit-learn 1.2.0)."
                ),
            ))

        # Ethics
        if not has_eth and is_empirical:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_ethics_statement",
                severity    = "high",
                description = (
                    "No ethics approval or IRB statement found. "
                    "Human subject research requires documented ethics approval."
                ),
                evidence    = "No ethics committee, IRB, or Helsinki declaration reference.",
                suggestion  = (
                    "Include ethics approval number and committee name. "
                    "State that participants gave informed consent."
                ),
            ))

        # Conflict of interest
        if not has_conflict:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_conflict_statement",
                severity    = "low",
                description = "No conflict of interest statement detected.",
                evidence    = "No COI or competing interests declaration found.",
                suggestion  = (
                    "Add a 'Conflict of Interest' or 'Competing Interests' "
                    "statement even if there are none to declare."
                ),
            ))

        # Funding
        if not has_funding:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_funding_disclosure",
                severity    = "low",
                description = "No funding disclosure or acknowledgment found.",
                evidence    = "No funding, grant, or sponsor mention detected.",
                suggestion  = (
                    "Disclose all funding sources. If unfunded, state 'This research "
                    "received no specific funding'."
                ),
            ))

        # Limitations
        if not has_limit:
            flags.append(ReproducibilityFlag(
                flag_type   = "missing_limitations",
                severity    = "low",
                description = "No limitations section detected.",
                evidence    = "No limitation, caveat, or future work discussion found.",
                suggestion  = (
                    "Add a dedicated Limitations section discussing sample constraints, "
                    "generalizability, and study design weaknesses."
                ),
            ))

        # ── Score calculation ─────────────────────────────────────────────────
        core_checklist     = [has_code, has_data, has_pre, has_sw, has_eth]
        extended_checklist = [has_conflict, has_funding, has_limit, has_raw, has_repl]

        core_score     = sum(1 for c in core_checklist     if c) / len(core_checklist)
        extended_score = sum(1 for c in extended_checklist if c) / len(extended_checklist)
        open_sci_bonus = 0.05 if has_os_badge else 0.0

        repro_score = min(
            core_score * 0.70 + extended_score * 0.25 + open_sci_bonus,
            1.0
        )

        # ── Risk level ────────────────────────────────────────────────────────
        critical_flags = sum(1 for f in flags if f.severity == "high")
        medium_flags   = sum(1 for f in flags if f.severity == "medium")

        if critical_flags >= 2:
            risk_level = "critical"
        elif critical_flags == 1 or medium_flags >= 2:
            risk_level = "high"
        elif medium_flags == 1:
            risk_level = "medium"
        else:
            risk_level = "low"

        # ── Summary ───────────────────────────────────────────────────────────
        high_count = sum(1 for f in flags if f.severity == "high")
        summary = (
            f"Reproducibility score: {round(repro_score * 100)}%. "
            f"Flagged {len(flags)} concern(s)"
            + (f", including {high_count} critical gap(s)" if high_count else "")
            + (". Note: 'available upon request' is not a valid open science statement"
               if request_only else "")
            + f". Risk level: {risk_level.upper()}."
        )

        return ReproducibilityResult(
            has_code_link          = has_code,
            has_data_link          = has_data,
            has_software_versions  = has_sw,
            has_preregistration    = has_pre,
            has_ethics_statement   = has_eth,
            reproducibility_score  = round(repro_score, 4),
            risk_level             = risk_level,
            summary                = summary,
            flags                  = flags,
            flags_count            = len(flags),
            open_science_score     = round(extended_score, 4),
            has_conflict_statement = has_conflict,
            has_funding_statement  = has_funding,
            has_limitations        = has_limit,
            has_raw_data           = has_raw,
            has_replication        = has_repl,
        )