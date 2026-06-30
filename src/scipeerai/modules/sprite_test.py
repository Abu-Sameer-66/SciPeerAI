# src/scipeerai/modules/sprite_test.py
#
# SPRITE Test â€” Sample Parameter Reconstruction via Iterative Techniques
# Based on: Heathers & Brown (2019)
#
# GRIM checks if a mean is possible.
# SPRITE checks if a mean AND standard deviation are
# simultaneously possible given N and scale bounds.
# Catches fabricated datasets that pass GRIM alone.

import re
import math
import itertools
from dataclasses import dataclass, field


@dataclass
class SpriteFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class SpriteResult:
    impossible_combinations: list
    possible_combinations:   list
    sprite_score:            float
    risk_level:              str
    summary:                 str
    flags:                   list = field(default_factory=list)
    flags_count:             int  = 0


class SpriteTest:
    """
    SPRITE Test implementation.
    Reconstructs possible integer distributions and checks
    whether reported mean + SD are jointly achievable.
    """

    # matches: mean=X, sd=Y, n=Z, scale=A-B
    MEAN_PAT  = re.compile(r'(?:mean|m)\s*[=:]\s*(-?\d+\.\d+)', re.I)
    SD_PAT    = re.compile(r'(?:sd|std|s\.d\.)\s*[=:]\s*(\d+\.\d+)', re.I)
    N_PAT     = re.compile(r'\bn\s*[=:]\s*(\d+)', re.I)
    SCALE_PAT = re.compile(r'(?:scale|range)\s*[=:]\s*(\d+)\s*[-â€“]\s*(\d+)', re.I)

    # max N to attempt full reconstruction â€” above this use sampling
    RECONSTRUCTION_LIMIT = 12

    def analyze(self, text: str) -> SpriteResult:
        groups     = self._extract_groups(text)
        impossible = []
        possible   = []
        flags      = []

        for g in groups:
            mean, sd, n, lo, hi = g
            ok = self._sprite_check(mean, sd, n, lo, hi)
            if ok:
                possible.append(g)
            else:
                impossible.append(g)
                flags.append(SpriteFlag(
                    flag_type   = "sprite_impossible_distribution",
                    severity    = "high",
                    description = (
                        f"No integer distribution exists that produces "
                        f"M={mean}, SD={sd} with N={n} on a {lo}-{hi} scale. "
                        f"The reported statistics are mathematically "
                        f"inconsistent â€” potential data fabrication."
                    ),
                    evidence    = (
                        f"M={mean}, SD={sd}, N={n}, Scale={lo}-{hi} | "
                        f"Exhaustive reconstruction failed."
                    ),
                    suggestion  = (
                        "Re-verify raw data. Recalculate mean and SD "
                        "from original scores. Check scale bounds and "
                        "sample size reporting."
                    ),
                ))

        total  = len(impossible) + len(possible)
        score  = (len(impossible) / total) if total > 0 else 0.0
        level  = self._risk(score, len(impossible))
        summary = self._build_summary(impossible, possible, score, level)

        return SpriteResult(
            impossible_combinations = impossible,
            possible_combinations   = possible,
            sprite_score            = round(score, 4),
            risk_level              = level,
            summary                 = summary,
            flags                   = flags,
            flags_count             = len(flags),
        )

    # â”€â”€ internal helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _sprite_check(self, mean: float, sd: float,
                      n: int, lo: int, hi: int) -> bool:
        """
        Core SPRITE logic.
        For small N: exhaustive search over all integer distributions.
        For large N: use variance bounds check (fast approximation).
        """
        if n > self.RECONSTRUCTION_LIMIT:
            return self._variance_bounds_check(mean, sd, n, lo, hi)
        return self._exhaustive_check(mean, sd, n, lo, hi)

    def _exhaustive_check(self, mean: float, sd: float,
                          n: int, lo: int, hi: int) -> bool:
        """Try all combinations of n integers in [lo, hi]."""
        target_sum = mean * n
        # only proceed if sum is near-integer (GRIM passes)
        if abs(target_sum - round(target_sum)) > 0.01:
            return False
        int_sum = round(target_sum)
        target_var = sd ** 2

        scale = list(range(lo, hi + 1))
        for combo in itertools.combinations_with_replacement(scale, n):
            if sum(combo) != int_sum:
                continue
            var = sum((x - mean) ** 2 for x in combo) / n
            if abs(math.sqrt(var) - sd) < 0.01:
                return True
        return False

    def _variance_bounds_check(self, mean: float, sd: float,
                               n: int, lo: int, hi: int) -> bool:
        """
        Fast check for large N.
        Checks both max and min possible SD for given mean and scale.
        v2.3.2: Added minimum SD check for suspicious near-zero SDs.
        """
        if hi == lo:
            return sd < 0.01
        p = (mean - lo) / (hi - lo)
        max_var = p * (1 - p) * (hi - lo) ** 2
        max_sd  = math.sqrt(max_var)
        if sd > max_sd + 0.05:
            return False
        scale_range = hi - lo
        min_reasonable_sd = scale_range / (2.0 * math.sqrt(n))
        if sd < min_reasonable_sd * 0.3 and n >= 10:
            return False
        return True

    def _extract_groups(self, text: str):
        """Extract (mean, sd, n, scale_lo, scale_hi) tuples."""
        groups = []
        means  = [(m.start(), float(m.group(1))) for m in self.MEAN_PAT.finditer(text)]
        sds    = [(m.start(), float(m.group(1))) for m in self.SD_PAT.finditer(text)]
        ns     = [(m.start(), int(m.group(1)))   for m in self.N_PAT.finditer(text)]
        scales = [(m.start(), int(m.group(1)), int(m.group(2)))
                  for m in self.SCALE_PAT.finditer(text)]

        if not (means and sds and ns):
            return groups

        # default scale if not found
        default_lo, default_hi = 1, 7

        for (mp, mean), (sp, sd) in zip(means, sds):
            # find closest n
            if not ns:
                continue
            n_pos, n_val = min(ns, key=lambda x: abs(x[0] - mp))
            if n_val < 2 or n_val > 500:
                continue
            # find closest scale
            if scales:
                _, lo, hi = min(scales, key=lambda x: abs(x[0] - mp))
            else:
                lo, hi = default_lo, default_hi
            groups.append((mean, sd, n_val, lo, hi))

        return groups

    def _risk(self, score: float, count: int) -> str:
        if count >= 2 or score >= 0.6:
            return "critical"
        if count == 1 or score >= 0.3:
            return "high"
        if score >  0:
            return "medium"
        return "low"

    def _build_summary(self, impossible, possible,
                       score, level) -> str:
        total = len(impossible) + len(possible)
        if total == 0:
            return (
                "SPRITE Test: No mean/SD/N groups detected. "
                "Include M=, SD=, N= and scale=X-Y for analysis."
            )
        pct = round(score * 100)
        return (
            f"SPRITE Test analyzed {total} mean/SD/N group(s). "
            f"{len(impossible)} impossible distribution(s) detected "
            f"({pct}% failure rate). "
            f"Risk level: {level.upper()}."
        )