"""Lightweight updater library for fresh-apps.nix.

Adapted from numtide/llm-agents.nix (MIT, Copyright (c) 2024 Numtide).
"""

from .hash import calculate_url_hash, hex_to_sri
from .hashes_file import load_hashes, save_hashes
from .http import fetch_json, fetch_text

__all__ = [
    "calculate_url_hash",
    "fetch_json",
    "fetch_text",
    "hex_to_sri",
    "load_hashes",
    "save_hashes",
]
