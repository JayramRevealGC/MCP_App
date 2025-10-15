from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server with custom port and host for Docker
mcp = FastMCP("nlp-db-server", host="0.0.0.0", port=8001)
