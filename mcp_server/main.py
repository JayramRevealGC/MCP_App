import sys
import asyncio
from server.core import mcp
from server.tools import query_users

async def test_query():
    """Test query_users tool directly without MCP transport."""
    user_queries = ["All the tables in the database", "10 random rows from the table item_kaus", "Row with id 1957777 from the table item_kaus", "7 joined records from the table item_kaus_original and item_kaus"]
    for user_query in user_queries:
        result = await query_users(user_query)
        print(result)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tool directly for quick testing
        asyncio.run(test_query())
    else:
        # Run MCP server
        print("Starting MCP server...")
        mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()
