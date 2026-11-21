"""Release notes as one small file per user-visible change."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("relnotes")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0"
