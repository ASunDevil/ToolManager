# Tool Manager Project

This project implements a versatile `ToolManager` in Python that unifies access to local function-based tools and remote/local Model Context Protocol (MCP) server tools. It allows you to register Python functions as tools, connect to MCP servers (via stdio or SSE), and invoke them through a common interface.

## Features

*   **Unified Interface**: List and call tools from disparate sources using `list_tools()` and `call_tool()`.
*   **Local Tool Registration**: Decorate standard Python functions to expose them as tools. Automatic JSON schema generation from type hints.
*   **MCP Support**: Full integration with the Model Context Protocol (MCP) Python SDK.
    *   **Stdio Support**: Connect to local MCP servers running as subprocesses.
    *   **SSE Support**: Connect to remote MCP servers via Server-Sent Events (HTTP).
*   **Built-in Tools**:
    *   **Shell**: Execute shell commands (with safety timeouts).
    *   **Buildkite**: Trigger builds, check status, and list builds for Buildkite pipelines.
    *   **Calculator**: A sample local MCP server providing basic math operations.
*   **Async/Sync Safety**: Automatically offloads synchronous local tools to threads to prevent blocking the async event loop.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    This project requires `mcp`, `anyio`, `pybuildkite`, and other standard libraries.

## Usage

### Basic Usage

Use the `ToolManager` as an async context manager. It automatically starts and connects to the bundled local `Calculator` MCP server.

```python
import asyncio
from src.tool_manager import ToolManager

async def main():
    async with ToolManager() as tm:
        # List all available tools (local + MCP)
        tools = await tm.list_tools()
        for tool in tools:
            print(f"Tool: {tool['name']}")

        # Call a local tool (Shell)
        result = await tm.call_tool("execute_shell_command", command="echo Hello World")
        print("Shell Output:", result)

        # Call an MCP tool (Calculator)
        result = await tm.call_tool("add", a=10, b=5)
        print("Math Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Adding Custom Local Tools

You can register your own Python functions using the `register_tool` decorator or method.

```python
    async with ToolManager() as tm:
        @tm.register_tool
        def my_custom_tool(name: str) -> str:
            """Greets the user."""
            return f"Hello, {name}!"

        await tm.call_tool("my_custom_tool", name="Alice")
```

### Connecting to External MCP Servers

You can connect to additional MCP servers beyond the default one.

```python
    # Connect to a local server process
    await tm.add_mcp_server(
        name="my-server",
        command="python",
        args=["path/to/server.py"]
    )

    # Connect to a remote SSE server
    await tm.add_remote_mcp_server(
        name="remote-server",
        url="http://localhost:8000/sse"
    )
```

## Built-in Tools Configuration

*   **Buildkite Tools**: Require the `BUILDKITE_API_TOKEN` environment variable to be set.
    *   `buildkite_trigger_build`
    *   `buildkite_get_build_status`
    *   `buildkite_list_builds`

## Testing

The project uses `pytest` for testing. Ensure the project root is in your python path.

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest tests/
```

This runs tests for:
*   Local tool registration and execution.
*   Internal MCP server integration.
*   Shell tool execution.
*   Buildkite tool integration (using mocks).

## Project Structure

*   `src/tool_manager.py`: Core `ToolManager` class implementation.
*   `src/std_tools.py`: Standard library tools (e.g., shell execution).
*   `src/buildkite_tools.py`: Buildkite API integration tools.
*   `src/mcp_server.py`: A sample FastMCP server implementation (Calculator).
*   `tests/`: Unit and integration tests.
