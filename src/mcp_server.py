from mcp.server.fastmcp import FastMCP

# Initialize a FastMCP server named "Calculator".
# FastMCP simplifies creation of MCP servers by using decorators.
mcp = FastMCP("Calculator")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Adds two numbers."""
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtracts b from a."""
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiplies two numbers."""
    return a * b

if __name__ == "__main__":
    # Runs the MCP server, listening on stdio by default.
    # This allows it to be connected to clients (like ToolManager) via subprocess pipes.
    mcp.run()
