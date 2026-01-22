# MCP Integration Guide

RLM Runtime includes an MCP (Model Context Protocol) server that integrates with Claude Desktop and Claude Code, providing sandboxed Python execution and multi-project support.

## Installation

```bash
pip install rlm-runtime[mcp]
```

## Configuration

### Claude Code

Add to `~/.claude/claude_code_config.json`:

```json
{
  "mcpServers": {
    "rlm": {
      "command": "rlm",
      "args": ["mcp-serve"]
    }
  }
}
```

### Claude Desktop

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rlm": {
      "command": "rlm",
      "args": ["mcp-serve"]
    }
  }
}
```

After editing, restart Claude to load the MCP server.

## Available Tools

### execute_python

Execute Python code in a sandboxed environment using RestrictedPython.

**Safe operations:**
- Math calculations
- Data processing (json, re, datetime)
- Collections and algorithms
- String manipulation

**Blocked operations:**
- File I/O
- Network access
- System calls
- Subprocess execution

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | string | Yes | Python code to execute |
| `timeout` | integer | No | Timeout in seconds (default: 30, max: 60) |

**Example:**
```python
# Calculate fibonacci sequence
def fib(n):
    a, b = 0, 1
    seq = []
    while a <= n:
        seq.append(a)
        a, b = b, a + b
    return seq

result = fib(100)
print(result)
```

**Output:**
```
[0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
result = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
```

### run_completion

Run a recursive LLM completion using the RLM runtime. The LLM can use tools and execute code to solve complex tasks.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `prompt` | string | Yes | The prompt to send to the LLM |
| `model` | string | No | Model to use (default: from project config or gpt-4o-mini) |
| `system` | string | No | Optional system message |
| `max_depth` | integer | No | Maximum recursion depth (default: 4) |

**Requirements:**
- API keys must be set (`OPENAI_API_KEY` or `ANTHROPIC_API_KEY`)
- Uses project config if available (from `rlm.toml`)

### set_project

Switch between projects for multi-project workflows. Load configuration from a directory or set Snipara project directly.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `directory` | string | No | Path to project directory containing `rlm.toml` |
| `snipara_project` | string | No | Snipara project slug to use directly |
| `snipara_api_key` | string | No | Snipara API key (uses env var if not set) |

**Example:**
```
set_project(directory="/Users/me/projects/my-app")
```

**Output:**
```
Loaded config from /Users/me/projects/my-app/rlm.toml

Current status:
  Snipara enabled: true
  Snipara project: my-app
  Model: claude-sonnet-4-20250514
  Environment: docker
```

### get_project

View current project configuration and Snipara status.

**Output:**
```
Current project configuration:
  Project path: /Users/me/projects/my-app
  Config loaded: true
  Snipara enabled: true
  Snipara project: my-app
  Model: claude-sonnet-4-20250514
  Environment: docker
```

### get_repl_context

Get all variables stored in the persistent REPL context.

### set_repl_context

Set a variable in the REPL context that persists across `execute_python` calls.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | Variable name |
| `value` | string | Yes | JSON-encoded value to store |

### clear_repl_context

Clear all variables and reset the REPL to a clean state.

## Multi-Project Support

The MCP server supports working across multiple projects with different configurations.

### Auto-Detection

When the MCP server starts, it automatically loads `rlm.toml` from the current working directory.

### Per-Project Configuration

Create `rlm.toml` in each project:

```
~/projects/
├── frontend/
│   └── rlm.toml          # Frontend project config
├── backend/
│   └── rlm.toml          # Backend project config
└── data-pipeline/
    └── rlm.toml          # Data project config
```

Example `rlm.toml`:

```toml
[rlm]
model = "claude-sonnet-4-20250514"
environment = "docker"
max_depth = 4
token_budget = 8000

# Snipara integration (optional)
snipara_api_key = "rlm_..."
snipara_project_slug = "frontend"
```

### Switching Projects

Use the `set_project` tool to switch between projects:

```
User: Switch to the backend project

Claude: [set_project directory="~/projects/backend"]

Output:
Loaded config from /Users/me/projects/backend/rlm.toml
Snipara project: backend
Model: gpt-4o
```

Or set a Snipara project directly:

```
Claude: [set_project snipara_project="data-pipeline"]
```

## Allowed Imports

The sandboxed Python environment allows these safe modules:

| Category | Modules |
|----------|---------|
| **Core** | json, re, math, datetime, time, uuid, hashlib, base64, string, textwrap |
| **Collections** | collections, itertools, functools, operator |
| **Data** | dataclasses, typing, enum, copy |
| **Parsing** | csv, statistics, decimal, fractions |
| **Paths** | pathlib, posixpath, ntpath |
| **URLs** | urllib.parse |
| **Text** | difflib, unicodedata |

## Blocked Operations

The following are blocked for security:

| Category | Examples |
|----------|----------|
| **System** | os, sys, subprocess, shutil, platform |
| **Network** | socket, ssl, requests, http, urllib.request |
| **Serialization** | pickle, shelve, marshal |
| **Database** | sqlite3 |
| **Low-level** | ctypes, cffi, mmap |
| **Concurrency** | multiprocessing, threading, asyncio |
| **Code execution** | importlib, builtins, eval, exec, compile |
| **File operations** | tempfile, fileinput, glob |
| **Debugging** | pdb, bdb, trace, traceback |

## Environment Variables

Set these for the MCP server:

```bash
# LLM API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Snipara (optional)
export SNIPARA_API_KEY=rlm_...
export SNIPARA_PROJECT_SLUG=my-project
```

## Troubleshooting

### "MCP dependencies not installed"

```bash
pip install rlm-runtime[mcp]
```

### MCP server not appearing in Claude

1. Verify the config file path is correct
2. Check JSON syntax is valid
3. Restart Claude completely
4. Check `rlm mcp-serve --help` works

### "Import not allowed"

The sandbox blocks certain imports for security. Use only the allowed modules listed above.

### Python code errors

Check the error message returned. Common issues:
- Syntax errors in code
- Using blocked imports
- Timeout exceeded (default: 30 seconds)

## Example Workflows

### Data Analysis

```
User: Calculate the mean and standard deviation of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

Claude: [execute_python]
import statistics
data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
mean = statistics.mean(data)
stdev = statistics.stdev(data)
print(f"Mean: {mean}")
print(f"Standard Deviation: {stdev:.2f}")
```

### JSON Processing

```
User: Parse this JSON and extract all email addresses

Claude: [execute_python]
import json
import re

data = '''{"users": [{"email": "a@example.com"}, {"email": "b@test.org"}]}'''
parsed = json.loads(data)
emails = [user["email"] for user in parsed["users"]]
result = emails
```

### Algorithm Implementation

```
User: Implement binary search

Claude: [execute_python]
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Test
arr = [1, 3, 5, 7, 9, 11, 13, 15]
result = binary_search(arr, 7)
print(f"Found at index: {result}")
```
