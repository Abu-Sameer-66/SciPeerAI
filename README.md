<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:000000,30:0a0020,60:120038,100:1a0050&height=320&section=header&text=🔬%20SciPeerAI&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=The%20AI%20That%20Catches%20What%20Peer%20Reviewers%20Miss&descSize=20&descAlignY=60&descAlign=50&descColor=bb88ff" width="100%"/>

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&weight=700&size=24&pause=1000&color=BB88FF&center=true&vCenter=true&width=900&lines=Statistical+Fraud+Detection+Engine;Figure+Forensics+%2B+ELA+Analysis;Methodology+Logic+%2B+Citation+Integrity;27+Tests+Passing+%7C+Live+on+Railway" />

<br/><br/>

<a href="https://web-production-f526d.up.railway.app/docs">
<img src="https://img.shields.io/badge/%F0%9F%9F%A2%20LIVE%20API-Railway-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>
&nbsp;
<a href="https://web-production-f526d.up.railway.app">
<img src="https://img.shields.io/badge/%F0%9F%9F%A2%20LIVE%20DEMO-Online-9955ff?style=for-the-badge&labelColor=120038"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI">
<img src="https://img.shields.io/badge/%F0%9F%9F%A3%20REPO-GitHub-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>
&nbsp;
<a href="https://sameer-nadeem-portfolio.vercel.app">
<img src="https://img.shields.io/badge/%F0%9F%8C%90%20PORTFOLIO-Live-9955ff?style=for-the-badge&labelColor=120038"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI/blob/main/LICENSE">
<img src="https://img.shields.io/badge/License-MIT-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.10-bb88ff?style=flat-square&logo=python&logoColor=black&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/FastAPI-0.115-9955ff?style=flat-square&logo=fastapi&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/PyMuPDF-PDF%20Engine-bb88ff?style=flat-square&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/Pillow-Image%20Analysis-9955ff?style=flat-square&labelColor=120038"/>
<img src="https://img.shields.io/badge/imagehash-Perceptual%20Hash-bb88ff?style=flat-square&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/pytest-27%20Tests-9955ff?style=flat-square&logo=pytest&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/Railway-Deployed-bb88ff?style=flat-square&logo=railway&logoColor=white&labelColor=0a0020"/>

</div>

---

## The Crisis Nobody Is Solving

**70% of published scientific findings cannot be replicated.**

That number is not a typo. It is the reproducibility crisis — and it is quietly costing the world billions of dollars in wasted follow-up research, corrupting medical decisions, and eroding the public's trust in science itself.

The problem is not that scientists are dishonest. The problem is that **peer review is broken by design.**

Reviewers are overworked. They check one paper at a time. They cannot cross-reference figures across 50 pages. They cannot detect when p-values have been massaged to look significant. They cannot run forensic analysis on every image in a manuscript.

**A machine can. That is what SciPeerAI is.**

---

## Live Deployment

