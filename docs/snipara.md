# Snipara Integration

Snipara provides intelligent context optimization for RLM Runtime. Instead of reading entire files, the LLM queries Snipara for the most relevant sections.

## Why Snipara?

| Without Snipara | With Snipara |
|-----------------|--------------|
| Read all files (~500K tokens) | Get relevant context (~5K tokens) |
| Exceed token limits | Stay within budget |
| Basic file search | Semantic + keyword search |
| No shared knowledge | Team best practices |
| Manual context management | Automatic optimization |
| No persistent memory | Semantic memory recall |

## How It Works

RLM accesses Snipara through **two mechanisms** — a native HTTP client
(preferred) and the `snipara-mcp` package (backward-compatible fallback):

```
Orchestrator._register_snipara_tools()
    |
    +-- Attempt 1: Native HTTP client (src/rlm/tools/snipara.py)
    |   SniparaClient.from_config(config)
    |       -> resolves auth automatically
    |       -> returns None when no credentials found
    |   get_native_snipara_tools(client, memory_enabled)
    |       -> 5 tools (Tiers 1+3) or 9 tools (all tiers)
    |
    +-- Attempt 2: snipara-mcp package (backward compat)
        from snipara_mcp.rlm_tools import get_snipara_tools
```

The native client sends **JSON-RPC 2.0** payloads to the Snipara API
endpoint at `https://api.snipara.com/mcp/{project_slug}`.

## Setup

### Option A: OAuth (Recommended)

No API key copying — authenticate via browser:

```bash
pip install rlm-runtime[mcp]
snipara-mcp-login      # Opens browser for OAuth Device Flow
snipara-mcp-status     # Verify auth status
```

Tokens are stored at `~/.snipara/tokens.json` and refreshed automatically.

### Option B: API Key

For open-source or non-Snipara users:

**Environment Variables:**

```bash
export SNIPARA_API_KEY=rlm_your_key_here
export SNIPARA_PROJECT_SLUG=your-project
```

**Config File (rlm.toml):**

```toml
[rlm]
snipara_api_key = "rlm_your_key_here"
snipara_project_slug = "your-project"
```

**Code:**

```python
from rlm import RLM

rlm = RLM(
    snipara_api_key="rlm_your_key_here",
    snipara_project_slug="your-project",
)
```

### Option C: snipara-mcp Package (Backward Compat)

```bash
pip install rlm-runtime[mcp] snipara-mcp
```

This uses the `snipara-mcp` package directly. The native client is
preferred for new installations.

### Auth Resolution Order

Credentials are resolved top-down; the first match wins:

| Priority | Source | Header | Notes |
|----------|--------|--------|-------|
| 1 | OAuth tokens (`~/.snipara/tokens.json`) | `Authorization: Bearer <token>` | Via `snipara-mcp-login` |
| 2 | `SNIPARA_API_KEY` env var | `x-api-key: <key>` | For plain API keys |
| 3 | `snipara_api_key` in `rlm.toml` | `x-api-key: <key>` | Static config fallback |
| 4 | `snipara-mcp` package import | (package handles auth) | Backward compat only |

If none are available, Snipara tools are silently skipped.

## Available Tools

Tools are organised into three tiers:

### Tier 1 — Context Retrieval (always registered)

#### rlm_context_query

Primary semantic/keyword/hybrid documentation search.

```
Parameters:
  - query: string (required) - What to search for
  - max_tokens: integer (default: 4000) - Token budget for results
  - search_mode: "keyword" | "semantic" | "hybrid" (default: "hybrid")
  - prefer_summaries: boolean (default: false)
  - include_metadata: boolean (default: true)
```

#### rlm_search

Regex pattern search across all indexed documentation.

```
Parameters:
  - pattern: string (required) - Regex pattern
  - max_results: integer (default: 20)
```

#### rlm_sections

List indexed documentation sections with pagination.

```
Parameters:
  - filter: string (optional) - Title prefix filter (case-insensitive)
  - limit: integer (default: 50)
  - offset: integer (default: 0)
```

#### rlm_read

Read specific lines from indexed documentation.

```
Parameters:
  - start_line: integer (required)
  - end_line: integer (required)
```

### Tier 2 — Memory (gated by `memory_enabled`)

These tools require `memory_enabled = true` in config or `RLM_MEMORY_ENABLED=true` env var.

#### rlm_remember

Store a memory for later semantic recall.

```
Parameters:
  - content: string (required) - Memory content
  - type: "fact" | "decision" | "learning" | "preference" | "todo" | "context" (default: "fact")
  - scope: "agent" | "project" | "team" | "user" (default: "project")
  - category: string (optional) - Grouping category
  - ttl_days: integer (optional) - Days until expiration
  - related_to: array of string (optional) - Related memory IDs
  - document_refs: array of string (optional) - Referenced document paths
```

