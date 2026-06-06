

# import re
# import json
# import pickle
# import warnings
# import numpy as np
# from pathlib import Path
# from dataclasses import dataclass, field
# from typing import List

# warnings.filterwarnings("ignore")

# MODEL_DIR    = Path(__file__).resolve().parent.parent.parent.parent / "models" / "v2"
# CONFIG_PATH  = MODEL_DIR / "ensemble_config_v2.json"

# _config   = None
# _models   = None


# def _load_assets():
#     global _config, _models
#     if _models is not None:
#         return

#     with open(CONFIG_PATH) as fh:
#         _config = json.load(fh)

#     names   = ["lgbm_v2", "xgb_v2", "rf_v2", "lr_v2"]
#     _models = {}
#     for name in names:
#         path = MODEL_DIR / f"{name}.pkl"
#         if not path.exists():
#             raise FileNotFoundError(f"Model file missing: {path}")
#         with open(path, "rb") as fh:
#             _models[name] = pickle.load(fh)


# def _extract_features(text: str, title: str = "", journal: str = "", subject: str = "") -> np.ndarray:
#     t  = text.lower()
#     tt = title.lower()

#     features = {}

#     # basic text stats
#     words = t.split()
#     features["word_count"]      = len(words)
#     features["text_length"]     = len(text)
#     features["title_length"]    = len(title.split()) if title else 0
#     features["vocab_diversity"] = len(set(words)) / max(len(words), 1)

#     # p-values
#     pvals = re.findall(r'p\s*[<=]\s*0\.0\d+', t)
#     features["n_pvalues"]      = len(pvals)
#     features["has_p05"]        = 1.0 if re.search(r'p\s*[<=]\s*0\.05', t) else 0.0
#     features["pval_cluster"]   = 1.0 if len(pvals) > 4 else 0.0
#     features["sig_word_count"] = t.count("significant")

#     # sample sizes
#     samples = re.findall(r'\bn\s*=\s*(\d+)', t)
#     features["n_samples_found"] = len(samples)
#     if samples:
#         sizes = [int(x) for x in samples]
#         features["min_sample"]  = min(sizes)
#         features["max_sample"]  = max(sizes)
#         features["tiny_sample"] = 1.0 if min(sizes) < 20 else 0.0
#     else:
#         features["min_sample"]  = 0
#         features["max_sample"]  = 0
#         features["tiny_sample"] = 0.0

#     # numbers
#     all_nums = re.findall(r'\b\d+\.?\d*\b', t)
#     features["number_density"] = len(all_nums) / max(len(words), 1)
#     features["n_numbers"]      = len(all_nums)
#     if all_nums:
#         nums   = [float(x) for x in all_nums[:300]]
#         rounds = sum(1 for n in nums if n > 0 and n == int(n) and int(n) % 5 == 0)
#         features["round_number_ratio"] = rounds / max(len(nums), 1)
#         terms  = [int(str(int(n))[-1]) for n in nums if n > 9]
#         features["terminal_zero_bias"] = terms.count(0) / max(len(terms), 1) if terms else 0.0
#     else:
#         features["round_number_ratio"] = 0.0
#         features["terminal_zero_bias"] = 0.0

#     # ai phrase signals
#     ai_phrases = [
#         "it is worth noting", "importantly", "furthermore", "in conclusion",
#         "it should be noted", "notably", "these findings suggest",
#         "our results demonstrate", "taken together", "in summary",
#         "delve", "comprehensive", "robust", "novel approach",
#         "state-of-the-art", "leverage", "utilize", "facilitate",
#         "shedding light", "in this context", "it is noteworthy"
#     ]
#     features["ai_phrase_count"]   = sum(1 for p in ai_phrases if p in t)
#     features["ai_phrase_density"] = features["ai_phrase_count"] / max(len(words), 1)

#     # sentence structure
#     sents = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
#     if len(sents) > 2:
#         lens = [len(s.split()) for s in sents]
#         features["sentence_uniformity"] = 1.0 - (np.std(lens) / max(np.mean(lens), 1))
#         features["avg_sentence_len"]    = float(np.mean(lens))
#         features["burstiness"]          = float(np.std(lens) / max(np.mean(lens), 1))
#         features["n_sentences"]         = len(sents)
#     else:
#         features["sentence_uniformity"] = 0.5
#         features["avg_sentence_len"]    = 15.0
#         features["burstiness"]          = 0.5
#         features["n_sentences"]         = len(sents)

