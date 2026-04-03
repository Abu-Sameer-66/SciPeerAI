<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0a0a0a,50:0d0040,100:001a33&height=300&section=header&text=🔬%20SciPeerAI&fontSize=75&fontColor=00aaff&animation=fadeIn&fontAlignY=38&desc=Automated%20Scientific%20Integrity%20%26%20Peer%20Review%20Analysis%20System&descSize=18&descAlignY=58&descAlign=50&descColor=0077cc" width="100%"/>

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&weight=700&size=22&pause=1000&color=00AAFF&center=true&vCenter=true&width=900&lines=p-Hacking+Detection+%E2%80%94+Statistical+Audit+Engine;Figure+Forensics+%E2%80%94+ELA+%2B+Perceptual+Hashing;Methodology+Logic+Checker+%E2%80%94+LLM-Powered;Production+FastAPI+%7C+Docker+%7C+13+Tests+Passing" />

<br/><br/>

<a href="https://github.com/Abu-Sameer-66/SciPeerAI">
<img src="https://img.shields.io/badge/%F0%9F%94%AC%20SciPeerAI-Scientific%20Integrity%20AI-00aaff?style=for-the-badge&labelColor=001a33"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI/blob/main/LICENSE">
<img src="https://img.shields.io/badge/License-MIT-0077cc?style=for-the-badge&labelColor=001a33"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI/actions">
<img src="https://img.shields.io/badge/Tests-13%20Passing-00ff88?style=for-the-badge&labelColor=001a33"/>
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.10-00aaff?style=flat-square&logo=python&logoColor=black&labelColor=001a33"/>
<img src="https://img.shields.io/badge/FastAPI-REST%20API-0077cc?style=flat-square&logo=fastapi&logoColor=white&labelColor=001a33"/>
<img src="https://img.shields.io/badge/PyMuPDF-PDF%20Engine-00aaff?style=flat-square&labelColor=001a33"/>
<img src="https://img.shields.io/badge/Pillow-Image%20Analysis-0077cc?style=flat-square&labelColor=001a33"/>
<img src="https://img.shields.io/badge/imagehash-Perceptual%20Hash-00aaff?style=flat-square&labelColor=001a33"/>
<img src="https://img.shields.io/badge/pytest-13%20Tests-00ff88?style=flat-square&logo=pytest&logoColor=black&labelColor=001a33"/>
<img src="https://img.shields.io/badge/Docker-Ready-0077cc?style=flat-square&logo=docker&logoColor=white&labelColor=001a33"/>

</div>

---

## The Problem

Science has a **reproducibility crisis**.

Over **70% of researchers** cannot replicate published findings (Nature, 2016). Peer review is broken — overworked reviewers, months of delays, human bias, missed statistical fraud. Every year, flawed papers get published that:

- Waste **billions** in follow-up research
- In medical contexts — **directly harm patients**
- Erode **public trust** in science globally

The root causes are detectable. They hide inside the statistics, figures, and methodology of every paper. The problem is **scale** — no human reviewer can check everything, in every paper, every time.

**SciPeerAI does.**

---

## What It Does

SciPeerAI is a multi-module REST API that ingests a scientific paper and returns a structured integrity report across six dimensions:
Paper Input (Text / PDF)
│
├── [✅] Statistical Audit      → p-hacking, underpowered studies,
│                                  suspicious round numbers, missing tests
│
├── [✅] Figure Forensics       → duplicate images (perceptual hash),
│                                  ELA editing artifacts, brightness anomalies
│
├── [🔧] Methodology Checker   → LLM-powered logic validation
│                                  "Does the method actually prove the claim?"
│
├── [🔧] Citation Analyzer     → retracted sources, self-citation abuse,
│                                  citation manipulation detection
│
├── [🔧] Reproducibility Check → linked code/data availability,
│                                  environment reproducibility scoring
│
└── [🔧] Novelty Scorer        → semantic similarity vs existing literature,
incremental vs genuinely novel contribution
Every module returns:
- **Risk Score** `0.0 → 1.0`
- **Risk Level** `low / medium / high / critical`
- **Specific Flags** with evidence and actionable reviewer suggestions

---

## Novel Technical Contributions

This is not a wrapper around existing tools. Each module introduces approaches not found in any current peer review system.

<table>
<tr>
<td width="50%">

### 📊 Statistical Audit Engine
Combined detection of **p-hacking + underpowered sample sizes + suspiciously round p-values** into a single unified risk score. Existing tools (Statcheck) check one dimension only. We check four simultaneously and weight them into a calibrated risk score.

</td>
<td width="50%">

