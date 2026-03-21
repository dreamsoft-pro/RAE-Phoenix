# main.py
import asyncio
import os
import httpx
import logging
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from typing import Dict, Any, Optional
import uvicorn

# Import Bridge Handler
from rae_core.bridge.handler import register_bridge
from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Phoenix")

class PhoenixRefactorer:
    """The Autonomous Refactoring Engine for Silicon Oracle RAE Suite."""
    
    def __init__(self):
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-phoenix")
        self.api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")

    @audited_operation(operation_name="autonomous_fix", impact_level="high")
    async def process_repair_request(self, project_id: str, code: str, reason: str) -> Dict[str, Any]:
        """Autonomously analyzes, fixes, and re-verifies code after a Quality rejection."""
        logger.warning(f"phoenix_waking_up: Fixing code for {project_id} due to: {reason}")
        
        # 1. ANALYZE & FIX: Consult LLM via Bridge
        fixed_code = await self._generate_fix(code, reason, project_id)
        
        # 2. SELF-VERIFY: Ask Quality Tribunal for a new verdict before submitting
        verdict = await self._request_quality_re_audit(fixed_code, project_id)
        
        if verdict.get("verdict") == "PASSED":
            logger.info("phoenix_fix_verified", project=project_id)
            # 3. COMMIT (Simulated: Update project via Bridge/Filesystem)
            return {"status": "SUCCESS", "code": fixed_code, "reasoning": "Self-corrected and verified by Tribunal."}
        else:
            logger.error("phoenix_fix_rejected", reasoning=verdict.get("reasoning"))
            return {"status": "FAILED", "reason": "Failed to satisfy Quality Tribunal after refactoring."}

    async def _generate_fix(self, code: str, reason: str, project_id: str) -> str:
        """Consults LLM for the fix, injecting project context from Memory."""
        # Wzorzec Advanced Senior: Evidence Injection (znowu)
        prompt = f"""
        Jesteś RAE Phoenix (Ekspert Refaktoryzacji). 
        KOD DO NAPRAWY: {code}
        POWÓD ODRZUCENIA PRZEZ TRYBUNAŁ: {reason}
        PROJEKT: {project_id}
        
        Zastosuj poprawki, które spełnią wymagania Quality Tribunal. Zadbaj o SOLID i czysty kod.
        Odpowiedz TYLKO naprawionym kodem Python.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                "intent": "CODE_REFACTORING_REQUEST",
                "target_agent": "rae-oracle-gemini",
                "payload": {"prompt": prompt}
            })
            return resp.json().get("payload", {}).get("interaction_data", {}).get("code", code) if resp.status_code == 200 else code

    async def _request_quality_re_audit(self, code: str, project_id: str) -> Dict[str, Any]:
        """Asks RAE-Quality (Tribunal) for a new semantic audit."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_url}/v2/quality/audit", json={
                "code": code,
                "project_id": project_id,
                "importance": "medium"
            })
            return resp.json() if resp.status_code == 200 else {"verdict": "REJECTED", "reasoning": "Quality API unreachable."}

# Inicjalizacja usług
refactorer = PhoenixRefactorer()
mcp_server = Server("rae-phoenix")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="trigger_refactoring",
            description="Manually triggers Phoenix to refactor code based on a specific reason.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "code": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["project_id", "code", "reason"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "trigger_refactoring":
        res = await refactorer.process_repair_request(
            arguments.get("project_id"),
            arguments.get("code"),
            arguments.get("reason")
        )
        return [TextContent(type="text", text=str(res))]
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
register_bridge(app, "rae-phoenix")
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.post("/v2/phoenix/repair")
async def api_repair(payload: dict):
    """Bridge endpoint for automated repair requests from Quality/CEO."""
    return await refactorer.process_repair_request(
        payload.get("project_id"),
        payload.get("code"),
        payload.get("reason")
    )

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
