"""REPL execution environments."""

from rlm.repl.base import BaseREPL
from rlm.repl.local import LocalREPL

__all__ = [
    "BaseREPL",
    "LocalREPL",
]

# Docker REPL is optional - only import if docker package is available
try:
    from rlm.repl.docker import DockerREPL

    __all__.append("DockerREPL")
except ImportError:
    pass
