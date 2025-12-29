import pytest
from src.tool_manager import ToolManager
from src.std_tools import execute_shell_command

@pytest.mark.asyncio
async def test_shell_command_execution():
    tm = ToolManager()

    # Register the tool
    tm.register_tool(execute_shell_command)

    # Verify registration
    tools = await tm.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "execute_shell_command" in tool_names

    # Test success case
    result = await tm.call_tool("execute_shell_command", command="echo 'hello world'")
    assert not result["isError"]
    assert result["content"][0]["text"] == "hello world"

    # Test failure case
    result = await tm.call_tool("execute_shell_command", command="exit 1")
    assert not result["isError"] # The tool execution didn't throw Python exception, it returned an error string
    assert "Error (Exit Code 1)" in result["content"][0]["text"]

    # Test compound command
    result = await tm.call_tool("execute_shell_command", command="echo foo; echo bar")
    assert not result["isError"]
    # Output might depend on shell buffering, but typically 'foo\nbar'
    assert "foo" in result["content"][0]["text"]
    assert "bar" in result["content"][0]["text"]
