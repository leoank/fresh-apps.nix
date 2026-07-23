"""HTTP utilities."""

from __future__ import annotations

import json
import urllib.request
from typing import Any, cast

DEFAULT_USER_AGENT = "fresh-apps-nix-updater"


def fetch_text(url: str, *, timeout: int = 30) -> str:
    """Fetch ``url`` and return its body decoded as UTF-8 text."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", DEFAULT_USER_AGENT)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return cast("str", response.read().decode("utf-8"))


def fetch_json(url: str, *, timeout: int = 30) -> dict[str, Any] | list[Any]:
    """Fetch ``url`` and parse its body as JSON."""
    return cast(
        "dict[str, Any] | list[Any]", json.loads(fetch_text(url, timeout=timeout))
    )