#     # methodology
#     method_good = ["randomized", "control group", "placebo", "double-blind",
#                    "pre-registered", "blinded", "confound", "limitation"]
#     method_bad  = ["we prove", "our study proves", "conclusively shows",
#                    "undeniably", "without doubt", "clearly demonstrates"]
#     features["method_good_count"] = sum(1 for w in method_good if w in t)
#     features["method_bad_count"]  = sum(1 for w in method_bad if w in t)
#     features["methodology_score"] = features["method_good_count"] / len(method_good)

#     # citations
#     cites = re.findall(r'\[\d+\]|\(\w+\s*,\s*\d{4}\)', text)
#     features["n_citations"]       = len(cites)
#     features["citation_density"]  = len(cites) / max(len(words), 1)
#     self_cite = ["our previous", "our earlier", "we previously", "we reported"]
#     features["self_cite_signals"] = sum(1 for w in self_cite if w in t)

#     # reproducibility
#     repro_pos = ["github", "zenodo", "figshare", "data available",
#                  "code available", "open source", "supplementary"]
#     repro_neg = ["upon request", "data not available", "available on request"]
#     features["repro_positive"] = sum(1 for w in repro_pos if w in t)
#     features["repro_negative"] = sum(1 for w in repro_neg if w in t)

#     # title signals
#     title_hype = ["novel", "innovative", "significant", "first", "groundbreaking",
#                   "unprecedented", "revolutionary", "remarkable"]
#     features["title_hype_count"]  = sum(1 for w in title_hype if w in tt)
#     features["title_has_numbers"] = 1.0 if re.search(r'\d', title) else 0.0

#     # metadata signals (0 if not provided)
#     predatory = ["frontiers", "mdpi", "hindawi", "sciencepg", "omics",
#                  "scirp", "waset", "ijser", "iiste"]
#     features["predatory_journal"] = 1.0 if any(p in journal.lower() for p in predatory) else 0.0

#     high_risk_subj = ["biology - cellular", "genetics", "biochemistry",
#                       "cancer", "computer science", "data science"]
#     features["high_risk_subject"] = 1.0 if any(s in subject.lower() for s in high_risk_subj) else 0.0

#     # benford deviation
#     dec_nums = re.findall(r'\b\d+\.\d+\b', t)
#     if len(dec_nums) >= 5:
#         first_d = [str(float(n))[0] for n in dec_nums if float(n) > 0]
#         first_d = [d for d in first_d if d.isdigit() and d != '0']
#         if first_d:
#             counts  = [first_d.count(str(d)) for d in range(1, 10)]
#             total   = sum(counts)
#             obs     = [c / total for c in counts]
#             exp     = [np.log10(1 + 1 / d) for d in range(1, 10)]
#             features["benford_deviation"] = float(sum(abs(o - e) for o, e in zip(obs, exp)))
#         else:
#             features["benford_deviation"] = 0.0
#     else:
#         features["benford_deviation"] = 0.0

#     # composite
#     features["high_risk_combo"] = (
#         (1 if features["pval_cluster"] else 0) +
#         (1 if features["ai_phrase_count"] > 4 else 0) +
#         (1 if features["round_number_ratio"] > 0.5 else 0) +
#         (1 if features["predatory_journal"] else 0)
#     ) / 4.0

#     features["integrity_index"] = (
#         features["methodology_score"]          * 0.20 +
#         features["repro_positive"]             * 0.02 +
#         features["vocab_diversity"]            * 0.15 +
#         features["burstiness"]                 * 0.15 +
#         (1 - features["round_number_ratio"])   * 0.15 +
#         max(0, 1 - features["ai_phrase_density"] * 8) * 0.10 +
#         (1 - features["predatory_journal"])    * 0.10 +
#         features["method_good_count"]          * 0.02
#     )

#     feat_order = _config["features"]
#     return np.array([features.get(k, 0.0) for k in feat_order], dtype=np.float64)


# def _interpret(replication_prob: float) -> tuple:
#     if replication_prob >= 0.75:
#         level   = "HIGH"
#         verdict = "Strong indicators of replicability detected across linguistic signals."
#     elif replication_prob >= 0.50:
#         level   = "MODERATE"
#         verdict = "Replication plausible but some integrity concerns present."
#     elif replication_prob >= 0.30:
#         level   = "LOW"
#         verdict = "Multiple integrity signals suggest replication difficulty."
#     else:
#         level   = "VERY LOW"
#         verdict = "Serious integrity concerns — independent replication unlikely without raw data."
#     return level, verdict


