<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:000000,30:0a0020,60:120038,100:1a0050&height=320&section=header&text=🔬%20SciPeerAI&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=The%20AI%20That%20Catches%20What%20Peer%20Reviewers%20Miss&descSize=20&descAlignY=60&descAlign=50&descColor=bb88ff" width="100%"/>

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&weight=700&size=24&pause=1000&color=BB88FF&center=true&vCenter=true&width=900&lines=Statistical+Fraud+Detection+Engine;Figure+Forensics+%2B+ELA+Analysis;p-Hacking+%7C+Duplicate+Images+%7C+Risk+Scoring;Built+for+the+Global+Scientific+Community" />

<br/><br/>

<a href="https://github.com/Abu-Sameer-66/SciPeerAI">
<img src="https://img.shields.io/badge/%F0%9F%9F%A3%20LIVE%20REPO-GitHub-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI/blob/main/LICENSE">
<img src="https://img.shields.io/badge/License-MIT-9955ff?style=for-the-badge&labelColor=120038"/>
</a>
&nbsp;
<a href="https://sameer-nadeem-portfolio.vercel.app">
<img src="https://img.shields.io/badge/%F0%9F%8C%90%20PORTFOLIO-Live-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.10-bb88ff?style=flat-square&logo=python&logoColor=black&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/FastAPI-0.115-9955ff?style=flat-square&logo=fastapi&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/PyMuPDF-PDF%20Engine-bb88ff?style=flat-square&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/Pillow-Image%20Analysis-9955ff?style=flat-square&labelColor=120038"/>
<img src="https://img.shields.io/badge/imagehash-Perceptual%20Hash-bb88ff?style=flat-square&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/pytest-13%20Tests-9955ff?style=flat-square&logo=pytest&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/Docker-Ready-bb88ff?style=flat-square&logo=docker&logoColor=white&labelColor=0a0020"/>

</div>

---

## The Crisis Nobody Is Solving

**70% of published scientific findings cannot be replicated.**

That number is not a typo. It is the reproducibility crisis — and it is quietly costing the world billions of dollars in wasted follow-up research, corrupting medical decisions, and eroding the public's trust in science itself.

The problem is not that scientists are dishonest. The problem is that **peer review is broken by design.**

Reviewers are overworked. They check one paper at a time. They cannot cross-reference figures across 50 pages. They cannot detect when p-values have been massaged to look significant. They cannot run forensic analysis on every image in a manuscript.

**A machine can.**

That is what SciPeerAI is.

---

## What It Does

<table>
<tr>
<td width="50%">

### ✅ Statistical Audit Engine
Detects p-hacking by identifying suspicious clusters of p-values near the 0.05 threshold. Flags underpowered sample sizes. Catches suspiciously round numbers that real data almost never produces.

**Novel:** Combines three detection patterns into one unified weighted risk score. No existing tool — Statcheck, GRIM, or SPRITE — does all three simultaneously.

### ✅ Figure Forensics Pipeline
Extracts every image from a PDF and runs three-layer forensic analysis: perceptual hashing for duplicate/recycled figures, Error Level Analysis for JPEG editing artifacts, and brightness uniformity scoring for artificial image enhancement.

**Novel:** No existing automated tool combines all three forensic layers in one pipeline.

</td>
<td width="50%">

### 🔧 Methodology Logic Checker *(Coming)*
LLM-powered reasoning engine that reads the methods section and asks: does this method actually prove this claim? The gap between what was done and what was concluded is where most soft fraud lives.

### 🔧 Citation Integrity Analyzer *(Coming)*
Graph-based detection of self-citation abuse, circular citation rings, and references to retracted papers — problems invisible to manual review.

### 🔧 SciPeerBench *(Coming)*
The first curated benchmark dataset of papers with known integrity issues — retracted, corrected, fraudulent — built specifically for evaluating AI review systems. Designed to be a globally cited research contribution.

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
│  │          Statistical Audit Engine           │     │
│  │  regex extraction → pattern recognition     │     │
│  │  → p-hack score + sample score + round      │     │
│  │  → unified weighted risk score 0.0–1.0      │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─────────────────────────────────────────────┐     │
│  │         Figure Forensics Pipeline           │     │
│  │  PDF → image extraction (PyMuPDF)           │     │
│  │  → perceptual hash comparison               │     │
│  │  → Error Level Analysis (ELA)               │     │
│  │  → brightness uniformity scoring            │     │
│  │  → forensic flags with evidence             │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  [ Methodology Checker ]  [ Citation Analyzer ]      │
│  [ Reproducibility   ]    [ Novelty Scorer    ]      │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│                   OUTPUT LAYER                       │
│   FastAPI REST API  ──  3 endpoints live, OAS 3.1    │
│   Structured JSON   ──  flags + evidence + score     │
│   Risk Reports      ──  severity-weighted analysis   │
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

