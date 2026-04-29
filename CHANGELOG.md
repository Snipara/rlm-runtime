# Changelog

All notable changes to this project are documented in this file.

## [2.1.2] - 2026-04-29

### Fixed

- `rlm --version` now works from the root CLI entrypoint.
- CLI version output now reflects the source version and the installed package version when they differ.
- Project `.env` files are loaded automatically by the CLI and config loader, so `rlm doctor` and `rlm run` no longer depend on manual `source .env`.
- Failed runs now return non-zero exit codes instead of reporting `success: true`.
- CLI JSON mode now emits clean JSON without debug logs mixed into stdout.
- `--max-depth 0` is rejected immediately with a clear error.

### Changed

- Added explicit failure propagation to `RLMResult`.
- Added tests covering CLI version handling, `.env` loading, JSON output, and max-depth validation.
- Documented the confirmed bugs, fixes, and remaining notes in `docs/rlm-runtime-audit-2026-04-29.md`.

### Notes

- `--max-depth 1` is still a tight setting and may fail on prompts that need at least one extra recursive or tool step.
- The repository's GitHub release workflow attempted trusted publishing, but PyPI rejected the repo as an invalid trusted publisher. The `2.1.2` package was published successfully with the existing local PyPI token fallback.
