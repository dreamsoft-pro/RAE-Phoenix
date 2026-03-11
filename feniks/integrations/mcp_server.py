# Model Context Protocol (MCP) Server for Feniks
from mcp.server.fastmcp import FastMCP
from feniks.core.behavior.contract_engine import ContractEngine
from feniks.core.models.behavior import BehaviorSnapshot, BehaviorContract
mcp = FastMCP("Phoenix")
@mcp.tool()
async def behavior_check(snapshot_json: str, contract_json: str) -> str:
    engine = ContractEngine()
    snapshot = BehaviorSnapshot.model_validate_json(snapshot_json)
    contract = BehaviorContract.model_validate_json(contract_json)
    result = engine.comparison_engine.check_snapshot(snapshot, contract)
    return result.model_dump_json()
if __name__ == "__main__":
    mcp.run()