# @dataclass
# class ReplicationResult:
#     module:                  str   = "Replication Probability Score"
#     replication_probability: float = 0.0
#     fraud_probability:       float = 0.0
#     replication_level:       str   = "UNKNOWN"
#     verdict:                 str   = ""
#     risk_score:              float = 0.0
#     risk_level:              str   = "UNKNOWN"
#     summary:                 str   = ""
#     flags:                   List[dict] = field(default_factory=list)
#     flags_count:             int   = 0
#     model_version:           str   = "2.0.0"
#     ensemble_auc:            float = 0.895
#     error:                   str   = ""


# def analyze(scores: dict, text: str = "", title: str = "",
#             journal: str = "", subject: str = "") -> ReplicationResult:
#     result = ReplicationResult()
#     try:
#         _load_assets()

#         feat_vec = _extract_features(text, title, journal, subject)
#         X        = feat_vec.reshape(1, -1)

#         w       = _config["weights"]
#         thresh  = _config["threshold"]

#         p_lgbm  = float(_models["lgbm_v2"].predict_proba(X)[0][1])
#         p_xgb   = float(_models["xgb_v2"].predict_proba(X)[0][1])
#         p_rf    = float(_models["rf_v2"].predict_proba(X)[0][1])
#         p_lr    = float(_models["lr_v2"].predict_proba(X)[0][1])

#         fraud_prob  = (p_lgbm * w["lgbm"] + p_xgb * w["xgb"] +
#                        p_rf   * w["rf"]   + p_lr  * w["lr"])
#         replic_prob = round(1.0 - fraud_prob, 4)
#         fraud_prob  = round(fraud_prob, 4)

#         level, verdict = _interpret(replic_prob)

#         result.replication_probability = replic_prob
#         result.fraud_probability       = fraud_prob
#         result.replication_level       = level
#         result.verdict                 = verdict
#         result.risk_score              = fraud_prob
#         result.risk_level              = (
#             "LOW"    if fraud_prob < 0.35 else
#             "MEDIUM" if fraud_prob < 0.60 else
#             "HIGH"
#         )
#         result.summary = (
#             f"Ensemble ML replication probability: {replic_prob:.1%}. "
#             f"Fraud likelihood: {fraud_prob:.1%}. "
#             f"Confidence level: {level}. "
#             f"Model AUC: 0.895 on 91,779 papers."
#         )

#         flags = []

#         feat_vec_named = dict(zip(_config["features"], feat_vec.tolist()))

#         if feat_vec_named.get("predatory_journal", 0) > 0:
#             flags.append({
#                 "flag_type":   "Predatory Journal Signal",
#                 "severity":    "HIGH",
#                 "description": "Journal name matches known predatory publisher patterns.",
#                 "evidence":    f"journal={journal}",
#                 "suggestion":  "Verify journal indexing in DOAJ or Scopus before citing.",
#             })

#         if feat_vec_named.get("ai_phrase_count", 0) > 4:
#             flags.append({
#                 "flag_type":   "AI-Generated Content Pattern",
#                 "severity":    "MEDIUM",
#                 "description": "High density of AI-typical phrases detected in abstract.",
#                 "evidence":    f"ai_phrase_count={feat_vec_named['ai_phrase_count']:.0f}",
#                 "suggestion":  "Cross-check methodology section for AI-generated boilerplate.",
#             })

#         if feat_vec_named.get("methodology_score", 0) < 0.05:
#             flags.append({
#                 "flag_type":   "Weak Methodology Reporting",
#                 "severity":    "MEDIUM",
#                 "description": "Abstract contains few standard methodology terms.",
#                 "evidence":    f"methodology_score={feat_vec_named['methodology_score']:.3f}",
#                 "suggestion":  "Request full methods section before citation.",
#             })

#         if feat_vec_named.get("repro_positive", 0) == 0:
#             flags.append({
#                 "flag_type":   "No Reproducibility Statement",
#                 "severity":    "LOW",
#                 "description": "No data availability or code sharing mentioned.",
#                 "evidence":    "repro_positive=0",
#                 "suggestion":  "Contact authors for data and code availability.",
#             })

#         if replic_prob < 0.35:
#             flags.append({
#                 "flag_type":   "Low Replication Probability",
#                 "severity":    "HIGH",
#                 "description": "Ensemble model signals high fraud likelihood from text patterns.",
#                 "evidence":    f"fraud_prob={fraud_prob:.3f}, threshold={thresh:.2f}",
#                 "suggestion":  "Do not replicate without obtaining raw data from authors.",
#             })

