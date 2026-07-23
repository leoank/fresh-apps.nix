#!/usr/bin/env python3
"""Generate markdown documentation for all packages and update README.md."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BEGIN_MARKER = "<!-- BEGIN GENERATED PACKAGE DOCS -->"
END_MARKER = "<!-- END GENERATED PACKAGE DOCS -->"

REPO = "leoank/fresh-apps.nix"  # update once the repo is published


def get_all_packages_metadata() -> dict[str, dict[str, Any]]:
    """Evaluate the docs Nix expression and return its result as a dict."""
    nix_file = Path(__file__).parent / "generate-package-docs.nix"
    try:
        result = subprocess.run(
            ["nix", "eval", "--json", "--impure", "--file", str(nix_file)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running nix eval: {e}", file=sys.stderr)
        if e.stderr:
            print(f"stderr: {e.stderr}", file=sys.stderr)
        raise

    data: dict[str, dict[str, Any]] = json.loads(result.stdout)
    return {k: v for k, v in data.items() if v is not None}


def generate_package_doc(package: str, metadata: dict[str, Any]) -> str:
    """Render one package as a ``<details>`` block."""
    lines: list[str] = []
    description = metadata.get("description", "No description available")
    platforms = ", ".join(metadata.get("platforms", []) or [])

    lines.append("<details>")
    lines.append(f"<summary><strong>{package}</strong> - {description}</summary>")
    lines.append("")
    lines.append(f"- **Source**: {metadata.get('sourceType', 'unknown')}")
    lines.append(f"- **License**: {metadata.get('license', 'Check package')}")
    if metadata.get("homepage"):
        lines.append(f"- **Homepage**: {metadata['homepage']}")
    if platforms:
        lines.append(f"- **Platforms**: {platforms}")
    lines.append(f"- **Usage**: `nix run github:{REPO}#{package} -- --help`")
    lines.append(
        f"- **Nix**: [packages/{package}/package.nix](packages/{package}/package.nix)"
    )
    readme_path = Path(f"packages/{package}/README.md")
    if readme_path.exists():
        lines.append(
            f"- **Documentation**: See [packages/{package}/README.md]"
            f"(packages/{package}/README.md) for detailed usage"
        )
    lines.append("")
    lines.append("</details>")
    return "\n".join(lines)


CATEGORY_ORDER = [
    "Chat",
    "Uncategorized",
]


def generate_all_docs() -> str:
    """Generate documentation for all packages, grouped by category."""
    all_metadata = get_all_packages_metadata()

    by_category: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for package in sorted(all_metadata.keys()):
        metadata = all_metadata[package]
        category = metadata.get("category", "Uncategorized")
        by_category.setdefault(category, []).append((package, metadata))

    docs: list[str] = []
    seen: set[str] = set()
    for category in CATEGORY_ORDER:
        if category in by_category:
            seen.add(category)
            docs.append(f"### {category}\n")
            for package, metadata in by_category[category]:
                docs.append(generate_package_doc(package, metadata))
            docs.append("")
    for category in sorted(by_category):
        if category not in seen:
            docs.append(f"### {category}\n")
            for package, metadata in by_category[category]:
                docs.append(generate_package_doc(package, metadata))
            docs.append("")

    return "\n".join(docs).rstrip()


def update_readme(readme_path: Path) -> bool:
    """Splice generated docs between the markers; return True if modified."""
    content = readme_path.read_text()
    begin_idx = content.find(BEGIN_MARKER)
    end_idx = content.find(END_MARKER)
    if begin_idx == -1 or end_idx == -1:
        print(f"Error: missing markers in {readme_path}", file=sys.stderr)
        sys.exit(1)
    if end_idx < begin_idx:
        print("Error: END marker before BEGIN marker", file=sys.stderr)
        sys.exit(1)

    generated_docs = generate_all_docs()
    new_content = (
        content[: begin_idx + len(BEGIN_MARKER)]
        + "\n\n"
        + generated_docs
        + "\n"
        + content[end_idx:]
    )
    if new_content == content:
        return False
    readme_path.write_text(new_content)
    return True


def main() -> None:
    """Update README with current package metadata."""
    script_dir = Path(__file__).parent
    readme_path = script_dir.parent / "README.md"
    if not readme_path.exists():
        print(f"Error: README.md not found at {readme_path}", file=sys.stderr)
        sys.exit(1)
    if update_readme(readme_path):
        print(f"Updated {readme_path}")
    else:
        print(f"No changes to {readme_path}")


if __name__ == "__main__":
    main()
