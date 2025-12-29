import pytest
from src.tool_manager import ToolManager

@pytest.mark.asyncio
async def test_default_tools_registered():
    tm = ToolManager()

    tools = await tm.list_tools()
    tool_names = [t["name"] for t in tools]

    assert "execute_shell_command" in tool_names
    assert "buildkite_trigger_build" in tool_names
    assert "buildkite_get_build_status" in tool_names
    assert "buildkite_list_builds" in tool_names

@pytest.mark.asyncio
async def test_call_default_tool_shell():
    tm = ToolManager()
    result = await tm.call_tool("execute_shell_command", command="echo 'default tool test'")
    assert not result["isError"]
    assert "default tool test" in result["content"][0]["text"]
