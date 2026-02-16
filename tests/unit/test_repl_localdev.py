"""Tests for LocalDevREPL (unrestricted local execution)."""

from pathlib import Path

import pytest

from rlm.repl.localdev import LocalDevREPL


class TestLocalDevREPL:
    """Tests for unrestricted local development REPL."""

    @pytest.fixture
    def repl(self, tmp_path: Path) -> LocalDevREPL:
        """Create a LocalDevREPL instance for testing."""
        return LocalDevREPL(
            timeout=30,
            working_dir=tmp_path,
            audit_log=False,  # Disable logging in tests
        )

    @pytest.mark.asyncio
    async def test_simple_execution(self, repl: LocalDevREPL) -> None:
        """Test basic code execution."""
        result = await repl.execute("print(1 + 1)")
        assert result.success
        assert "2" in result.output

    @pytest.mark.asyncio
    async def test_result_variable(self, repl: LocalDevREPL) -> None:
        """Test result variable assignment."""
        result = await repl.execute("result = 42")
        assert result.success
        assert "result = 42" in result.output

    @pytest.mark.asyncio
    async def test_os_import_allowed(self, repl: LocalDevREPL) -> None:
        """Test that os import is allowed in local dev mode."""
        result = await repl.execute("import os; print(os.getcwd())")
        assert result.success
        assert result.error is None

    @pytest.mark.asyncio
    async def test_subprocess_allowed(self, repl: LocalDevREPL) -> None:
        """Test that subprocess is allowed in local dev mode."""
        result = await repl.execute(
            "import subprocess; result = subprocess.run(['echo', 'hello'], capture_output=True, text=True).stdout.strip()"
        )
        assert result.success
        assert "hello" in result.output

    @pytest.mark.asyncio
    async def test_file_write_allowed(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test that file writing is allowed in local dev mode."""
        test_file = tmp_path / "test.txt"
        result = await repl.execute(f"""
from pathlib import Path
Path('{test_file}').write_text('hello world')
result = 'written'
""")
        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "hello world"

    @pytest.mark.asyncio
    async def test_file_read_allowed(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test that file reading is allowed in local dev mode."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = await repl.execute(f"""
from pathlib import Path
result = Path('{test_file}').read_text()
""")
        assert result.success
        assert "test content" in result.output

    @pytest.mark.asyncio
    async def test_context_persistence(self, repl: LocalDevREPL) -> None:
        """Test that context persists across executions."""
        await repl.execute("context['x'] = 42")
        result = await repl.execute("print(context['x'])")
        assert result.success
        assert "42" in result.output

    @pytest.mark.asyncio
    async def test_context_api(self, repl: LocalDevREPL) -> None:
        """Test context get/set/clear API."""
        repl.set_context("key", "value")
        assert repl.get_context()["key"] == "value"

        repl.clear_context()
        assert "key" not in repl.get_context()

    @pytest.mark.asyncio
    async def test_globals_persistence(self, repl: LocalDevREPL) -> None:
        """Test that defined variables persist across executions."""
        await repl.execute("my_var = 123")
        result = await repl.execute("print(my_var)")
        assert result.success
        assert "123" in result.output

    @pytest.mark.asyncio
    async def test_syntax_error(self, repl: LocalDevREPL) -> None:
        """Test syntax error handling."""
        result = await repl.execute("if True print('x')")
        assert not result.success
        assert "SyntaxError" in result.error

    @pytest.mark.asyncio
    async def test_runtime_error(self, repl: LocalDevREPL) -> None:
        """Test runtime error handling."""
        result = await repl.execute("1 / 0")
        assert not result.success
        assert "ZeroDivisionError" in result.error

    @pytest.mark.asyncio
    async def test_timeout(self, repl: LocalDevREPL) -> None:
        """Test timeout enforcement."""
        result = await repl.execute(
            "import time; time.sleep(10)",
            timeout=1,
        )
        assert not result.success
        assert "timed out" in result.error.lower()

    @pytest.mark.asyncio
    async def test_stderr_capture(self, repl: LocalDevREPL) -> None:
        """Test that stderr is captured."""
        result = await repl.execute("""
import sys
print("stdout message")
print("stderr message", file=sys.stderr)
""")
        assert result.success
        assert "stdout message" in result.output
        assert "stderr" in result.output
        assert "stderr message" in result.output

    @pytest.mark.asyncio
    async def test_run_shell_convenience(self, repl: LocalDevREPL) -> None:
        """Test the run_shell convenience method."""
        result = await repl.run_shell("echo 'hello from shell'")
        assert result.success
        assert "hello from shell" in result.output

    @pytest.mark.asyncio
    async def test_read_file_convenience(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test the read_file convenience method."""
        test_file = tmp_path / "read_test.txt"
        test_file.write_text("content to read")

        result = await repl.read_file(test_file)
        assert result.success
        assert "content to read" in result.output

    @pytest.mark.asyncio
    async def test_write_file_convenience(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test the write_file convenience method."""
        test_file = tmp_path / "write_test.txt"

        result = await repl.write_file(test_file, "written content")
        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "written content"

    def test_get_project_info(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test project info retrieval."""
        # Create a pyproject.toml to simulate a project
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        info = repl.get_project_info()
        assert info["working_dir"] == str(tmp_path)
        assert "pyproject.toml" in info["project_files"]
        assert "python_version" in info

    def test_reset(self, repl: LocalDevREPL) -> None:
        """Test REPL reset."""
        repl.set_context("key", "value")
        repl.reset()
        assert repl.get_context() == {}


class TestLocalDevREPLAudit:
    """Tests for audit logging functionality."""

    @pytest.mark.asyncio
    async def test_audit_log_enabled(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that audit logging works when enabled."""
        import logging

        # Enable logging capture
        caplog.set_level(logging.INFO, logger="rlm.repl.localdev")

        repl = LocalDevREPL(
            timeout=30,
            working_dir=tmp_path,
            audit_log=True,
        )

        await repl.execute("print('test')")

        # Check that execution was logged
        assert any("executed" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_execution_count(self, tmp_path: Path) -> None:
        """Test that execution count is tracked when audit_log is enabled."""
        repl = LocalDevREPL(
            timeout=30,
            working_dir=tmp_path,
            audit_log=True,  # Must be True to track execution count
        )

        # Execution count starts at 0 (init doesn't count)
        initial_count = repl._execution_count
        await repl.execute("print(1)")
        assert repl._execution_count == initial_count + 1
        await repl.execute("print(2)")
        assert repl._execution_count == initial_count + 2


class TestLocalDevREPLLibraries:
    """Tests for using external libraries in local dev mode."""

    @pytest.fixture
    def repl(self, tmp_path: Path) -> LocalDevREPL:
        """Create a LocalDevREPL instance."""
        return LocalDevREPL(
            timeout=30,
            working_dir=tmp_path,
            audit_log=False,
        )

    @pytest.mark.asyncio
    async def test_json_module(self, repl: LocalDevREPL) -> None:
        """Test JSON module (should work in both modes)."""
        result = await repl.execute("""
import json
data = {"key": "value"}
result = json.dumps(data)
""")
        assert result.success
        assert '"key"' in result.output

    @pytest.mark.asyncio
    async def test_pathlib_available(self, repl: LocalDevREPL) -> None:
        """Test that Path is pre-imported."""
        result = await repl.execute("result = str(Path('.'))")
        assert result.success
        assert "." in result.output

    @pytest.mark.asyncio
    async def test_working_directory(self, repl: LocalDevREPL, tmp_path: Path) -> None:
        """Test that working directory is set correctly."""
        # The working_dir attribute should be correctly set
        assert repl.working_dir == tmp_path
        # Verify we can execute code successfully
        exec_result = await repl.execute("print('working')")
        assert exec_result.success
