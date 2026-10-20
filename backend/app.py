"""
FastAPI Application — Main backend for the Product Pulse AI Workflow.
Orchestrates dual-store review analysis (Google Play & Apple App Store),
content generation, and MCP actions with approval gating.
"""

import json
import os
import sys
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import (
    AnalysisResult, GeneratedContent, MCPAction,
    MCPActionRequest, WorkflowPayload, EmailDraft
)
from analyzer import load_reviews_from_csv, analyze_reviews
from generator import (
    generate_all_content, build_workflow_payload, build_email_draft
)
from mcp_client import MCPClient

# ─── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Voxora — Customer Feedback Intelligence",
    description="Customer voices. Clear insights. Informed action. Scrapes Google Play & Apple App Store and executes MCP governance.",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
REVIEWS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

os.makedirs(OUTPUTS_DIR, exist_ok=True)

# ─── State ───────────────────────────────────────────────────────────────────

# In-memory state
workflow_state = {
    "reviews_loaded": False,
    "reviews_path": None,
    "scraper_meta": None,
    "analysis": None,
    "content": None,
    "payload": None,
    "email_draft": None,
    "mcp_actions": [],
    "step": "idle"  # idle → reviews_loaded → analyzing → analyzed → generating → generated → approving → completed
}

mcp_client = MCPClient()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


class ConfigUpdateRequest(BaseModel):
    openai_api_key: Optional[str] = None
    grok_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    preferred_provider: Optional[str] = None


@app.get("/api/config")
async def get_config():
    """Get active AI provider and key configuration status."""
    from llm_client import get_active_provider_info
    return get_active_provider_info()


@app.post("/api/config")
async def update_config(request: ConfigUpdateRequest):
    """Update AI API keys dynamically (OpenAI, Grok/xAI, Gemini)."""
    env_path = os.path.join(REVIEWS_DIR, ".env")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        env_vars[parts[0].strip()] = parts[1].strip()

    from llm_client import sanitize_api_key

    if request.openai_api_key is not None and request.openai_api_key.strip():
        k = sanitize_api_key(request.openai_api_key)
        os.environ["OPENAI_API_KEY"] = k
        env_vars["OPENAI_API_KEY"] = k

    if request.grok_api_key is not None and request.grok_api_key.strip():
        k = sanitize_api_key(request.grok_api_key)
        os.environ["GROK_API_KEY"] = k
        os.environ["XAI_API_KEY"] = k
        env_vars["GROK_API_KEY"] = k
        env_vars["XAI_API_KEY"] = k

    if request.gemini_api_key is not None and request.gemini_api_key.strip():
        k = sanitize_api_key(request.gemini_api_key)
        os.environ["GEMINI_API_KEY"] = k
        env_vars["GEMINI_API_KEY"] = k

    if request.preferred_provider:
        p = request.preferred_provider.strip().lower()
        os.environ["PREFERRED_LLM_PROVIDER"] = p
        env_vars["PREFERRED_LLM_PROVIDER"] = p

    try:
        with open(env_path, "w", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f"{k}={v}\n")
    except Exception:
        pass

    from llm_client import get_active_provider_info
    info = get_active_provider_info()
    return {
        "status": "success",
        "message": f"AI configuration saved. Active provider: {info['active_provider']} ({info['active_model']}).",
        "provider_info": info
    }



@app.get("/api/status")
async def get_status():
    """Get the current workflow status."""
    return {
        "step": workflow_state["step"],
        "reviews_loaded": workflow_state["reviews_loaded"],
        "has_analysis": workflow_state["analysis"] is not None,
        "has_content": workflow_state["content"] is not None,
        "pending_actions": len([
            a for a in workflow_state["mcp_actions"]
            if a.get("status") == "pending"
        ]) if isinstance(workflow_state["mcp_actions"], list) else 0,
        "scraper_meta": workflow_state.get("scraper_meta")
    }


class ScrapeReviewsRequest(BaseModel):
    app_query: Optional[str] = "Groww"
    store: Optional[str] = "both"  # "both", "google", "apple"
    count: Optional[int] = 500
    country: Optional[str] = "in"