#         result.flags       = flags
#         result.flags_count = len(flags)

#     except Exception as exc:
#         result.error   = str(exc)
#         result.summary = f"Replication analysis failed: {exc}"

#     return result



import re
import json
import pickle
import warnings
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List

warnings.filterwarnings("ignore")

MODEL_DIR   = Path(__file__).resolve().parent.parent.parent.parent / "models" / "v2"
CONFIG_PATH = MODEL_DIR / "ensemble_config_v2.json"

_config  = None
_models  = None


def _load_assets():
    global _config, _models
    if _models is not None:
        return

    with open(CONFIG_PATH) as fh:
        _config = json.load(fh)

    names   = ["lgbm_v2", "xgb_v2", "rf_v2", "lr_v2"]
    _models = {}
    for name in names:
        path = MODEL_DIR / f"{name}.pkl"
        if path.exists():
            with open(path, "rb") as fh:
                _models[name] = pickle.load(fh)
        else:
            _models[name] = None


def _extract_features(text: str, title: str = "", journal: str = "", subject: str = "") -> np.ndarray:
    t  = text.lower()
    tt = title.lower()

    features = {}

    words = t.split()
    features["word_count"]      = len(words)
    features["text_length"]     = len(text)
    features["title_length"]    = len(title.split()) if title else 0
    features["vocab_diversity"] = len(set(words)) / max(len(words), 1)

    pvals = re.findall(r'p\s*[<=]\s*0\.0\d+', t)
    features["n_pvalues"]      = len(pvals)
    features["has_p05"]        = 1.0 if re.search(r'p\s*[<=]\s*0\.05', t) else 0.0
    features["pval_cluster"]   = 1.0 if len(pvals) > 4 else 0.0
    features["sig_word_count"] = t.count("significant")

    samples = re.findall(r'\bn\s*=\s*(\d+)', t)
    features["n_samples_found"] = len(samples)
    if samples:
        sizes = [int(x) for x in samples]
        features["min_sample"]  = min(sizes)
        features["max_sample"]  = max(sizes)
        features["tiny_sample"] = 1.0 if min(sizes) < 20 else 0.0
    else:
        features["min_sample"]  = 0
        features["max_sample"]  = 0
        features["tiny_sample"] = 0.0

    all_nums = re.findall(r'\b\d+\.?\d*\b', t)
    features["number_density"] = len(all_nums) / max(len(words), 1)
    features["n_numbers"]      = len(all_nums)
    if all_nums:
        nums   = [float(x) for x in all_nums[:300]]
        rounds = sum(1 for n in nums if n > 0 and n == int(n) and int(n) % 5 == 0)
        features["round_number_ratio"] = rounds / max(len(nums), 1)
        terms  = [int(str(int(n))[-1]) for n in nums if n > 9]
        features["terminal_zero_bias"] = terms.count(0) / max(len(terms), 1) if terms else 0.0
    else:
        features["round_number_ratio"] = 0.0
        features["terminal_zero_bias"] = 0.0

    ai_phrases = [
        "it is worth noting", "importantly", "furthermore", "in conclusion",
        "it should be noted", "notably", "these findings suggest",
        "our results demonstrate", "taken together", "in summary",
        "delve", "comprehensive", "robust", "novel approach",
        "state-of-the-art", "leverage", "utilize", "facilitate",
        "shedding light", "in this context", "it is noteworthy"
    ]
    features["ai_phrase_count"]   = sum(1 for p in ai_phrases if p in t)
    features["ai_phrase_density"] = features["ai_phrase_count"] / max(len(words), 1)

    sents = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]
    if len(sents) > 2:
        lens = [len(s.split()) for s in sents]
        features["sentence_uniformity"] = 1.0 - (np.std(lens) / max(np.mean(lens), 1))
        features["avg_sentence_len"]    = float(np.mean(lens))
        features["burstiness"]          = float(np.std(lens) / max(np.mean(lens), 1))
        features["n_sentences"]         = len(sents)
    else:
        features["sentence_uniformity"] = 0.5
        features["avg_sentence_len"]    = 15.0
        features["burstiness"]          = 0.5
        features["n_sentences"]         = len(sents)

    method_good = ["randomized", "control group", "placebo", "double-blind",
                   "pre-registered", "blinded", "confound", "limitation"]
    method_bad  = ["we prove", "our study proves", "conclusively shows",
                   "undeniably", "without doubt", "clearly demonstrates"]
    features["method_good_count"] = sum(1 for w in method_good if w in t)
    features["method_bad_count"]  = sum(1 for w in method_bad if w in t)
    features["methodology_score"] = features["method_good_count"] / len(method_good)

    cites = re.findall(r'\[\d+\]|\(\w+\s*,\s*\d{4}\)', text)
    features["n_citations"]       = len(cites)
    features["citation_density"]  = len(cites) / max(len(words), 1)
    self_cite = ["our previous", "our earlier", "we previously", "we reported"]
    features["self_cite_signals"] = sum(1 for w in self_cite if w in t)

    repro_pos = ["github", "zenodo", "figshare", "data available",
                 "code available", "open source", "supplementary"]
    repro_neg = ["upon request", "data not available", "available on request"]
    features["repro_positive"] = sum(1 for w in repro_pos if w in t)
    features["repro_negative"] = sum(1 for w in repro_neg if w in t)

    title_hype = ["novel", "innovative", "significant", "first", "groundbreaking",
                  "unprecedented", "revolutionary", "remarkable"]
    features["title_hype_count"]  = sum(1 for w in title_hype if w in tt)
    features["title_has_numbers"] = 1.0 if re.search(r'\d', title) else 0.0

    predatory = ["frontiers", "mdpi", "hindawi", "sciencepg", "omics",
                 "scirp", "waset", "ijser", "iiste"]
    features["predatory_journal"] = 1.0 if any(p in journal.lower() for p in predatory) else 0.0

    high_risk_subj = ["biology - cellular", "genetics", "biochemistry",
                      "cancer", "computer science", "data science"]
    features["high_risk_subject"] = 1.0 if any(s in subject.lower() for s in high_risk_subj) else 0.0

    dec_nums = re.findall(r'\b\d+\.\d+\b', t)
    if len(dec_nums) >= 5:
        first_d = [str(float(n))[0] for n in dec_nums if float(n) > 0]
        first_d = [d for d in first_d if d.isdigit() and d != '0']
        if first_d:
            counts  = [first_d.count(str(d)) for d in range(1, 10)]
            total   = sum(counts)
            obs     = [c / total for c in counts]
            exp     = [np.log10(1 + 1 / d) for d in range(1, 10)]
            features["benford_deviation"] = float(sum(abs(o - e) for o, e in zip(obs, exp)))
        else:
            features["benford_deviation"] = 0.0
    else:
        features["benford_deviation"] = 0.0

    features["high_risk_combo"] = (
        (1 if features["pval_cluster"] else 0) +
        (1 if features["ai_phrase_count"] > 4 else 0) +
        (1 if features["round_number_ratio"] > 0.5 else 0) +
        (1 if features["predatory_journal"] else 0)
    ) / 4.0

    features["integrity_index"] = (
        features["methodology_score"]          * 0.20 +
        features["repro_positive"]             * 0.02 +
        features["vocab_diversity"]            * 0.15 +
        features["burstiness"]                 * 0.15 +
        (1 - features["round_number_ratio"])   * 0.15 +
        max(0, 1 - features["ai_phrase_density"] * 8) * 0.10 +
        (1 - features["predatory_journal"])    * 0.10 +
        features["method_good_count"]          * 0.02
    )

    feat_order = _config["features"]
    return np.array([features.get(k, 0.0) for k in feat_order], dtype=np.float64)