| Service | URL | Status |
|:---|:---|:---:|
| REST API | [web-production-f526d.up.railway.app](https://web-production-f526d.up.railway.app) | 🟢 Live |
| API Docs | [/docs](https://web-production-f526d.up.railway.app/docs) | 🟢 Live |
| System Status | [/api/v1/status](https://web-production-f526d.up.railway.app/api/v1/status) | 🟢 Live |

---

## What It Does

<table>
<tr>
<td width="50%">

### ✅ Statistical Audit Engine
Detects p-hacking by identifying suspicious clusters of p-values near the 0.05 threshold. Flags underpowered sample sizes. Catches suspiciously round numbers that real data almost never produces.

**Novel:** Combines three detection patterns into one unified weighted risk score. No existing tool — Statcheck, GRIM, or SPRITE — does all three simultaneously.

### ✅ Figure Forensics Pipeline
Extracts every image from a PDF and runs three-layer forensic analysis: perceptual hashing for duplicate figures, Error Level Analysis for JPEG editing artifacts, and brightness uniformity scoring for artificial enhancement.

**Novel:** No existing automated tool combines all three forensic layers in one pipeline.

</td>
<td width="50%">

### ✅ Methodology Logic Checker
Rule-based + LLM-powered reasoning engine. Detects causation claims without RCT, missing control groups, timeframe mismatches between study duration and long-term claims.

**Novel:** First system to systematically map the logical gap between methods section and conclusions in automated peer review.

### ✅ Citation Integrity Analyzer
Detects self-citation abuse, unsupported broad claims, low citation density, and et al. overuse. Checks author name patterns for citation cartel signals.

**Novel:** Combines citation pattern analysis with claim-level validation in one unified pipeline.

</td>
</tr>
</table>

---

## System Architecture
```
┌──────────────────────────────────────────────────────┐
│                     INPUT LAYER                      │
│        Paper Text  /  PDF Upload  /  API Call        │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│                  ANALYSIS PIPELINE                   │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │    ✅ Statistical Audit Engine              │     │
│  │    regex → p-hack + sample + round numbers  │     │
│  │    → unified weighted risk score 0.0–1.0    │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │    ✅ Figure Forensics Pipeline             │     │
│  │    PyMuPDF → pHash + ELA + brightness       │     │
│  │    → forensic flags with evidence           │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │    ✅ Methodology Logic Checker             │     │
│  │    causation + control + timeframe + LLM    │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │    ✅ Citation Integrity Analyzer           │     │
│  │    self-cite + unsupported + density        │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  [ 🔧 Reproducibility ]  [ 🔧 Novelty Scorer ]       │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│                   OUTPUT LAYER                       │
│   FastAPI REST API  ──  5 endpoints, OAS 3.1         │
│   Structured JSON   ──  flags + evidence + score     │
│   Railway Cloud     ──  24/7 globally accessible     │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start
```bash
git clone https://github.com/Abu-Sameer-66/SciPeerAI.git
cd SciPeerAI
conda create -n scipeerai python=3.10 -y
conda activate scipeerai
pip install -r requirements.txt
python main.py
```

Local API → `http://localhost:8000`
Live API → `https://web-production-f526d.up.railway.app`
Docs → `https://web-production-f526d.up.railway.app/docs`

---

## API Usage

### Statistical Fraud Detection
```bash
curl -X POST "https://web-production-f526d.up.railway.app/api/v1/analyze/statistics" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We recruited n=12 participants. Results were significant (p=0.048). Secondary measures also significant (p=0.049). Tertiary analysis confirmed (p=0.046)."
  }'
```
```json
{
  "risk_level": "critical",
  "risk_score": 0.9,
  "summary": "Statistical audit flagged 2 high-severity issues, 1 medium-severity concern.",
  "flags": [
    {
      "flag_type": "p_hacking_suspected",
      "severity": "high",
      "description": "3 out of 3 p-values clustered between 0.04 and 0.051. That is 100% at the significance threshold.",
      "evidence": "[0.048, 0.049, 0.046]",
      "suggestion": "Check whether all conducted analyses are reported."
    }
  ],
  "flags_count": 2
}
```

### Figure Forensics
```bash
curl -X POST "https://web-production-f526d.up.railway.app/api/v1/analyze/figures" \
  -F "file=@paper.pdf"
```

### Methodology Check
```bash
curl -X POST "https://web-production-f526d.up.railway.app/api/v1/analyze/methodology" \
  -H "Content-Type: application/json" \
  -d '{"text": "We conducted a survey. Our results demonstrate that social media causes anxiety.", "abstract": ""}'
```

### Citation Audit
```bash
curl -X POST "https://web-production-f526d.up.railway.app/api/v1/analyze/citations" \
  -H "Content-Type: application/json" \
  -d '{"text": "Studies show that X. It is well known that Y. Research shows Z.", "author_name": ""}'
```

---

## Test Suite
```bash
pytest tests/ -v
```
```
tests/test_citation_analyzer.py::test_extracts_bracketed_citations      PASSED
tests/test_citation_analyzer.py::test_extracts_author_year_citations    PASSED
tests/test_citation_analyzer.py::test_flags_excessive_self_citation     PASSED
tests/test_citation_analyzer.py::test_flags_unsupported_claims          PASSED
tests/test_citation_analyzer.py::test_cited_claims_not_flagged          PASSED
tests/test_citation_analyzer.py::test_result_structure                  PASSED
tests/test_citation_analyzer.py::test_empty_text_safe                   PASSED
tests/test_figure_forensics.py::test_identical_images_flagged           PASSED
tests/test_figure_forensics.py::test_different_images_not_flagged       PASSED
tests/test_figure_forensics.py::test_flat_image_high_uniformity         PASSED
tests/test_figure_forensics.py::test_noisy_image_low_uniformity         PASSED
tests/test_figure_forensics.py::test_ela_returns_float                  PASSED
tests/test_figure_forensics.py::test_no_figures_returns_clean           PASSED
tests/test_methodology_checker.py::test_flags_causation_without_rct     PASSED
tests/test_methodology_checker.py::test_rct_does_not_flag_causation     PASSED
tests/test_methodology_checker.py::test_flags_missing_control_group     PASSED
tests/test_methodology_checker.py::test_no_flag_when_control_present    PASSED
tests/test_methodology_checker.py::test_flags_timeframe_mismatch        PASSED
tests/test_methodology_checker.py::test_result_structure                PASSED
tests/test_methodology_checker.py::test_empty_text_safe                 PASSED
tests/test_stat_audit.py::test_flags_suspicious_p_clustering            PASSED
tests/test_stat_audit.py::test_clean_paper_passes                       PASSED
tests/test_stat_audit.py::test_flags_tiny_sample                        PASSED
tests/test_stat_audit.py::test_acceptable_sample_passes                 PASSED
tests/test_stat_audit.py::test_flags_exact_p_value                      PASSED
tests/test_stat_audit.py::test_result_is_correct_type                   PASSED
tests/test_stat_audit.py::test_empty_text_doesnt_crash                  PASSED

27 passed in 10.95s
```

---

## Real-World Fraud This Catches

| Case | Scale | Fraud Type | SciPeerAI Module |
|:---|:---:|:---|:---|
| Fujii Yoshitaka | 183 papers retracted | Duplicate gel figures | Figure Forensics |
| Diederik Stapel | 58 papers retracted | Fabricated statistics | Statistical Audit |
| Hwang Woo-suk | Landmark stem cell fraud | Manipulated images | Figure Forensics |
| LaCour political study | Major retraction | Fabricated data patterns | Statistical Audit |
| Smeesters marketing fraud | 3 papers retracted | Causation overclaiming | Methodology Checker |

---

## Project Structure
```
SciPeerAI/
├── src/
│   └── scipeerai/
│       ├── api/
│       │   ├── __init__.py              FastAPI app factory
│       │   └── routes.py                5 live endpoints
│       ├── modules/
│       │   ├── stat_audit.py            Statistical fraud detection
│       │   ├── figure_forensics.py      CV-based forensic analysis
│       │   ├── methodology_checker.py   Logic gap detection
│       │   └── citation_analyzer.py     Citation integrity analysis
│       └── core/
│           └── pdf_parser.py            PDF ingestion pipeline
├── tests/
│   ├── test_stat_audit.py
│   ├── test_figure_forensics.py
│   ├── test_methodology_checker.py
│   └── test_citation_analyzer.py
├── main.py
├── Procfile
├── railway.json
└── requirements.txt
```

---

## Roadmap

- [x] Statistical Audit Engine — p-hacking, sample size, round numbers
- [x] Figure Forensics Engine — duplicate detection, ELA, brightness
- [x] Methodology Logic Checker — causation, control group, timeframe
- [x] Citation Integrity Analyzer — self-citation, unsupported claims
- [x] Production REST API — FastAPI + OAS 3.1 — 5 endpoints
- [x] 27 unit tests — all passing
- [x] Live deployment — Railway cloud
- [ ] Reproducibility Scanner
- [ ] Novelty Scorer
- [ ] SciPeerBench — evaluation benchmark dataset
- [ ] arXiv research paper
- [ ] Web UI — drag and drop
- [ ] Stripe API monetization

---

## Author

<div align="center">

**Sameer Nadeem** — AI/ML Engineer · Data Scientist · Open Source Contributor · GSoC 2026

<br/>

<a href="https://sameer-nadeem-portfolio.vercel.app"><img src="https://img.shields.io/badge/Portfolio-Live-bb88ff?style=for-the-badge&labelColor=0a0020"/></a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66"><img src="https://img.shields.io/badge/GitHub-Abu--Sameer--66-9955ff?style=for-the-badge&logo=github&labelColor=120038"/></a>
&nbsp;
<a href="https://www.linkedin.com/in/sameer-nadeem-66339a357/"><img src="https://img.shields.io/badge/LinkedIn-Sameer%20Nadeem-bb88ff?style=for-the-badge&logo=linkedin&labelColor=0a0020"/></a>
&nbsp;
<a href="https://www.kaggle.com/sameernadeem66"><img src="https://img.shields.io/badge/Kaggle-sameernadeem66-9955ff?style=for-the-badge&logo=kaggle&labelColor=120038"/></a>

</div>

---

<div align="center">

*Built to make science trustworthy again.*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:1a0050,50:120038,100:000000&height=140&section=footer" width="100%"/>

</div>
