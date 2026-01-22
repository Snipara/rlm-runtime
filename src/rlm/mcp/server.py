"""MCP Server implementation for RLM Runtime.

This module provides an MCP (Model Context Protocol) server that exposes
RLM's capabilities to Claude Desktop, Claude Code, and other MCP clients.

Tools provided:
- execute_python: Run Python code in a sandboxed environment
- run_completion: Execute a recursive LLM completion
- get_repl_context: Get the current REPL context
- set_repl_context: Set variables in the REPL context
- set_project: Set the current project for Snipara integration
- get_project: Get the current project configuration
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)

from rlm.core.config import RLMConfig, load_config
from rlm.repl.local import LocalREPL


class ProjectContext:
    """Manages project-specific configuration for the MCP server."""

    def __init__(self):
        self._config: RLMConfig | None = None
        self._project_path: Path | None = None
        self._snipara_api_key: str | None = os.environ.get("SNIPARA_API_KEY")
        self._snipara_project_slug: str | None = os.environ.get("SNIPARA_PROJECT_SLUG")

    def load_from_directory(self, directory: Path | str) -> bool:
        """Load project config from a directory.

        Args:
            directory: Path to the project directory

        Returns:
            True if config was loaded, False otherwise
        """
        directory = Path(directory)
        config_path = directory / "rlm.toml"

        if config_path.exists():
            self._config = load_config(config_path)
            self._project_path = directory

            # Update Snipara settings from project config
            if self._config.snipara_api_key:
                self._snipara_api_key = self._config.snipara_api_key
            if self._config.snipara_project_slug:
                self._snipara_project_slug = self._config.snipara_project_slug

            return True
        return False

    def set_snipara_project(self, project_slug: str, api_key: str | None = None) -> None:
        """Manually set the Snipara project.

        Args:
            project_slug: Snipara project slug
            api_key: Optional API key (uses env var if not provided)
        """
        self._snipara_project_slug = project_slug
        if api_key:
            self._snipara_api_key = api_key

    @property
    def config(self) -> RLMConfig:
        """Get the current config, loading from cwd if needed."""
        if self._config is None:
            cwd = Path.cwd()
            if not self.load_from_directory(cwd):
                self._config = RLMConfig()
        return self._config

    @property
    def project_path(self) -> Path | None:
        """Get the current project path."""
        return self._project_path

    @property
    def snipara_api_key(self) -> str | None:
        """Get the Snipara API key."""
        return self._snipara_api_key or self.config.snipara_api_key

    @property
    def snipara_project_slug(self) -> str | None:
        """Get the Snipara project slug."""
        return self._snipara_project_slug or self.config.snipara_project_slug

    @property
    def snipara_enabled(self) -> bool:
        """Check if Snipara is configured."""
        return bool(self.snipara_api_key and self.snipara_project_slug)

    def get_status(self) -> dict[str, Any]:
        """Get current project status."""
        return {
            "project_path": str(self._project_path) if self._project_path else None,
            "config_loaded": self._config is not None,
            "snipara_enabled": self.snipara_enabled,
            "snipara_project": self.snipara_project_slug,
            "model": self.config.model,
            "environment": self.config.environment,
        }


def create_server() -> Server:
    """Create and configure the MCP server with RLM tools."""
    server = Server("rlm-runtime")

    # Shared state
    repl = LocalREPL(timeout=30)
    project = ProjectContext()

    # Try to auto-detect project from cwd
    project.load_from_directory(Path.cwd())

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
                    "Uses project config if available (model, Snipara, etc.). "
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
                            "description": "Model to use (default: from project config or gpt-4o-mini)",
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
            Tool(
                name="set_project",
                description=(
                    "Set the current project for Snipara integration. "
                    "You can either provide a directory path to load rlm.toml from, "
                    "or directly specify a Snipara project slug."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Path to project directory containing rlm.toml",
                        },
                        "snipara_project": {
                            "type": "string",
                            "description": "Snipara project slug to use directly",
                        },
                        "snipara_api_key": {
                            "type": "string",
                            "description": "Snipara API key (optional, uses env var if not set)",
                        },
                    },
                },
            ),
            Tool(
                name="get_project",
                description="Get the current project configuration and Snipara status.",
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
            return await _run_completion(project, arguments)

        elif name == "get_repl_context":
            return await _get_repl_context(repl)

        elif name == "set_repl_context":
            return await _set_repl_context(repl, arguments)

        elif name == "clear_repl_context":
            return await _clear_repl_context(repl)

        elif name == "set_project":
            return await _set_project(project, arguments)

        elif name == "get_project":
            return await _get_project(project)

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


async def _run_completion(project: ProjectContext, arguments: dict[str, Any]) -> CallToolResult:
    """Run a recursive LLM completion."""
    from rlm.core.orchestrator import RLM
    from rlm.core.types import CompletionOptions

    prompt = arguments.get("prompt", "")
    model = arguments.get("model") or project.config.model
    system = arguments.get("system")
    max_depth = arguments.get("max_depth", project.config.max_depth)

    if not prompt.strip():
        return CallToolResult(
            content=[TextContent(type="text", text="Error: No prompt provided")],
            isError=True,
        )

    try:
        # Build RLM with project config
        rlm_kwargs: dict[str, Any] = {
            "model": model,
            "environment": project.config.environment,
            "verbose": False,
        }

        # Add Snipara config if available
        if project.snipara_enabled:
            rlm_kwargs["snipara_api_key"] = project.snipara_api_key
            rlm_kwargs["snipara_project_slug"] = project.snipara_project_slug

        rlm = RLM(**rlm_kwargs)

        options = CompletionOptions(
            max_depth=max_depth,
            token_budget=project.config.token_budget,
        )

        result = await rlm.completion(prompt, system=system, options=options)

        # Format response with metadata
        response = result.response
        metadata_parts = [
            f"Calls: {result.total_calls}",
            f"Tokens: {result.total_tokens}",
            f"Tools: {result.total_tool_calls}",
            f"Duration: {result.duration_ms}ms",
        ]
        if project.snipara_enabled:
            metadata_parts.append(f"Project: {project.snipara_project_slug}")

        metadata = "\n\n---\n" + " | ".join(metadata_parts)

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


async def _set_project(project: ProjectContext, arguments: dict[str, Any]) -> CallToolResult:
    """Set the current project configuration."""
    directory = arguments.get("directory")
    snipara_project = arguments.get("snipara_project")
    snipara_api_key = arguments.get("snipara_api_key")

    messages = []

    # Load from directory if provided
    if directory:
        dir_path = Path(directory).expanduser().resolve()
        if project.load_from_directory(dir_path):
            messages.append(f"Loaded config from {dir_path / 'rlm.toml'}")
        else:
            messages.append(f"No rlm.toml found in {dir_path}")

    # Set Snipara project directly if provided
    if snipara_project:
        project.set_snipara_project(snipara_project, snipara_api_key)
        messages.append(f"Set Snipara project: {snipara_project}")

    if not messages:
        return CallToolResult(
            content=[TextContent(type="text", text="No project settings provided")],
            isError=True,
        )

    # Add status
    status = project.get_status()
    messages.append("")
    messages.append("Current status:")
    messages.append(f"  Snipara enabled: {status['snipara_enabled']}")
    if status['snipara_project']:
        messages.append(f"  Snipara project: {status['snipara_project']}")
    messages.append(f"  Model: {status['model']}")
    messages.append(f"  Environment: {status['environment']}")

    return CallToolResult(
        content=[TextContent(type="text", text="\n".join(messages))],
    )


async def _get_project(project: ProjectContext) -> CallToolResult:
    """Get the current project configuration."""
    status = project.get_status()

    lines = ["Current project configuration:"]
    lines.append(f"  Project path: {status['project_path'] or '(none)'}")
    lines.append(f"  Config loaded: {status['config_loaded']}")
    lines.append(f"  Snipara enabled: {status['snipara_enabled']}")
    if status['snipara_project']:
        lines.append(f"  Snipara project: {status['snipara_project']}")
    lines.append(f"  Model: {status['model']}")
    lines.append(f"  Environment: {status['environment']}")

    return CallToolResult(
        content=[TextContent(type="text", text="\n".join(lines))],
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
