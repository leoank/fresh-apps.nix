#!/usr/bin/env python3
"""Update whatsapp (macOS) hashes.

WhatsApp publishes a Sparkle appcast for the macOS native client at the
``mac_native/updates/`` endpoint (the same source nixpkgs' whatsapp-for-mac
uses). The newest ``<enclosure>`` points at a versioned ``.zip`` download whose
URL embeds the version in a ``version=`` query parameter. That versioned URL is
deterministic and can be pinned, unlike the "latest" endpoint which serves
unstable content.

WhatsApp ships a universal binary; the same zip works for both Intel and Apple
Silicon, so we compute the hash once and write it under both Nix platforms.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from updater import fetch_text, load_hashes, save_hashes
from updater.hash import calculate_url_hash

HASHES_FILE = Path(__file__).parent / "hashes.json"
UPDATES = (
    "https://web.whatsapp.com/desktop/mac_native/updates/"
    "?branch=master&configuration=Release"
)


def latest_release() -> tuple[str, str]:
    """Return ``(version, zip_url)`` for the newest enclosure in the appcast."""
    # Updates feed is a first-party WhatsApp HTTPS resource, not attacker input.
    root = ET.fromstring(fetch_text(UPDATES))  # noqa: S314
    enclosures = root.findall(".//enclosure")
    if not enclosures:
        msg = "WhatsApp updates feed contained no <enclosure> entries"
        raise RuntimeError(msg)

    def version_of(enclosure: ET.Element) -> tuple[int, ...]:
        match = re.search(r"version=([0-9.]+)", enclosure.attrib.get("url", ""))
        return tuple(int(x) for x in match.group(1).split(".")) if match else ()

    newest = max(enclosures, key=version_of)
    url = newest.attrib["url"]
    match = re.search(r"version=([0-9.]+)", url)
    if match is None:
        msg = f"could not extract version= from enclosure url: {url}"
        raise RuntimeError(msg)
    return match.group(1), url


def main() -> None:
    """Update ``hashes.json`` if a newer WhatsApp release is available."""
    data = load_hashes(HASHES_FILE)
    current = data["version"]

    version, url = latest_release()
    print(f"Current: {current}, Latest: {version}")
    if current == version:
        print("Already up to date")
        return

    print(f"Hashing {url} ...")
    sri = calculate_url_hash(url, name="WhatsApp.zip")

    new = {
        "version": version,
        "url": url,
        "hashes": {
            "x86_64-darwin": sri,
            "aarch64-darwin": sri,
        },
    }
    save_hashes(HASHES_FILE, new)
    print(f"Updated whatsapp {current} -> {version}")


if __name__ == "__main__":
    main()
