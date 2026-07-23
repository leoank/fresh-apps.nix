"""Hash utilities."""

from __future__ import annotations

import base64
import json
import subprocess
from typing import cast


def hex_to_sri(hex_hash: str, algo: str = "sha256") -> str:
    """Convert a hex digest to Nix SRI format (e.g. ``sha256-...``)."""
    digest = bytes.fromhex(hex_hash)
    return f"{algo}-{base64.b64encode(digest).decode('ascii')}"


def calculate_url_hash(url: str) -> str:
    """Download ``url`` via ``nix store prefetch-file`` and return its SRI hash."""
    out = subprocess.check_output(
        ["nix", "store", "prefetch-file", "--json", "--hash-type", "sha256", url],
        text=True,
    )
    return cast("str", json.loads(out)["hash"])
