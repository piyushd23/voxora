# Voxora — Customer voices. Clear insights. Informed action.

> **Voxora** is an enterprise customer intelligence platform that ingests live, verified customer reviews across the **Google Play Store** and **Apple App Store**, clusters friction themes and fee misconceptions using multi-provider AI, synthesizes executive product pulse briefings and regulatory support collateral, and executes governed tool actions via the **Model Context Protocol (MCP)**.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-1.9-purple?style=flat)](https://modelcontextprotocol.io)
[![Multi-AI](https://img.shields.io/badge/AI_Engine-Grok_%7C_OpenAI_%7C_Claude_%7C_Gemini-EA580C?style=flat)](https://github.com/piyushd23/voxora)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Project Specification & Architecture

Voxora is engineered as an end-to-end customer feedback intelligence and agentic dispatch pipeline for FinTech and Mutual Fund applications. It solves customer friction surrounding mutual fund transactions, holding period exit loads, SIP deductions, and regulatory transparency by turning high-volume feedback into structured executive deliverables.

### Core Capabilities

- **High-Volume Dual-Store Ingestion**: Concurrent scraping of 500, 1,000, or 5,000 live reviews across the Google Play Store and Apple App Store, with fallback to custom CSV dataset uploads.
- **Thematic Clustering & Fee Misconception Diagnosis**: Multi-provider semantic analysis identifying top friction clusters, hidden fee confusion (e.g., exit load holding periods, NAV timing), and verbatim quote attribution.
- **Synthesized Executive Artifacts**:
  - Executive Product Pulse Memo ($\le$250 words) with structured Action Priority Matrix.
  - Reusable Customer Support Guidance ($\le$6 bullet points) with official SEBI regulatory source links.
  - RFC-822 formatted team notification email draft (`.eml` and text).
  - Synchronized Google Doc briefing (`google_doc_weekly_pulse.txt`, `weekly_pulse.md`, and `.docx`).
- **Human-in-the-Loop MCP Governance Gate**: Native implementation of the Model Context Protocol (MCP) using stdio JSON-RPC transport. All tool dispatches require explicit human authorization before execution. Rejecting authorization immediately resets the workflow to prevent unapproved data leakage.
- **Multi-LLM Engine with Runtime Fallback**: Flexible runtime supporting **OpenAI (GPT-4o-mini)**, **Grok (xAI)**, **Anthropic Claude (3.5 Haiku / Sonnet)**, and **Google Gemini (2.0 Flash)** with automatic fallback.

---

## 5-Phase Pipeline Architecture

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

## Detailed Phase Specifications

| Phase | Phase Name | System Action | Specification & Deliverables |
|:---:|:---|:---|:---|
| **01** | **Loaded Reviews** | Ingestion & Telemetry | Harvest 500, 1,000, or 5,000 reviews across Google Play & App Store. Calculates rating distribution, store breakdown, and review velocity. |
| **02** | **Themes & Fee Friction** | Semantic Clustering | Clusters customer feedback into core themes (SIP failures, NAV delays, KYC, UI bugs) and detects fee confusion with direct customer quotes. |
| **03** | **Prepared Mail & Docs** | AI Synthesis | Generates an executive pulse memo ($\le$250 words), customer support clarification snippets with official SEBI citations, and team email drafts. |
| **04** | **Review & Approve** | MCP Governance Gate | Human-in-the-loop authorization via stdio JSON-RPC. Single unified approval executes all tools; decline triggers a safe pipeline reset. Phase 05 is strictly locked until approval. |
| **05** | **Mail & Docs Side-by-Side** | Deliverable Inspection & Dispatch | Side-by-side inspection of generated email draft and Google Doc text. Includes 1-click Gmail composer prefill, Google Docs copy assistant modal, reader view, and `.docx` download. |

---

## Model Context Protocol (MCP) Specification

Voxora implements the Model Context Protocol (MCP) standard to establish a secure boundary between AI synthesis and external tool execution.

- **Transport**: `stdio` via subprocess invocation (`mcp_server/server.py`)
- **Protocol**: Model Context Protocol JSON-RPC standard
- **Governance Model**: Human-in-the-loop (HITL) authorization gate
- **Registered Tools**:
  - `create_email_draft`: Generates compliant RFC-822 `.eml` team emails with subject, recipients, and HTML styling.
  - `append_to_document`: Writes synchronized executive briefings to `google_doc_weekly_pulse.txt` and `weekly_pulse.md`.
  - `log_to_tracker`: Writes review telemetry, sentiment aggregates, and governance audit trails to `tracker_log.json`.

---

## AI Engine & Multi-Provider Fallback

The backend provides a unified LLM client with dynamic key management and automatic fallback:

| Provider | Default Model | Fallback Models | Supported Key Prefix |
|:---|:---|:---|:---|
| **Google Gemini** | `gemini-2.0-flash` | `gemini-1.5-flash`, `gemini-1.5-pro` | `AIzaSy...` |
| **OpenAI** | `gpt-4o-mini` | `gpt-4o` | `sk-...`, `sk-proj-...` |
| **Grok (xAI)** | `grok-2-latest` | `grok-beta` | `xai-...` |
| **Anthropic Claude** | `claude-3-5-haiku-20241022` | `claude-3-haiku-20240307`, `claude-3-5-sonnet-20241022` | `sk-ant-...` |

- **Zero-Storage Security**: API keys can be passed via `.env` or entered dynamically through the UI. Keys entered dynamically are held in server memory for that runtime session and are never written to public source code.
- **Sanitization**: Automatic stripping of quotation marks, surrounding chat text, and whitespace from pasted API tokens.

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.10+
- An API key for at least one supported provider:
  - **Google Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
  - **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  - **xAI Grok**: [console.x.ai](https://console.x.ai)
  - **Anthropic Claude**: [console.anthropic.com](https://console.anthropic.com)

### 1. Clone & Set Up Virtual Environment

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

Copy `.env.example` to `.env` and add your preferred API key (or configure dynamically via the UI):

```bash
cp .env.example .env
```

```env
# Configure at least one provider:
GEMINI_API_KEY=your-gemini-api-key
# OR
OPENAI_API_KEY=your-openai-api-key
# OR
GROK_API_KEY=your-grok-api-key
# OR
CLAUDE_API_KEY=your-claude-api-key
```

### 3. Start Application

```bash
cd backend
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## Repository Structure

```
voxora/
├── backend/
│   ├── app.py             # FastAPI orchestrator, REST endpoints & static server
│   ├── scraper.py         # Google Play & Apple App Store review harvest engine
│   ├── analyzer.py        # Multi-provider AI thematic clustering & fee diagnosis
│   ├── generator.py       # Executive memo synthesizer & support snippet builder
│   ├── llm_client.py      # Unified LLM client (OpenAI, Grok, Claude, Gemini)
│   ├── mcp_client.py      # Stdio MCP client with governance approval tracking
│   └── models.py          # Pydantic schemas for data transfer
├── frontend/
│   ├── index.html         # Single-page 5-phase wizard interface
│   ├── style.css          # Signature orange & white enterprise design system
│   └── app.js             # Client-side state manager and API orchestrator
├── mcp_server/
│   └── server.py          # FastMCP server with registered tool specifications
├── outputs/               # Deliverables (.eml, .docx, .txt, .md, .json)
├── reviews.csv            # Baseline customer review dataset
├── sources.md             # SEBI and regulatory reference citations
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
└── README.md
```

---

## License

MIT License © [Piyush Deshmukh](https://github.com/piyushd23)
