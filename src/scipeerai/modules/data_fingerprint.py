# Cross-Paper Data Fingerprinting
# --------------------------------
# Independent studies on the same topic will produce
# similar but never identical numbers.
# Random sampling variation guarantees this.
#
# When two papers report the exact same mean to four
# decimal places, the same standard deviation, the same
# sample size, and the same p-value — they are not
# independent. One copied from the other, or both
# copied from a shared fabricated source.
#
# This module extracts the numerical fingerprint of a
# single paper: every mean, SD, sample size, percentage,
# correlation, and p-value it reports.
#
# That fingerprint can then be compared against others.
# But even in isolation, the fingerprint reveals problems:
# numbers that are suspiciously round, values that are
# mathematically impossible given each other, and
# distributions of digits that do not look like real data.
#
# A paper's numbers should look like they came from
# the world. When they look like they came from a
# spreadsheet cell someone typed by hand — that is a signal.

import re
import math
from dataclasses import dataclass, field
from collections import Counter


# ── data structures ────────────────────────────────────────────────────────────

@dataclass
class NumericFingerprint:
    means:        list
    std_devs:     list
    sample_sizes: list
    percentages:  list
    correlations: list
    p_values:     list
    all_decimals: list


@dataclass
class DataFingerprintFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class DataFingerprintResult:
    fingerprint:            NumericFingerprint
    total_numbers:          int
    round_number_ratio:     float
    terminal_digit_bias:    float
    impossible_pairs:       list
    suspicious_duplicates:  list
    fingerprint_score:      float
    risk_level:             str
    summary:                str
    flags:                  list
    flags_count:            int


# ── main class ────────────────────────────────────────────────────────────────

