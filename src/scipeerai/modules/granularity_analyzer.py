import re
import math
from dataclasses import dataclass, field
from typing import List, Tuple


# ── Constants ─────────────────────────────────────────────────────────────────

BENFORD_EXPECTED = [
    math.log10(1 + 1 / d) for d in range(1, 10)
]

SUSPICIOUS_DECIMAL_THRESHOLD = 4   # > 4 decimal places is suspicious
EXTREME_DECIMAL_THRESHOLD    = 8   # > 8 decimal places is very suspicious
MIN_NUMBERS_FOR_BENFORD      = 4   # lowered from 5 for better sensitivity
ROUND_NUMBER_THRESHOLD       = 0.6


# ── Data classes ──────────────────────────────────────────────────────────────

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
    flags:                  List[GranularityFlag] = field(default_factory=list)
    flags_count:            int = 0
    suspicious_numbers:     List[str] = field(default_factory=list)
    extreme_precision:      List[str] = field(default_factory=list)


# ── Main class ────────────────────────────────────────────────────────────────

class GranularityAnalyzer:
    """
    Granularity Analyzer v2.3.4

    Applies Benford's Law and precision analysis to numeric data.
    Real measurements follow predictable digit distributions —
    fabricated data does not.

    v2.3.4 upgrades:
    - Raw string extraction preserves full decimal precision
    - Extreme precision detection (> 8 decimal places)
    - Lower Benford threshold (4 numbers instead of 5)
    - Suspicious precision threshold lowered (> 4 instead of > 5)
    - Terminal digit bias detection improved
    """

    def analyze(self, text: str) -> GranularityResult:
        raw_numbers, float_numbers = self._extract_numbers(text)
        flags:                List[GranularityFlag] = []
        suspicious_numbers:   List[str] = []
        extreme_precision:    List[str] = []

        # ── Check 1: Benford's Law ────────────────────────────────────────────
        benford_score, benford_flags = self._check_benford(
            float_numbers, raw_numbers
        )
        flags.extend(benford_flags)

        # ── Check 2: Round number clustering ─────────────────────────────────
        round_ratio, round_flags = self._check_round_numbers(
            float_numbers, raw_numbers
        )
        flags.extend(round_flags)

        # ── Check 3: Suspicious precision ────────────────────────────────────
        prec_score, prec_flags, suspicious_numbers, extreme_precision = (
            self._check_suspicious_precision(raw_numbers)
        )
        flags.extend(prec_flags)

        # ── Check 4: Terminal digit bias ──────────────────────────────────────
        digit_score, digit_flags = self._check_terminal_digit_bias(
            float_numbers, raw_numbers
        )
        flags.extend(digit_flags)

        # ── Aggregate score ───────────────────────────────────────────────────
        granularity_score = self._compute_score(
            benford_score, round_ratio, prec_score, digit_score
        )
        risk_level = self._get_risk_level(granularity_score)

        summary = (
            f"Granularity analysis of {len(raw_numbers)} numerical values. "
            f"Anomaly score: {round(granularity_score * 100)}%. "
            f"{len(flags)} granularity concern(s) detected. "
            f"Risk level: {risk_level.upper()}."
        )

        return GranularityResult(
            digit_preference_score = round(digit_score,       4),
            benford_score          = round(benford_score,      4),
            round_number_ratio     = round(round_ratio,        4),
            granularity_score      = round(granularity_score,  4),
            risk_level             = risk_level,
            summary                = summary,
            flags                  = flags,
            flags_count            = len(flags),
            suspicious_numbers     = suspicious_numbers,
            extreme_precision      = extreme_precision,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _extract_numbers(self, text: str) -> Tuple[List[str], List[float]]:
        """
        v2.3.4 — Extract numbers preserving full raw string.
        Raw strings are used for precision checking.
        Float values are used for Benford and round-number checks.
        """
        # Raw string extraction — keeps full decimal precision
        raw_pattern = re.compile(r'\b(\d+\.\d+|\d+)\b')
        raw_numbers = raw_pattern.findall(text)

        float_numbers = []
        for r in raw_numbers:
            try:
                float_numbers.append(float(r))
            except ValueError:
                pass

        return raw_numbers, float_numbers

    def _check_benford(
        self, float_numbers: List[float], raw_numbers: List[str]
    ) -> Tuple[float, List[GranularityFlag]]:
        """Apply Benford's Law to first-digit distribution."""
        flags = []

        positives = [n for n in float_numbers if n > 0]
        if len(positives) < MIN_NUMBERS_FOR_BENFORD:
            return 0.0, flags

        first_digits = []
        for n in positives:
            s = str(n).lstrip('0').replace('.', '')
            if s and s[0].isdigit() and s[0] != '0':
                first_digits.append(int(s[0]))

        if not first_digits:
            return 0.0, flags

        observed = [
            first_digits.count(d) / len(first_digits)
            for d in range(1, 10)
        ]

        deviation = sum(
            abs(o - e) for o, e in zip(observed, BENFORD_EXPECTED)
        ) / 9

        if deviation > 0.15:
            flags.append(GranularityFlag(
                flag_type   = "benford_violation",
                severity    = "high" if deviation > 0.25 else "medium",
                description = (
                    f"First-digit distribution deviates from Benford's Law "
                    f"(deviation: {round(deviation, 3)}). "
                    f"Natural data follows Benford's Law — fabricated numbers often do not."
                ),
                evidence    = (
                    f"Benford deviation: {round(deviation, 3)} "
                    f"(threshold: 0.15) | "
                    f"Numbers analyzed: {len(positives)}"
                ),
                suggestion  = (
                    "Verify all reported numeric values against raw data. "
                    "Large Benford deviations are a validated fraud signal."
                ),
            ))

        return round(deviation, 4), flags

    def _check_round_numbers(
        self, float_numbers: List[float], raw_numbers: List[str]
    ) -> Tuple[float, List[GranularityFlag]]:
        """Detect suspicious clustering of round numbers."""
        flags = []

        if not float_numbers:
            return 0.0, flags

        round_count = sum(
            1 for n in float_numbers
            if n > 0 and n == int(n) and int(n) % 5 == 0
        )
        round_ratio = round_count / len(float_numbers)

        if round_ratio > ROUND_NUMBER_THRESHOLD:
            flags.append(GranularityFlag(
                flag_type   = "round_number_clustering",
                severity    = "medium",
                description = (
                    f"Unusually high proportion of round numbers detected "
                    f"({round(round_ratio * 100)}% of values). "
                    f"Real measurements rarely cluster at multiples of 5 or 10."
                ),
                evidence    = (
                    f"Round number ratio: {round(round_ratio, 3)} "
                    f"(threshold: {ROUND_NUMBER_THRESHOLD}) | "
                    f"Round values: {round_count}/{len(float_numbers)}"
                ),
                suggestion  = (
                    "Verify measurement precision. Report actual measured values "
                    "rather than rounded summaries."
                ),
            ))

        return round_ratio, flags

    def _check_suspicious_precision(
        self, raw_numbers: List[str]
    ) -> Tuple[float, List[GranularityFlag], List[str], List[str]]:
        """
        v2.3.4 — Detect suspicious decimal precision.
        Uses raw strings to preserve full decimal places.
        Flags > 4 decimal places as suspicious.
        Flags > 8 decimal places as extreme (likely fabricated/copy-pasted constants).
        """
        flags              = []
        suspicious         = []
        extreme            = []

        for raw in raw_numbers:
            if '.' not in raw:
                continue
            decimal_part = raw.split('.')[1]
            n_decimals   = len(decimal_part)

            if n_decimals > EXTREME_DECIMAL_THRESHOLD:
                extreme.append(raw)
            elif n_decimals > SUSPICIOUS_DECIMAL_THRESHOLD:
                suspicious.append(raw)

        score = 0.0

        if extreme:
            score = max(score, 0.80)
            flags.append(GranularityFlag(
                flag_type   = "extreme_precision",
                severity    = "high",
                description = (
                    f"{len(extreme)} value(s) with extreme decimal precision "
                    f"(> {EXTREME_DECIMAL_THRESHOLD} decimal places). "
                    f"This level of precision is physically impossible for most "
                    f"real measurements and suggests copy-pasted constants or fabricated data."
                ),
                evidence    = (
                    f"Extreme precision values: "
                    f"{', '.join(extreme[:5])}"
                    f"{'...' if len(extreme) > 5 else ''}"
                ),
                suggestion  = (
                    "Real measurements should be reported to appropriate significant figures. "
                    "Values with > 8 decimal places are almost always mathematical constants "
                    "or fabricated numbers."
                ),
            ))

        if suspicious and not extreme:
            score = max(score, 0.35)
            flags.append(GranularityFlag(
                flag_type   = "suspicious_precision",
                severity    = "medium",
                description = (
                    f"{len(suspicious)} value(s) with unusually high decimal precision "
                    f"(> {SUSPICIOUS_DECIMAL_THRESHOLD} decimal places). "
                    f"Verify that reported precision matches measurement instrument capability."
                ),
                evidence    = (
                    f"High-precision values: "
                    f"{', '.join(suspicious[:5])}"
                    f"{'...' if len(suspicious) > 5 else ''}"
                ),
                suggestion  = (
                    "Report values to the precision of your measurement instrument. "
                    "Excess precision may indicate data manipulation."
                ),
            ))

        return score, flags, suspicious, extreme

    def _check_terminal_digit_bias(
        self, float_numbers: List[float], raw_numbers: List[str]
    ) -> Tuple[float, List[GranularityFlag]]:
        """
        Detect terminal digit bias.
        Humans fabricating data tend to prefer certain digits (0, 5)
        as the last digit of reported values.
        """
        flags = []

        terminal_digits = []
        for raw in raw_numbers:
            clean = raw.replace('.', '').rstrip('0')
            if clean and clean[-1].isdigit():
                terminal_digits.append(int(clean[-1]))

        if len(terminal_digits) < MIN_NUMBERS_FOR_BENFORD:
            return 0.0, flags

        zero_five_count = terminal_digits.count(0) + terminal_digits.count(5)
        zero_five_ratio = zero_five_count / len(terminal_digits)
        expected_ratio  = 0.20  # random expectation: 2/10 digits are 0 or 5

        if zero_five_ratio > 0.50:
            score = min((zero_five_ratio - expected_ratio) / 0.80, 1.0)
            flags.append(GranularityFlag(
                flag_type   = "terminal_digit_bias",
                severity    = "medium" if zero_five_ratio < 0.70 else "high",
                description = (
                    f"Terminal digit bias detected: "
                    f"{round(zero_five_ratio * 100)}% of values end in 0 or 5 "
                    f"(expected ~20% by chance). "
                    f"Humans fabricating data disproportionately choose round endings."
                ),
                evidence    = (
                    f"Zero/five terminal digit ratio: {round(zero_five_ratio, 3)} "
                    f"(expected: {expected_ratio}) | "
                    f"Digits analyzed: {len(terminal_digits)}"
                ),
                suggestion  = (
                    "Verify all reported values against raw measurement records. "
                    "Terminal digit bias is a validated data fabrication signal."
                ),
            ))
            return round(score, 4), flags

        return 0.0, flags

    def _compute_score(
        self,
        benford_score: float,
        round_ratio:   float,
        prec_score:    float,
        digit_score:   float,
    ) -> float:
        round_component = min(
            max(round_ratio - ROUND_NUMBER_THRESHOLD, 0) / (1 - ROUND_NUMBER_THRESHOLD),
            1.0
        )
        score = (
            benford_score   * 0.30 +
            round_component * 0.20 +
            prec_score      * 0.30 +
            digit_score     * 0.20
        )
        return min(round(score, 4), 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.70:   return "critical"
        if score >= 0.45:   return "high"
        if score >= 0.20:   return "medium"
        return "low"