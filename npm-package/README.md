# @rlm/runtime

TypeScript SDK for RLM Runtime - Sandboxed Python execution for AI agents.

## Installation

```bash
npm install @rlm/runtime
```

## Usage

### Type Definitions

```typescript
import type {
  ExecutePythonParams,
  REPLResult,
  AgentRunParams,
  AgentResult,
  TrustLevel,
  ExecutionProfile,
} from '@rlm/runtime';

// Type-safe parameters for execute_python
const params: ExecutePythonParams = {
  code: 'print(2 + 2)',
  profile: 'default',
  session_id: 'my-session',
};
```

### Constants & Utilities

```typescript
import {
  EXECUTION_PROFILES,
  ALLOWED_IMPORTS,
  BLOCKED_IMPORTS,
  MCP_TOOLS,
  isImportAllowed,
  getProfile,
} from '@rlm/runtime';

// Check execution profiles
console.log(EXECUTION_PROFILES.analysis);
// { timeout: 120, memory: '2g', description: '...' }

// Check if import is allowed in sandbox
console.log(isImportAllowed('json'));      // true
console.log(isImportAllowed('subprocess')); // false

// Get MCP tool names
console.log(MCP_TOOLS.EXECUTE_PYTHON); // 'execute_python'
```

## Trust Levels

| Level | Description |
|-------|-------------|
| `sandboxed` | RestrictedPython, safe stdlib only (default) |
| `docker` | Docker container isolation |
| `local` | Full access to files, subprocess, network |

## Execution Profiles

| Profile | Timeout | Memory | Use Case |
|---------|---------|--------|----------|
| `quick` | 5s | 128MB | Simple math, string ops |
| `default` | 30s | 512MB | Standard algorithms |
| `analysis` | 120s | 2GB | Large datasets |
| `extended` | 300s | 4GB | Batch processing |

## MCP Tools

| Tool | Description |
|------|-------------|
| `execute_python` | Run Python code in sandbox |
| `get_repl_context` | Get persistent variables |
| `set_repl_context` | Set persistent variables |
| `clear_repl_context` | Clear session state |
| `list_sessions` | List active sessions |
| `destroy_session` | Destroy a session |
| `rlm_agent_run` | Start autonomous agent |
| `rlm_agent_status` | Check agent status |
| `rlm_agent_cancel` | Cancel running agent |

## License

MIT
