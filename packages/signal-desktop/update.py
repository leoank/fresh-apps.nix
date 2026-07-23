#!/usr/bin/env python3
"""Update signal-desktop hashes.

Signal Desktop ships from two channels:

* macOS  - electron-updater style ``latest-mac.yml`` under
           ``updates.signal.org/desktop/`` gives the version; we download the
           universal ``.dmg`` and hash it.
* Linux  - Debian apt repository at ``updates.signal.org/desktop/apt/``; we
           parse the Packages file to get the current x86_64 deb + sha256.

The macOS channel is authoritative for the version; we expect Linux to match
within a release window. If it doesn't, the update is deferred to the next
run so we never ship mismatched versions.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

import yaml
from updater import fetch_text, load_hashes, save_hashes
from updater.hash import calculate_url_hash, hex_to_sri

HASHES_FILE = Path(__file__).parent / "hashes.json"
BASE = "https://updates.signal.org/desktop"
MAC_YML = f"{BASE}/latest-mac.yml"
LINUX_PACKAGES = f"{BASE}/apt/dists/xenial/main/binary-amd64/Packages"


def fetch_mac() -> tuple[str, dict[str, str]]:
    """Return ``(version, {nix_platform: sri_hash})`` for the latest macOS release.

    Signal ships a single universal ``.dmg`` (plus per-arch ``.zip`` autoupdate
    payloads we don't consume); the same dmg serves both Intel and Apple
    Silicon, so its hash is written under both Nix platforms. The manifest's
    sha512 describes the pre-notarization file and does not match the stapled
    dmg actually served, so we download and hash the dmg rather than trust it.
    """
    doc = yaml.safe_load(fetch_text(MAC_YML))
    version: str = doc["version"]
    dmg_url = f"{BASE}/signal-desktop-mac-universal-{version}.dmg"
    sri = calculate_url_hash(dmg_url)
    return version, {"aarch64-darwin": sri, "x86_64-darwin": sri}


def parse_packages(text: str) -> list[dict[str, str]]:
    """Parse a Debian ``Packages`` file into a list of stanzas."""
    stanzas: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip():
            if current:
                stanzas.append(current)
                current = {}
            continue
        if raw[0].isspace():
            continue  # continuation line; we don't need multi-line fields
        key, _, value = raw.partition(":")
        current[key.strip()] = value.strip()
    if current:
        stanzas.append(current)
    return stanzas


def fetch_linux(want_version: str) -> str:
    """Find the deb for ``want_version`` in the apt Packages file and return its SRI hash."""
    stanzas = parse_packages(fetch_text(LINUX_PACKAGES))
    matches = [
        s
        for s in stanzas
        if s.get("Package") == "signal-desktop" and s.get("Version") == want_version
    ]
    if not matches:
        msg = (
            f"signal-desktop {want_version} not yet present in apt Packages; "
            "Linux build lags the macOS release. Try again later."
        )
        raise RuntimeError(msg)
    sha256 = matches[0]["SHA256"]
    return hex_to_sri(sha256)


def main() -> None:
    """Update ``hashes.json`` if a newer Signal release is available."""
    data = load_hashes(HASHES_FILE)
    current = data["version"]

    version, mac_hashes = fetch_mac()
    print(f"Current: {current}, Latest (mac): {version}")
    if current == version:
        print("Already up to date")
        return

    linux_hash = fetch_linux(version)

    new = {
        "version": version,
        "hashes": {
            "x86_64-linux": linux_hash,
            **mac_hashes,
        },
    }
    save_hashes(HASHES_FILE, new)
    print(f"Updated signal-desktop {current} -> {version}")


if __name__ == "__main__":
    main()
