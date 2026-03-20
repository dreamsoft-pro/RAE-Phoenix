# main.py
import asyncio
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.sse import SseServerTransport
import uvicorn

# Import Bridge Handler
from rae_core.bridge.handler import register_bridge

# Import Enterprise Guard
from rae_core.utils.enterprise_guard import RAE_Enterprise_Foundation, audited_operation

class PhoenixArchitect:
    def __init__(self):
        self.enterprise_foundation = RAE_Enterprise_Foundation(module_name="rae-phoenix")

    @audited_operation(operation_name="design_architecture", impact_level="high")
    def run_design(self, context: str):
        """Designs or refactors software architecture."""
        # Logika Trinity v3.0 here
        return "Architecture design initiated and audited."

# Inicjalizacja usług
architect = PhoenixArchitect()
mcp_server = Server("rae-phoenix")

@mcp_server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="design_architecture",
            description="Designs or refactors software architecture. Full audit trail generated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "context": {"type": "string"}
                },
                "required": ["context"]
            }
        )
    ]

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name == "design_architecture":
        ctx = arguments.get("context")
        result_text = architect.run_design(ctx)
        return [TextContent(type="text", text=result_text)]
    raise ValueError(f"Unknown tool: {name}")

app = FastAPI()
register_bridge(app, "rae-phoenix")
sse = SseServerTransport("/mcp/messages")

@app.get("/mcp/sse")
async def mcp_sse_endpoint(request: Request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
