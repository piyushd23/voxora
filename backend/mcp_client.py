"""
MCP Client — Custom implementation that connects to the MCP server via stdio transport.
Uses JSON-RPC 2.0 protocol following the MCP specification.
Manages tool discovery, approval gating, and tool execution.
"""

import asyncio
import json
import os
import sys
import subprocess
from typing import Dict, List, Optional

from models import MCPAction


class MCPClient:
    """Client for the ProductPulse MCP Server with approval gating."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.pending_actions: Dict[str, MCPAction] = {}
        self._action_counter = 0
        self._request_counter = 0
        self._connected = False
        self._server_info = None
        self._tools = []

    def _next_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        self._request_counter += 1
        return self._request_counter

    def _send_request(self, method: str, params: dict = None) -> dict:
        """Send a JSON-RPC request to the MCP server and wait for response."""
        if not self.process:
            raise RuntimeError("MCP server not connected")

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
        }
        if params:
            request["params"] = params

        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("MCP server closed connection")

        response = json.loads(response_line.strip())

        if "error" in response:
            raise RuntimeError(
                "MCP error: {} (code {})".format(
                    response["error"].get("message", "Unknown"),
                    response["error"].get("code", -1)
                )
            )

        return response.get("result", {})

    def _send_notification(self, method: str, params: dict = None):
        """Send a JSON-RPC notification (no response expected)."""
        if not self.process:
            return

        notification = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            notification["params"] = params

        notification_str = json.dumps(notification) + "\n"
        self.process.stdin.write(notification_str)
        self.process.stdin.flush()

    async def connect(self):
        """Connect to the MCP server via stdio."""
        if self._connected:
            return

        server_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "mcp_server", "server.py"
        )

        python_path = sys.executable

        self.process = subprocess.Popen(
            [python_path, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env={**os.environ}
        )

        # Step 1: Initialize the MCP session
        result = self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "Voxora Client",
                "version": "1.0.0"
            }
        })

        self._server_info = result.get("serverInfo", {})
        self._connected = True

        # Step 2: Send initialized notification
        self._send_notification("notifications/initialized")

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        self._connected = False

    async def list_tools(self) -> list:
        """List all available tools from the MCP server."""
        if not self._connected:
            await self.connect()

        result = self._send_request("tools/list")
        self._tools = result.get("tools", [])

        return [
            {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {})
            }
            for tool in self._tools
        ]

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call an MCP tool and return the result."""
        if not self.process:
            raise RuntimeError("MCP server not connected")

        result = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        # Parse the text content from the result
        content = result.get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "{}")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw_result": text}
        return {}

    def create_pending_action(
        self, tool_name: str, description: str, parameters: dict
    ) -> MCPAction:
        """Create a pending MCP action that requires approval."""
        self._action_counter += 1
        action_id = "action-{:03d}".format(self._action_counter)

        action = MCPAction(
            action_id=action_id,
            tool_name=tool_name,
            description=description,
            parameters=parameters,
            status="pending"
        )
        self.pending_actions[action_id] = action
        return action

    def get_pending_actions(self) -> List[MCPAction]:
        """Get all pending actions."""
        return [a for a in self.pending_actions.values() if a.status == "pending"]

    async def execute_action(self, action_id: str) -> dict:
        """Execute an approved MCP action."""
        action = self.pending_actions.get(action_id)
        if not action:
            raise ValueError("Action {} not found".format(action_id))

        if action.status != "approved":
            raise ValueError("Action {} is not approved (status: {})".format(
                action_id, action.status
            ))

        if not self._connected:
            await self.connect()

        # Call the MCP tool
        result = self.call_tool(action.tool_name, action.parameters)
        action.status = "executed"
        return result

    def approve_action(self, action_id: str) -> MCPAction:
        """Approve a pending action."""
        action = self.pending_actions.get(action_id)
        if not action:
            raise ValueError("Action {} not found".format(action_id))
        action.status = "approved"
        return action

    def reject_action(self, action_id: str) -> MCPAction:
        """Reject a pending action."""
        action = self.pending_actions.get(action_id)
        if not action:
            raise ValueError("Action {} not found".format(action_id))
        action.status = "rejected"
        return action

    async def prepare_actions(
        self, workflow_payload: dict, email_draft: dict
    ) -> List[MCPAction]:
        """
        Prepare all MCP actions from workflow output.
        Returns list of pending actions requiring approval:
          1. create_email_draft (Email dispatch to team)
          2. append_to_document (Google Doc text update)
          3. log_to_tracker (Structured tracker database entry)
        """
        actions = []

        # Action 1: Create email draft (Mail dispatch)
        actions.append(self.create_pending_action(
            tool_name="create_email_draft",
            description="Create email draft with weekly pulse + fee explanation (Mail Dispatch)",
            parameters={
                "subject": email_draft.get("subject", "Weekly Product Pulse"),
                "to": email_draft.get("to", "product-team@company.com"),
                "body": email_draft.get("body", ""),
                "cc": email_draft.get("cc", "")
            }
        ))

        # Action 2: Update Google Doc text
        doc_content = (
            f"{workflow_payload.get('weekly_pulse', '')}\n\n"
            f"---\n\n"
            f"## Fee Clarification: {workflow_payload.get('identified_fee_issue', 'Fee Issue')}\n"
            f"### Reusable Support Snippet\n\n"
            + "\n".join(f"  • {b}" for b in workflow_payload.get("explanation_bullets", []))
            + "\n\n**Official Sources:**\n"
            + "\n".join(f"  - {s}" for s in workflow_payload.get("source_links", []))
        )
        actions.append(self.create_pending_action(
            tool_name="append_to_document",
            description="Update Google Doc text with weekly product pulse & fee explanation (Google Docs text update)",
            parameters={
                "title": f"Weekly Pulse — {workflow_payload.get('date', 'Today')}",
                "content": doc_content,
                "document_name": "google_doc_weekly_pulse.txt"
            }
        ))

        # Action 3: Log to internal tracker
        tracker_data = {
            "date": workflow_payload.get("date", ""),
            "top_themes": workflow_payload.get("top_themes", []),
            "identified_fee_issue": workflow_payload.get("identified_fee_issue", ""),
            "explanation_bullets": workflow_payload.get("explanation_bullets", []),
            "source_links": workflow_payload.get("source_links", [])
        }
        actions.append(self.create_pending_action(
            tool_name="log_to_tracker",
            description="Log insights to internal tracker (Notion Database Simulation)",
            parameters={
                "entry_type": "weekly_pulse",
                "title": f"Weekly Pulse — {workflow_payload.get('date', 'Today')}",
                "data": json.dumps(tracker_data),
                "priority": "high",
                "tags": "weekly-pulse,exit-load,fee-confusion,product-insights"
            }
        ))

        return actions