#### rlm_recall

Semantically search stored memories using embedding-based similarity.

```
Parameters:
  - query: string (required) - Search query
  - limit: integer (default: 5)
  - min_relevance: float (default: 0.5) - Minimum relevance score (0-1)
  - type: string (optional) - Filter by memory type
  - scope: string (optional) - Filter by scope
  - category: string (optional) - Filter by category
```

#### rlm_memories

List stored memories with optional filters (no semantic search).

```
Parameters:
  - type: string (optional) - Filter by memory type
  - scope: string (optional) - Filter by scope
  - category: string (optional) - Filter by category
  - search: string (optional) - Text search in content
  - limit: integer (default: 20)
  - offset: integer (default: 0)
```

#### rlm_forget

Delete memories by ID, type, category, or age.

```
Parameters:
  - memory_id: string (optional) - Specific memory ID
  - type: string (optional) - Delete by type
  - category: string (optional) - Delete by category
  - older_than_days: integer (optional) - Delete memories older than N days
```

### Tier 3 — Advanced (always registered)

#### rlm_shared_context

Merged team documentation from shared collections with budget allocation.

```
Parameters:
  - categories: array of "MANDATORY" | "BEST_PRACTICES" | "GUIDELINES" | "REFERENCE" (optional)
  - max_tokens: integer (default: 4000)
  - include_content: boolean (default: true)
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SNIPARA_API_KEY` | Raw API key for authentication | None |
| `SNIPARA_PROJECT_SLUG` | Project slug for API URL | None |
| `RLM_SNIPARA_BASE_URL` | Override API base URL | `https://api.snipara.com/mcp` |
| `RLM_MEMORY_ENABLED` | Enable Tier 2 memory tools | `false` |

## Example Usage

```python
from rlm import RLM

async def main():
    rlm = RLM(
        model="gpt-4o-mini",
        snipara_api_key="rlm_...",
        snipara_project_slug="my-project",
    )

    # The LLM will automatically use Snipara tools
    result = await rlm.completion(
        "How does the authentication system work? "
        "Include code examples."
    )

    print(result.response)
    print(f"Tool calls: {result.total_tool_calls}")
```

## Workflow Example

```
1. User asks: "Explain authentication"
   |
2. LLM calls: rlm_context_query("authentication")
   |
3. Snipara returns:
   - Relevant sections from auth.md
   - Code snippets from auth.py
   - Related security guidelines
   - All within token budget (~5K tokens)
   |
4. LLM synthesizes answer using optimized context
```

## Best Practices

### Index Your Documentation

Make sure your project documentation is indexed in Snipara:

1. Go to your project in the [dashboard](https://snipara.com/dashboard)
2. Add documentation sources (Git, files, etc.)
3. Wait for indexing to complete

### Use Shared Context

For team-wide best practices:

```python
result = await rlm.completion(
    "What are our coding standards for error handling?",
    system="Use rlm_shared_context to find team guidelines."
)
```

### Enable Memory for Multi-Step Tasks

```toml
[rlm]
memory_enabled = true
```

The LLM can then store decisions and recall them across completions.

### Set Appropriate Token Budgets

```python
from rlm import RLM, CompletionOptions

rlm = RLM(snipara_api_key="...", snipara_project_slug="...")

# For detailed responses, allow more tokens
options = CompletionOptions(token_budget=12000)
result = await rlm.completion("Full architecture overview", options=options)
```

## Pricing

Snipara charges per context query:

| Plan | Queries/Month | Price |
|------|---------------|-------|
| Free | 100 | $0 |
| Pro | 5,000 | $19/mo |
| Team | 20,000 | $49/mo |
| Enterprise | Unlimited | Custom |

## Troubleshooting

### "Snipara tools not registered"

Check that at least one auth source is configured:

1. OAuth: Run `snipara-mcp-login` and verify with `snipara-mcp-status`
2. API key: `echo $SNIPARA_API_KEY`
3. Config: Check `snipara_api_key` in `rlm.toml`
4. Project slug is set: `echo $SNIPARA_PROJECT_SLUG`

### "SniparaAPIError: 401 Unauthorized"

1. OAuth tokens may have expired — run `snipara-mcp-login` again
2. Verify the API key at [snipara.com/dashboard](https://snipara.com/dashboard)
3. Check for typos (keys start with `rlm_`)
4. Ensure the key has access to the specified project

### "SniparaAPIError: Connection refused"

1. Check your internet connection
2. Verify `RLM_SNIPARA_BASE_URL` is correct (default: `https://api.snipara.com/mcp`)
3. Check for proxy/firewall blocking

### "No results returned"

1. Verify your project has indexed documentation
2. Try a broader search query
3. Check the project slug matches your dashboard
