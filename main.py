# main.py
import asyncio
import os
import httpx
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
from typing import Dict, Any, Optional, List
import uvicorn

# Import Bridge Handler
from rae_core.bridge.handler import register_bridge
from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation
from rae_core.utils.memory_bridge import RAEMemoryBridge

# Import Plugin System
from feniks.core.plugins.manager import PluginManager
from feniks.core.plugins.base import RefactorIntention, CreationSpec
from feniks.core.analysis.indexer import SystemIndexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAE-Phoenix")

class PhoenixRefactorer:
    """The Autonomous Refactoring Engine for Silicon Oracle RAE Suite (Intelligence v3.1)."""
    
    def __init__(self):
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-phoenix")
        self.api_url = os.getenv("RAE_API_URL", "http://rae-api-dev:8000")
        self.quality_url = os.getenv("QUALITY_API_URL", "http://rae-quality:8000")
        self.plugin_manager = PluginManager()
        self.bridge = RAEMemoryBridge(project_name="rae-phoenix")
        
        # System-wide Intelligence
        self.indexer = SystemIndexer(project_root=".")
        self.indexer.scan_project()
        
        logger.info(f"Loaded plugins: {self.plugin_manager.list_available_plugins()}")

    @audited_operation(operation_name="autonomous_fix", impact_level="high")
    async def process_repair_request(self, project_id: str, code: str, reason: str, file_path: str = "unknown.py") -> Dict[str, Any]:
        """Autonomously analyzes, fixes, and re-verifies code using RAE-First strategy."""
        
        # 0. RAE-FIRST
        history = await self._fetch_file_history(project_id, file_path)
        if history:
            logger.info(f"rae_first_context_acquired: Found {len(history)} historical audit events for {file_path}")
        
        # 1. IMPACT ANALYSIS
        impact = self.indexer.get_impact_zone(file_path)
        
        # [ISO 27001] UNIFIED AUDIT VIA BRIDGE
        self.bridge.log_decision(
            action="impact_analysis_complete",
            reasoning=f"Detected {impact['total_dependents']} dependents for {file_path}",
            payload={"file": file_path, "impact": impact}
        )

        if impact["total_dependents"] > 0:
            logger.warning(f"phoenix_impact_alert: Modifying {file_path} affects {impact['total_dependents']} dependents.")

        # 2. Route to Plugin
        plugin = self.plugin_manager.get_plugin_for_file(file_path)
        self.bridge.log_decision(
            action="plugin_selected",
            reasoning=f"Routing {file_path} to {plugin.name if plugin else 'fallback_llm'}",
            payload={"plugin": plugin.name if plugin else "fallback_llm", "file": file_path}
        )

        if not plugin:
            fixed_code = await self._fallback_llm_fix(code, reason, project_id, impact)
        else:
            intention = RefactorIntention(
                objective=reason,
                target_files=[file_path],
                context={"project_id": project_id, "impact_zone": impact}
            )
            fixed_code = await plugin.execute_refactor(code, intention)
        
        # 3. SELF-VERIFY
        verdict = await self._request_quality_re_audit(fixed_code, project_id)
        
        self.bridge.log_decision(
            action="quality_verdict_received",
            reasoning=f"Tribunal Verdict: {verdict.get('verdict')} (Level: {verdict.get('seniority_attained')})",
            payload=verdict
        )

        # HARD CONTRACT: Must be PASSED and reach ADVANCED_SENIOR seniority
        if verdict.get("verdict") == "PASSED" and verdict.get("seniority_attained") == "advanced_senior":
            logger.info("phoenix_fix_verified: Advanced Senior Standard Reached.", project=project_id)
            return {"status": "SUCCESS", "code": fixed_code, "reasoning": "Self-corrected and verified to Advanced Senior standard."}
        else:
            seniority = verdict.get("seniority_attained", "unknown")
            return {"status": "FAILED", "reason": f"Tribunal verdict: {verdict.get('reasoning')} (Level: {seniority})"}

    async def _fetch_file_history(self, project_id: str, file_path: str) -> List[Dict[str, Any]]:
        """Retrieves past audit results for a specific file to inform current planning (RAE-First)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.api_url}/v2/memories/query", json={
                    "query": f"historical audits and rejections for {file_path}",
                    "layer": "reflective",
                    "project": project_id,
                    "k": 5
                })
                return resp.json().get("results", []) if resp.status_code == 200 else []
        except Exception as e:
            logger.warning(f"rae_first_query_failed: {e}")
            return []

    @audited_operation(operation_name="autonomous_create", impact_level="high")
    async def process_create_request(self, project_id: str, objective: str, target_path: str, architecture_style: str = "Clean Architecture") -> Dict[str, Any]:
        """Scaffolds new code using Language Plugins and Unified Auditing."""
        logger.warning(f"phoenix_creating: {objective} at {target_path}")
        
        plugin = self.plugin_manager.get_plugin_for_file(target_path)
        
        # [ISO 27001] Unified Audit
        self.bridge.log_decision(
            action="creation_started",
            reasoning=f"Scaffolding {target_path} using {plugin.name if plugin else 'none'}",
            payload={"objective": objective, "style": architecture_style}
        )

        if not plugin:
            return {"status": "FAILED", "reason": f"No language plugin found for {target_path}"}
            
        spec = CreationSpec(
            objective=objective,
            target_path=target_path,
            architecture_style=architecture_style,
            context={"project_id": project_id}
        )
        generated_code = await plugin.execute_create(spec)
        return {"status": "SUCCESS", "code": generated_code, "plugin_used": plugin.name}

    async def _fallback_llm_fix(self, code: str, reason: str, project_id: str, impact: Dict[str, Any]) -> str:
        """Consults LLM for the fix (legacy fallback)."""
        prompt = f"""
        Jesteś RAE Phoenix (Ekspert Refaktoryzacji). 
        KOD DO NAPRAWY: {code}
        POWÓD ODRZUCENIA PRZEZ TRYBUNAŁ: {reason}
        PROJEKT: {project_id}
        IMPACT ZONE (ZALEŻNOŚCI): {impact}
        
        Zastosuj poprawki, które spełnią wymagania Quality Tribunal. Zadbaj o SOLID i czysty kod.
        Weź pod uwagę wpływ na inne moduły (Impact Zone).
        Odpowiedz TYLKO naprawionym kodem.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.api_url}/v2/bridge/interact", json={
                "intent": "CODE_REFACTORING_REQUEST",
                "target_agent": "rae-oracle-gemini",
                "payload": {"prompt": prompt}
            })
            return resp.json().get("payload", {}).get("interaction_data", {}).get("code", code) if resp.status_code == 200 else code

    async def _request_quality_re_audit(self, code: str, project_id: str) -> Dict[str, Any]:
        """Asks RAE-Quality (Tribunal) directly for a new semantic audit (Direct A2A)."""
        url = f"{self.quality_url}/v2/quality/audit"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json={
                    "code": code,
                    "project_id": project_id,
                    "importance": "medium"
                })
                return resp.json() if resp.status_code == 200 else {"verdict": "REJECTED", "reasoning": f"Quality API error: {resp.status_code}"}
        except Exception as e:
            logger.error(f"direct_quality_audit_failed: {e}")
            return {"verdict": "REJECTED", "reasoning": f"Quality API unreachable: {e}"}

