"""Pytest configuration for test import paths."""

from pathlib import Path
import sys


def _add_src_to_path() -> None:
    """Add project src directory to sys.path for test imports.

    This keeps imports stable in local runs and CI environments where
    PYTHONPATH may not be preconfigured.
    """
    project_root = Path(__file__).resolve().parents[1]
    src_path = project_root / "src"
    src_path_str = str(src_path)
    if src_path_str not in sys.path:
        sys.path.insert(0, src_path_str)


_add_src_to_path()
