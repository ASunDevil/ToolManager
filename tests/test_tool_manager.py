import pytest
import asyncio
from src.tool_manager import ToolManager

@pytest.mark.asyncio
async def test_local_tool_registration():
    tm = ToolManager()

    @tm.register_tool
    def add(a: int, b: int) -> int:
        """Adds two numbers."""
        return a + b

    tools = await tm.list_tools()
    # assert len(tools) == 1 # Now we have default tools

    # Check if 'add' is present
    add_tool = next((t for t in tools if t["name"] == "add"), None)
    assert add_tool is not None
    assert add_tool["description"] == "Adds two numbers."
    assert "a" in add_tool["inputSchema"]["properties"]
    assert "b" in add_tool["inputSchema"]["properties"]

    result = await tm.call_tool("add", a=1, b=2)
    assert result["content"][0]["text"] == "3"
    assert not result["isError"]

@pytest.mark.asyncio
async def test_local_tool_error():
    tm = ToolManager()

    @tm.register_tool
    def fail():
        raise ValueError("Oops")

    result = await tm.call_tool("fail")
    assert result["isError"]
    assert "Oops" in result["content"][0]["text"]

@pytest.mark.asyncio
async def test_context_manager():
    async with ToolManager() as tm:
        @tm.register_tool
        def echo(msg: str) -> str:
            return msg

        result = await tm.call_tool("echo", msg="hello")
        assert result["content"][0]["text"] == "hello"

@pytest.mark.asyncio
async def test_mcp_tool_integration():
    import sys
    import os

    server_script = os.path.join(os.path.dirname(__file__), "dummy_server.py")

    async with ToolManager() as tm:
        # Register dummy MCP server
        await tm.add_mcp_server(
            name="dummy",
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy()
        )

        # List tools
        tools = await tm.list_tools()
        tool_names = [t["name"] for t in tools]
        assert "multiply" in tool_names

        # Verify schema of remote tool
        multiply_tool = next(t for t in tools if t["name"] == "multiply")
        assert "a" in multiply_tool["inputSchema"]["properties"]
        assert "b" in multiply_tool["inputSchema"]["properties"]

        # Call remote tool
        result = await tm.call_tool("multiply", a=3, b=4)
        assert not result["isError"]
        # FastMCP or the tool might return text content with the result
        # Check if result is 12 (as string or something)
        # Note: FastMCP usually wraps return value in TextContent
        assert "12" in result["content"][0]["text"]

@pytest.mark.asyncio
async def test_tool_caching():
    # Test that call_tool uses cache and doesn't call list_tools on sessions

    # We mock a session
    from unittest.mock import AsyncMock, MagicMock
    from mcp.types import ListToolsResult, Tool, CallToolResult, TextContent

    mock_session = MagicMock()
    mock_session.initialize = AsyncMock()

    # Setup list_tools to return a tool
    mock_tool = Tool(name="cached_tool", description="desc", inputSchema={})
    mock_session.list_tools = AsyncMock(return_value=ListToolsResult(tools=[mock_tool]))

    # Setup call_tool response
    mock_session.call_tool = AsyncMock(return_value=CallToolResult(content=[TextContent(type="text", text="success")]))

    tm = ToolManager()

    # Manually inject the mock session (since add_mcp_server does complex stack logic)
    # Ideally we refactor ToolManager to allow easier testing, but we can hack it
    tm._mcp_sessions["mock"] = mock_session

    # Manually populate cache (simulate what add_mcp_server would do)
    await tm._refresh_tools("mock")

    # Verify list_tools was called once during refresh
    mock_session.list_tools.assert_called_once()
    mock_session.list_tools.reset_mock()

    # Call the tool
    result = await tm.call_tool("cached_tool", x=1)

    # Verify call_tool was called
    mock_session.call_tool.assert_called_once_with("cached_tool", arguments={"x": 1})

    # IMPORTANT: Verify list_tools was NOT called again
    mock_session.list_tools.assert_not_called()
