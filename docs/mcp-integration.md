# MCP Integration Guide

RLM Runtime includes an MCP (Model Context Protocol) server that provides a sandboxed Python execution environment to Claude Desktop, Claude Code, and other MCP clients.

**Zero API keys required** - Designed to work within Claude Code's billing. For Snipara context retrieval, use [snipara-mcp](https://pypi.org/project/snipara-mcp/) separately (with OAuth Device Flow authentication).

## Installation

```bash
pip install rlm-runtime[mcp]
```

## Configuration

### Claude Code

Add to your Claude Code MCP settings:

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

### get_repl_context

Get all variables stored in the persistent REPL context from previous `execute_python` calls.

### set_repl_context

Set a variable in the REPL context that persists across `execute_python` calls.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `key` | string | Yes | Variable name |
| `value` | string | Yes | JSON-encoded value to store |

### clear_repl_context

Clear all variables and reset the REPL to a clean state.

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

## Using with Snipara

For context retrieval from your documentation, use the snipara-mcp server alongside rlm-runtime:

```json
{
  "mcpServers": {
    "rlm": {
      "command": "rlm",
      "args": ["mcp-serve"]
    },
    "snipara": {
      "command": "snipara-mcp-server"
    }
  }
}
```

Authenticate with Snipara using OAuth Device Flow (no API key copying needed):

```bash
# Install snipara-mcp
pip install snipara-mcp

# Login via browser
snipara-mcp-login

# Check status
snipara-mcp-status
```

This provides:
- **rlm-runtime**: Code execution sandbox (no API keys)
- **snipara-mcp**: Context retrieval (OAuth authentication)

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

### Persistent State

```
User: Store some data for later use

Claude: [set_repl_context key="users" value='["Alice", "Bob", "Charlie"]']

User: Now process that data

Claude: [execute_python]
# 'users' is available from context
for i, user in enumerate(users):
    print(f"{i+1}. {user}")
```

## Architecture

```
Claude Code (LLM + billing included)
    │
    ├── rlm-runtime-mcp (code sandbox)
    │   ├── execute_python
    │   ├── get_repl_context
    │   ├── set_repl_context
    │   └── clear_repl_context
    │
    └── snipara-mcp (optional, OAuth auth)
        └── search_context
```

This architecture provides:
- **Zero API costs** - All LLM calls go through Claude Code
- **Sandboxed execution** - Safe Python code execution
- **Persistent state** - Variables carry over between calls
- **Context retrieval** - Optional Snipara integration
