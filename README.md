<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:000000,30:0a0020,60:120038,100:1a0050&height=320&section=header&text=🔬%20SciPeerAI&fontSize=80&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=The%20AI%20That%20Catches%20What%20Peer%20Reviewers%20Miss&descSize=20&descAlignY=60&descAlign=50&descColor=bb88ff" width="100%"/>

<br/>

<img src="https://readme-typing-svg.herokuapp.com?font=JetBrains+Mono&weight=700&size=24&pause=1000&color=BB88FF&center=true&vCenter=true&width=900&lines=Statistical+Fraud+Detection+Engine;Figure+Forensics+%2B+ELA+Analysis;Methodology+Logic+%2B+Citation+Integrity;27+Tests+%7C+Live+API+%7C+Live+Web+UI" />

<br/><br/>

<a href="https://scipeerai-ui.vercel.app">
<img src="https://img.shields.io/badge/%F0%9F%9F%A2%20LIVE%20WEB%20UI-Vercel-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>
&nbsp;
<a href="https://web-production-f526d.up.railway.app/docs">
<img src="https://img.shields.io/badge/%F0%9F%9F%A2%20LIVE%20API-Railway-9955ff?style=for-the-badge&labelColor=120038"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI">
<img src="https://img.shields.io/badge/%F0%9F%9F%A3%20REPO-GitHub-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>
&nbsp;
<a href="https://github.com/Abu-Sameer-66/SciPeerAI-UI">
<img src="https://img.shields.io/badge/%F0%9F%96%A5%20UI%20REPO-GitHub-9955ff?style=for-the-badge&labelColor=120038"/>
</a>
&nbsp;
<a href="https://sameer-nadeem-portfolio.vercel.app">
<img src="https://img.shields.io/badge/%F0%9F%8C%90%20PORTFOLIO-Live-bb88ff?style=for-the-badge&labelColor=0a0020"/>
</a>

<br/><br/>

<img src="https://img.shields.io/badge/Python-3.10-bb88ff?style=flat-square&logo=python&logoColor=black&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/FastAPI-0.115-9955ff?style=flat-square&logo=fastapi&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/Next.js-15-bb88ff?style=flat-square&logo=nextdotjs&logoColor=white&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/PyMuPDF-PDF%20Engine-9955ff?style=flat-square&labelColor=120038"/>
<img src="https://img.shields.io/badge/imagehash-Perceptual%20Hash-bb88ff?style=flat-square&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/pytest-27%20Tests-9955ff?style=flat-square&logo=pytest&logoColor=white&labelColor=120038"/>
<img src="https://img.shields.io/badge/Railway-API%20Live-bb88ff?style=flat-square&logo=railway&logoColor=white&labelColor=0a0020"/>
<img src="https://img.shields.io/badge/Vercel-UI%20Live-9955ff?style=flat-square&logo=vercel&logoColor=white&labelColor=120038"/>

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
| Web UI | [scipeerai-ui.vercel.app](https://scipeerai-ui.vercel.app) | 🟢 Live |
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
│     Web UI (Vercel)  /  API Call  /  PDF Upload      │
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
│   Next.js Web UI   ──  Vercel, globally accessible   │
│   Structured JSON  ──  flags + evidence + score      │
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
Live UI → `https://scipeerai-ui.vercel.app`

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
  -d '{"text": "Studies show that X. It is well known that Y.", "author_name": ""}'
```

---

## Test Suite
```bash
pytest tests/ -v
```
```
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
├── ui/                                  Web UI (Next.js)
├── main.py
├── Procfile
├── railway.json
└── requirements.txt
```

---

## Roadmap

- [x] Statistical Audit Engine
- [x] Figure Forensics Engine
- [x] Methodology Logic Checker
- [x] Citation Integrity Analyzer
- [x] Production REST API — 5 endpoints
- [x] 27 unit tests — all passing
- [x] Railway API deployment
- [x] Next.js Web UI
- [x] Vercel UI deployment
- [ ] Reproducibility Scanner
- [ ] Novelty Scorer
- [ ] SciPeerBench benchmark dataset
- [ ] arXiv research paper
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
