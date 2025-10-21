"""
Tools for the MCP server.
"""

from server.core import mcp
from server.db_layer import execute_action
from server.nlp_intent import parse_nl_to_intent

@mcp.tool()
async def query_users(user_query: str) -> dict:
    """Fetch users from DB based on natural language query."""
    intent = await parse_nl_to_intent(user_query)
    result = execute_action(intent["action"], intent.get("filters", {}))
    return {"result": result}
