"""
MCP Server — Custom implementation following the Model Context Protocol specification.
Uses JSON-RPC 2.0 over stdio transport.

Provides tools with approval gating:
  1. append_to_document / update_google_doc_text — Creates & updates Google Doc text and markdown document
  2. create_email_draft — Creates & saves email draft as .eml and .txt file (simulates Gmail)
  3. log_to_tracker — Appends to a JSON tracker (simulates Notion/issue tracker)
"""

import json
import os
import sys
from datetime import datetime

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "append_to_document",
        "description": "Update Google Doc text and append structured content to the internal product document (simulates Google Docs update). Requires approval before execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Section title for the appended content"
                },
                "content": {
                    "type": "string",
                    "description": "Structured text / Markdown content to update in Google Doc"
                },
                "document_name": {
                    "type": "string",
                    "description": "Target document filename",
                    "default": "weekly_pulse.md"
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "update_google_doc_text",
        "description": "Update Google Doc text document with the weekly pulse and fee explanation (Google Docs live text update). Requires approval before execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Section title for the Google Doc update"
                },
                "content": {
                    "type": "string",
                    "description": "Content to update in Google Doc"
                },
                "document_name": {
                    "type": "string",
                    "description": "Target document filename",
                    "default": "google_doc_weekly_pulse.txt"
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "create_email_draft",
        "description": "Create an email draft file (simulates Gmail draft creation with weekly pulse and fee explanation). Requires approval before execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient email address(es)"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "cc": {
                    "type": "string",
                    "description": "CC recipients",
                    "default": ""
                }
            },
            "required": ["subject", "to", "body"]
        }
    },
    {
        "name": "log_to_tracker",
        "description": "Log a structured entry to the internal issue/insight tracker (simulates Notion database). Requires approval before execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entry_type": {
                    "type": "string",
                    "description": "Type of entry (e.g., weekly_pulse, fee_explanation)"
                },
                "title": {
                    "type": "string",
                    "description": "Entry title"
                },
                "data": {
                    "type": "string",
                    "description": "JSON string of the entry data"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level",
                    "default": "medium"
                },
                "tags": {
                    "type": "string",
                    "description": "Comma-separated tags",
                    "default": ""
                }
            },
            "required": ["entry_type", "title", "data"]
        }
    }
]


# ─── Tool Implementations ────────────────────────────────────────────────────

def tool_append_to_document(arguments):
    """Update Google Doc text and append content to markdown document."""
    title = arguments.get("title", "Untitled")
    content = arguments.get("content", "")
    document_name = arguments.get("document_name", "weekly_pulse.md")

    # 1. Update markdown document
    md_filepath = os.path.join(OUTPUT_DIR, "weekly_pulse.md")
    if not os.path.exists(md_filepath):
        header = (
            "# Voxora — Internal Google Doc Document\n"
            "_Auto-managed by Voxora MCP Server_\n"
            f"_Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n---\n\n"
        )
        with open(md_filepath, "w", encoding="utf-8") as f:
            f.write(header)

    md_entry = (
        f"\n## {title}\n"
        f"_Appended via MCP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
        f"{content}\n\n---\n\n"
    )
    with open(md_filepath, "a", encoding="utf-8") as f:
        f.write(md_entry)

    # 2. Write dedicated Google Doc formatted text file
    doc_txt_filepath = os.path.join(OUTPUT_DIR, "google_doc_weekly_pulse.txt")
    doc_text_entry = (
        "========================================================================\n"
        f"GOOGLE DOC: {title.upper()}\n"
        f"UPDATED VIA MCP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "STATUS: LIVE UPDATE SYNCHRONIZED\n"
        "========================================================================\n\n"
        f"{content}\n\n"
        "------------------------------------------------------------------------\n"
        "End of Google Doc Section\n\n"
    )
    with open(doc_txt_filepath, "w", encoding="utf-8") as f:
        f.write(doc_text_entry)

    # 3. Write native Word/Docs (.docx) file
    try:
        import docx
        doc = docx.Document()
        doc.add_heading(title, 0)
        for line in content.split("\n"):
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
        docx_filepath = os.path.join(OUTPUT_DIR, "google_doc_weekly_pulse.docx")
        doc.save(docx_filepath)
    except Exception as e:
        logger.warning(f"Could not generate docx: {e}")

    return json.dumps({
        "status": "success",
        "action": "update_google_doc_text",
        "document": "google_doc_weekly_pulse.txt",
        "markdown_document": "weekly_pulse.md",
        "path": os.path.abspath(doc_txt_filepath),
        "markdown_path": os.path.abspath(md_filepath),
        "timestamp": datetime.now().isoformat(),
        "preview_text": content[:240] + ("..." if len(content) > 240 else ""),
        "message": "Google Doc text updated successfully in google_doc_weekly_pulse.txt and weekly_pulse.md."
    })


