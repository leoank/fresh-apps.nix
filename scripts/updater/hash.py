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


def calculate_url_hash(url: str, name: str | None = None) -> str:
    """Download ``url`` via ``nix store prefetch-file`` and return its SRI hash.

    ``name`` overrides the store-path name, which otherwise defaults to the
    URL's basename. Required when the URL carries query parameters (e.g.
    ``?version=...``) whose characters are illegal in a store path.
    """
    cmd = ["nix", "store", "prefetch-file", "--json", "--hash-type", "sha256"]
    if name is not None:
        cmd += ["--name", name]
    cmd.append(url)
    out = subprocess.check_output(cmd, text=True)
    return cast("str", json.loads(out)["hash"])