def _interpret(replication_prob: float) -> tuple:
    if replication_prob >= 0.75:
        level   = "HIGH"
        verdict = "Strong indicators of replicability detected across linguistic signals."
    elif replication_prob >= 0.50:
        level   = "MODERATE"
        verdict = "Replication plausible but some integrity concerns present."
    elif replication_prob >= 0.30:
        level   = "LOW"
        verdict = "Multiple integrity signals suggest replication difficulty."
    else:
        level   = "VERY LOW"
        verdict = "Serious integrity concerns — independent replication unlikely without raw data."
    return level, verdict


@dataclass
class ReplicationResult:
    module:                  str        = "Replication Probability Score"
    replication_probability: float      = 0.0
    fraud_probability:       float      = 0.0
    replication_level:       str        = "UNKNOWN"
    verdict:                 str        = ""
    risk_score:              float      = 0.0
    risk_level:              str        = "UNKNOWN"
    summary:                 str        = ""
    flags:                   List[dict] = field(default_factory=list)
    flags_count:             int        = 0
    model_version:           str        = "2.0.0"
    ensemble_auc:            float      = 0.895
    error:                   str        = ""


def analyze(scores: dict, text: str = "", title: str = "",
            journal: str = "", subject: str = "") -> ReplicationResult:
    result = ReplicationResult()
    try:
        _load_assets()

        feat_vec = _extract_features(text, title, journal, subject)
        X        = feat_vec.reshape(1, -1)

        w      = _config["weights"]
        thresh = _config["threshold"]

        p_lgbm = float(_models["lgbm_v2"].predict_proba(X)[0][1]) if _models.get("lgbm_v2") else None
        p_xgb  = float(_models["xgb_v2"].predict_proba(X)[0][1])  if _models.get("xgb_v2")  else None
        p_rf   = float(_models["rf_v2"].predict_proba(X)[0][1])   if _models.get("rf_v2")   else None
        p_lr   = float(_models["lr_v2"].predict_proba(X)[0][1])   if _models.get("lr_v2")   else None

        available = {
            "lgbm": p_lgbm,
            "xgb":  p_xgb,
            "rf":   p_rf,
            "lr":   p_lr,
        }
        loaded = {k: v for k, v in available.items() if v is not None}

        if not loaded:
            raise RuntimeError("No ensemble models could be loaded.")

        total_weight = sum(w[k] for k in loaded)
        fraud_prob   = sum(loaded[k] * w[k] for k in loaded) / total_weight
        replic_prob  = round(1.0 - fraud_prob, 4)
        fraud_prob   = round(fraud_prob, 4)

        models_used  = "+".join(k.upper() for k in loaded)
        missing      = [k.upper() for k in available if available[k] is None]

        level, verdict = _interpret(replic_prob)

        result.replication_probability = replic_prob
        result.fraud_probability       = fraud_prob
        result.replication_level       = level
        result.verdict                 = verdict
        result.risk_score              = fraud_prob
        result.risk_level              = (
            "LOW"    if fraud_prob < 0.35 else
            "MEDIUM" if fraud_prob < 0.60 else
            "HIGH"
        )

        missing_note = f" (RF excluded — large file, {missing} not deployed)" if missing else ""
        result.summary = (
            f"Ensemble ML replication probability: {replic_prob:.1%}. "
            f"Fraud likelihood: {fraud_prob:.1%}. "
            f"Confidence level: {level}. "
            f"Models used: {models_used}{missing_note}. "
            f"AUC: 0.895 on SciPeerBench v2.0 (91,779 papers)."
        )

        flags = []
        feat_vec_named = dict(zip(_config["features"], feat_vec.tolist()))

        if feat_vec_named.get("predatory_journal", 0) > 0:
            flags.append({
                "flag_type":   "Predatory Journal Signal",
                "severity":    "HIGH",
                "description": "Journal name matches known predatory publisher patterns.",
                "evidence":    f"journal={journal}",
                "suggestion":  "Verify journal indexing in DOAJ or Scopus before citing.",
            })

        if feat_vec_named.get("ai_phrase_count", 0) > 4:
            flags.append({
                "flag_type":   "AI-Generated Content Pattern",
                "severity":    "MEDIUM",
                "description": "High density of AI-typical phrases detected.",
                "evidence":    f"ai_phrase_count={feat_vec_named['ai_phrase_count']:.0f}",
                "suggestion":  "Cross-check methodology section for AI-generated boilerplate.",
            })

        if feat_vec_named.get("methodology_score", 0) < 0.05:
            flags.append({
                "flag_type":   "Weak Methodology Reporting",
                "severity":    "MEDIUM",
                "description": "Abstract contains few standard methodology terms.",
                "evidence":    f"methodology_score={feat_vec_named['methodology_score']:.3f}",
                "suggestion":  "Request full methods section before citation.",
            })

        if feat_vec_named.get("repro_positive", 0) == 0:
            flags.append({
                "flag_type":   "No Reproducibility Statement",
                "severity":    "LOW",
                "description": "No data availability or code sharing mentioned.",
                "evidence":    "repro_positive=0",
                "suggestion":  "Contact authors for data and code availability.",
            })

        if replic_prob < 0.35:
            flags.append({
                "flag_type":   "Low Replication Probability",
                "severity":    "HIGH",
                "description": "Ensemble model signals high fraud likelihood from text patterns.",
                "evidence":    f"fraud_prob={fraud_prob:.3f}, threshold={thresh:.2f}",
                "suggestion":  "Do not replicate without obtaining raw data from authors.",
            })

        result.flags       = flags
        result.flags_count = len(flags)

    except Exception as exc:
        result.error   = str(exc)
        result.summary = f"Replication analysis failed: {exc}"

    return result