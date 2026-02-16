"""Local Development REPL with unrestricted execution.

This module provides an unrestricted Python execution environment for local
development. Unlike the sandboxed LocalREPL, this allows full access to:
- File system (read/write)
- Shell commands (subprocess)
- Network access
- Any installed libraries (numpy, pandas, etc.)

SECURITY WARNING: This mode should ONLY be used for local development.
Never expose this to untrusted code or remote users.

Requires explicit opt-in via:
- Config: trust_level = "local"
- Environment: RLM_TRUST_LEVEL=local
"""

from __future__ import annotations

import asyncio
import io
import logging
import platform
import sys
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Resource tracking only available on Unix
try:
    import resource

    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

from rlm.core.types import REPLResult
from rlm.repl.base import BaseREPL
from rlm.repl.safety import MAX_EXECUTION_TIME, truncate_output

# Logger for audit trail
logger = logging.getLogger("rlm.repl.localdev")


class LocalDevREPL(BaseREPL):
    """Unrestricted local Python REPL for development.

    This REPL provides full access to the Python environment without
    any sandboxing restrictions. Use only for trusted code in local
    development scenarios.

    Features:
    - Full file system access
    - Shell command execution via subprocess
    - Network access
    - All installed packages available
    - Project working directory awareness
    - Audit logging of all executions

    Example:
        ```python
        repl = LocalDevREPL(
            working_dir="/path/to/project",
            audit_log=True,
        )
        result = await repl.execute("import pandas as pd; print(pd.__version__)")
        ```

    Security:
        - Requires explicit opt-in via trust_level="local"
        - All code execution is logged
        - Should only be used on localhost
    """

    def __init__(
        self,
        timeout: int = MAX_EXECUTION_TIME,
        working_dir: str | Path | None = None,
        audit_log: bool = True,
        venv_path: str | Path | None = None,
    ):
        """Initialize the local dev REPL.

        Args:
            timeout: Maximum execution time in seconds
            working_dir: Working directory for code execution (default: cwd)
            audit_log: Whether to log all executions (default: True)
            venv_path: Path to virtual environment (auto-detected if None)
        """
        self.timeout = timeout
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.audit_log = audit_log
        self.venv_path = Path(venv_path) if venv_path else self._detect_venv()

        self._globals: dict[str, Any] = {}
        self._context: dict[str, Any] = {}
        self._execution_count = 0
        self._setup_globals()

        if self.audit_log:
            logger.info(
                "LocalDevREPL initialized",
                extra={
                    "working_dir": str(self.working_dir),
                    "venv_path": str(self.venv_path) if self.venv_path else None,
                },
            )

    def _detect_venv(self) -> Path | None:
        """Auto-detect virtual environment path."""
        # Check common venv locations
        candidates = [
            self.working_dir / ".venv",
            self.working_dir / "venv",
            self.working_dir / ".env",
            Path(sys.prefix),  # Current interpreter's env
        ]

        for candidate in candidates:
            if candidate.exists() and (candidate / "bin" / "python").exists():
                return candidate
            # Windows support
            if candidate.exists() and (candidate / "Scripts" / "python.exe").exists():
                return candidate

        return None

    def _setup_globals(self) -> None:
        """Setup unrestricted globals for execution."""
        self._globals = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "__file__": str(self.working_dir / "<rlm-localdev>"),
            # Shared context accessible to user code
            "context": self._context,
            # Result variable for returning values
            "result": None,
            # Convenience imports (commonly used)
            "Path": Path,
        }

        # Add working directory to path for local imports
        if str(self.working_dir) not in sys.path:
            sys.path.insert(0, str(self.working_dir))

    def _get_resource_usage(self) -> tuple[float, int] | None:
        """Get current resource usage (CPU time in ms, memory in bytes).

        Returns:
            Tuple of (cpu_time_ms, memory_bytes) or None on Windows
        """
        if not HAS_RESOURCE:
            return None
        usage = resource.getrusage(resource.RUSAGE_SELF)
        cpu_time_ms = int((usage.ru_utime + usage.ru_stime) * 1000)
        # ru_maxrss is in bytes on Linux, kilobytes on macOS
        if platform.system() == "Darwin":
            memory_bytes = usage.ru_maxrss  # Already in bytes on macOS
        else:
            memory_bytes = usage.ru_maxrss * 1024  # Convert KB to bytes on Linux
        return cpu_time_ms, memory_bytes

    def _log_execution(self, code: str, result: REPLResult) -> None:
        """Log code execution for audit trail."""
        if not self.audit_log:
            return

        self._execution_count += 1
        log_data = {
            "execution_id": self._execution_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "working_dir": str(self.working_dir),
            "code_length": len(code),
            "code_preview": code[:200] + "..." if len(code) > 200 else code,
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
        }

        if result.success:
            logger.info("Code executed successfully", extra=log_data)
        else:
            log_data["error"] = result.error
            logger.warning("Code execution failed", extra=log_data)

    async def execute(self, code: str, timeout: int | None = None) -> REPLResult:
        """Execute code without restrictions.

        Args:
            code: Python code to execute
            timeout: Optional timeout override

        Returns:
            REPLResult with output, error, and timing
        """
        timeout = timeout or self.timeout
        start_time = time.time()

        # Get resource usage before execution
        start_resources = self._get_resource_usage()

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Sync context
            self._globals["context"] = self._context
            self._globals["result"] = None

            # Compile the code
            compiled = compile(code, "<rlm-localdev>", "exec")

            # Execute with timeout using asyncio
            loop = asyncio.get_event_loop()

            def _run_code() -> None:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(compiled, self._globals)

            # Run in thread pool with timeout
            await asyncio.wait_for(
                loop.run_in_executor(None, _run_code),
                timeout=timeout,
            )

            # Get resource usage after execution
            end_resources = self._get_resource_usage()

            # Calculate resource deltas
            cpu_time_ms: int | None = None
            memory_peak_bytes: int | None = None
            if start_resources and end_resources:
                cpu_time_ms = int(end_resources[0] - start_resources[0])
                memory_peak_bytes = end_resources[1]

            # Collect output
            output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            if stderr_output:
                if output:
                    output += "\n"
                output += f"[stderr]\n{stderr_output}"

            # Check for result variable
            result_value = self._globals.get("result")
            if result_value is not None:
                if output and not output.endswith("\n"):
                    output += "\n"
                output += f"result = {result_value!r}"

            # Apply truncation if needed
            output, truncated = truncate_output(output)

            result = REPLResult(
                output=output,
                error=None,
                execution_time_ms=int((time.time() - start_time) * 1000),
                truncated=truncated,
                memory_peak_bytes=memory_peak_bytes,
                cpu_time_ms=cpu_time_ms,
            )

            self._log_execution(code, result)
            return result

        except asyncio.TimeoutError:
            result = REPLResult(
                output="",
                error=f"Execution timed out after {timeout} seconds",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            self._log_execution(code, result)
            return result

        except Exception as e:
            error_msg = self._format_error(e, code)
            result = REPLResult(
                output=stdout_capture.getvalue(),
                error=error_msg,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            self._log_execution(code, result)
            return result

    def _format_error(self, exc: Exception, code: str) -> str:
        """Format an exception with full traceback."""
        lines = code.splitlines()
        parts = [f"{type(exc).__name__}: {exc}"]

        # Extract line number from traceback
        tb = traceback.extract_tb(exc.__traceback__)
        line_no = None
        for frame in reversed(tb):
            if frame.filename == "<rlm-localdev>":
                line_no = frame.lineno
                break

        # Show the offending line
        if line_no and 1 <= line_no <= len(lines):
            offending_line = lines[line_no - 1]
            parts.append(f"  Line {line_no}: {offending_line.strip()}")

        # Add full traceback for debugging
        parts.append("\nFull traceback:")
        parts.append(traceback.format_exc())

        return "\n".join(parts)

    def get_context(self) -> dict[str, Any]:
        """Get the current context."""
        return self._context.copy()

    def set_context(self, key: str, value: Any) -> None:
        """Set a value in the context."""
        self._context[key] = value

    def clear_context(self) -> None:
        """Clear the context."""
        self._context.clear()
        self._globals["result"] = None

    def reset(self) -> None:
        """Reset the REPL to a clean state."""
        self.clear_context()
        self._setup_globals()

    async def run_shell(self, command: str, timeout: int | None = None) -> REPLResult:
        """Execute a shell command.

        Convenience method for running shell commands without writing
        subprocess boilerplate.

        Args:
            command: Shell command to execute
            timeout: Optional timeout override

        Returns:
            REPLResult with command output
        """
        code = f"""
import subprocess
_proc = subprocess.run(
    {command!r},
    shell=True,
    capture_output=True,
    text=True,
    cwd={str(self.working_dir)!r},
    timeout={timeout or self.timeout},
)
print(_proc.stdout)
if _proc.stderr:
    print("[stderr]", _proc.stderr)
result = _proc.returncode
"""
        return await self.execute(code, timeout=timeout)

    async def read_file(self, path: str | Path) -> REPLResult:
        """Read a file from the project.

        Args:
            path: Path to file (relative to working_dir or absolute)

        Returns:
            REPLResult with file contents
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.working_dir / file_path

        code = f"""
_path = Path({str(file_path)!r})
if _path.exists():
    result = _path.read_text()
    print(f"Read {{len(result)}} bytes from {{_path}}")
else:
    raise FileNotFoundError(f"File not found: {{_path}}")
"""
        return await self.execute(code)

    async def write_file(self, path: str | Path, content: str) -> REPLResult:
        """Write content to a file.

        Args:
            path: Path to file (relative to working_dir or absolute)
            content: Content to write

        Returns:
            REPLResult confirming write
        """
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.working_dir / file_path

        code = f"""
_path = Path({str(file_path)!r})
_path.parent.mkdir(parents=True, exist_ok=True)
_content = {content!r}
_path.write_text(_content)
print(f"Wrote {{len(_content)}} bytes to {{_path}}")
result = str(_path)
"""
        return await self.execute(code)

    def get_project_info(self) -> dict[str, Any]:
        """Get information about the current project environment.

        Returns:
            Dict with project details
        """
        info = {
            "working_dir": str(self.working_dir),
            "venv_path": str(self.venv_path) if self.venv_path else None,
            "python_version": sys.version,
            "platform": platform.platform(),
            "execution_count": self._execution_count,
        }

        # Check for common project files
        project_files = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            "package.json",
            ".git",
            "Cargo.toml",
            "go.mod",
        ]
        info["project_files"] = [f for f in project_files if (self.working_dir / f).exists()]

        return info
