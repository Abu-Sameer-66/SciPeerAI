# Methodology Logic Checker
# -------------------------
# The most subtle form of scientific fraud is not
# fabricating data — it is making claims that your
# method cannot actually support.
#
# "Correlation does not imply causation" is the
# famous example. But there are dozens of variations:
# underpowered claims, wrong timeframes, missing
# controls, self-report data for clinical conclusions.
#
# This module catches them — using both rule-based
# pattern matching and LLM-powered reasoning.

import re
import os
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


# ── data structures ───────────────────────────────────────────

@dataclass
class MethodologyFlag:
    flag_type: str
    severity: str
    claim: str
    issue: str
    evidence: str
    suggestion: str


@dataclass
class MethodologyResult:
    claims_found: list
    methods_found: list
    flags: list
    llm_assessment: str
    llm_available: bool
    risk_score: float
    risk_level: str
    summary: str


# ── main class ────────────────────────────────────────────────

class MethodologyChecker:
    """
    Two-layer methodology analysis:

    Layer 1 — Rule-based: fast, deterministic, catches
    known patterns (causation language, tiny samples,
    missing controls, short timeframes for long-term claims)

    Layer 2 — LLM reasoning: slower, probabilistic,
    catches subtle logical gaps that rules miss.
    Falls back gracefully if API unavailable.
    """

    # words that claim causation — need RCT to justify
    CAUSATION_WORDS = [
        "causes", "caused by", "leads to", "results in",
        "produces", "induces", "drives", "responsible for",
        "due to", "because of", "proves that", "demonstrates that"
    ]

    # words that only justify correlation
    CORRELATION_WORDS = [
        "associated with", "correlated", "linked to",
        "related to", "predicts", "suggests"
    ]

    # study designs that cannot prove causation
    WEAK_DESIGNS = [
        "survey", "questionnaire", "self-report", "cross-sectional",
        "retrospective", "observational", "case study", "anecdotal"
    ]

    # long-term claims need long-term studies
    LONGTERM_CLAIMS = [
        "long-term", "chronic", "sustained", "permanent",
        "lasting", "durable", "years", "lifetime"
    ]

    def __init__(self):
        self._hf_token = os.getenv("HF_API_TOKEN", "")
        # free model on HuggingFace — good at reasoning
        self._hf_model = "mistralai/Mistral-7B-Instruct-v0.1"
        self._hf_api_url = (
            f"https://api-inference.huggingface.co/models/{self._hf_model}"
        )

    # ── public method ─────────────────────────────────────────

    def analyze(self, text: str, abstract: str = "") -> MethodologyResult:
        """
        Full methodology analysis.
        Pass full paper text. Optionally pass abstract separately
        for cleaner claim extraction.
        """
        working_text = abstract if abstract else text

        claims   = self._extract_claims(working_text)
        methods  = self._extract_methods(text)

        flags    = []
        flags.extend(self._check_causation_without_rct(text, claims))
        flags.extend(self._check_weak_design_strong_claim(text, claims))
        flags.extend(self._check_longterm_claim_shortterm_study(text, claims))
        flags.extend(self._check_missing_control_group(text))
        flags.extend(self._check_generalization(text, claims))

        # try LLM reasoning — graceful fallback if unavailable
        llm_text, llm_ok = self._llm_assess(
            claims=claims,
            methods=methods,
            paper_snippet=text[:1500]
        )

        risk_score = self._calculate_risk(flags)
        risk_level = self._get_risk_level(risk_score)

        return MethodologyResult(
            claims_found=claims,
            methods_found=methods,
            flags=flags,
            llm_assessment=llm_text,
            llm_available=llm_ok,
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            summary=self._write_summary(flags, risk_level, llm_ok),
        )

    # ── claim / method extraction ─────────────────────────────

    def _extract_claims(self, text: str) -> list:
        """
        Pull claim-like sentences — those that assert findings,
        conclusions, or implications.
        Looks for language that signals a conclusion.
        """
        claim_markers = [
            "we found", "we show", "we demonstrate", "we conclude",
            "our results", "our findings", "this study shows",
            "this study demonstrates", "results indicate",
            "results suggest", "data show", "analysis reveals",
            "we report", "evidence suggests", "we establish"
        ]
        claims = []
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 20:
                continue
            s_lower = sentence.lower()
            if any(marker in s_lower for marker in claim_markers):
                claims.append(sentence)

        return claims[:8]  # cap at 8 — enough signal

    def _extract_methods(self, text: str) -> list:
        """
        Pull sentences from the methods section that describe
        how the study was actually conducted.
        """
        method_markers = [
            "we used", "we conducted", "we recruited", "we collected",
            "we measured", "we analyzed", "participants were",
            "subjects were", "samples were", "data were collected",
            "randomized", "controlled", "double-blind", "survey",
            "questionnaire", "interview", "experiment"
        ]
        methods = []
        sentences = re.split(r'[.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 20:
                continue
            s_lower = sentence.lower()
            if any(marker in s_lower for marker in method_markers):
                methods.append(sentence)

        return methods[:8]

    # ── rule-based checks ─────────────────────────────────────

    def _check_causation_without_rct(self, text: str, claims: list) -> list:
        """
        Detects causal language in claims combined with
        study designs that cannot establish causation.
        Classic example: observational study claiming X causes Y.
        """
        flags = []
        text_lower = text.lower()

        has_causal_claim = any(
            word in text_lower for word in self.CAUSATION_WORDS
        )
        has_weak_design = any(
            design in text_lower for design in self.WEAK_DESIGNS
        )
        has_rct = any(
            word in text_lower
            for word in ["randomized", "randomised", "rct",
                         "control group", "placebo", "double-blind"]
        )

        if has_causal_claim and has_weak_design and not has_rct:
            # find the actual causal sentence as evidence
            evidence_sentence = ""
            for sentence in re.split(r'[.!?]', text):
                if any(w in sentence.lower() for w in self.CAUSATION_WORDS):
                    evidence_sentence = sentence.strip()
                    break

            flags.append(MethodologyFlag(
                flag_type="causation_without_rct",
                severity="high",
                claim="Causal language detected in conclusions",
                issue=(
                    "The study uses causal language "
                    f"({', '.join([w for w in self.CAUSATION_WORDS if w in text_lower[:500]])}) "
                    "but the study design "
                    f"({', '.join([d for d in self.WEAK_DESIGNS if d in text_lower])}) "
                    "cannot establish causation."
                ),
                evidence=evidence_sentence or "See causal language in conclusions",
                suggestion=(
                    "Causal claims require randomized controlled trials. "
                    "Replace causal language with correlation language, "
                    "or acknowledge the design limitation explicitly."
                ),
            ))

        return flags

    def _check_weak_design_strong_claim(
        self, text: str, claims: list
    ) -> list:
        """
        Self-report surveys and questionnaires cannot support
        strong clinical or behavioral conclusions.
        """
        flags = []
        text_lower = text.lower()

        has_self_report = any(
            w in text_lower
            for w in ["self-report", "self report", "questionnaire",
                      "survey", "interview", "participants reported"]
        )
        has_strong_claim = any(
            w in text_lower
            for w in ["proves", "demonstrates", "establishes",
                      "confirms", "validates", "clinical evidence"]
        )

        if has_self_report and has_strong_claim:
            flags.append(MethodologyFlag(
                flag_type="weak_design_strong_claim",
                severity="medium",
                claim="Strong claim based on self-report data",
                issue=(
                    "Self-report or questionnaire data has known limitations "
                    "(social desirability bias, recall bias) that undermine "
                    "strong conclusive claims."
                ),
                evidence="Self-report instrument combined with conclusive language",
                suggestion=(
                    "Acknowledge self-report limitations explicitly. "
                    "Soften conclusions to match data quality."
                ),
            ))

        return flags

    def _check_longterm_claim_shortterm_study(
        self, text: str, claims: list
    ) -> list:
        """
        Studies lasting days or weeks cannot make
        long-term or chronic effect claims.
        """
        flags = []
        text_lower = text.lower()

        has_longterm_claim = any(
            w in text_lower for w in self.LONGTERM_CLAIMS
        )
        has_shortterm_study = any(
            w in text_lower
            for w in ["two weeks", "2 weeks", "one week", "1 week",
                      "3 days", "7 days", "short-term pilot",
                      "preliminary study"]
        )

        if has_longterm_claim and has_shortterm_study:
            flags.append(MethodologyFlag(
                flag_type="timeframe_mismatch",
                severity="medium",
                claim="Long-term claim from short-term study",
                issue=(
                    "The study duration appears insufficient to support "
                    "long-term or chronic effect claims."
                ),
                evidence="Long-term language with short study duration",
                suggestion=(
                    "Either extend the study duration or explicitly "
                    "limit claims to short-term effects only."
                ),
            ))

        return flags

    def _check_missing_control_group(self, text: str) -> list:
        """
        Studies measuring treatment effects without a
        control group cannot isolate the treatment's impact.
        """
        flags = []
        text_lower = text.lower()

        has_treatment = any(
            w in text_lower
            for w in ["treatment", "intervention", "drug", "therapy",
                      "program", "training"]
        )
        has_effect_claim = any(
            w in text_lower
            for w in ["improved", "reduced", "increased", "effective",
                      "significant effect"]
        )
        has_control = any(
            w in text_lower
            for w in ["control group", "control condition", "placebo",
                      "comparison group", "waitlist"]
        )

        if has_treatment and has_effect_claim and not has_control:
            flags.append(MethodologyFlag(
                flag_type="missing_control_group",
                severity="high",
                claim="Treatment effect claimed without control group",
                issue=(
                    "Effect claims for a treatment or intervention "
                    "require a control group to rule out confounds, "
                    "placebo effects, and natural recovery."
                ),
                evidence="Treatment + effect language with no control group mention",
                suggestion=(
                    "Add a control/comparison condition, or acknowledge "
                    "that without a control group, the effect cannot be "
                    "attributed to the intervention specifically."
                ),
            ))

        return flags

    def _check_generalization(self, text: str, claims: list) -> list:
        """
        Small, homogeneous samples cannot support
        broad population-level generalizations.
        """
        flags = []
        text_lower = text.lower()

        has_broad_claim = any(
            w in text_lower
            for w in ["all patients", "general population", "universally",
                      "across all", "globally applicable", "all humans"]
        )
        has_limited_sample = any(
            w in text_lower
            for w in ["undergraduate students", "college students",
                      "single institution", "convenience sample",
                      "homogeneous sample"]
        )

        if has_broad_claim and has_limited_sample:
            flags.append(MethodologyFlag(
                flag_type="overgeneralization",
                severity="medium",
                claim="Broad generalization from limited sample",
                issue=(
                    "The sample characteristics (e.g., undergraduate students, "
                    "single institution) limit generalizability beyond "
                    "the studied population."
                ),
                evidence="Broad claim language with limited sample description",
                suggestion=(
                    "Explicitly acknowledge sampling limitations "
                    "and restrict claims to the studied population."
                ),
            ))

        return flags

    # ── llm reasoning ─────────────────────────────────────────

    def _llm_assess(
        self, claims: list, methods: list, paper_snippet: str
    ) -> tuple:
        """
        Ask an LLM to reason about whether the methods
        logically support the claims.

        Returns (assessment_text, success_bool).
        Falls back gracefully if token missing or API down.
        """
        if not self._hf_token or self._hf_token == "hf_xxxxxxxxxxxxxxxx":
            return (
                "LLM assessment unavailable — HF_API_TOKEN not configured.",
                False
            )

        claims_text  = " | ".join(claims[:3]) if claims else "Not extracted"
        methods_text = " | ".join(methods[:3]) if methods else "Not extracted"

        prompt = f"""[INST] You are a scientific peer reviewer.

Paper excerpt:
{paper_snippet[:800]}

Claims made: {claims_text}
Methods used: {methods_text}

In 2-3 sentences, identify the most critical logical gap between the methods and claims. Be specific and direct. [/INST]"""

        try:
            payload = json.dumps({
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 150,
                    "temperature": 0.3,
                    "return_full_text": False,
                }
            }).encode("utf-8")

            req = urllib.request.Request(
                self._hf_api_url,
                data=payload,
                headers={
                    "Authorization": f"Bearer {self._hf_token}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))

            if isinstance(result, list) and result:
                text = result[0].get("generated_text", "").strip()
                return (text, True) if text else ("No assessment generated.", False)

            return ("Unexpected API response format.", False)

        except urllib.error.HTTPError as e:
            if e.code == 503:
                return ("LLM model loading — try again in 20 seconds.", False)
            return (f"API error {e.code}: {str(e)}", False)
        except Exception as e:
            return (f"LLM unavailable: {str(e)}", False)

    # ── scoring ───────────────────────────────────────────────

    def _calculate_risk(self, flags: list) -> float:
        weights = {"high": 0.35, "medium": 0.20, "low": 0.08}
        score = sum(weights.get(f.severity, 0) for f in flags)
        return min(score, 1.0)

    def _get_risk_level(self, score: float) -> str:
        if score >= 0.7:   return "critical"
        elif score >= 0.4: return "high"
        elif score >= 0.2: return "medium"
        return "low"

    def _write_summary(
        self, flags: list, risk_level: str, llm_ok: bool
    ) -> str:
        if not flags:
            base = "No methodology logic issues detected."
        else:
            high = sum(1 for f in flags if f.severity == "high")
            med  = sum(1 for f in flags if f.severity == "medium")
            parts = []
            if high: parts.append(f"{high} high-severity issue{'s' if high > 1 else ''}")
            if med:  parts.append(f"{med} medium-severity concern{'s' if med > 1 else ''}")
            base = (
                f"Methodology checker flagged {', '.join(parts)}. "
                f"Risk level: {risk_level.upper()}."
            )

        llm_note = " LLM reasoning included." if llm_ok else " LLM reasoning unavailable."
        return base + llm_note