### 🖼️ Figure Forensics Pipeline
Three-layer forensic analysis: **perceptual hashing** for duplicate detection + **Error Level Analysis** for JPEG editing artifacts + **brightness uniformity scoring** for artificial enhancement. No existing tool combines all three in one automated pipeline.

</td>
</tr>
<tr>
<td width="50%">

### 🧠 SciPeerBench (Coming)
A curated benchmark dataset of papers with **known integrity issues** (retracted, corrected, fraudulent) for evaluating AI review systems. The first benchmark of its kind — designed to be a globally citable research contribution.

</td>
<td width="50%">

### ⚙️ Unified Risk Engine
All modules feed into a single **pipeline orchestrator** that produces a composite integrity report. A journal can integrate one API call and get back a structured audit — replacing months of manual review.

</td>
</tr>
</table>

---

## Why SciPeerAI is Different

| Capability | Existing Tools | SciPeerAI |
|:---|:---:|:---:|
| p-hacking detection | ✅ Statcheck (basic) | ✅ Multi-pattern |
| Sample size validation | ❌ | ✅ |
| Round p-value detection | ❌ | ✅ |
| Figure duplicate detection | ❌ | ✅ Perceptual hash |
| ELA editing artifacts | ❌ | ✅ |
| Brightness forensics | ❌ | ✅ |
| Unified risk score | ❌ | ✅ 0.0–1.0 |
| REST API integration | ❌ | ✅ 3 endpoints live |
| Methodology logic check | ❌ | 🔧 Coming |
| Open source + extensible | ❌ | ✅ |

---

## System Architecture
┌────────────────────────────────────────────────────┐
│                    INPUT LAYER                     │
│         Paper Text  /  PDF Upload  /  API          │
└──────────────────────────┬─────────────────────────┘
│
┌──────────────────────────▼─────────────────────────┐
│                  CORE PIPELINE                     │
│                                                    │
│  PDFParser ──────── Text Extraction                │
│      │              Section splitting              │
│      │              Figure extraction              │
│      │                                             │
│  StatAuditEngine ── p-value extraction             │
│      │              p-hacking detection            │
│      │              Sample size validation         │
│      │              Round number detection         │
│      │                                             │
│  FigureForensics ── Perceptual hashing             │
│                     Error Level Analysis           │
│                     Brightness uniformity          │
└──────────────────────────┬─────────────────────────┘
│
┌──────────────────────────▼─────────────────────────┐
│                 INTELLIGENCE LAYER                 │
│                                                    │
│  Risk Scoring Engine                               │
│  ├── Per-module weighted risk score (0.0–1.0)      │
│  ├── Severity classification (low→critical)        │
│  └── Natural language summary generation          │
│                                                    │
│  Flag Aggregator                                   │
│  ├── flag_type + severity + description            │
│  ├── evidence (exact values/text)                  │
│  └── actionable suggestion for reviewer            │
└──────────────────────────┬─────────────────────────┘
│
┌──────────────────────────▼─────────────────────────┐
│                   OUTPUT LAYER                     │
│                                                    │
│  FastAPI REST API  ── OAS 3.1 interactive docs     │
│  Structured JSON   ── Exportable integrity report  │
│  (Coming) Web UI   ── Drag-drop paper analysis     │
└────────────────────────────────────────────────────┘
---

## Quick Start

### Prerequisites
- Python 3.10+
- Anaconda

### Installation
```bash
git clone https://github.com/Abu-Sameer-66/SciPeerAI.git
cd SciPeerAI

conda create -n scipeerai python=3.10 -y
conda activate scipeerai

pip install -r requirements.txt
```

### Run
```bash
python main.py
```

API live at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

---

## API Usage

### Statistical Audit
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/statistics" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "We recruited n=12 participants. Results were significant (p=0.048). Secondary outcome also significant (p=0.049). Tertiary measure borderline significant (p=0.046)."
  }'
```

**Response:**
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

### Figure Forensics
```bash
curl -X POST "http://localhost:8000/api/v1/analyze/figures" \
  -F "file=@your_paper.pdf"
```

### System Status
```bash
curl http://localhost:8000/api/v1/status
```

---

## Running Tests
```bash
# Full test suite
pytest tests/ -v