class DataFingerprintAnalyzer:
    """
    Extracts the complete numerical fingerprint of a paper
    and tests it for signs of fabrication or cloning.

    Four detection layers:
    1. Round number bias — fabricated data rounds too cleanly
    2. Terminal digit bias — humans avoid certain ending digits
    3. Impossible value pairs — SD larger than mean for positive scales
    4. Suspicious internal duplicates — same value repeated too often
    """

    # regex patterns for specific statistical values
    _MEAN_PATTERN   = re.compile(
        r'(?:mean|average|M)\s*[=:]\s*(-?\d+\.?\d*)', re.IGNORECASE
    )
    _SD_PATTERN     = re.compile(
        r'(?:SD|S\.D\.|std|standard deviation)\s*[=:]\s*(\d+\.?\d*)',
        re.IGNORECASE
    )
    _N_PATTERN      = re.compile(
        r'(?:N|n|sample size)\s*[=:]\s*(\d+)', re.IGNORECASE
    )
    _PCT_PATTERN    = re.compile(
        r'(\d+\.?\d*)\s*%'
    )
    _CORR_PATTERN   = re.compile(
        r'(?:r|correlation)\s*[=:]\s*(-?\d*\.?\d+)', re.IGNORECASE
    )
    _PVAL_PATTERN   = re.compile(
        r'p\s*[=<>]\s*(0?\.\d+|\d+\.\d+[eE][+-]?\d+)', re.IGNORECASE
    )

    def analyze(self, text: str) -> DataFingerprintResult:
        fp    = self._extract_fingerprint(text)
        flags = []

        round_ratio   = self._check_round_number_bias(fp, flags)
        terminal_bias = self._check_terminal_digit_bias(fp, flags)
        impossible    = self._check_impossible_pairs(fp, flags)
        duplicates    = self._check_suspicious_duplicates(fp, flags)

        total   = self._count_total(fp)
        score   = self._compute_score(
            round_ratio, terminal_bias, impossible, duplicates, total
        )
        level   = self._get_risk_level(score)

        return DataFingerprintResult(
            fingerprint           = fp,
            total_numbers         = total,
            round_number_ratio    = round(round_ratio,   3),
            terminal_digit_bias   = round(terminal_bias, 3),
            impossible_pairs      = impossible,
            suspicious_duplicates = duplicates,
            fingerprint_score     = round(score, 3),
            risk_level            = level,
            summary               = self._write_summary(flags, level, total),
            flags                 = flags,
            flags_count           = len(flags),
        )

    # ── extraction ─────────────────────────────────────────────────────────────

    def _extract_fingerprint(self, text: str) -> NumericFingerprint:
        means        = self._parse_floats(self._MEAN_PATTERN,  text)
        std_devs     = self._parse_floats(self._SD_PATTERN,    text)
        sample_sizes = self._parse_ints(  self._N_PATTERN,     text)
        percentages  = self._parse_floats(self._PCT_PATTERN,   text)
        correlations = self._parse_floats(self._CORR_PATTERN,  text)
        p_values     = self._parse_floats(self._PVAL_PATTERN,  text)

        # all decimal numbers in the paper for digit-level analysis
        all_decimals = [
            float(m.group())
            for m in re.finditer(r'-?\d+\.\d+', text)
            if self._safe_float(m.group()) is not None
        ]

        return NumericFingerprint(
            means        = means,
            std_devs     = std_devs,
            sample_sizes = sample_sizes,
            percentages  = percentages,
            correlations = correlations,
            p_values     = p_values,
            all_decimals = all_decimals,
        )

    def _parse_floats(self, pattern: re.Pattern, text: str) -> list:
        results = []
        for match in pattern.finditer(text):
            val = self._safe_float(match.group(1))
            if val is not None:
                results.append(val)
        return results

    def _parse_ints(self, pattern: re.Pattern, text: str) -> list:
        results = []
        for match in pattern.finditer(text):
            try:
                val = int(match.group(1))
                if 1 <= val <= 1_000_000:
                    results.append(val)
            except (ValueError, IndexError):
                pass
        return results

    def _safe_float(self, raw: str) -> float:
        try:
            return float(raw.strip())
        except (ValueError, AttributeError):
            return None

    # ── detection checks ───────────────────────────────────────────────────────

    def _check_round_number_bias(
        self, fp: NumericFingerprint, flags: list
    ) -> float:
        """
        Real data does not round to whole numbers or .5 steps very often.
        When more than 60% of reported values are suspiciously round,
        someone likely typed them rather than computed them.
        """
        all_vals = fp.means + fp.std_devs + fp.percentages
        if len(all_vals) < 4:
            return 0.0

        round_count = sum(
            1 for v in all_vals
            if v == round(v, 0) or v == round(v, 1) and str(v).endswith(('0', '5'))
        )
        ratio = round_count / len(all_vals)

        if ratio >= 0.60:
            flags.append(DataFingerprintFlag(
                flag_type   = "round_number_bias",
                severity    = "medium",
                description = (
                    f"{round_count}/{len(all_vals)} reported values "
                    f"({round(ratio * 100, 1)}%) are suspiciously round. "
                    f"Real measured data rarely rounds this cleanly."
                ),
                evidence    = (
                    f"Round values detected among means, SDs, and percentages. "
                    f"Round ratio: {round(ratio, 3)}."
                ),
                suggestion  = (
                    "Verify that reported values are directly from analysis "
                    "output, not manually entered approximations."
                ),
            ))

        return ratio

    def _check_terminal_digit_bias(
        self, fp: NumericFingerprint, flags: list
    ) -> float:
        """
        The last digit of a truly random number is uniformly distributed
        across 0-9. Humans fabricating numbers unconsciously prefer
        certain digits (0, 5) and avoid others (7, 9).
        A chi-square test on terminal digits detects this.
        """
        all_vals = fp.all_decimals + [float(n) for n in fp.sample_sizes]
        if len(all_vals) < 10:
            return 0.0

        terminals = []
        for v in all_vals:
            parts = str(abs(v)).replace('.', '')
            if parts:
                terminals.append(int(parts[-1]))

        if not terminals:
            return 0.0

        counter  = Counter(terminals)
        expected = len(terminals) / 10.0
        chi_sq   = sum(
            ((counter.get(d, 0) - expected) ** 2) / expected
            for d in range(10)
        )

        # chi-square critical value at p=0.05 with 9 df is 16.92
        bias_score = min(chi_sq / 50.0, 1.0)

        if chi_sq >= 16.92:
            dominant_digit = counter.most_common(1)[0]
            flags.append(DataFingerprintFlag(
                flag_type   = "terminal_digit_bias",
                severity    = "medium",
                description = (
                    f"Terminal digit distribution deviates significantly "
                    f"from uniform expectation. "
                    f"Chi-square statistic: {round(chi_sq, 2)} "
                    f"(critical value: 16.92). "
                    f"This pattern is consistent with human number fabrication."
                ),
                evidence    = (
                    f"Most frequent terminal digit: "
                    f"'{dominant_digit[0]}' appears {dominant_digit[1]} times. "
                    f"Expected uniform frequency: {round(expected, 1)} each."
                ),
                suggestion  = (
                    "Re-examine raw data files to confirm reported values "
                    "match analysis output. Terminal digit bias is a "
                    "well-established fabrication marker."
                ),
            ))

        return round(bias_score, 3)

    def _check_impossible_pairs(
        self, fp: NumericFingerprint, flags: list
    ) -> list:
        """
        Statistical relationships constrain what values can coexist.
        SD > mean is impossible for strictly positive Likert-scale data.
        Correlation outside [-1, 1] is mathematically impossible.
        P-value outside [0, 1] cannot exist.
        """
        impossible = []

        # SD > mean for positive scales (Likert 1-7, reaction times, etc.)
        for mean, sd in zip(fp.means, fp.std_devs):
            if mean > 0 and sd > mean * 2:
                pair = f"M={mean}, SD={sd}"
                impossible.append(pair)

        if impossible:
            flags.append(DataFingerprintFlag(
                flag_type   = "impossible_sd_mean_pair",
                severity    = "high",
                description = (
                    f"{len(impossible)} mean/SD pair(s) where the standard "
                    f"deviation is implausibly large relative to the mean. "
                    f"For bounded positive scales, SD > 2*mean is suspicious."
                ),
                evidence    = f"Impossible pairs: {impossible[:3]}.",
                suggestion  = (
                    "Verify these values against the original analysis output. "
                    "Large SDs relative to means may indicate data entry error "
                    "or scale confusion."
                ),
            ))

        # correlation outside valid range
        bad_corr = [r for r in fp.correlations if abs(r) > 1.0]
        if bad_corr:
            impossible.extend([f"r={r}" for r in bad_corr])
            flags.append(DataFingerprintFlag(
                flag_type   = "impossible_correlation",
                severity    = "high",
                description = (
                    f"{len(bad_corr)} correlation value(s) outside [-1, 1]. "
                    f"These values are mathematically impossible."
                ),
                evidence    = f"Invalid correlations: {bad_corr}.",
                suggestion  = "Correct these values before submission.",
            ))

        # p-value outside [0, 1]
        bad_p = [p for p in fp.p_values if p < 0 or p > 1]
        if bad_p:
            impossible.extend([f"p={p}" for p in bad_p])
            flags.append(DataFingerprintFlag(
                flag_type   = "impossible_p_value",
                severity    = "high",
                description = (
                    f"{len(bad_p)} p-value(s) outside [0, 1]. "
                    f"These values cannot exist."
                ),
                evidence    = f"Invalid p-values: {bad_p}.",
                suggestion  = "Check analysis code for unit or scale errors.",
            ))

        return impossible

    def _check_suspicious_duplicates(
        self, fp: NumericFingerprint, flags: list
    ) -> list:
        """
        The same specific decimal value appearing 3+ times in a paper
        is unusual unless it is a threshold or constant.
        In fabricated data, a single invented number gets reused.
        """
        all_vals = fp.means + fp.std_devs + fp.percentages + fp.correlations
        if len(all_vals) < 6:
            return []

        counter    = Counter(all_vals)
        duplicates = [
            v for v, count in counter.items()
            if count >= 3 and v not in (0.0, 1.0, 0.5, 100.0, 0.05)
        ]

        if duplicates:
            flags.append(DataFingerprintFlag(
                flag_type   = "suspicious_value_repetition",
                severity    = "medium",
                description = (
                    f"{len(duplicates)} specific value(s) appear 3 or more "
                    f"times across different reported statistics. "
                    f"Genuine independent measurements rarely share "
                    f"exact decimal values."
                ),
                evidence    = (
                    f"Repeated values: "
                    f"{[round(v, 4) for v in duplicates[:5]]}."
                ),
                suggestion  = (
                    "Verify that repeated values reflect genuinely "
                    "identical measurements and are not copy-paste artifacts."
                ),
            ))

        return duplicates

    # ── helpers ────────────────────────────────────────────────────────────────

    def _count_total(self, fp: NumericFingerprint) -> int:
        return (
            len(fp.means) + len(fp.std_devs) + len(fp.sample_sizes) +
            len(fp.percentages) + len(fp.correlations) + len(fp.p_values)
        )

    # ── scoring ────────────────────────────────────────────────────────────────

    def _compute_score(
        self,
        round_ratio:   float,
        terminal_bias: float,
        impossible:    list,
        duplicates:    list,
        total:         int,
    ) -> float:
        if total == 0:
            return 0.0

        impossible_score = min(len(impossible) * 0.25, 1.0)
        duplicate_score  = min(len(duplicates) * 0.15, 1.0)

        score = (
            round_ratio      * 0.25 +
            terminal_bias    * 0.25 +
            impossible_score * 0.35 +
            duplicate_score  * 0.15
        )
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.25:   return "medium"
        return "low"

    def _write_summary(
        self, flags: list, risk_level: str, total: int
    ) -> str:
        if total == 0:
            return (
                "Data Fingerprint Analysis: No statistical values extracted. "
                "Include explicit M=, SD=, N=, r=, and p= reporting "
                f"for full analysis. Risk level: {risk_level.upper()}."
            )

        if not flags:
            return (
                f"Data Fingerprint Analysis: {total} statistical value(s) "
                f"analyzed. No fabrication signals detected. "
                f"Numerical patterns appear consistent with genuine data. "
                f"Risk level: {risk_level.upper()}."
            )

        high   = sum(1 for f in flags if f.severity == "high")
        medium = sum(1 for f in flags if f.severity == "medium")
        parts  = []
        if high:
            parts.append(
                f"{high} impossible value{'s' if high > 1 else ''} detected"
            )
        if medium:
            parts.append(
                f"{medium} fabrication signal{'s' if medium > 1 else ''} found"
            )

        return (
            f"Data Fingerprint Analysis: {total} value(s) analyzed. "
            f"{'; '.join(parts)}. "
            f"Risk level: {risk_level.upper()}."
        )