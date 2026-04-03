# Statistical Audit Module
# ------------------------
# This is where we catch the kind of statistical
# manipulation that slips past human reviewers.
#
# Three main things we look for:
#   1. p-values clustered suspiciously near 0.05
#   2. Sample sizes too small to trust the results
#   3. Numbers that look "too clean" to be real data

import re
from dataclasses import dataclass, field


# ── data structures ──────────────────────────────────────────

@dataclass
class StatFlag:
    # one issue we found
    flag_type: str
    severity: str        # "high", "medium", "low"
    description: str
    evidence: str        # the actual text/number that triggered this
    suggestion: str


@dataclass
class StatAuditResult:
    p_values_found: list
    sample_sizes_found: list
    flags: list
    risk_score: float       # 0.0 to 1.0
    risk_level: str         # "low" / "medium" / "high" / "critical"
    summary: str


# ── main class ───────────────────────────────────────────────

class StatAuditEngine:
    """
    Scans paper text for statistical red flags.

    I wrote this as a class because later we'll want to
    configure thresholds differently for different fields —
    medicine needs stricter p-value cutoffs than psychology,
    for instance.
    """

    # p-values this close to 0.05 are suspicious
    # real results don't magically cluster right at the cutoff
    P_HACK_ZONE = (0.04, 0.051)

    # below this sample size, most findings are unreliable
    MIN_SAMPLE_SIZE = 30

    def __init__(self):
        # regex for p-values — catches things like:
        # p=0.04, p < 0.001, p-value = 0.032, (p=.049)
        self._p_pattern = re.compile(
            r'p\s*[=<>≤≥]\s*\.?(\d+\.?\d*)',
            re.IGNORECASE
        )

        # regex for sample sizes — catches n=50, N = 120, n=32 etc
        self._n_pattern = re.compile(
            r'\bn\s*=\s*(\d+)',
            re.IGNORECASE
        )

        # t-statistics, F-statistics, chi-square values
        self._tstat_pattern = re.compile(
            r't\s*[=\(]\s*(\d+\.?\d*)',
            re.IGNORECASE
        )

    # ── public method ─────────────────────────────────────────

    def analyze(self, text: str) -> StatAuditResult:
        """
        Main entry point. Give it the paper text, get back
        a full audit report.
        """
        p_values = self._extract_p_values(text)
        sample_sizes = self._extract_sample_sizes(text)

        flags = []
        flags.extend(self._check_p_hacking(p_values))
        flags.extend(self._check_sample_sizes(sample_sizes))
        flags.extend(self._check_round_numbers(p_values))
        flags.extend(self._check_p_value_absence(text, sample_sizes))

        risk_score = self._calculate_risk(flags)
        risk_level = self._get_risk_level(risk_score)

        return StatAuditResult(
            p_values_found=p_values,
            sample_sizes_found=sample_sizes,
            flags=flags,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            summary=self._write_summary(flags, risk_level),
        )

    # ── extraction helpers ────────────────────────────────────

    def _extract_p_values(self, text: str) -> list:
        matches = self._p_pattern.findall(text)
        values = []
        for m in matches:
            try:
                val = float(m)
                if 0.0 < val <= 1.0:   # must be a valid probability
                    values.append(val)
            except ValueError:
                pass
        return values

    def _extract_sample_sizes(self, text: str) -> list:
        matches = self._n_pattern.findall(text)
        sizes = []
        for m in matches:
            try:
                sizes.append(int(m))
            except ValueError:
                pass
        return sizes

    # ── flag checks ───────────────────────────────────────────

    def _check_p_hacking(self, p_values: list) -> list:
        """
        Look for p-values suspiciously clustered just below 0.05.
        If more than 40% of reported p-values live in this tiny window,
        something probably went wrong in the analysis.
        """
        flags = []
        if not p_values:
            return flags

        low, high = self.P_HACK_ZONE
        borderline = [p for p in p_values if low <= p <= high]
        ratio = len(borderline) / len(p_values)

        if ratio >= 0.6 and len(borderline) >= 3:
            flags.append(StatFlag(
                flag_type="p_hacking_suspected",
                severity="high",
                description=(
                    f"{len(borderline)} out of {len(p_values)} reported "
                    f"p-values fall between {low} and {high}. "
                    f"That's {round(ratio*100)}% clustered right at "
                    f"the significance threshold."
                ),
                evidence=str(borderline),
                suggestion=(
                    "Check whether all conducted analyses are reported. "
                    "Selective reporting inflates this pattern."
                ),
            ))
        elif ratio >= 0.4 and len(borderline) >= 2:
            flags.append(StatFlag(
                flag_type="borderline_p_values",
                severity="medium",
                description=(
                    f"{len(borderline)} p-values near the 0.05 cutoff. "
                    f"Worth a closer look at the analysis pipeline."
                ),
                evidence=str(borderline),
                suggestion="Request full analysis scripts and pre-registration info.",
            ))

        return flags

    def _check_sample_sizes(self, sample_sizes: list) -> list:
        """
        Tiny sample sizes mean the results probably won't replicate.
        Below n=30 is a concern in most quantitative fields.
        """
        flags = []
        small = [n for n in sample_sizes if 0 < n < self.MIN_SAMPLE_SIZE]

        if small:
            flags.append(StatFlag(
                flag_type="small_sample_size",
                severity="high" if min(small) < 15 else "medium",
                description=(
                    f"Sample size(s) below recommended minimum: {small}. "
                    f"Studies with n < {self.MIN_SAMPLE_SIZE} are typically "
                    f"underpowered for reliable inference."
                ),
                evidence=str(small),
                suggestion=(
                    "A post-hoc power analysis would clarify whether "
                    "the study had sufficient power to detect the claimed effects."
                ),
            ))

        return flags

    def _check_round_numbers(self, p_values: list) -> list:
        """
        Real data rarely produces perfectly round p-values.
        p = 0.05 exactly is almost impossible to get naturally.
        p = 0.049 right at the boundary is also suspicious.
        """
        flags = []
        suspicious = []

        for p in p_values:
            # exact boundary value
            if p == 0.05:
                suspicious.append(p)
            # suspiciously precise cutoff-hugging
            elif p in (0.049, 0.001, 0.01):
                suspicious.append(p)

        if suspicious:
            flags.append(StatFlag(
                flag_type="suspiciously_round_p_values",
                severity="medium",
                description=(
                    f"Found p-values that are unusually precise "
                    f"or exactly at significance boundaries: {suspicious}"
                ),
                evidence=str(suspicious),
                suggestion=(
                    "Request raw data to verify these values. "
                    "Exact boundary values sometimes indicate rounding "
                    "or post-hoc adjustment."
                ),
            ))

        return flags

    def _check_p_value_absence(self, text: str, sample_sizes: list) -> list:
        """
        If a paper reports results with sample sizes but no p-values,
        it's avoiding statistical scrutiny — also a red flag.
        """
        flags = []
        has_stats_claim = any(
            phrase in text.lower()
            for phrase in ["significant", "effect", "difference", "result"]
        )
        p_mentions = len(self._p_pattern.findall(text))

        if sample_sizes and has_stats_claim and p_mentions == 0:
            flags.append(StatFlag(
                flag_type="missing_statistical_tests",
                severity="high",
                description=(
                    "Paper makes statistical claims but reports no p-values "
                    "or test statistics. Results cannot be independently evaluated."
                ),
                evidence="No p-values found despite significance claims",
                suggestion="Request full statistical output tables from authors.",
            ))

        return flags

    # ── scoring ───────────────────────────────────────────────

    def _calculate_risk(self, flags: list) -> float:
        """
        Weighted scoring — high severity flags count more.
        Capped at 1.0 so the score stays interpretable.
        """
        weights = {"high": 0.35, "medium": 0.20, "low": 0.08}
        score = sum(weights.get(f.severity, 0) for f in flags)
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.7:
            return "critical"
        elif score >= 0.4:
            return "high"
        elif score >= 0.2:
            return "medium"
        return "low"

    def _write_summary(self, flags: list, risk_level: str) -> str:
        if not flags:
            return (
                "No statistical anomalies detected. "
                "Standard metrics appear within normal ranges."
            )

        high = sum(1 for f in flags if f.severity == "high")
        med  = sum(1 for f in flags if f.severity == "medium")

        parts = []
        if high:
            parts.append(f"{high} high-severity issue{'s' if high > 1 else ''}")
        if med:
            parts.append(f"{med} medium-severity concern{'s' if med > 1 else ''}")

        return (
            f"Statistical audit flagged {', '.join(parts)}. "
            f"Overall risk level: {risk_level.upper()}."
        )