def tool_create_email_draft(arguments):
    """Save an email draft as a .eml file and text draft."""
    subject = arguments.get("subject", "")
    to = arguments.get("to", "")
    body = arguments.get("body", "")
    cc = arguments.get("cc", "")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"email_draft_{timestamp}.eml"
    filepath = os.path.join(OUTPUT_DIR, filename)

    eml_content = (
        f"From: product-pulse-bot@company.com\n"
        f"To: {to}\n"
        f"Cc: {cc}\n"
        f"Subject: {subject}\n"
        f"Date: {datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0530')}\n"
        f"Content-Type: text/plain; charset=\"utf-8\"\n"
        f"X-Draft-Status: draft\n"
        f"X-Created-By: Voxora MCP Server\n"
        f"\n{body}\n"
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(eml_content)

    # Also save/overwrite a latest email text file for quick access
    latest_txt_path = os.path.join(OUTPUT_DIR, "email_draft_latest.txt")
    with open(latest_txt_path, "w", encoding="utf-8") as f:
        f.write(
            f"SUBJECT: {subject}\n"
            f"TO: {to}\n"
            f"CC: {cc}\n"
            f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"---------------------------------------------------\n\n"
            f"{body}\n"
        )

    return json.dumps({
        "status": "success",
        "action": "create_email_draft",
        "filename": filename,
        "path": os.path.abspath(filepath),
        "txt_path": os.path.abspath(latest_txt_path),
        "timestamp": datetime.now().isoformat(),
        "subject": subject,
        "to": to,
        "preview": body[:200] + ("..." if len(body) > 200 else ""),
        "message": f"Email draft saved as {filename}. Ready for team dispatch."
    })


def tool_log_to_tracker(arguments):
    """Append a structured entry to the JSON tracker."""
    entry_type = arguments.get("entry_type", "")
    title = arguments.get("title", "")
    data_str = arguments.get("data", "{}")
    priority = arguments.get("priority", "medium")
    tags = arguments.get("tags", "")

    filepath = os.path.join(OUTPUT_DIR, "tracker_log.json")

    # Load existing or create new
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                tracker = json.load(f)
            except Exception:
                tracker = {
                    "tracker_name": "Voxora Insight Tracker",
                    "created_at": datetime.now().isoformat(),
                    "entries": []
                }
    else:
        tracker = {
            "tracker_name": "Voxora Insight Tracker",
            "created_at": datetime.now().isoformat(),
            "entries": []
        }

    # Parse data
    try:
        data = json.loads(data_str) if isinstance(data_str, str) else data_str
    except (json.JSONDecodeError, TypeError):
        data = {"raw": data_str}

    # Create entry
    entry = {
        "id": f"PP-{len(tracker.get('entries', [])) + 1:04d}",
        "entry_type": entry_type,
        "title": title,
        "data": data,
        "priority": priority,
        "tags": [t.strip() for t in tags.split(",") if t.strip()] if tags else [],
        "created_at": datetime.now().isoformat(),
        "status": "logged"
    }

    if "entries" not in tracker:
        tracker["entries"] = []
    tracker["entries"].append(entry)
    tracker["last_updated"] = datetime.now().isoformat()

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)

    return json.dumps({
        "status": "success",
        "action": "log_to_tracker",
        "entry_id": entry["id"],
        "path": os.path.abspath(filepath),
        "timestamp": datetime.now().isoformat(),
        "message": f"Entry {entry['id']} logged to tracker successfully."
    })


# Tool dispatch
TOOL_HANDLERS = {
    "append_to_document": tool_append_to_document,
    "update_google_doc_text": tool_append_to_document,
    "create_email_draft": tool_create_email_draft,
    "log_to_tracker": tool_log_to_tracker,
}


# ─── MCP JSON-RPC Server ─────────────────────────────────────────────────────

SERVER_INFO = {
    "name": "Voxora MCP Server",
    "version": "1.0.0"
}

CAPABILITIES = {
    "tools": {"listChanged": False}
}


def handle_request(request):
    """Handle a JSON-RPC 2.0 request following MCP protocol."""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": CAPABILITIES,
                "serverInfo": SERVER_INFO
            }
        }

    elif method == "notifications/initialized":
        # Notification, no response needed
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
            }

        try:
            result_text = handler(arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    elif method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {}
        }

    else:
        # Unknown method
        if req_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        return None


def main():
    """Run the MCP server with stdio transport (JSON-RPC 2.0)."""
    sys.stderr.write("[MCP Server] Voxora MCP Server v1.0.0 started\n")
    sys.stderr.write("[MCP Server] Transport: stdio\n")
    sys.stderr.write(f"[MCP Server] Tools: {', '.join(TOOL_HANDLERS.keys())}\n")
    sys.stderr.flush()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            line = line.strip()
            if not line:
                continue

            request = json.loads(line)
            response = handle_request(request)

            if response is not None:
                response_str = json.dumps(response)
                sys.stdout.write(response_str + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError as e:
            sys.stderr.write(f"[MCP Server] JSON parse error: {e}\n")
            sys.stderr.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stderr.write(f"[MCP Server] Error: {e}\n")
            sys.stderr.flush()

    sys.stderr.write("[MCP Server] Shutting down\n")
    sys.stderr.flush()


if __name__ == "__main__":
    main()
