# src/scipeerai/modules/pcurve_analyzer.py
#
# P-Curve Analyzer
# Detects publication bias by analyzing p-value distribution.
# Real effects: p-values uniformly distributed 0.00-0.05
# P-hacking:   p-values cluster just below 0.05
#
# Based on Simonsohn, Nelson & Simmons (2014)
# Published in Journal of Experimental Psychology

import re
import math
from dataclasses import dataclass, field


@dataclass
class PCurveFlag:
    flag_type:   str
    severity:    str
    description: str
    evidence:    str
    suggestion:  str


@dataclass
class PCurveResult:
    p_values_found:      list
    significant_p:       list
    right_skew_ratio:    float
    clustering_score:    float
    pcurve_score:        float
    risk_level:          str
    summary:             str
    flags:               list = field(default_factory=list)
    flags_count:         int  = 0


class PCurveAnalyzer:
    """
    P-Curve Analyzer.
    Analyzes distribution of p-values to detect
    publication bias and p-hacking patterns.

    Key insight:
    - Real effects → p-values RIGHT skewed (more near 0.01)
    - P-hacking    → p-values cluster near 0.05
    - No effect    → p-values uniformly distributed
    """

    P_PATTERN = re.compile(
        r'p\s*[=<>≤]\s*(0?\.\d+)',
        re.IGNORECASE
    )

    def analyze(self, text: str) -> PCurveResult:
        all_p     = self._extract_p_values(text)
        sig_p     = [p for p in all_p if p <= 0.05]
        flags     = []

        if len(sig_p) < 3:
            return PCurveResult(
                p_values_found   = all_p,
                significant_p    = sig_p,
                right_skew_ratio = 0.0,
                clustering_score = 0.0,
                pcurve_score     = 0.0,
                risk_level       = "low",
                summary          = (
                    f"P-Curve Analysis: {len(sig_p)} significant p-value(s) "
                    f"found. Minimum 3 required for curve analysis."
                ),
                flags      = [],
                flags_count= 0,
            )

        right_skew  = self._right_skew_ratio(sig_p)
        clustering  = self._clustering_score(sig_p)
        score       = self._aggregate_score(right_skew, clustering, sig_p)
        level       = self._risk(score, clustering, right_skew)

        # ── Flag 1: P-value clustering near 0.05 ─────────────────
        if clustering > 0.5:
            near_05 = sum(1 for p in sig_p if p >= 0.04)
            flags.append(PCurveFlag(
                flag_type   = "p_value_clustering",
                severity    = "high" if clustering > 0.7 else "medium",
                description = (
                    f"{near_05}/{len(sig_p)} significant p-values "
                    f"({round(near_05/len(sig_p)*100)}%) fall between "
                    f"0.040-0.050. This clustering pattern is the "
                    f"hallmark of p-hacking — results were likely "
                    f"manipulated to just reach significance."
                ),
                evidence    = (
                    f"Significant p-values: {[round(p,4) for p in sig_p]} | "
                    f"Near-0.05 ratio: {round(clustering*100)}%"
                ),
                suggestion  = (
                    "Pre-register hypotheses before data collection. "
                    "Report all tests conducted including non-significant. "
                    "Use sequential testing or Bayesian methods."
                ),
            ))

        # ── Flag 2: Lack of right skew (no real effect) ───────────
        if right_skew < 0.3 and len(sig_p) >= 4:
            flags.append(PCurveFlag(
                flag_type   = "flat_pcurve",
                severity    = "medium",
                description = (
                    f"P-curve lacks right skew — only {round(right_skew*100)}% "
                    f"of p-values fall below 0.025. A genuine effect "
                    f"produces a right-skewed p-curve. Flat curve suggests "
                    f"the findings may lack evidentiary value."
                ),
                evidence    = (
                    f"Right-skew ratio: {round(right_skew*100)}% "
                    f"(expected >50% for real effects) | "
                    f"P-values: {[round(p,4) for p in sig_p]}"
                ),
                suggestion  = (
                    "Conduct a power analysis. If the effect is real, "
                    "p-values should skew toward 0. Consider increasing "
                    "sample size for a more definitive test."
                ),
            ))

        # ── Flag 3: Too many exactly 0.05 values ──────────────────
        exact_05 = sum(1 for p in all_p if abs(p - 0.05) < 0.001)
        if exact_05 >= 2:
            flags.append(PCurveFlag(
                flag_type   = "exact_threshold_reporting",
                severity    = "medium",
                description = (
                    f"{exact_05} p-values reported as exactly p=0.05. "
                    f"This is statistically rare in real data and "
                    f"suggests threshold-seeking behavior or rounding."
                ),
                evidence    = (
                    f"{exact_05} values equal to exactly 0.050 found"
                ),
                suggestion  = (
                    "Report exact p-values to 3+ decimal places. "
                    "Avoid rounding to threshold values."
                ),
            ))

        summary = self._build_summary(
            all_p, sig_p, score, level,
            right_skew, clustering
        )

        return PCurveResult(
            p_values_found   = all_p,
            significant_p    = sig_p,
            right_skew_ratio = round(right_skew, 4),
            clustering_score = round(clustering, 4),
            pcurve_score     = round(score, 4),
            risk_level       = level,
            summary          = summary,
            flags            = flags,
            flags_count      = len(flags),
        )

    # ── internal helpers ─────────────────────────────────────────

    def _extract_p_values(self, text: str) -> list:
        values = []
        for m in self.P_PATTERN.finditer(text):
            try:
                v = float(m.group(1))
                if 0 < v <= 1:
                    values.append(round(v, 4))
            except ValueError:
                pass
        return values

    def _right_skew_ratio(self, sig_p: list) -> float:
        """
        Ratio of p-values below 0.025 vs 0.025-0.05.
        Real effects: >50% below 0.025 (right skewed).
        """
        if not sig_p:
            return 0.0
        below_half = sum(1 for p in sig_p if p <= 0.025)
        return below_half / len(sig_p)

    def _clustering_score(self, sig_p: list) -> float:
        """
        Ratio of p-values in 0.04-0.05 range.
        High clustering = p-hacking signature.
        """
        if not sig_p:
            return 0.0
        near_05 = sum(1 for p in sig_p if p >= 0.04)
        return near_05 / len(sig_p)

    def _aggregate_score(self, right_skew: float,
                         clustering: float,
                         sig_p: list) -> float:
        """Combine signals into 0-1 risk score."""
        cluster_risk    = clustering
        no_skew_risk    = 1.0 - right_skew
        score = (cluster_risk * 0.6 + no_skew_risk * 0.4)
        return min(round(score, 4), 1.0)

    def _risk(self, score: float,
              clustering: float,
              right_skew: float) -> str:
        if clustering > 0.7 or score >= 0.7:
            return "critical"
        if clustering > 0.5 or score >= 0.5:
            return "high"
        if clustering > 0.3 or score >= 0.3:
            return "medium"
        return "low"

    def _build_summary(self, all_p, sig_p, score,
                       level, right_skew, clustering) -> str:
        pct = round(score * 100)
        return (
            f"P-Curve analyzed {len(all_p)} p-value(s), "
            f"{len(sig_p)} significant (p≤0.05). "
            f"Clustering score: {round(clustering*100)}% near p=0.05. "
            f"Right-skew ratio: {round(right_skew*100)}%. "
            f"Overall bias score: {pct}%. "
            f"Risk level: {level.upper()}."
        )