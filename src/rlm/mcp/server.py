"""MCP Server implementation for RLM Runtime.

This module provides an MCP (Model Context Protocol) server that exposes
RLM's capabilities to Claude Desktop, Claude Code, and other MCP clients.

Tools provided:
- execute_python: Run Python code in a sandboxed environment
- run_completion: Execute a recursive LLM completion
- get_repl_context: Get the current REPL context
- set_repl_context: Set variables in the REPL context
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from rlm.repl.local import LocalREPL


def create_server() -> Server:
    """Create and configure the MCP server with RLM tools."""
    server = Server("rlm-runtime")

    # Shared REPL instance for persistent context
    repl = LocalREPL(timeout=30)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available RLM tools."""
        return [
            Tool(
                name="execute_python",
                description=(
                    "Execute Python code in a sandboxed environment with RestrictedPython. "
                    "Safe for math, data processing, and algorithm work. "
                    "Allowed imports: json, re, math, datetime, collections, itertools, etc. "
                    "Blocked: os, subprocess, socket, file I/O, network access. "
                    "Use 'result = <value>' to return a value. Use print() for output."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 30, max: 60)",
                            "default": 30,
                        },
                    },
                    "required": ["code"],
                },
            ),
            Tool(
                name="run_completion",
                description=(
                    "Run a recursive LLM completion using the RLM runtime. "
                    "The LLM can use tools and execute code to solve complex tasks. "
                    "Requires API keys to be configured (OPENAI_API_KEY or ANTHROPIC_API_KEY)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The prompt to send to the LLM",
                        },
                        "model": {
                            "type": "string",
                            "description": "Model to use (default: gpt-4o-mini)",
                            "default": "gpt-4o-mini",
                        },
                        "system": {
                            "type": "string",
                            "description": "Optional system message",
                        },
                        "max_depth": {
                            "type": "integer",
                            "description": "Maximum recursion depth (default: 4)",
                            "default": 4,
                        },
                    },
                    "required": ["prompt"],
                },
            ),
            Tool(
                name="get_repl_context",
                description=(
                    "Get the current REPL context. Returns all variables stored "
                    "in the persistent execution context."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="set_repl_context",
                description=(
                    "Set a variable in the REPL context. The variable will persist "
                    "across multiple execute_python calls."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "key": {
                            "type": "string",
                            "description": "Variable name",
                        },
                        "value": {
                            "type": "string",
                            "description": "JSON-encoded value to store",
                        },
                    },
                    "required": ["key", "value"],
                },
            ),
            Tool(
                name="clear_repl_context",
                description="Clear all variables from the REPL context and reset to clean state.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Handle tool calls."""

        if name == "execute_python":
            return await _execute_python(repl, arguments)

        elif name == "run_completion":
            return await _run_completion(arguments)

        elif name == "get_repl_context":
            return await _get_repl_context(repl)

        elif name == "set_repl_context":
            return await _set_repl_context(repl, arguments)

        elif name == "clear_repl_context":
            return await _clear_repl_context(repl)

        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True,
            )

    return server


async def _execute_python(repl: LocalREPL, arguments: dict[str, Any]) -> CallToolResult:
    """Execute Python code in the sandbox."""
    code = arguments.get("code", "")
    timeout = min(arguments.get("timeout", 30), 60)  # Cap at 60 seconds

    if not code.strip():
        return CallToolResult(
            content=[TextContent(type="text", text="Error: No code provided")],
            isError=True,
        )

    result = await repl.execute(code, timeout=timeout)

    if result.success:
        output = result.output or "(no output)"
        if result.truncated:
            output += "\n... (output truncated)"
        return CallToolResult(
            content=[TextContent(type="text", text=output)],
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {result.error}")],
            isError=True,
        )


async def _run_completion(arguments: dict[str, Any]) -> CallToolResult:
    """Run a recursive LLM completion."""
    from rlm.core.orchestrator import RLM
    from rlm.core.types import CompletionOptions

    prompt = arguments.get("prompt", "")
    model = arguments.get("model", "gpt-4o-mini")
    system = arguments.get("system")
    max_depth = arguments.get("max_depth", 4)

    if not prompt.strip():
        return CallToolResult(
            content=[TextContent(type="text", text="Error: No prompt provided")],
            isError=True,
        )

    try:
        rlm = RLM(
            model=model,
            environment="local",
            verbose=False,
        )

        options = CompletionOptions(
            max_depth=max_depth,
            token_budget=8000,
        )

        result = await rlm.completion(prompt, system=system, options=options)

        # Format response with metadata
        response = result.response
        metadata = (
            f"\n\n---\n"
            f"Calls: {result.total_calls} | "
            f"Tokens: {result.total_tokens} | "
            f"Tools: {result.total_tool_calls} | "
            f"Duration: {result.duration_ms}ms"
        )

        return CallToolResult(
            content=[TextContent(type="text", text=response + metadata)],
        )

    except Exception as e:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")],
            isError=True,
        )


async def _get_repl_context(repl: LocalREPL) -> CallToolResult:
    """Get the current REPL context."""
    context = repl.get_context()

    if not context:
        return CallToolResult(
            content=[TextContent(type="text", text="Context is empty")],
        )

    # Format context as readable output
    lines = ["Current REPL context:"]
    for key, value in context.items():
        try:
            value_str = json.dumps(value, indent=2, default=str)
        except (TypeError, ValueError):
            value_str = repr(value)
        lines.append(f"  {key} = {value_str}")

    return CallToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
    )


async def _set_repl_context(repl: LocalREPL, arguments: dict[str, Any]) -> CallToolResult:
    """Set a variable in the REPL context."""
    key = arguments.get("key", "")
    value_str = arguments.get("value", "")

    if not key:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: No key provided")],
            isError=True,
        )

    try:
        value = json.loads(value_str)
    except json.JSONDecodeError:
        # If not valid JSON, store as string
        value = value_str

    repl.set_context(key, value)

    return CallToolResult(
        content=[TextContent(type="text", text=f"Set context['{key}'] = {repr(value)}")],
    )


async def _clear_repl_context(repl: LocalREPL) -> CallToolResult:
    """Clear the REPL context."""
    repl.clear_context()
    return CallToolResult(
        content=[TextContent(type="text", text="REPL context cleared")],
    )


def run_server() -> None:
    """Run the MCP server using stdio transport."""
    server = create_server()

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(main())


if __name__ == "__main__":
    run_server()
