<div align="center">

# SciPeerAI

### Automated Scientific Integrity & Peer Review Analysis System

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-13%20Passed-brightgreen?style=for-the-badge)]()
[![Status](https://img.shields.io/badge/Status-Active%20Development-orange?style=for-the-badge)]()

*Catching what human reviewers miss — at machine speed.*

</div>

---

## The Problem

Science has a reproducibility crisis. Over **70% of researchers** report being unable to replicate published findings (Nature, 2016). Peer review is broken — overworked reviewers, 3–6 month delays, human bias, and missed statistical errors.

Every year, flawed papers get published that:
- Waste **billions** in follow-up research budgets
- In medical contexts — **directly harm patients**
- Erode **public trust** in science

The root causes are detectable. They hide in plain sight inside the statistics, figures, and methodology of every paper. The problem is scale — no human reviewer can check everything, in every paper, every time.

**SciPeerAI does.**

---

## What It Does

SciPeerAI is a multi-module REST API that ingests a scientific paper and returns a structured integrity report across six dimensions:
Paper Input (Text / PDF)
│
├── [✅] Statistical Audit      → p-hacking, underpowered studies,
│                                  suspicious round numbers
│
├── [✅] Figure Forensics       → duplicate images, ELA manipulation
│                                  detection, brightness anomalies
│
├── [🔧] Methodology Checker   → LLM-powered logic validation
│
├── [🔧] Citation Analyzer     → retracted sources, self-citation abuse
│
├── [🔧] Reproducibility Check → linked code/data availability
│
└── [🔧] Novelty Scorer        → semantic similarity vs existing literature
Each module returns a **risk score** (0.0 → 1.0), **risk level** (low / medium / high / critical), and **specific flags** with evidence and actionable suggestions.

---

## Novel Technical Contributions

This is not a wrapper around existing tools.

**Statistical Audit Engine**
Combined detection of p-hacking + underpowered sample sizes + suspiciously round p-values into a single unified risk score. Existing tools (Statcheck) check one dimension only.

**Figure Forensics Pipeline**
Three-layer forensic analysis: perceptual hashing for duplicate detection + Error Level Analysis for editing artifacts + brightness uniformity scoring. No existing tool combines all three in one automated pipeline.

**Coming: SciPeerBench**
A curated benchmark dataset of papers with known integrity issues for evaluating AI review systems — the first benchmark of its kind.

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
  "summary": "Statistical audit flagged 2 high-severity issues, 1 medium-severity concern.",
  "flags": [
    {
      "flag_type": "p_hacking_suspected",
      "severity": "high",
      "description": "3 out of 3 reported p-values fall between 0.04 and 0.051. That is 100% clustered right at the significance threshold.",
      "evidence": "[0.048, 0.049, 0.046]",
      "suggestion": "Check whether all conducted analyses are reported."
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
pytest tests/ -v
```

Current: **13 tests — all passing**

---

## Project Structure
SciPeerAI/
├── src/
│   └── scipeerai/
│       ├── api/
│       │   ├── init.py
│       │   └── routes.py
│       ├── modules/
│       │   ├── stat_audit.py
│       │   └── figure_forensics.py
│       └── core/
│           └── pdf_parser.py
├── tests/
│   ├── test_stat_audit.py
│   └── test_figure_forensics.py
├── main.py
└── requirements.txt
---

## Roadmap

- [x] Statistical Audit Engine
- [x] Figure Forensics Engine
- [x] REST API with FastAPI
- [ ] Methodology Logic Checker (LLM-powered)
- [ ] Citation Integrity Analyzer
- [ ] Reproducibility Scanner
- [ ] Novelty Scorer
- [ ] SciPeerBench benchmark dataset
- [ ] Research paper submission
- [ ] Web UI
- [ ] Cloud deployment

---

## Real-World Fraud This Would Catch

| Case | Fraud Type | SciPeerAI Module |
|------|-----------|-----------------|
| Fujii Yoshitaka (183 papers) | Duplicate figures | Figure Forensics |
| Diederik Stapel (psychology) | Statistical anomalies | Statistical Audit |
| Hwang Woo-suk (stem cells) | Image manipulation | Figure Forensics |
| LaCour (political science) | Fabricated data patterns | Statistical Audit |

---

## Author

**Sameer Nadeem** — AI/ML Engineer & Data Scientist

[![GitHub](https://img.shields.io/badge/GitHub-Abu--Sameer--66-181717?style=flat&logo=github)](https://github.com/Abu-Sameer-66)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-sameer--nadeem-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/sameer-nadeem-66339a357/)
[![Portfolio](https://img.shields.io/badge/Portfolio-Live-brightgreen?style=flat)](https://sameer-nadeem-portfolio.vercel.app)

---

<div align="center">

*Built to make science trustworthy again.*

</div>
