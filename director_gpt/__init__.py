"""DirectorGPT: A collaborative multi-agent film production studio."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("directorgpt")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"

__all__ = ["__version__"]
