#!/usr/bin/env python3
"""Update whatsapp (macOS) hashes.

WhatsApp publishes a Sparkle appcast for the macOS native client. We pull the
latest entry from the appcast, follow its enclosure URL, and hash the dmg per
architecture.

WhatsApp ships a universal binary; the same dmg works for both Intel and Apple
Silicon, so we compute the hash once and write it under both Nix platforms.

If WhatsApp ever splits the dmg per arch, the per-architecture URL pattern can
be detected here and hashes diverged.
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
APPCAST = "https://www.whatsapp.com/desktop/mac_native/sparkle/appcast.xml"
NS = {"sparkle": "http://www.andymatuschak.org/xml-namespaces/sparkle"}


def latest_release() -> tuple[str, str]:
    """Return ``(version, dmg_url)`` for the newest enclosure in the appcast."""
    # Appcast is a first-party WhatsApp HTTPS resource, not attacker-controlled.
    root = ET.fromstring(fetch_text(APPCAST))  # noqa: S314
    items = root.findall(".//item")
    if not items:
        msg = "Sparkle appcast contained no <item> entries"
        raise RuntimeError(msg)

    def parse_version(item: ET.Element) -> tuple[int, ...]:
        v = item.findtext("sparkle:shortVersionString", default="0", namespaces=NS)
        return tuple(int(x) for x in re.findall(r"\d+", v))

    newest = max(items, key=parse_version)
    version = newest.findtext("sparkle:shortVersionString", namespaces=NS)
    enclosure = newest.find("enclosure")
    if version is None or enclosure is None:
        msg = "newest appcast item missing version or enclosure"
        raise RuntimeError(msg)
    url = enclosure.attrib["url"]
    return version, url


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
    sri = calculate_url_hash(url)

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