@app.post("/api/scrape-reviews")
async def handle_scrape_reviews(request: Optional[ScrapeReviewsRequest] = None):
    """
    Scrape customer reviews from Google Play Store, Apple App Store, or Both.
    Supports app name queries, package IDs, and preset lookups.
    """
    app_query = request.app_query if request and request.app_query else "Groww"
    store = request.store if request and request.store else "both"
    count = request.count if request and request.count else 500
    country = request.country if request and request.country else "in"

    from scraper import scrape_reviews
    scraped_csv = os.path.join(OUTPUTS_DIR, "scraped_reviews.csv")
    reviews, meta = scrape_reviews(
        app_query=app_query,
        store=store,
        count=count,
        country=country,
        save_csv_path=scraped_csv
    )

    if not reviews:
        raise HTTPException(500, "Failed to scrape reviews from selected stores.")

    workflow_state["reviews_path"] = scraped_csv
    workflow_state["reviews_loaded"] = True
    workflow_state["scraper_meta"] = meta
    from analyzer import aggregate_dataset_metrics
    metrics = aggregate_dataset_metrics(reviews)

    return {
        "status": "success",
        "app_name": meta["app_name"],
        "play_id": meta["play_id"],
        "apple_id": meta["apple_id"],
        "store": meta["store"],
        "review_count": meta["total_count"],
        "google_count": meta["google_count"],
        "apple_count": meta["apple_count"],
        "metrics": metrics,
        "preview": [r.model_dump() for r in reviews[:60]],
        "date_range": meta["date_range"]
    }


