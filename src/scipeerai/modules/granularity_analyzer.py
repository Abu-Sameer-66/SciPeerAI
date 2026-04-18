# src/scipeerai/modules/granularity_analyzer.py
#
# Statistical Granularity Analyzer
# Detects: digit preference, too-perfect variance,
# Benford's Law violations, suspiciously round numbers.
#
# Fabricated data tends to look "too clean" —
# real data has natural messiness. This module
# catches papers where numbers look manufactured.

import re
import math
import collections
from dataclasses import dataclass, field


@dataclass
class GranularityFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class GranularityResult:
    digit_preference_score: float
    benford_score:          float
    round_number_ratio:     float
    granularity_score:      float
    risk_level:             str
    summary:                str
    flags:                  list = field(default_factory=list)
    flags_count:            int  = 0


class GranularityAnalyzer:
    """
    Statistical Granularity Analyzer.
    Real data has natural digit distribution.
    Fabricated data shows digit preference (e.g. too many 0s and 5s)
    and first-digit anomalies (Benford's Law violations).
    """

    # extract all decimal numbers from text
    NUMBER_PAT  = re.compile(r'\b\d+\.\d+\b')
    INTEGER_PAT = re.compile(r'\b\d{2,}\b')

    # Benford's Law expected first-digit distribution
    BENFORD_EXPECTED = {
        1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
        5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
    }

    def analyze(self, text: str) -> GranularityResult:
        decimals = [float(x) for x in self.NUMBER_PAT.findall(text)]
        integers = [int(x)   for x in self.INTEGER_PAT.findall(text)
                    if 10 <= int(x) <= 99999]
        all_nums = decimals + [float(x) for x in integers]

        flags = []

        # ── 1. Digit Preference ───────────────────────────────────
        dp_score, dp_flag = self._digit_preference(decimals)
        if dp_flag:
            flags.append(dp_flag)

        # ── 2. Benford's Law ──────────────────────────────────────
        bf_score, bf_flag = self._benford_check(all_nums)
        if bf_flag:
            flags.append(bf_flag)

        # ── 3. Round Number Ratio ─────────────────────────────────
        rn_ratio, rn_flag = self._round_number_check(decimals)
        if rn_flag:
            flags.append(rn_flag)

        # ── 4. Too-Perfect Variance ───────────────────────────────
        tp_flag = self._too_perfect_check(decimals)
        if tp_flag:
            flags.append(tp_flag)

        # ── Aggregate Score ───────────────────────────────────────
        components = [dp_score, bf_score, rn_ratio]
        score      = round(sum(components) / len(components), 4)
        level      = self._risk(score, len(flags))
        summary    = self._build_summary(score, level, len(flags), len(decimals))

        return GranularityResult(
            digit_preference_score = round(dp_score, 4),
            benford_score          = round(bf_score, 4),
            round_number_ratio     = round(rn_ratio, 4),
            granularity_score      = score,
            risk_level             = level,
            summary                = summary,
            flags                  = flags,
            flags_count            = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _digit_preference(self, numbers: list):
        """
        Check last digits of decimal numbers.
        Real data: uniform distribution across 0-9.
        Fabricated data: too many 0s and 5s.
        """
        if len(numbers) < 5:
            return 0.0, None

        last_digits = []
        for n in numbers:
            s = str(n)
            if '.' in s:
                last_digits.append(int(s[-1]))

        if not last_digits:
            return 0.0, None

        counts    = collections.Counter(last_digits)
        total     = len(last_digits)
        zero_five = (counts.get(0, 0) + counts.get(5, 0)) / total
        expected  = 0.2  # 2 out of 10 digits

        score = min((zero_five - expected) / 0.4, 1.0) if zero_five > expected else 0.0
        score = max(score, 0.0)

        if zero_five > 0.45:
            return score, GranularityFlag(
                flag_type   = "digit_preference_detected",
                severity    = "high" if zero_five > 0.6 else "medium",
                description = (
                    f"Unusual digit preference detected. "
                    f"{round(zero_five * 100)}% of decimal values end in "
                    f"0 or 5 — expected ~20% in real data. "
                    f"Suggests manually entered or rounded values."
                ),
                evidence    = (
                    f"Last-digit analysis: {round(zero_five * 100)}% "
                    f"end in 0 or 5 (expected: ~20%) | "
                    f"Sample: {last_digits[:10]}"
                ),
                suggestion  = (
                    "Report raw unrounded values. Verify that "
                    "data was not manually entered or post-hoc rounded."
                ),
            )
        return score, None

    def _benford_check(self, numbers: list):
        """
        Benford's Law: first digits of naturally occurring
        numbers follow a logarithmic distribution.
        Violations suggest fabrication.
        """
        valid = [n for n in numbers if n >= 1]
        if len(valid) < 10:
            return 0.0, None

        first_digits = [int(str(abs(n)).replace('.', '')[0])
                        for n in valid if str(abs(n)).replace('.', '')[0] != '0']
        if not first_digits:
            return 0.0, None

        counts = collections.Counter(first_digits)
        total  = len(first_digits)

        # Chi-square distance from Benford
        chi_sq = 0.0
        for d in range(1, 10):
            observed = counts.get(d, 0) / total
            expected = self.BENFORD_EXPECTED[d]
            chi_sq  += ((observed - expected) ** 2) / expected

        # normalize to 0-1
        score = min(chi_sq / 15.0, 1.0)

        if score > 0.4:
            return score, GranularityFlag(
                flag_type   = "benford_law_violation",
                severity    = "high" if score > 0.7 else "medium",
                description = (
                    f"First-digit distribution deviates from Benford's Law. "
                    f"Naturally occurring datasets follow a predictable "
                    f"logarithmic distribution — deviation suggests "
                    f"non-natural or fabricated data."
                ),
                evidence    = (
                    f"Chi-square deviation: {round(chi_sq, 3)} "
                    f"(threshold: 6.0) | "
                    f"First digits analyzed: {total}"
                ),
                suggestion  = (
                    "Verify data collection process. Large Benford "
                    "violations in financial or count data are a "
                    "strong fabrication signal."
                ),
            )
        return score, None

    def _round_number_check(self, numbers: list):
        """
        Too many round numbers (X.0, X.00) suggests
        manual entry or fabrication.
        """
        if len(numbers) < 5:
            return 0.0, None

        round_count = sum(1 for n in numbers
                          if abs(n - round(n)) < 0.001)
        ratio = round_count / len(numbers)

        if ratio > 0.6:
            return ratio, GranularityFlag(
                flag_type   = "excessive_round_numbers",
                severity    = "medium",
                description = (
                    f"{round(ratio * 100)}% of reported decimal values "
                    f"are whole numbers (X.0). Real measurement data "
                    f"rarely produces this pattern — suggests rounding "
                    f"or manual data entry."
                ),
                evidence    = (
                    f"{round_count}/{len(numbers)} values are "
                    f"whole numbers ({round(ratio * 100)}%)"
                ),
                suggestion  = (
                    "Report values to appropriate decimal precision. "
                    "Avoid post-hoc rounding of raw measurements."
                ),
            )
        return ratio, None

    def _too_perfect_check(self, numbers: list):
        """
        If all reported values have identical decimal precision,
        this is suspicious — real data has natural variation.
        """
        if len(numbers) < 6:
            return None

        precisions = []
        for n in numbers:
            s = str(n)
            if '.' in s:
                precisions.append(len(s.split('.')[1]))

        if not precisions:
            return None

        unique_precisions = len(set(precisions))
        if unique_precisions == 1 and len(precisions) >= 6:
            p = precisions[0]
            return GranularityFlag(
                flag_type   = "uniform_decimal_precision",
                severity    = "medium",
                description = (
                    f"All {len(precisions)} decimal values reported to "
                    f"exactly {p} decimal place(s). Real measurement "
                    f"data rarely has perfectly uniform precision — "
                    f"suggests post-processing or fabrication."
                ),
                evidence    = (
                    f"All values use exactly {p} decimal place(s) | "
                    f"Count: {len(precisions)}"
                ),
                suggestion  = (
                    "Report values at their natural precision. "
                    "Verify that uniform rounding was not applied."
                ),
            )
        return None

    def _risk(self, score: float, flag_count: int) -> str:
        if flag_count >= 3 or score >= 0.6:
            return "critical"
        if flag_count == 2 or score >= 0.4:
            return "high"
        if flag_count == 1 or score >= 0.2:
            return "medium"
        return "low"

    def _build_summary(self, score: float, level: str,
                       flag_count: int, num_count: int) -> str:
        if num_count < 5:
            return (
                "Granularity Analysis: Insufficient numerical data "
                "for full analysis (minimum 5 decimal values required)."
            )
        pct = round(score * 100)
        return (
            f"Granularity analysis of {num_count} numerical values. "
            f"Anomaly score: {pct}%. "
            f"{flag_count} granularity concern(s) detected. "
            f"Risk level: {level.upper()}."
        )