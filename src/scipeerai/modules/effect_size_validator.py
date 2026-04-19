# src/scipeerai/modules/effect_size_validator.py
#
# Effect Size Validator
# Extracts and validates Cohen's d, r, eta-squared,
# odds ratios, and performs post-hoc power analysis.
#
# Small N + large effect size = fabrication signal.
# Underpowered studies with significant results = suspect.

import re
import math
from dataclasses import dataclass, field


@dataclass
class EffectSizeFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class EffectSizeResult:
    effect_sizes_found:  list
    power_estimates:     list
    inflated_effects:    list
    underpowered:        list
    effect_score:        float
    risk_level:          str
    summary:             str
    flags:               list = field(default_factory=list)
    flags_count:         int  = 0


class EffectSizeValidator:
    """
    Effect Size Validator.
    Validates reported effect sizes against sample sizes.
    Detects inflated effects and underpowered studies.

    Key insight:
    - Real large effects (d>0.8) need N>50 to be credible
    - Small N + large effect = likely false positive
    - Significant result + low power = suspicious
    """

    # Cohen's d pattern
    COHENS_D = re.compile(
        r"cohen['\s]?s?\s*d\s*[=:]\s*(-?\d+\.?\d*)",
        re.IGNORECASE
    )
    # Pearson r
    PEARSON_R = re.compile(
        r"\br\s*[=:]\s*(-?0?\.\d+)",
        re.IGNORECASE
    )
    # Eta squared
    ETA_SQ = re.compile(
        r"eta[²2\s-]*squared?\s*[=:]\s*(0?\.\d+)",
        re.IGNORECASE
    )
    # Omega squared
    OMEGA_SQ = re.compile(
        r"omega[²2\s-]*squared?\s*[=:]\s*(0?\.\d+)",
        re.IGNORECASE
    )
    # Odds ratio
    ODDS_R = re.compile(
        r"odds\s*ratio\s*[=:]\s*(\d+\.?\d*)",
        re.IGNORECASE
    )
    # Sample size
    N_PAT = re.compile(
        r"\bn\s*[=:]\s*(\d+)",
        re.IGNORECASE
    )

    # Cohen's benchmarks
    COHENS_BENCHMARKS = {
        "small":  0.2,
        "medium": 0.5,
        "large":  0.8,
    }

    def analyze(self, text: str) -> EffectSizeResult:
        effects   = self._extract_effects(text)
        ns        = self._extract_ns(text)
        n_val     = min(ns) if ns else None

        flags          = []
        inflated       = []
        underpowered   = []
        power_ests     = []

        for etype, evalue in effects:
            # ── Power estimation ──────────────────────────────────
            if n_val and etype == "cohens_d":
                power = self._estimate_power(evalue, n_val)
                power_ests.append({
                    "effect_type":  etype,
                    "effect_value": evalue,
                    "n":            n_val,
                    "power":        round(power, 3),
                })

                # ── Flag: inflated effect size ─────────────────────
                if abs(evalue) > 2.0 and n_val < 30:
                    inflated.append((etype, evalue, n_val))
                    flags.append(EffectSizeFlag(
                        flag_type   = "inflated_effect_size",
                        severity    = "high",
                        description = (
                            f"Cohen's d = {evalue} is extremely large "
                            f"with only N = {n_val}. Effect sizes above "
                            f"d = 2.0 with small samples are rarely "
                            f"genuine — likely reflects noise, "
                            f"outliers, or fabrication."
                        ),
                        evidence    = (
                            f"Cohen's d = {evalue}, N = {n_val} | "
                            f"Expected power: {round(power*100)}% | "
                            f"Cohen's large effect benchmark: d = 0.8"
                        ),
                        suggestion  = (
                            "Report confidence intervals for effect "
                            "sizes. Conduct sensitivity analysis. "
                            "Verify no outliers are driving the effect."
                        ),
                    ))

                # ── Flag: underpowered study ───────────────────────
                elif power < 0.8 and n_val < 50:
                    underpowered.append((etype, evalue, n_val, power))
                    flags.append(EffectSizeFlag(
                        flag_type   = "underpowered_study",
                        severity    = "medium",
                        description = (
                            f"Study is underpowered (estimated power = "
                            f"{round(power*100)}%). With N = {n_val} and "
                            f"d = {evalue}, there is only a "
                            f"{round(power*100)}% chance of detecting "
                            f"a real effect. Significant results from "
                            f"underpowered studies are likely false positives."
                        ),
                        evidence    = (
                            f"Cohen's d = {evalue}, N = {n_val} | "
                            f"Estimated power = {round(power*100)}% "
                            f"(recommended minimum: 80%)"
                        ),
                        suggestion  = (
                            "Conduct a priori power analysis. "
                            "Increase sample size to achieve 80% power. "
                            "Report power analysis in methods section."
                        ),
                    ))

            # ── Flag: impossible r value ───────────────────────────
            if etype == "pearson_r" and abs(evalue) > 1.0:
                flags.append(EffectSizeFlag(
                    flag_type   = "impossible_correlation",
                    severity    = "high",
                    description = (
                        f"Pearson r = {evalue} is impossible — "
                        f"correlations must be between -1 and 1. "
                        f"This indicates a reporting error or fabrication."
                    ),
                    evidence    = f"r = {evalue} reported",
                    suggestion  = (
                        "Verify raw correlation values. "
                        "Check if r² was mistakenly reported as r."
                    ),
                ))

            # ── Flag: suspiciously large eta squared ──────────────
            if etype == "eta_squared" and evalue > 0.5:
                flags.append(EffectSizeFlag(
                    flag_type   = "large_eta_squared",
                    severity    = "medium",
                    description = (
                        f"Eta-squared = {evalue} is unusually large. "
                        f"Values above 0.5 are rare in behavioral and "
                        f"social science research and warrant scrutiny."
                    ),
                    evidence    = f"η² = {evalue} (large effect threshold: 0.14)",
                    suggestion  = (
                        "Report partial eta-squared separately. "
                        "Verify ANOVA calculations and degrees of freedom."
                    ),
                ))

        # ── Flag: no effect sizes reported ────────────────────────
        if len(effects) == 0:
            flags.append(EffectSizeFlag(
                flag_type   = "missing_effect_sizes",
                severity    = "medium",
                description = (
                    "No effect sizes reported in the paper. "
                    "Effect sizes (Cohen's d, r, eta-squared) are "
                    "essential for interpreting practical significance "
                    "and are required by most major journals."
                ),
                evidence    = "No Cohen's d, r, or eta-squared found",
                suggestion  = (
                    "Report effect sizes with confidence intervals "
                    "for all primary outcomes. Use Cohen's d for "
                    "mean differences, r for correlations."
                ),
            ))

        score   = self._aggregate_score(inflated, underpowered, effects)
        level   = self._risk(score, len(inflated), len(underpowered))
        summary = self._build_summary(
            effects, inflated, underpowered, score, level
        )

        return EffectSizeResult(
            effect_sizes_found = effects,
            power_estimates    = power_ests,
            inflated_effects   = inflated,
            underpowered       = underpowered,
            effect_score       = round(score, 4),
            risk_level         = level,
            summary            = summary,
            flags              = flags,
            flags_count        = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _extract_effects(self, text: str) -> list:
        effects = []
        for m in self.COHENS_D.finditer(text):
            try:
                effects.append(("cohens_d", float(m.group(1))))
            except ValueError:
                pass
        for m in self.PEARSON_R.finditer(text):
            try:
                v = float(m.group(1))
                if -1.5 <= v <= 1.5:
                    effects.append(("pearson_r", v))
            except ValueError:
                pass
        for m in self.ETA_SQ.finditer(text):
            try:
                effects.append(("eta_squared", float(m.group(1))))
            except ValueError:
                pass
        for m in self.OMEGA_SQ.finditer(text):
            try:
                effects.append(("omega_squared", float(m.group(1))))
            except ValueError:
                pass
        for m in self.ODDS_R.finditer(text):
            try:
                v = float(m.group(1))
                if 0.1 <= v <= 50:
                    effects.append(("odds_ratio", v))
            except ValueError:
                pass
        return effects

    def _extract_ns(self, text: str) -> list:
        ns = []
        for m in self.N_PAT.finditer(text):
            try:
                v = int(m.group(1))
                if 2 <= v <= 100000:
                    ns.append(v)
            except ValueError:
                pass
        return ns

    def _estimate_power(self, d: float, n: int) -> float:
        """
        Approximate statistical power for two-sample t-test.
        Uses normal approximation of non-central t distribution.
        """
        try:
            ncp   = abs(d) * math.sqrt(n / 2)
            power = 1 - self._normal_cdf(1.96 - ncp)
            return min(max(power, 0.0), 1.0)
        except Exception:
            return 0.5

    def _normal_cdf(self, x: float) -> float:
        """Approximation of standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def _aggregate_score(self, inflated, underpowered,
                         effects) -> float:
        if not effects:
            return 0.3
        score = 0.0
        if inflated:
            score += 0.5 * min(len(inflated), 2) / 2
        if underpowered:
            score += 0.3 * min(len(underpowered), 2) / 2
        return min(score, 1.0)

    def _risk(self, score: float,
              n_inflated: int,
              n_underpowered: int) -> str:
        if n_inflated >= 1 or score >= 0.6:
            return "critical"
        if n_underpowered >= 2 or score >= 0.4:
            return "high"
        if n_underpowered >= 1 or score >= 0.2:
            return "medium"
        return "low"

    def _build_summary(self, effects, inflated,
                       underpowered, score, level) -> str:
        if not effects:
            return (
                "Effect Size Validation: No effect sizes detected. "
                "Cohen's d, r, or eta-squared reporting is recommended "
                "for all primary outcomes. Risk level: MEDIUM."
            )
        pct = round(score * 100)
        return (
            f"Effect Size Validator analyzed {len(effects)} effect "
            f"size(s). {len(inflated)} inflated, "
            f"{len(underpowered)} underpowered study/studies detected. "
            f"Overall risk score: {pct}%. "
            f"Risk level: {level.upper()}."
        )