@app.post("/api/upload-reviews")
async def upload_reviews(file: UploadFile = File(...)):
    """Upload a reviews CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted")

    upload_path = os.path.join(REVIEWS_DIR, "uploaded_reviews.csv")
    content = await file.read()
    with open(upload_path, "wb") as f:
        f.write(content)

    workflow_state["reviews_path"] = upload_path
    workflow_state["reviews_loaded"] = True
    workflow_state["step"] = "reviews_loaded"

    reviews = load_reviews_from_csv(upload_path)
    google_count = sum(1 for r in reviews if "Google" in r.source)
    apple_count = sum(1 for r in reviews if "Apple" in r.source or "App Store" in r.source)

    meta = {
        "app_name": "Custom Uploaded Reviews",
        "play_id": "N/A",
        "apple_id": "N/A",
        "store": "custom",
        "total_count": len(reviews),
        "google_count": google_count,
        "apple_count": apple_count,
        "date_range": f"{reviews[0].date} to {reviews[-1].date}" if reviews else "N/A"
    }
    workflow_state["scraper_meta"] = meta

    from analyzer import aggregate_dataset_metrics
    metrics = aggregate_dataset_metrics(reviews)

    return {
        "status": "success",
        "filename": file.filename,
        "review_count": len(reviews),
        "google_count": google_count,
        "apple_count": apple_count,
        "metrics": metrics,
        "preview": [r.model_dump() for r in reviews[:60]],
        "date_range": meta["date_range"]
    }


@app.get("/api/load-default-reviews")
async def load_default_reviews():
    """Load the default reviews.csv."""
    default_path = os.path.join(REVIEWS_DIR, "reviews.csv")
    if not os.path.exists(default_path):
        raise HTTPException(404, "Default reviews.csv not found")

    workflow_state["reviews_path"] = default_path
    workflow_state["reviews_loaded"] = True
    workflow_state["step"] = "reviews_loaded"

    reviews = load_reviews_from_csv(default_path)
    google_count = sum(1 for r in reviews if "Google" in r.source)
    apple_count = sum(1 for r in reviews if "App Store" in r.source or "Apple" in r.source)

    meta = {
        "app_name": "Mutual Fund Feedback (Default)",
        "play_id": "com.nextbillion.groww",
        "apple_id": "1404871703",
        "store": "both",
        "total_count": len(reviews),
        "google_count": google_count,
        "apple_count": apple_count,
        "date_range": f"{reviews[0].date} to {reviews[-1].date}" if reviews else "N/A"
    }
    workflow_state["scraper_meta"] = meta

    from analyzer import aggregate_dataset_metrics
    metrics = aggregate_dataset_metrics(reviews)

    return {
        "status": "success",
        "filename": "reviews.csv",
        "review_count": len(reviews),
        "google_count": google_count,
        "apple_count": apple_count,
        "metrics": metrics,
        "preview": [r.model_dump() for r in reviews[:60]],
        "date_range": meta["date_range"]
    }


@app.post("/api/analyze")
async def run_analysis():
    """Step 1: Analyze reviews — theme clustering, quote extraction, fee detection."""
    from llm_client import get_active_provider_info
    info = get_active_provider_info()
    if not info.get("is_online"):
        raise HTTPException(
            status_code=400,
            detail="API key is mandatory. Please configure your OpenAI, Grok (xAI), or Google Gemini API key to proceed."
        )

    if not workflow_state["reviews_loaded"]:
        raise HTTPException(400, "No reviews loaded. Scrape or load reviews first.")

    workflow_state["step"] = "analyzing"

    try:
        reviews = load_reviews_from_csv(workflow_state["reviews_path"])
        analysis = await analyze_reviews(reviews)

        workflow_state["analysis"] = analysis.model_dump()
        workflow_state["step"] = "analyzed"

        return {
            "status": "success",
            "analysis": analysis.model_dump()
        }
    except Exception as e:
        workflow_state["step"] = "reviews_loaded"
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/api/generate")
async def run_generation():
    """Step 2: Generate weekly pulse and fee explanation."""
    from llm_client import get_active_provider_info
    info = get_active_provider_info()
    if not info.get("is_online"):
        raise HTTPException(
            status_code=400,
            detail="API key is mandatory. Please configure your OpenAI, Grok (xAI), or Google Gemini API key to proceed."
        )

    if workflow_state["analysis"] is None:
        raise HTTPException(400, "No analysis available. Run analysis first.")

    workflow_state["step"] = "generating"

    try:
        analysis = AnalysisResult(**workflow_state["analysis"])
        content = await generate_all_content(analysis)
        payload = build_workflow_payload(analysis, content)
        email_draft = build_email_draft(analysis, content, payload)

        workflow_state["content"] = content.model_dump()
        workflow_state["payload"] = payload.model_dump()
        workflow_state["email_draft"] = email_draft.model_dump()
        workflow_state["step"] = "generated"

        # Construct full Google Doc formatted briefing
        doc_content = (
            f"{payload.weekly_pulse}\n\n"
            f"---\n\n"
            f"## Fee Clarification: {payload.identified_fee_issue or 'Fee Issue'}\n"
            f"### Reusable Support Snippet\n\n"
            + "\n".join(f"  • {b}" for b in payload.explanation_bullets)
            + "\n\n**Official Sources:**\n"
            + "\n".join(f"  - {s}" for s in payload.source_links)
        )

        title = f"Weekly Pulse — {payload.date}"
        doc_text_entry = (
            "========================================================================\n"
            f"GOOGLE DOC: {title.upper()}\n"
            f"UPDATED VIA MCP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "STATUS: READY FOR GOOGLE DOCS SYNCHRONIZATION\n"
            "========================================================================\n\n"
            f"{doc_content}\n\n"
            "------------------------------------------------------------------------\n"
            "End of Google Doc Section\n\n"
        )

        # Write txt file for immediate preview and copy
        doc_txt_filepath = os.path.join(OUTPUTS_DIR, "google_doc_weekly_pulse.txt")
        with open(doc_txt_filepath, "w", encoding="utf-8") as f:
            f.write(doc_text_entry)

        # Write docx file for immediate download
        try:
            import docx
            doc = docx.Document()
            doc.add_heading(title, 0)
            for line in doc_content.split("\n"):
                line_str = line.strip()
                if not line_str:
                    continue
                if line_str.startswith("## "):
                    doc.add_heading(line_str[3:], level=1)
                elif line_str.startswith("### "):
                    doc.add_heading(line_str[4:], level=2)
                elif line_str.startswith("- ") or line_str.startswith("• "):
                    doc.add_paragraph(line_str[2:], style="List Bullet")
                elif line_str == "---":
                    doc.add_paragraph("—" * 30)
                else:
                    doc.add_paragraph(line_str)
            docx_filepath = os.path.join(OUTPUTS_DIR, "google_doc_weekly_pulse.docx")
            doc.save(docx_filepath)
        except Exception as e:
            logger.warning(f"Could not generate docx in generate endpoint: {e}")

        # Also write preview email draft
        email_txt_filepath = os.path.join(OUTPUTS_DIR, "email_draft_latest.txt")
        with open(email_txt_filepath, "w", encoding="utf-8") as f:
            f.write(
                f"SUBJECT: {email_draft.subject}\n"
                f"TO: {email_draft.to}\n"
                f"CC: {email_draft.cc}\n"
                f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"---------------------------------------------------\n\n"
                f"{email_draft.body}\n"
            )

        return {
            "status": "success",
            "weekly_pulse": content.weekly_pulse.model_dump(),
            "fee_explanation": content.fee_explanation.model_dump(),
            "payload": payload.model_dump(),
            "email_draft": email_draft.model_dump(),
            "google_doc_text": doc_text_entry,
            "email_text": email_draft.body
        }
    except Exception as e:
        workflow_state["step"] = "analyzed"
        raise HTTPException(500, f"Generation failed: {str(e)}")


@app.post("/api/prepare-actions")
async def prepare_mcp_actions():
    """Step 3: Prepare MCP actions for approval."""
    if workflow_state["payload"] is None:
        raise HTTPException(400, "No content generated. Run generation first.")

    try:
        await mcp_client.connect()

        # List available tools
        tools = await mcp_client.list_tools()

        # Prepare actions
        actions = await mcp_client.prepare_actions(
            workflow_state["payload"],
            workflow_state["email_draft"]
        )

        workflow_state["mcp_actions"] = [a.model_dump() for a in actions]
        workflow_state["step"] = "approving"

        return {
            "status": "success",
            "tools": tools,
            "pending_actions": [a.model_dump() for a in actions]
        }
    except Exception as e:
        raise HTTPException(500, f"MCP preparation failed: {str(e)}")


@app.post("/api/approve-action")
async def approve_action(request: MCPActionRequest):
    """Approve or reject a specific MCP action."""
    try:
        if request.approved:
            action = mcp_client.approve_action(request.action_id)
        else:
            action = mcp_client.reject_action(request.action_id)

        # Update state
        for i, a in enumerate(workflow_state["mcp_actions"]):
            if a["action_id"] == request.action_id:
                workflow_state["mcp_actions"][i] = action.model_dump()
                break

        return {
            "status": "success",
            "action": action.model_dump()
        }
    except Exception as e:
        raise HTTPException(500, f"Approval failed: {str(e)}")


@app.post("/api/execute-actions")
async def execute_approved_actions():
    """Execute all approved MCP actions."""
    results = []

    try:
        await mcp_client.connect()

        for action_data in workflow_state["mcp_actions"]:
            action_id = action_data["action_id"]
            action = mcp_client.pending_actions.get(action_id)

            if action and action.status == "approved":
                result = await mcp_client.execute_action(action_id)
                results.append({
                    "action_id": action_id,
                    "tool_name": action.tool_name,
                    "status": "executed",
                    "result": result
                })
                # Update state
                for i, a in enumerate(workflow_state["mcp_actions"]):
                    if a["action_id"] == action_id:
                        workflow_state["mcp_actions"][i]["status"] = "executed"
                        break
            elif action and action.status == "rejected":
                results.append({
                    "action_id": action_id,
                    "tool_name": action.tool_name,
                    "status": "skipped (rejected)",
                    "result": None
                })

        workflow_state["step"] = "completed"

        return {
            "status": "success",
            "results": results,
            "message": "All approved actions have been executed."
        }
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {str(e)}")


@app.post("/api/approve-all")
@app.post("/api/run-both-actions")
async def approve_and_execute_all():
    """
    One-click approval and execution of MCP actions.
    Runs both tools:
      1. create_email_draft (Email draft creation)
      2. append_to_document (Google Doc text update)
      3. log_to_tracker (Structured tracker entry)
    """
    results = []

    try:
        # If actions are not prepared yet, prepare them on the fly
        if not workflow_state["mcp_actions"] and workflow_state["payload"]:
            await mcp_client.connect()
            actions = await mcp_client.prepare_actions(
                workflow_state["payload"],
                workflow_state["email_draft"]
            )
            workflow_state["mcp_actions"] = [a.model_dump() for a in actions]

        await mcp_client.connect()

        for action_data in workflow_state["mcp_actions"]:
            action_id = action_data["action_id"]
            action = mcp_client.pending_actions.get(action_id)
            if action and action.status in ("pending", "approved"):
                mcp_client.approve_action(action_id)
                result = await mcp_client.execute_action(action_id)
                results.append({
                    "action_id": action_id,
                    "tool_name": action.tool_name,
                    "status": "executed",
                    "result": result
                })
                for i, a in enumerate(workflow_state["mcp_actions"]):
                    if a["action_id"] == action_id:
                        workflow_state["mcp_actions"][i]["status"] = "executed"
                        break

        workflow_state["step"] = "completed"

        # Read back latest Google Doc text and Email draft text for UI preview
        doc_text = ""
        doc_path = os.path.join(OUTPUTS_DIR, "google_doc_weekly_pulse.txt")
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                doc_text = f.read()

        email_text = ""
        email_txt_path = os.path.join(OUTPUTS_DIR, "email_draft_latest.txt")
        if os.path.exists(email_txt_path):
            with open(email_txt_path, "r", encoding="utf-8") as f:
                email_text = f.read()

        return {
            "status": "success",
            "results": results,
            "google_doc_text": doc_text,
            "email_text": email_text,
            "message": "Both actions (Email Creation & Google Doc Update) executed successfully via MCP."
        }
    except Exception as e:
        raise HTTPException(500, f"Execution failed: {str(e)}")


@app.get("/api/doc-text")
async def get_google_doc_text():
    """Get the current content of the Google Doc text update."""
    doc_path = os.path.join(OUTPUTS_DIR, "google_doc_weekly_pulse.txt")
    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "source": "google_doc_weekly_pulse.txt"}

    md_path = os.path.join(OUTPUTS_DIR, "weekly_pulse.md")
    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "source": "weekly_pulse.md"}

    return {"content": "No Google Doc content updated yet.", "source": None}


@app.get("/api/doc-view", response_class=HTMLResponse)
async def view_google_doc_html():
    """Render a clean, minimal document reader view of the weekly pulse document."""
    content = ""
    title = "Weekly Product Pulse — Notes & Document View"
    doc_path = os.path.join(OUTPUTS_DIR, "google_doc_weekly_pulse.txt")
    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        md_path = os.path.join(OUTPUTS_DIR, "weekly_pulse.md")
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif workflow_state.get("payload"):
            payload = workflow_state["payload"]
            content = (
                f"{payload.get('weekly_pulse', '')}\n\n"
                f"---\n\n"
                f"## Fee Clarification: {payload.get('identified_fee_issue', 'Fee Issue')}\n"
                f"### Reusable Support Snippet\n\n"
                + "\n".join(f"  • {b}" for b in payload.get("explanation_bullets", []))
                + "\n\n**Official Sources:**\n"
                + "\n".join(f"  - {s}" for s in payload.get("source_links", []))
            )
        else:
            content = "No document has been generated yet. Please run the workflow first."

    import html
    escaped_raw = html.escape(content)

    # Basic markdown parsing to rich HTML
    lines = content.split("\n")
    formatted_html = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("===") or stripped.startswith("---") or stripped.startswith("GOOGLE DOC:") or stripped.startswith("UPDATED VIA") or stripped.startswith("STATUS:") or stripped.startswith("End of Google Doc"):
            if in_list:
                formatted_html.append("</ul>")
                in_list = False
            if stripped.startswith("---"):
                formatted_html.append("<hr class='doc-divider'/>")
            continue

        if stripped.startswith("## "):
            if in_list:
                formatted_html.append("</ul>")
                in_list = False
            h_text = html.escape(stripped[3:])
            formatted_html.append(f"<h2 class='doc-h2'>{h_text}</h2>")
        elif stripped.startswith("### "):
            if in_list:
                formatted_html.append("</ul>")
                in_list = False
            h_text = html.escape(stripped[4:])
            formatted_html.append(f"<h3 class='doc-h3'>{h_text}</h3>")
        elif stripped.startswith("- ") or stripped.startswith("• "):
            if not in_list:
                formatted_html.append("<ul class='doc-ul'>")
                in_list = True
            b_text = html.escape(stripped[2:])
            # Turn links into clickable anchors
            import re
            b_text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', b_text)
            formatted_html.append(f"<li>{b_text}</li>")
        else:
            if in_list:
                formatted_html.append("</ul>")
                in_list = False
            p_text = html.escape(stripped)
            # Check for quotes
            if p_text.startswith('&quot;') or p_text.startswith('"'):
                formatted_html.append(f"<div class='doc-quote'>{p_text}</div>")
            else:
                formatted_html.append(f"<p class='doc-p'>{p_text}</p>")

    if in_list:
        formatted_html.append("</ul>")

    parsed_body = "\n".join(formatted_html)
    
    html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f8fafc;
      color: #1e293b;
      line-height: 1.65;
      padding: 2.5rem 1rem;
      display: flex;
      justify-content: center;
    }}
    .doc-container {{
      max-width: 840px;
      width: 100%;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.03);
      padding: 3rem 3.5rem;
    }}
    @media (max-width: 640px) {{
      .doc-container {{ padding: 2rem 1.25rem; }}
    }}
    .doc-nav {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 2rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid #e2e8f0;
    }}
    .doc-tag {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #2563eb;
      background: #eff6ff;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
    }}
    .doc-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .doc-btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      font-size: 0.82rem;
      font-weight: 500;
      padding: 0.45rem 0.85rem;
      border-radius: 6px;
      border: 1px solid #cbd5e1;
      background: #ffffff;
      color: #334155;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }}
    .doc-btn:hover {{ background: #f8fafc; border-color: #94a3b8; }}
    .doc-btn.primary {{
      background: #2563eb;
      color: #ffffff;
      border-color: #2563eb;
    }}
    .doc-btn.primary:hover {{ background: #1d4ed8; }}
    .doc-banner {{
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 0.75rem 1rem;
      font-size: 0.82rem;
      color: #475569;
      margin-bottom: 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }}
    .doc-h2 {{
      font-size: 1.35rem;
      font-weight: 700;
      color: #0f172a;
      margin-top: 1.75rem;
      margin-bottom: 0.85rem;
      padding-bottom: 0.4rem;
      border-bottom: 1px solid #f1f5f9;
    }}
    .doc-h3 {{
      font-size: 1rem;
      font-weight: 600;
      color: #2563eb;
      margin-top: 1.25rem;
      margin-bottom: 0.5rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .doc-p {{
      font-size: 0.92rem;
      color: #334155;
      margin-bottom: 0.85rem;
      line-height: 1.65;
    }}
    .doc-ul {{
      margin-bottom: 1.25rem;
      padding-left: 1.25rem;
    }}
    .doc-ul li {{
      font-size: 0.9rem;
      color: #334155;
      margin-bottom: 0.45rem;
      line-height: 1.55;
    }}
    .doc-quote {{
      background: #f8fafc;
      border-left: 3px solid #2563eb;
      padding: 0.75rem 1rem;
      margin: 0.5rem 0 0.85rem 0;
      font-style: italic;
      font-size: 0.88rem;
      color: #475569;
      border-radius: 0 6px 6px 0;
    }}
    .doc-divider {{
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 2.25rem 0;
    }}
    a {{ color: #2563eb; text-decoration: underline; }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .doc-container {{ border: none; box-shadow: none; padding: 0; }}
      .doc-nav, .doc-banner {{ display: none; }}
    }}
  </style>
</head>
<body>
  <div class="doc-container">
    <div class="doc-nav">
      <div class="doc-tag">Weekly Pulse • Internal Document</div>
      <div class="doc-actions">
        <button class="doc-btn" id="copyBtn" onclick="copyDocument()">
          <span>Copy for Google Docs</span>
        </button>
        <a href="https://docs.new" target="_blank" rel="noopener" class="doc-btn primary" onclick="copyDocument()">
          <span>Open in Google Docs</span>
        </a>
        <a href="/api/outputs/google_doc_weekly_pulse.docx" target="_blank" class="doc-btn">
          <span>Download .docx</span>
        </a>
        <button class="doc-btn" onclick="window.print()">
          <span>Print / PDF</span>
        </button>
      </div>
    </div>

    <div class="doc-banner">
      <span>💡 <strong>Tip for Google Docs:</strong> Click <em>"Copy for Google Docs"</em>, switch to your Google Doc tab, and press <kbd style="background:#e2e8f0; padding:1px 5px; border-radius:3px;">⌘V</kbd> or <kbd style="background:#e2e8f0; padding:1px 5px; border-radius:3px;">Ctrl+V</kbd>.</span>
    </div>

    <div class="doc-body" id="docRenderArea">
      {parsed_body}
    </div>
    
    <textarea id="rawDocText" style="position:fixed; left:-9999px; opacity:0;">{escaped_raw}</textarea>
  </div>

  <script>
    function copyDocument() {{
      const text = document.getElementById('rawDocText').value;
      const htmlContent = document.getElementById('docRenderArea').innerHTML;
      
      // Synchronous copy fallback
      const t = document.createElement('textarea');
      t.value = text;
      t.style.position = 'fixed';
      t.style.left = '-9999px';
      document.body.appendChild(t);
      t.select();
      try {{ document.execCommand('copy'); }} catch(_) {{}}
      document.body.removeChild(t);

      // Rich HTML copy for Google Docs
      if (navigator.clipboard && window.ClipboardItem) {{
        const bText = new Blob([text], {{ type: 'text/plain' }});
        const bHtml = new Blob([htmlContent], {{ type: 'text/html' }});
        navigator.clipboard.write([
          new ClipboardItem({{ 'text/plain': bText, 'text/html': bHtml }})
        ]).catch(() => {{}});
      }}

      const btn = document.getElementById('copyBtn');
      if (btn) {{
        const orig = btn.innerHTML;
        btn.innerHTML = '<span>Copied with Formatting!</span>';
        setTimeout(() => {{ btn.innerHTML = orig; }}, 2000);
      }}
    }}
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_page)


@app.get("/api/email-text")
async def get_email_text():
    """Get the latest email draft content."""
    email_path = os.path.join(OUTPUTS_DIR, "email_draft_latest.txt")
    if os.path.exists(email_path):
        with open(email_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": "No email draft created yet."}


@app.post("/api/reset")
async def reset_workflow():
    """Reset the entire workflow to start fresh."""
    global mcp_client

    try:
        await mcp_client.disconnect()
    except Exception:
        pass

    mcp_client = MCPClient()

    workflow_state.update({
        "reviews_loaded": False,
        "reviews_path": None,
        "scraper_meta": None,
        "analysis": None,
        "content": None,
        "payload": None,
        "email_draft": None,
        "mcp_actions": [],
        "step": "idle"
    })

    return {"status": "success", "message": "Workflow reset."}


@app.get("/api/outputs/{filename}")
async def get_output_file(filename: str):
    """Download a generated output file."""
    filepath = os.path.join(OUTPUTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(404, f"File {filename} not found")
    return FileResponse(filepath)


@app.get("/api/outputs")
async def list_outputs():
    """List all generated output files."""
    if not os.path.exists(OUTPUTS_DIR):
        return {"files": []}

    files = []
    for f in sorted(os.listdir(OUTPUTS_DIR), reverse=True):
        fp = os.path.join(OUTPUTS_DIR, f)
        if os.path.isfile(fp):
            files.append({
                "name": f,
                "size": os.path.getsize(fp),
                "path": fp
            })
    return {"files": files}


# Mount static files for frontend (after API routes)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.on_event("shutdown")
async def shutdown():
    """Clean up MCP client on shutdown."""
    try:
        await mcp_client.disconnect()
    except Exception:
        pass
