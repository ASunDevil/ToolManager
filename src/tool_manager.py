import inspect
import json
import typing
from typing import Any, Callable, Dict, List, Optional, Union
from contextlib import AsyncExitStack

from mcp import types
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

# Import standard and buildkite tools
from src.std_tools import execute_shell_command
from src.buildkite_tools import buildkite_trigger_build, buildkite_get_build_status, buildkite_list_builds

import sys
import os

class ToolManager:
    """
    Manages registration and execution of tools.
    Supports local Python functions and tools from MCP (Model Context Protocol) servers.
    """
    def __init__(self):
        # Registry for local tools: tool_name -> {func: callable, info: ToolSchema}
        self._local_tools: Dict[str, Dict[str, Any]] = {}
        # Registry for connected MCP sessions: session_name -> ClientSession
        self._mcp_sessions: Dict[str, ClientSession] = {}
        # Cache mapping tool names to session names for routing MCP calls: tool_name -> session_name
        self._tool_to_session: Dict[str, str] = {}
        # AsyncExitStack to manage lifecycle of MCP connections (automatic cleanup on exit)
        self._exit_stack = AsyncExitStack()

        # Register default tools available in the system
        self.register_tool(execute_shell_command)
        self.register_tool(buildkite_trigger_build)
        self.register_tool(buildkite_get_build_status)
        self.register_tool(buildkite_list_builds)

    async def __aenter__(self):
        """
        Async context manager entry.
        Automatically starts and connects to the internal 'Calculator' MCP server.
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_script = os.path.join(current_dir, "mcp_server.py")

            if os.path.exists(server_script):
                await self.add_mcp_server(
                    name="calculator",
                    command=sys.executable,
                    args=[server_script],
                    env=os.environ.copy()
                )
            else:
                print(f"Warning: Internal MCP server script not found at {server_script}")
        except Exception as e:
            print(f"Error starting internal MCP server: {e}")

        # Add GitHub MCP server if token is present
        try:
            if "GITHUB_PERSONAL_ACCESS_TOKEN" in os.environ:
                await self.add_mcp_server(
                    name="github",
                    command="docker",
                    args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
                    env=os.environ.copy()
                )
        except Exception as e:
            print(f"Error starting GitHub MCP server: {e}")

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """
        Async context manager exit.
        Ensures all MCP connections are closed properly.
        """
        await self._exit_stack.aclose()

    def register_tool(self, func: Callable) -> Callable:
        """
        Decorator/Method to register a local function as a tool.
        Inspects function signature to generate JSON schema for arguments.

        Args:
            func: The function to register.

        Returns:
            The registered function.
        """
        name = func.__name__
        description = func.__doc__ or ""

        # Generate schema by inspecting function signature
        sig = inspect.signature(func)
        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            properties[param_name] = self._get_json_type(param.annotation)

            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        input_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }

        tool_info = types.Tool(
            name=name,
            description=description,
            inputSchema=input_schema
        )

        self._local_tools[name] = {
            "func": func,
            "info": tool_info
        }
        return func

    def _get_json_type(self, annotation: Any) -> Dict[str, Any]:
        """
        Helper to convert a Python type annotation to a JSON schema type.
        Supports basic types (int, float, bool, dict, list) and Optional/Union.
        """
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        if origin is Union:
            # Handle Optional (Union[T, None])
            non_none_types = [t for t in args if t is not type(None)]
            if len(non_none_types) == 1:
                return self._get_json_type(non_none_types[0])
            # For complex unions, just default to string or simple type if possible
            return {"type": "string"}

        if annotation == int:
            return {"type": "integer"}
        elif annotation == float:
            return {"type": "number"}
        elif annotation == bool:
            return {"type": "boolean"}
        elif annotation == dict or origin is dict or origin is Dict:
            return {"type": "object"}
        elif annotation == list or origin is list or origin is List:
            return {"type": "array"}

        return {"type": "string"}

    async def add_mcp_server(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        """
        Connects to a local MCP server via stdio transport.

        Args:
            name: Unique name for this session.
            command: Executable command to start the server.
            args: Arguments for the command.
            env: Environment variables.
        """
        server_params = StdioServerParameters(command=command, args=args, env=env)

        # Enter contexts and store session
        read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        session = await self._exit_stack.enter_async_context(ClientSession(read, write))

        await session.initialize()
        self._mcp_sessions[name] = session
        await self._refresh_tools(name)

    async def add_remote_mcp_server(self, name: str, url: str, headers: Optional[Dict[str, Any]] = None):
        """
        Connects to a remote MCP server via SSE (Server-Sent Events) transport.

        Args:
            name: Unique name for this session.
            url: URL of the SSE endpoint.
            headers: HTTP headers to include.
        """
        # Enter contexts and store session
        read, write = await self._exit_stack.enter_async_context(sse_client(url=url, headers=headers))
        session = await self._exit_stack.enter_async_context(ClientSession(read, write))

        await session.initialize()
        self._mcp_sessions[name] = session
        await self._refresh_tools(name)

    async def _refresh_tools(self, session_name: str):
        """
        Fetches the list of tools from a specific MCP session and updates the routing cache.
        """
        session = self._mcp_sessions[session_name]
        try:
            result = await session.list_tools()
            for tool in result.tools:
                self._tool_to_session[tool.name] = session_name
        except Exception as e:
            print(f"Error fetching tools from {session_name}: {e}")

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of all available tools (local and MCP) in JSON schema format.
        Refreshes tool lists from MCP servers to ensure up-to-date availability.
        """
        all_tools = []

        # Add registered local tools
        for tool_data in self._local_tools.values():
            all_tools.append(tool_data["info"].model_dump())

        # Iterate through connected MCP sessions to fetch and add their tools
        for session_name, session in self._mcp_sessions.items():
            try:
                result = await session.list_tools()
                for tool in result.tools:
                    all_tools.append(tool.model_dump())
                    # Update cache while we are listing
                    self._tool_to_session[tool.name] = session_name
            except Exception as e:
                print(f"Error listing tools from {session_name}: {e}")

        return all_tools

    async def call_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Executes a specific tool by name with provided arguments.
        Routes to local function or MCP session.

        Args:
            name: Name of the tool to call.
            **kwargs: Arguments for the tool.

        Returns:
            JSON-serializable dict containing the tool output or error.
        """

        # 1. Try to find the tool in local registry
        if name in self._local_tools:
            func = self._local_tools[name]["func"]
            try:
                import asyncio
                # Handle both async and sync functions
                if inspect.iscoroutinefunction(func):
                    result = await func(**kwargs)
                else:
                    # Run sync functions in a thread to avoid blocking the asyncio event loop
                    result = await asyncio.to_thread(func, **kwargs)

                content = types.TextContent(type="text", text=str(result))
                return types.CallToolResult(content=[content], isError=False).model_dump()
            except Exception as e:
                content = types.TextContent(type="text", text=str(e))
                return types.CallToolResult(content=[content], isError=True).model_dump()

        # 2. Try to find the tool in MCP session cache
        session_name = self._tool_to_session.get(name)
        if session_name:
            session = self._mcp_sessions.get(session_name)
            if session:
                result = await session.call_tool(name, arguments=kwargs)
                return result.model_dump()

        # 3. Tool not found
        raise ValueError(f"Tool '{name}' not found.")
