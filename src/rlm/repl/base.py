"""Abstract base class for REPL environments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from rlm.core.types import REPLResult


class BaseREPL(ABC):
    """Abstract base class for REPL execution environments.

    Implement this class to add support for new execution environments.
    """

    @abstractmethod
    async def execute(self, code: str, timeout: int | None = None) -> REPLResult:
        """Execute code in the REPL environment.

        Args:
            code: Python code to execute
            timeout: Optional timeout in seconds

        Returns:
            REPLResult with output, error, and timing information
        """
        ...

    @abstractmethod
    def get_context(self) -> dict[str, Any]:
        """Get the current shared context.

        The context is a dictionary that persists across executions
        within the same REPL instance.

        Returns:
            Current context dictionary
        """
        ...

    @abstractmethod
    def set_context(self, key: str, value: Any) -> None:
        """Set a value in the shared context.

        Args:
            key: Context key
            value: Value to store
        """
        ...

    @abstractmethod
    def clear_context(self) -> None:
        """Clear all values from the shared context."""
        ...

    def reset(self) -> None:
        """Reset the REPL to a clean state.

        Default implementation just clears context.
        Subclasses may override for additional cleanup.
        """
        self.clear_context()
