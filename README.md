# Voxora — Customer voices. Clear insights. Informed action.

> **Voxora** is an enterprise-grade customer feedback intelligence platform that harvests verified customer reviews across the **Google Play Store** and **Apple App Store**, clusters friction themes with multi-provider AI, synthesizes executive product pulse briefings and regulatory support collateral, and executes governed team dispatches via **Model Context Protocol (MCP)**.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-1.9-purple?style=flat)](https://modelcontextprotocol.io)
[![Multi-AI](https://img.shields.io/badge/AI_Engine-Grok_%7C_OpenAI_%7C_Gemini-EA580C?style=flat)](https://github.com/piyushd23/voxora)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/piyushd23/voxora)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?referralCode=&template=https%3A%2F%2Fgithub.com%2Fpiyushd23%2Fvoxora)

---

## Key Highlights

- **Dual-Store Scraper (500 to 5,000 volume)**: Ingests live customer feedback in parallel from Google Play Store and Apple App Store.
- **AI Feedback Intelligence**: Automatically clusters customer friction, extracts authentic verbatim quotes, and identifies hidden fee & regulatory misconceptions (e.g. mutual fund exit load & holding period rules).
- **Multi-Provider AI Fallback Engine**: Seamless plug-and-play support for **Grok (xAI)**, **OpenAI (GPT-4o)**, and **Google Gemini (2.5 Flash)** with automatic fallback and key validation.
- **Model Context Protocol (MCP) Governance**: Stdio-based JSON-RPC MCP server with human-in-the-loop gating for all external tool executions.
- **Synchronized Deliverables**:
  - Weekly Executive Product Pulse Memo ($\le$250 words)
  - Customer Support & Regulatory Clarification Snippet ($\le$6 bullets with official SEBI citations)
  - Ready-to-send team email draft (`.eml` + 1-click open in Gmail)
  - Live Google Docs synchronized briefing (`.docx` + 1-click clipboard paste assistant)

---

## 5-Step Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Voxora Web Platform (Single-Page)                    │
│   Phase 1: Ingestion  →  Phase 2: Themes  →  Phase 3: Synthesized      │
│   Phase 4: MCP Gate   →  Phase 5: Mail & Docs Side-by-Side             │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │ REST API (FastAPI)             │
┌───────────────────▼────────────────────────────────▼───────────────────┐
│                       FastAPI Backend Server                           │
│  • scraper.py: Parallel Google Play & Apple App Store review harvest   │
│  • analyzer.py: Semantic cluster mapping & verbatim quotes             │
│  • generator.py: Executive memo & SEBI regulatory guidance             │
│  • mcp_client.py: JSON-RPC stdio client with governance approval gating │
└───────────────────┬────────────────────────────────────────────────────┘
                    │ stdio (JSON-RPC)
┌───────────────────▼────────────────────────────────────────────────────┐
│                    MCP Server (mcp SDK / FastMCP)                      │
│   Tools:                                                               │
│    append_to_document    → Updates Google Doc text                     │
│    create_email_draft    → Creates RFC-822 formatted .eml              │
│    log_to_tracker        → Dispatches to structured governance log     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5 Execution Stages

| Stage | Name | Description |
|:---:|:---|:---|
| **01** | **Loaded Reviews** | Harvest 500, 1,000, or 5,000 live reviews from Google Play & Apple Store (or upload custom CSV) with KPI analytics. |
| **02** | **Themes & Fee Friction** | AI cluster mapping with sentiment indicators, verbatim user quotes, and fee misconception diagnosis. |
| **03** | **Prepared Mail & Docs** | Review AI-synthesized executive memo ($\le$250 words), support guidance, and team email dispatch. |
| **04** | **Review & Approve** | Human authorization gate for Model Context Protocol (MCP) tool execution. |
| **05** | **Mail & Docs Side-by-Side** | Side-by-side inspection of outputs with 1-click dispatch to Gmail and Google Docs. |

---

## Quickstart

### Prerequisites
- Python 3.10+
- An API key from any of the following:
  - **xAI Grok**: [console.x.ai](https://console.x.ai)
  - **OpenAI**: [platform.openai.com](https://platform.openai.com)
  - **Google Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 1. Clone & Set Up

```bash
git clone https://github.com/piyushd23/voxora.git
cd voxora

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your API key:

```bash
cp .env.example .env
```

```env
# At least one key is required:
GROK_API_KEY=your-grok-api-key
# OR
OPENAI_API_KEY=your-openai-api-key
# OR
GEMINI_API_KEY=your-gemini-api-key
```

### 3. Run Application

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## ☁️ Cloud Deployment & Hosting

### Option 1: Render (1-Click Deployment)
Click the button below to deploy Voxora directly to Render using the preconfigured [`render.yaml`](render.yaml):

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/piyushd23/voxora)

1. Connect your GitHub account and select your repository.
2. In Environment Variables, enter your `GROK_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`.
3. Render automatically installs dependencies and starts the FastAPI server.

### Option 2: Railway (1-Click Deployment)
Click the button below to deploy on Railway using [`railway.toml`](railway.toml) and [`Procfile`](Procfile):

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?referralCode=&template=https%3A%2F%2Fgithub.com%2Fpiyushd23%2Fvoxora)

### Option 3: Docker Container
Build and run anywhere with Docker:

```bash
docker build -t voxora .
docker run -p 8000:8000 -e GEMINI_API_KEY="your-key" voxora
```

---

## MCP Server Specification

- **Transport**: stdio via subprocess `mcp_server/server.py`
- **Protocol**: Model Context Protocol (MCP) JSON-RPC standard
- **Tools Registered**:
  - `create_email_draft`: Generates compliant RFC-822 `.eml` team emails with subject, recipients, and HTML styling.
  - `append_to_document`: Writes synchronized executive briefings to `google_doc_weekly_pulse.txt` and `weekly_pulse.md`.
  - `log_to_tracker`: Logs review telemetry and governance audit trails to `tracker_log.json`.

---

## Directory Structure

```
voxora/
├── backend/
│   ├── app.py             # FastAPI backend orchestrator & review scraper
│   ├── analyzer.py        # Multi-provider AI clustering engine
│   ├── generator.py       # Pulse memo & support content synthesizer
│   ├── mcp_client.py      # MCP stdio client with governance state
│   └── models.py          # Pydantic schemas
├── frontend/
│   ├── index.html         # Single-page 5-stage workspace
│   ├── style.css          # Signature orange & white design system
│   └── app.js             # Client workflow orchestrator
├── mcp_server/
│   └── server.py          # FastMCP server with registered tools
├── outputs/               # Generated deliverables (.eml, .docx, .txt)
├── reviews.csv            # Sample customer review dataset
├── sources.md             # SEBI and regulatory reference citations
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── README.md
```

---

## License

MIT © [Piyush Deshmukh](https://github.com/piyushd23)