# Individual modules
pytest tests/test_stat_audit.py -v
pytest tests/test_figure_forensics.py -v
```

**Current: 13 tests — all passing**
tests/test_stat_audit.py::test_flags_suspicious_p_clustering     PASSED
tests/test_stat_audit.py::test_clean_paper_passes                PASSED
tests/test_stat_audit.py::test_flags_tiny_sample                 PASSED
tests/test_stat_audit.py::test_acceptable_sample_passes          PASSED
tests/test_stat_audit.py::test_flags_exact_p_value               PASSED
tests/test_stat_audit.py::test_result_is_correct_type            PASSED
tests/test_stat_audit.py::test_empty_text_doesnt_crash           PASSED
tests/test_figure_forensics.py::test_identical_images_flagged    PASSED
tests/test_figure_forensics.py::test_different_images_not_flagged PASSED
tests/test_figure_forensics.py::test_flat_image_high_uniformity  PASSED
tests/test_figure_forensics.py::test_noisy_image_low_uniformity  PASSED
tests/test_figure_forensics.py::test_ela_returns_float           PASSED
tests/test_figure_forensics.py::test_no_figures_returns_clean    PASSED
---

## Project Structure
SciPeerAI/
├── src/
│   └── scipeerai/
│       ├── api/
│       │   ├── init.py          FastAPI app factory
│       │   └── routes.py            All API endpoints
│       ├── modules/
│       │   ├── stat_audit.py        Statistical integrity engine
│       │   └── figure_forensics.py  CV-based figure analysis
│       └── core/
│           └── pdf_parser.py        PDF ingestion pipeline
├── tests/
│   ├── test_stat_audit.py
│   └── test_figure_forensics.py
├── main.py
└── requirements.txt
---

## Real-World Fraud This Catches

| Case | Fraud Type | SciPeerAI Module |
|:---|:---|:---|
| Fujii Yoshitaka — 183 papers retracted | Duplicate gel figures | Figure Forensics |
| Diederik Stapel — psychology fabrication | Statistical anomalies | Statistical Audit |
| Hwang Woo-suk — stem cell fraud | Image manipulation | Figure Forensics |
| LaCour — political science fabrication | Fabricated data patterns | Statistical Audit |

---

## Novel Technical Contributions

**Statistical Audit Engine**
Combined detection of p-hacking + underpowered sample sizes + suspiciously round p-values into a single unified weighted risk score. No existing tool (Statcheck, GRIM, SPRITE) combines all three dimensions simultaneously.

**Figure Forensics Pipeline**
Three-layer forensic analysis in one pipeline: perceptual hashing for duplicate detection + Error Level Analysis for JPEG editing artifacts + brightness uniformity scoring for artificial enhancement. No existing automated tool combines all three.

**SciPeerBench (Coming)**
A curated benchmark dataset of papers with known integrity issues — retracted, corrected, fraudulent — for evaluating AI review systems. The first benchmark of its kind designed explicitly for automated integrity detection research.

---

## Roadmap

- [x] Statistical Audit Engine — p-hacking, sample size, round numbers
- [x] Figure Forensics Engine — duplicate detection, ELA, brightness
- [x] Production REST API — FastAPI, OAS 3.1, file upload
- [x] 13 unit tests — all passing
- [ ] Methodology Logic Checker — LLM-powered
- [ ] Citation Integrity Analyzer — graph-based
- [ ] Reproducibility Scanner
- [ ] Novelty Scorer
- [ ] SciPeerBench — evaluation benchmark dataset
- [ ] Research paper — arXiv preprint
- [ ] Web UI — drag and drop paper analysis
- [ ] Cloud deployment — Railway / HuggingFace Spaces
- [ ] Stripe integration — pay-per-analysis API

---

## Author

<div align="center">

**Sameer Nadeem** — AI/ML Engineer · Data Scientist · GSoC 2026 Contributor

<br/>

<a href="https://sameer-nadeem-portfolio.vercel.app"><img src="https://img.shields.io/badge/Portfolio-Live-00aaff?style=for-the-badge&labelColor=0d0d2b"/></a>
<a href="https://github.com/Abu-Sameer-66"><img src="https://img.shields.io/badge/GitHub-Abu--Sameer--66-0077cc?style=for-the-badge&logo=github&labelColor=001a33"/></a>
<a href="https://www.linkedin.com/in/sameer-nadeem-66339a357/"><img src="https://img.shields.io/badge/LinkedIn-Sameer%20Nadeem-00aaff?style=for-the-badge&logo=linkedin&labelColor=0d0d2b"/></a>
<a href="https://www.kaggle.com/sameernadeem66"><img src="https://img.shields.io/badge/Kaggle-sameernadeem66-0077cc?style=for-the-badge&logo=kaggle&labelColor=001a33"/></a>

</div>

---

<div align="center">

*Built to make science trustworthy again.*

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d0d2b,50:001a33,100:0a0a0a&height=120&section=footer" width="100%"/>

</div>