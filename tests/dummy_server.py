import asyncio
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("demo-server")

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

if __name__ == "__main__":
    mcp.run()
