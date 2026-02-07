# /repl - Python REPL Command

Execute Python code in a sandboxed environment with persistent context.

## Usage

```
/repl <code>           Execute Python code
/repl context          Show current REPL context
/repl clear            Clear REPL context
/repl set <key> <val>  Set a context variable
```

## Instructions

When the user invokes `/repl`, determine the action:

### 1. Execute Code (default)
If the user provides code after `/repl`, execute it using `mcp__rlm__execute_python`:

```
User: /repl print("Hello, World!")
Action: Call mcp__rlm__execute_python with code="print('Hello, World!')"
```

For multi-line code, the user can use triple backticks:
```
User: /repl
```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print([fibonacci(i) for i in range(10)])
```

### 2. Show Context
If the user types `/repl context`, call `mcp__rlm__get_repl_context` to show stored variables.

### 3. Clear Context
If the user types `/repl clear`, call `mcp__rlm__clear_repl_context` to reset the session.

### 4. Set Variable
If the user types `/repl set <key> <value>`, call `mcp__rlm__set_repl_context` with the key and JSON-encoded value.

## Available Imports

The sandboxed REPL allows these imports:
- `json`, `re`, `math`, `datetime`
- `collections`, `itertools`, `functools`
- `operator`, `string`, `random`
- `hashlib`, `base64`, `urllib.parse`

## Session Persistence

Variables created in one `/repl` call persist for subsequent calls within the same session. Use `/repl context` to see what's stored.

## Examples

```
# Simple calculation
/repl 2 + 2

# Store and retrieve
/repl data = {"users": 100, "active": 42}
/repl print(f"Active rate: {data['active']/data['users']*100}%")

# Check context
/repl context

# Clear and start fresh
/repl clear
```
