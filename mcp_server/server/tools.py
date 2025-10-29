"""
Tools for the MCP server.
"""

from server.core import mcp
from server.db_layer import execute_action
from server.nlp_layer import parse_nl_to_intent
from server.memory import store_query, get_query_history

@mcp.tool()
async def query_users(user_query: str, session_id: str = None) -> dict:
    """Fetch users from DB based on natural language query."""
    # Retrieve previous queries for this session
    previous_queries = get_query_history(session_id) if session_id else []
    
    # Store the current query
    if session_id:
        store_query(session_id, user_query)
    
    # Parse intent with conversation history
    intent = await parse_nl_to_intent(user_query, previous_queries)
    result = execute_action(intent["action"], intent.get("filters", {}))
    return {"result": result}