API live at → `http://localhost:8000`
Interactive docs → `http://localhost:8000/docs`

---

## API Usage

### Detect Statistical Fraud
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/statistics" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We recruited n=12 participants. The primary outcome showed significant improvement (p=0.048). Secondary measures were also significant (p=0.049). A tertiary analysis confirmed the pattern (p=0.046)."
  }'
```
```json
{
  "risk_level": "critical",
  "risk_score": 0.9,
  "summary": "Statistical audit flagged 2 high-severity issues, 1 medium-severity concern. Overall risk level: CRITICAL.",
  "flags": [
    {
      "flag_type": "p_hacking_suspected",
      "severity": "high",
      "description": "3 out of 3 reported p-values fall between 0.04 and 0.051. That is 100% clustered right at the significance threshold.",
      "evidence": "[0.048, 0.049, 0.046]",
      "suggestion": "Check whether all conducted analyses are reported. Selective reporting inflates this pattern."
    },
    {
      "flag_type": "small_sample_size",
      "severity": "high",
      "description": "Sample size below recommended minimum: [12]. Studies with n < 30 are typically underpowered.",
      "evidence": "[12]",
      "suggestion": "A post-hoc power analysis would clarify whether the study had sufficient power."
    }
  ],
  "flags_count": 2
}
```

### Analyze Paper Figures
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/figures" \
  -F "file=@paper.pdf"
```

### System Status
```bash
curl http://localhost:8000/api/v1/status
```

---

## Test Suite
```bash
pytest tests/ -v
```
```
tests/test_stat_audit.py::test_flags_suspicious_p_clustering      PASSED
tests/test_stat_audit.py::test_clean_paper_passes                 PASSED
tests/test_stat_audit.py::test_flags_tiny_sample                  PASSED
tests/test_stat_audit.py::test_acceptable_sample_passes           PASSED
tests/test_stat_audit.py::test_flags_exact_p_value                PASSED
tests/test_stat_audit.py::test_result_is_correct_type             PASSED
tests/test_stat_audit.py::test_empty_text_doesnt_crash            PASSED
tests/test_figure_forensics.py::test_identical_images_flagged     PASSED
tests/test_figure_forensics.py::test_different_images_not_flagged PASSED
tests/test_figure_forensics.py::test_flat_image_high_uniformity   PASSED
tests/test_figure_forensics.py::test_noisy_image_low_uniformity   PASSED
tests/test_figure_forensics.py::test_ela_returns_float            PASSED
tests/test_figure_forensics.py::test_no_figures_returns_clean     PASSED

13 passed in 3.07s
```

---

## Real-World Fraud This Catches

| Case | Scale | Fraud Type | SciPeerAI Module |
|:---|:---:|:---|:---|
| Fujii Yoshitaka | 183 papers retracted | Duplicate gel figures recycled across papers | Figure Forensics |
| Diederik Stapel | 58 papers retracted | Fabricated statistical results | Statistical Audit |
| Hwang Woo-suk | Landmark stem cell fraud | Manipulated microscopy images | Figure Forensics |
| LaCour political study | Major retraction | Fabricated survey data patterns | Statistical Audit |

---

## Project Structure
```
SciPeerAI/
├── src/
│   └── scipeerai/
│       ├── api/
│       │   ├── __init__.py            FastAPI app factory
│       │   └── routes.py              All API endpoints
│       ├── modules/
│       │   ├── stat_audit.py          Statistical fraud detection
│       │   └── figure_forensics.py    CV-based forensic analysis
│       └── core/
│           └── pdf_parser.py          PDF ingestion pipeline
├── tests/
│   ├── test_stat_audit.py
│   └── test_figure_forensics.py
├── main.py
└── requirements.txt
```

---

## Roadmap

- [x] Statistical Audit Engine
- [x] Figure Forensics Engine
- [x] Production REST API — FastAPI + OAS 3.1
- [x] 13 unit tests — all passing
- [ ] Methodology Logic Checker — LLM-powered
- [ ] Citation Integrity Analyzer — graph-based
- [ ] Reproducibility Scanner
- [ ] Novelty Scorer
- [ ] SciPeerBench — evaluation benchmark dataset
- [ ] arXiv research paper
- [ ] Web UI — drag and drop paper analysis
- [ ] Cloud deployment
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

</div>" width="100%"/>

</div>
