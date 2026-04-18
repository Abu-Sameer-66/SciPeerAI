# src/scipeerai/modules/grim_test.py
#
# GRIM Test — Granularity-Related Inconsistency of Means
# Based on: Brown & Heathers (2017), Social Psychological
# and Personality Science — scientifically validated.
#
# Catches mathematically impossible means given sample size.
# Example: mean=2.34 with n=20 is IMPOSSIBLE.

import re
import math
from dataclasses import dataclass, field


@dataclass
class GrimFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class GrimResult:
    impossible_means:     list
    possible_means:       list
    grim_score:           float
    risk_level:           str
    summary:              str
    flags:                list = field(default_factory=list)
    flags_count:          int  = 0


class GrimTest:
    """
    GRIM Test implementation.
    Checks whether reported means are mathematically
    possible given the reported sample size and scale.
    """

    # regex to pull mean/average + sample size pairs
    MEAN_PATTERN = re.compile(
        r'(?:mean|average|m)\s*[=:]\s*(-?\d+\.?\d*)',
        re.IGNORECASE
    )
    N_PATTERN = re.compile(
        r'n\s*[=:]\s*(\d+)',
        re.IGNORECASE
    )
    FULL_PATTERN = re.compile(
        r'(?:mean|average|m)\s*[=:]\s*(-?\d+\.\d+)'
        r'.{0,80}'
        r'n\s*[=:]\s*(\d+)'
        r'|'
        r'n\s*[=:]\s*(\d+)'
        r'.{0,80}'
        r'(?:mean|average|m)\s*[=:]\s*(-?\d+\.\d+)',
        re.IGNORECASE
    )

    def analyze(self, text: str) -> GrimResult:
        pairs        = self._extract_pairs(text)
        impossible   = []
        possible     = []
        flags        = []

        for mean_val, n_val in pairs:
            ok = self._grim_check(mean_val, n_val)
            if ok:
                possible.append((mean_val, n_val))
            else:
                impossible.append((mean_val, n_val))
                flags.append(GrimFlag(
                    flag_type   = "grim_impossible_mean",
                    severity    = "high",
                    description = (
                        f"Mean={mean_val} is mathematically "
                        f"impossible with N={n_val}. "
                        f"This value cannot arise from integer "
                        f"item scores — potential data fabrication."
                    ),
                    evidence    = (
                        f"Reported: M={mean_val}, N={n_val} | "
                        f"Closest valid means: "
                        f"{self._nearest_valid(mean_val, n_val)}"
                    ),
                    suggestion  = (
                        "Re-check raw data and recalculate. "
                        "If using Likert scales, verify item "
                        "scoring and sample size."
                    ),
                ))

        total     = len(impossible) + len(possible)
        score     = (len(impossible) / total) if total > 0 else 0.0
        level     = self._risk(score, len(impossible))
        summary   = self._build_summary(
            impossible, possible, score, level
        )

        return GrimResult(
            impossible_means = impossible,
            possible_means   = possible,
            grim_score       = round(score, 4),
            risk_level       = level,
            summary          = summary,
            flags            = flags,
            flags_count      = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _grim_check(self, mean: float, n: int) -> bool:
        """
        Core GRIM logic.
        A mean is possible iff (mean * n) rounds to an integer.
        Tolerance: 0.001 to handle floating-point noise.
        """
        product   = mean * n
        remainder = abs(product - round(product))
        return remainder < 0.001

    def _extract_pairs(self, text: str):
        pairs = []
        for m in self.FULL_PATTERN.finditer(text):
            if m.group(1) and m.group(2):
                mean_val = float(m.group(1))
                n_val    = int(m.group(2))
            else:
                mean_val = float(m.group(4))
                n_val    = int(m.group(3))
            if 2 <= n_val <= 10000:
                pairs.append((mean_val, n_val))
        return pairs

    def _nearest_valid(self, mean: float, n: int) -> str:
        decimals = len(str(mean).split(".")[-1])
        step     = round(1 / n, decimals + 2)
        lower    = math.floor(mean * n) / n
        upper    = math.ceil(mean * n)  / n
        return f"{round(lower, decimals)} or {round(upper, decimals)}"

    def _risk(self, score: float, count: int) -> str:
        if count >= 3 or score >= 0.6:
            return "critical"
        if count == 2 or score >= 0.4:
            return "high"
        if count == 1 or score >= 0.2:
            return "medium"
        return "low"

    def _build_summary(self, impossible, possible,
                       score, level) -> str:
        total = len(impossible) + len(possible)
        if total == 0:
            return (
                "GRIM Test: No mean/N pairs detected in text. "
                "Add explicit M= and N= values for analysis."
            )
        pct = round(score * 100)
        return (
            f"GRIM Test analyzed {total} mean/N pair(s). "
            f"{len(impossible)} impossible mean(s) detected "
            f"({pct}% failure rate). "
            f"Risk level: {level.upper()}."
        )