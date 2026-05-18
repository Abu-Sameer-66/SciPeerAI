import pickle
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

MODEL_PATH = Path(__file__).resolve().parent.parent.parent.parent / "models" / "replication_predictor_honest.pkl"

SCORE_KEYS = [
    "score_stat", "score_method", "score_citation", "score_repro",
    "score_novelty", "score_grim", "score_sprite", "score_granularity",
    "score_pcurve", "score_effect", "score_retraction", "score_cartel",
    "score_llm", "score_fraud", "score_temporal", "score_dna",
    "score_dataprint", "score_peerreview", "score_spectrum",
]

_model = None

def _load_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Replication model not found at {MODEL_PATH}")
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model


def _build_feature_vector(scores: dict) -> np.ndarray:
    base = [float(scores.get(k, 0.0)) for k in SCORE_KEYS]

    nonzero_count = sum(1 for v in base if v > 0.0)

    integrity_index = (
        base[0]  * 0.20 +   # stat
        base[1]  * 0.15 +   # method
        base[12] * 0.15 +   # llm
        base[13] * 0.20 +   # fraud
        base[2]  * 0.10 +   # citation
        base[3]  * 0.10 +   # repro
        base[14] * 0.10     # temporal
    )

    return np.array(base + [nonzero_count, integrity_index], dtype=np.float64)


def _interpret(prob_fraud: float) -> tuple:
    replication_prob = round(1.0 - prob_fraud, 4)

    if replication_prob >= 0.75:
        level = "HIGH"
        verdict = "This paper shows strong indicators of replicability."
    elif replication_prob >= 0.50:
        level = "MODERATE"
        verdict = "Replication is plausible but some concerns exist."
    elif replication_prob >= 0.30:
        level = "LOW"
        verdict = "Multiple integrity signals suggest replication difficulty."
    else:
        level = "VERY LOW"
        verdict = "Serious integrity concerns — replication unlikely without raw data."

    return replication_prob, level, verdict


@dataclass
class ReplicationResult:
    module: str = "Replication Probability Score"
    replication_probability: float = 0.0
    fraud_probability: float = 0.0
    replication_level: str = "UNKNOWN"
    verdict: str = ""
    risk_score: float = 0.0
    risk_level: str = "UNKNOWN"
    summary: str = ""
    flags: List[dict] = field(default_factory=list)
    flags_count: int = 0
    model_version: str = "1.0.0"
    error: str = ""


def analyze(scores: dict) -> ReplicationResult:
    result = ReplicationResult()

    try:
        model = _load_model()
        features = _build_feature_vector(scores)
        features_2d = features.reshape(1, -1)

        prob_fraud = float(model.predict_proba(features_2d)[0][1])
        replication_prob, level, verdict = _interpret(prob_fraud)

        result.replication_probability = replication_prob
        result.fraud_probability = round(prob_fraud, 4)
        result.replication_level = level
        result.verdict = verdict
        result.risk_score = round(prob_fraud, 4)
        result.risk_level = (
            "LOW" if prob_fraud < 0.35 else
            "MEDIUM" if prob_fraud < 0.60 else
            "HIGH"
        )
        result.summary = (
            f"ML-based replication probability: {replication_prob:.1%}. "
            f"Fraud likelihood: {prob_fraud:.1%}. "
            f"Replication confidence: {level}."
        )

        flags = []

        if scores.get("score_stat", 0) > 0.5:
            flags.append({
                "flag_type": "Statistical Anomaly",
                "severity": "HIGH",
                "description": "Statistical irregularities reduce replication confidence.",
                "evidence": f"stat_score={scores['score_stat']:.3f}",
                "suggestion": "Request raw data and re-run all statistical tests independently."
            })

        if scores.get("score_llm", 0) > 0.5:
            flags.append({
                "flag_type": "AI-Generated Content",
                "severity": "MEDIUM",
                "description": "High AI-text signal may indicate synthetic results.",
                "evidence": f"llm_score={scores['score_llm']:.3f}",
                "suggestion": "Cross-check methodology with similar published work."
            })

        if scores.get("score_fraud", 0) > 0.5:
            flags.append({
                "flag_type": "Fraud Pattern Detected",
                "severity": "HIGH",
                "description": "Fraud fingerprint module flagged anomalous patterns.",
                "evidence": f"fraud_score={scores['score_fraud']:.3f}",
                "suggestion": "Contact authors for raw dataset access before citing."
            })

        if replication_prob < 0.35:
            flags.append({
                "flag_type": "Low Replication Probability",
                "severity": "HIGH",
                "description": "Combined module signals indicate replication is unlikely.",
                "evidence": f"replication_prob={replication_prob:.3f}, fraud_prob={prob_fraud:.3f}",
                "suggestion": "Do not replicate without first contacting the original authors."
            })

        result.flags = flags
        result.flags_count = len(flags)

    except Exception as exc:
        result.error = str(exc)
        result.summary = f"Replication analysis failed: {exc}"
        result.risk_level = "UNKNOWN"

    return result