# Inicjalizacja usług
refactorer = PhoenixRefactorer()
mcp_server = Server("rae-phoenix")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="trigger_refactoring",
            description="Manually triggers Phoenix to refactor code using AST plugins based on a specific reason.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "code": {"type": "string"},
                    "reason": {"type": "string"},
                    "file_path": {"type": "string", "description": "Crucial for routing to the correct language plugin"}
                },
                "required": ["project_id", "code", "reason", "file_path"]
            }
        ),
        Tool(
            name="trigger_creation",
            description="Manually triggers Phoenix to scaffold new code using AST plugins.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string"},
                    "objective": {"type": "string"},
                    "target_path": {"type": "string"},
                    "architecture_style": {"type": "string"}
                },
                "required": ["project_id", "objective", "target_path"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "trigger_refactoring":
        res = await refactorer.process_repair_request(
            arguments.get("project_id"),
            arguments.get("code"),
            arguments.get("reason"),
            arguments.get("file_path", "unknown.py")
        )
        return [TextContent(type="text", text=str(res))]
    elif name == "trigger_creation":
        res = await refactorer.process_create_request(
            arguments.get("project_id"),
            arguments.get("objective"),
            arguments.get("target_path"),
            arguments.get("architecture_style", "Clean Architecture")
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
        payload.get("reason"),
        payload.get("file_path", "unknown.py")
    )

@app.post("/v2/phoenix/create")
async def api_create(payload: dict):
    """Bridge endpoint for automated scaffolding requests."""
    return await refactorer.process_create_request(
        payload.get("project_id"),
        payload.get("objective"),
        payload.get("target_path"),
        payload.get("architecture_style", "Clean Architecture")
    )

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
