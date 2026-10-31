"""Google ADK agent using OpenAI GPT-4o mini and three MCP servers."""
import os
import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from retailops_mcp.db.database import initialize_database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

# Ensure the local SQL database and synthetic demo records exist.
initialize_database()

def make_mcp_toolset(module_name: str) -> McpToolset:
    """Launch one local MCP server as a child process and expose its tools to ADK."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=PYTHON,
                args=["-m", module_name],
                cwd=str(PROJECT_ROOT),
                env=os.environ.copy(),
            )
        )
    )

procurement_mcp = make_mcp_toolset("retailops_mcp.servers.procurement_server")
inventory_mcp = make_mcp_toolset("retailops_mcp.servers.inventory_server")
vendor_mcp = make_mcp_toolset("retailops_mcp.servers.vendor_server")

root_agent = LlmAgent(
    name="retailops_enterprise_agent",
    model=LiteLlm(model=os.getenv("ADK_MODEL", "openai/gpt-4o-mini")),
    description="Retail operations assistant for procurement, inventory and vendor analysis.",
    instruction="""
You are RetailOps AI, an enterprise retail operations assistant.

MANDATORY TOOL USAGE:
- For questions about purchase orders, use the procurement MCP tools.
- For questions about inventory and stock, use the inventory MCP tools.
- For questions about vendors and vendor performance, use the vendor MCP tools.
- For questions requesting lists, counts, summaries or analysis of
  existing business records, retrieve the relevant data using MCP tools
  before answering.
- Never claim that you cannot access data simply because the system
  is read-only. Read-only tools can retrieve database records.
- If a relevant tool is unavailable or returns an error, explain
  the actual limitation.

DATA ACCURACY:
- Never invent PO, vendor, stock, ASN or GRN values.
- Clearly state that the initial dataset is synthetic demonstration data.
- Explain calculations and distinguish:
  pending ASN = PO quantity - ASN quantity;
  pending GRN against ASN = ASN quantity - GRN quantity;
  unreceived against PO = PO quantity - GRN quantity.
- Do not label a delivery late unless actual delivery information is available.
- This version is read-only. Never claim to update a PO, change stock,
  approve an action or send an email.
- If the data is missing, state what is missing.
""",
    tools=[procurement_mcp, inventory_mcp, vendor_mcp],
)
