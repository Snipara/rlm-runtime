"""REPL execution environments."""

from rlm.repl.base import BaseREPL
from rlm.repl.local import LocalREPL
from rlm.repl.localdev import LocalDevREPL

__all__ = [
    "BaseREPL",
    "LocalREPL",
    "LocalDevREPL",
]

# Docker REPL is optional - only import if docker package is available
try:
    from rlm.repl.docker import DockerREPL  # noqa: F401

    __all__.append("DockerREPL")
except ImportError:
    pass

# WebAssembly REPL is optional - only import if pyodide is available
try:
    from rlm.repl.wasm import WasmREPL  # noqa: F401

    __all__.append("WasmREPL")
except ImportError:
    pass
