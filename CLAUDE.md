# CLAUDE.md - RLM Runtime

This document helps Claude Code understand the rlm-runtime project.

## Project Overview

RLM Runtime is a **Recursive Language Model runtime** with sandboxed REPL execution. It enables LLMs to recursively decompose tasks, execute real code in isolated environments, and retrieve context on demand.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  RLM Orchestrator                                               │
│  • Manages recursion depth and token budgets                    │
│  • Coordinates LLM calls and tool execution                     │
├─────────────────────────────────────────────────────────────────┤
│  LLM Backends              │  REPL Environments                 │
│  • LiteLLM (100+ providers)│  • Local (RestrictedPython)        │
│  • OpenAI                  │  • Docker (isolated)               │
│  • Anthropic               │  • WebAssembly (Pyodide)           │
├─────────────────────────────────────────────────────────────────┤
│  Tool Registry             │  MCP Server                        │
│  • execute_code            │  • execute_python (sandbox)        │
│  • file_read               │  • get/set/clear_repl_context      │
│  • Custom tools            │  • Zero API keys required          │
└─────────────────────────────────────────────────────────────────┘
```

## Key Directories

```
src/rlm/
├── core/                    # Core orchestrator and types
│   ├── orchestrator.py      # Main RLM class, completion logic
│   ├── types.py             # Message, Tool, Result types
│   ├── config.py            # Configuration loading
│   └── exceptions.py        # Custom exception hierarchy
├── backends/                # LLM provider integrations
│   ├── base.py              # Abstract backend class
│   ├── litellm.py           # LiteLLM (100+ providers)
│   ├── openai.py            # OpenAI direct
│   └── anthropic.py         # Anthropic direct
├── repl/                    # Code execution environments
│   ├── local.py             # RestrictedPython sandbox
│   ├── docker.py            # Docker container isolation
│   └── wasm.py              # WebAssembly via Pyodide
├── mcp/                     # MCP server for Claude Code
│   ├── server.py            # MCP server implementation
│   └── auth.py              # Snipara OAuth token support
├── tools/                   # Tool system
│   └── registry.py          # Tool registration and lookup
├── visualizer/              # Trajectory visualizer
│   └── app.py               # Streamlit dashboard
└── cli/                     # CLI commands
    └── main.py              # Typer CLI app
```

## MCP Server (Zero API Keys)

The MCP server is designed to work within Claude Code without external API costs:

```python
# src/rlm/mcp/server.py - Key tools
Tools:
- execute_python: Sandboxed code execution (RestrictedPython)
- get_repl_context: Get persistent variables
- set_repl_context: Set persistent variables
- clear_repl_context: Reset state
```

**Why zero API keys?**
- Claude Code IS the LLM (billing included)
- No need for external LLM calls
- Snipara uses OAuth Device Flow (no key copying)

## REPL Environments

### Local (RestrictedPython)
- Fast, no setup required
- Limited isolation
- Best for development/trusted code

### Docker
- Full container isolation
- Configurable resources (CPU, memory)
- Network disabled by default
- Best for production/untrusted code

### WebAssembly (Pyodide)
- Browser-compatible sandbox
- No Docker required
- Portable across platforms

## Exception Hierarchy

```python
from rlm.core.exceptions import (
    RLMError,              # Base exception
    MaxDepthExceeded,      # Recursion limit hit
    TokenBudgetExhausted,  # Token limit hit
    ToolBudgetExhausted,   # Tool call limit hit
    REPLExecutionError,    # Code execution failed
    REPLSecurityError,     # Security violation
    ToolNotFoundError,     # Unknown tool
    BackendConnectionError, # LLM API error
)
```

## Configuration

### rlm.toml
```toml
[rlm]
model = "gpt-4o-mini"
environment = "docker"  # local, docker, wasm
max_depth = 4
token_budget = 8000

[docker]
image = "python:3.11-slim"
cpus = 1.0
memory = "512m"
```

### Environment Variables
```bash
RLM_MODEL=gpt-4o-mini
RLM_ENVIRONMENT=docker
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## CLI Commands

```bash
rlm init              # Create rlm.toml
rlm run "prompt"      # Run completion
rlm run --env docker  # With Docker isolation
rlm logs              # View trajectories
rlm visualize         # Launch Streamlit dashboard
rlm mcp-serve         # Start MCP server
rlm doctor            # Check setup
```

## Testing

```bash
# Run all tests
pytest tests/

# Specific test file
pytest tests/unit/test_repl_local.py

# With coverage
pytest --cov=src/rlm tests/
```

## Development Workflow

1. **Edit code** in `src/rlm/`
2. **Run tests** with `pytest`
3. **Check types** with `mypy src/`
4. **Lint** with `ruff check src/`
5. **Commit** with descriptive messages

## Snipara Integration

For context retrieval, use snipara-mcp separately:

```bash
pip install snipara-mcp
snipara-mcp-login      # OAuth Device Flow (browser)
snipara-mcp-status     # Check auth status
snipara-mcp-logout     # Clear tokens
```

Tokens stored at `~/.snipara/tokens.json`.

## Key Files for Common Tasks

| Task | Files |
|------|-------|
| Add MCP tool | `src/rlm/mcp/server.py` |
| Add CLI command | `src/rlm/cli/main.py` |
| Modify sandbox | `src/rlm/repl/local.py` |
| Add exception | `src/rlm/core/exceptions.py` |
| Change config | `src/rlm/core/config.py` |
| Update orchestrator | `src/rlm/core/orchestrator.py` |

## Recent Changes

- **MCP Server Refactor**: Simplified to code sandbox only (no LLM calls)
- **OAuth Support**: Added auth.py for Snipara token integration
- **WebAssembly REPL**: New wasm.py for Pyodide execution
- **Exception Hierarchy**: Comprehensive error handling in exceptions.py
- **Trajectory Visualizer**: Streamlit dashboard for debugging
