import pytest
from src.tool_manager import ToolManager

@pytest.mark.asyncio
async def test_internal_mcp_integration():
    async with ToolManager() as tm:
        tools = await tm.list_tools()
        tool_names = [t["name"] for t in tools]

        # Check if calculator tools are present
        assert "add" in tool_names
        assert "subtract" in tool_names
        assert "multiply" in tool_names

        # Test calling add
        result_add = await tm.call_tool("add", a=5, b=3)
        assert not result_add["isError"]
        assert "8" in result_add["content"][0]["text"]

        # Test calling multiply
        result_mul = await tm.call_tool("multiply", a=4, b=3)
        assert not result_mul["isError"]
        assert "12" in result_mul["content"][0]["text"]
