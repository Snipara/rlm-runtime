# RLM Runtime Audit - 2026-04-29

This note records the confirmed issues from the runtime investigation, the fixes that were applied in this workspace, and the remaining gaps that were observed but not changed.

## Confirmed Issues

| Issue | Evidence | Status |
| --- | --- | --- |
| `rlm --version` failed, while `rlm version` worked | Root Typer command lacked a version callback | Fixed |
| CLI/package version mismatch | Source reported `2.1.2`, installed package reported `2.0.0` | Documented in version output |
| `.env` was not loaded by `rlm doctor` / `rlm run` | `OPENAI_API_KEY` was visible only after `source .env` | Fixed |
| Errors returned exit code `0` and `success: true` | Missing OpenAI key and recursion errors were treated as success | Fixed |
| `--json` was not clean JSON | Debug logs were emitted before the payload | Fixed |
| `--max-depth 0` was accepted | It failed immediately instead of being rejected up front | Fixed |
| `--max-depth 1` was too shallow for trivial prompts | Smoke tests only became reliable at `--max-depth 3` with the environment loaded | Still a behavior limit |
| Repo MCP config did not include the runtime target | `.mcp.json` only exposed Snipara | Still open |

## Changes Applied

### CLI behavior

- Added a root Typer callback so `rlm --version` now works.
- Kept `version` and `--version` aligned, including the installed-package mismatch when it exists.
- Added early validation for `--max-depth 0`.
- Made `run` and `agent` return non-zero exit codes when the result is not successful.
- Captured stdout/stderr during JSON runs so `--json` emits only the final JSON payload.

### Configuration loading

- Added explicit `.env` loading in `src/rlm/core/config.py`.
- The loader walks upward from the project directory, stops at the repo root, and parses standard `KEY=VALUE` lines without depending on `python-dotenv`.
- `load_config()` now loads the environment before building runtime config.
- The CLI also loads the project environment during startup so `doctor` and `run` see the same variables.

### Result/error propagation

- Added `error` to `RLMResult`.
- A result is successful only when there is no top-level error and no event-level error.
- The orchestrator now propagates completion failures into the returned result instead of masking them.

### Test coverage

- Added CLI tests for:
  - root `--version`
  - non-zero failure exit codes
  - clean JSON output
  - `--max-depth 0` rejection
- Added config tests for `.env` loading.
- Added type/result tests so failures without trajectory data still count as failures.

## Validation Performed

- `python3 -m pytest tests/unit/test_config.py tests/unit/test_types.py tests/unit/test_cli.py -q`
- `python3 -m pytest tests/unit/test_orchestrator.py tests/unit/test_sub_llm.py -q`
- `python3 -m ruff check src/rlm/core/config.py src/rlm/core/types.py src/rlm/core/orchestrator.py src/rlm/cli/main.py tests/unit/test_config.py tests/unit/test_types.py tests/unit/test_cli.py`

## Remaining Notes

- `--max-depth 1` remains a tight setting and may still fail on prompts that need one or more tool or recursion steps.
- The repo release path is present via `make build` and `make publish`, and the GitHub release workflow also builds and uploads artifacts, but no package publish has been executed yet in this session.
- The MCP runtime config issue is still only documented here; it has not been changed in the repository.
