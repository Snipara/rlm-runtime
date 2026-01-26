"""Safety utilities for REPL execution."""

from __future__ import annotations

# Allowed imports in sandboxed execution
# These are safe standard library modules
ALLOWED_IMPORTS: frozenset[str] = frozenset(
    {
        # Core utilities
        "json",
        "re",
        "math",
        "datetime",
        "time",
        "uuid",
        "hashlib",
        "base64",
        "string",
        "textwrap",
        # Collections and iteration
        "collections",
        "itertools",
        "functools",
        "operator",
        # Data structures
        "dataclasses",
        "typing",
        "enum",
        "copy",
        # Parsing
        "csv",
        "statistics",
        "decimal",
        "fractions",
        # Path operations (read-only)
        "pathlib",
        "posixpath",
        "ntpath",
        # URL parsing (no requests)
        "urllib.parse",
        # Text processing
        "difflib",
        "unicodedata",
    }
)

# Explicitly blocked - dangerous or can escape sandbox
BLOCKED_IMPORTS: frozenset[str] = frozenset(
    {
        # System access
        "os",
        "sys",
        "subprocess",
        "shutil",
        "platform",
        "signal",
        "resource",
        # Network access
        "socket",
        "ssl",
        "requests",
        "urllib.request",
        "urllib.error",
        "http",
        "http.client",
        "http.server",
        "ftplib",
        "smtplib",
        "poplib",
        "imaplib",
        "telnetlib",
        # Serialization (can execute arbitrary code)
        "pickle",
        "shelve",
        "marshal",
        # Database
        "sqlite3",
        # Low-level
        "ctypes",
        "cffi",
        "mmap",
        # Concurrency (can escape sandbox)
        "multiprocessing",
        "threading",
        "concurrent",
        "asyncio",
        # Code execution
        "importlib",
        "builtins",
        "__builtins__",
        "eval",
        "exec",
        "compile",
        "code",
        "codeop",
        # File operations beyond basic
        "tempfile",
        "fileinput",
        "glob",
        "fnmatch",
        # Debugging
        "pdb",
        "bdb",
        "trace",
        "traceback",
        # Other dangerous
        "atexit",
        "gc",
        "inspect",
        "dis",
        "ast",
    }
)


def is_import_allowed(module_name: str) -> bool:
    """Check if a module import is allowed in the sandbox.

    Args:
        module_name: Full module name (e.g., "json", "urllib.parse")

    Returns:
        True if the import is allowed, False otherwise
    """
    # Check exact match against blocked list first
    if module_name in BLOCKED_IMPORTS:
        return False

    # Check exact match against allowed list
    if module_name in ALLOWED_IMPORTS:
        return True

    # Check parent modules
    parts = module_name.split(".")
    for i in range(len(parts)):
        parent = ".".join(parts[: i + 1])
        if parent in BLOCKED_IMPORTS:
            return False
        if parent in ALLOWED_IMPORTS:
            return True

    # Default deny - if not explicitly allowed, block it
    return False


# Output limits
MAX_OUTPUT_SIZE: int = 100_000  # 100KB max output
MAX_OUTPUT_LINES: int = 1000  # Max lines in output

# Execution limits
MAX_EXECUTION_TIME: int = 30  # Default timeout in seconds
MAX_MEMORY_MB: int = 512  # Memory limit for Docker


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> tuple[str, bool]:
    """Truncate output if it exceeds the maximum size.

    Args:
        output: Output string to potentially truncate
        max_size: Maximum allowed size in bytes

    Returns:
        Tuple of (possibly truncated output, was_truncated)
    """
    if len(output) <= max_size:
        return output, False

    truncated = output[:max_size]
    # Try to truncate at a line boundary
    last_newline = truncated.rfind("\n")
    if last_newline > max_size // 2:
        truncated = truncated[:last_newline]

    return truncated + "\n... (output truncated)", True
