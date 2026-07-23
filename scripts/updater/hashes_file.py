"""Hashes file I/O."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from pathlib import Path


def load_hashes(path: Path) -> dict[str, Any]:
    """Load and parse a package's ``hashes.json`` file."""
    return cast("dict[str, Any]", json.loads(path.read_text()))


def save_hashes(path: Path, data: dict[str, Any]) -> None:
    """Write ``data`` to a package's ``hashes.json`` (JSON, 2-space indent)."""
    path.write_text(json.dumps(data, indent=2) + "\n")
