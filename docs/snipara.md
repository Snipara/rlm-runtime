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

## Setup

### 1. Install the Plugin

```bash
pip install rlm-runtime[snipara]
# or
pip install snipara-mcp
```

### 2. Get API Credentials

1. Go to [snipara.com/dashboard](https://snipara.com/dashboard)
2. Create or select a project
3. Copy your API key and project slug

### 3. Configure

**Option A: Environment Variables**

```bash
export SNIPARA_API_KEY=rlm_your_key_here
export SNIPARA_PROJECT_SLUG=your-project
```

**Option B: Config File (rlm.toml)**

```toml
[rlm]
snipara_api_key = "rlm_your_key_here"
snipara_project_slug = "your-project"
```

**Option C: Code**

```python
from rlm import RLM

rlm = RLM(
    snipara_api_key="rlm_your_key_here",
    snipara_project_slug="your-project",
)
```

## Available Tools

When Snipara is configured, these tools are automatically registered:

### context_query

Query for relevant documentation context.

```
Tool: context_query
Parameters:
  - query: string (required) - What to search for
  - max_tokens: integer (default: 4000) - Token budget
  - search_mode: "keyword" | "semantic" | "hybrid" (default: "hybrid")
  - include_metadata: boolean (default: true)
```

### sections

List all available documentation sections.

```
Tool: sections
Parameters: none
```

### search

Search for patterns across documentation.

```
Tool: search
Parameters:
  - pattern: string (required) - Regex pattern
  - file_pattern: string (default: "*") - File glob
```

### shared_context

Get team best practices and guidelines.

```
Tool: shared_context
Parameters:
  - query: string (optional) - Filter query
  - max_tokens: integer (default: 4000)
  - categories: array of "MANDATORY" | "BEST_PRACTICES" | "GUIDELINES" | "REFERENCE"
```

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

## How It Works

```
1. User asks: "Explain authentication"
   │
2. LLM calls: context_query("authentication")
   │
3. Snipara returns:
   - Relevant sections from auth.md
   - Code snippets from auth.py
   - Related security guidelines
   - All within token budget (~5K tokens)
   │
4. LLM synthesizes answer using optimized context
```

## Best Practices

### Index Your Documentation

Make sure your project documentation is indexed in Snipara:

1. Go to your project in the dashboard
2. Add documentation sources (Git, files, etc.)
3. Wait for indexing to complete

### Use Shared Context

For team-wide best practices:

```python
# Query shared context first
result = await rlm.completion(
    "What are our coding standards for error handling?",
    system="Use shared_context to find team guidelines."
)
```

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

Check that:
1. `snipara-mcp` is installed: `pip install snipara-mcp`
2. API key is set correctly
3. Project slug is valid

### "API key invalid"

1. Verify the key at [snipara.com/dashboard](https://snipara.com/dashboard)
2. Check for typos (keys start with `rlm_`)
3. Ensure the key has access to the specified project

### "No results returned"

1. Verify your project has indexed documentation
2. Try a broader search query
3. Check the project slug matches your dashboard
