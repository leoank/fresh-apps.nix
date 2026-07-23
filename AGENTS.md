# Repository Guidelines

## Project Structure & Module Organization

- Root: `flake.nix`, `flake.lock`, `devshell.nix`, `README.md`.
- Packages live under `packages/<tool>/` with `package.nix`, `default.nix`, optional `update.py`, and `hashes.json` when needed.
- Formatting config: `packages/formatter/treefmt.nix`.
- Utilities and docs: `scripts/`, `.github/`.
- Custom maintainers: `lib/default.nix`.
- Flake-check guards: `checks/`.

## Build, Test, and Development Commands

- Enter dev shell: `nix develop`.
- Build a package: `nix build .#<package>` (e.g., `nix build .#signal-desktop`).
- Run without installing: `nix run .#<package> -- --help` (CLI-friendly packages only).
- Repo checks: `nix flake check`.
- Format everything: `nix fmt`.
- Regenerate README package section: `./scripts/generate-package-docs.py`.

## Coding Style & Naming Conventions

- Indentation: 2 spaces; no tabs.
- Nix: small, composable derivations; prefer `stdenv.mkDerivation` / `stdenvNoCC.mkDerivation` as in existing packages.
- File layout per package: `package.nix` (definition), `default.nix` (wrapper), `update.py` (custom updater), `hashes.json` (version + per-platform SRI hashes).
- Tools via treefmt: nixfmt, deadnix, shfmt, shellcheck, mdformat, yamlfmt, taplo, ruff. Always run `nix fmt` before committing.

### Updating Packages

These packages bundle binary `.dmg` / `.deb` payloads, so they cannot use `nix-update` against an upstream Git source. Each package owns a `hashes.json` and an `update.py` that fetches the upstream channel and rewrites both. To run manually:

```bash
python packages/<package>/update.py
nix build .#<package>
```

### Package Metadata Requirements

Every package MUST have proper metadata in `package.nix`:

```nix
meta = with lib; {
  description = "Clear, concise description";
  homepage = "https://project-homepage.com";
  changelog = "https://upstream/releases/tag/v${version}";
  license = licenses.mit; # or licenses.unfree
  sourceProvenance = with sourceTypes; [ binaryNativeCode ];
  maintainers = with maintainers; [ username ];
  mainProgram = "binary-name";
  platforms = platforms.darwin; # or platforms.linux, etc.
};
```

The `changelog` attribute is required — our updater uses it to generate release notes.

### Package Categories

Every package should declare a category in `passthru` for README organization:

```nix
passthru.category = "Chat";
```

Available categories (in display order): **Chat**, **Uncategorized**.

#### Custom Maintainers

For maintainers not yet in nixpkgs, define them in `lib/default.nix`. Then in `packages/<package>/default.nix`, pass `flake` to the package:

```nix
{ pkgs, flake }: pkgs.callPackage ./package.nix { inherit flake; }
```

And in `packages/<package>/package.nix`, reference custom maintainers:

```nix
{ lib, flake, ... }:
stdenv.mkDerivation {
  # ...
  meta.maintainers = with flake.lib.maintainers; [ username ];
}
```

## Testing Guidelines

- Build locally on the right platform: Linux for `signal-desktop`, macOS for `whatsapp` and the darwin Signal build.
- Run flake checks: `nix flake check`.

## Commit & Pull Request Guidelines

- Commit style: `<package>: summary`.
  - Version bumps: `<package>: X -> Y`.
  - New packages: `<package>: init at X.Y.Z`.
- PRs: clear description, rationale, and testing notes; link issues.
- Before pushing: run `nix fmt` and `nix flake check`.

## Security & Configuration Tips

- All upstream payloads are unfree binaries — set `nixpkgs.config.allowUnfree = true` in consumer configs (this flake already does so for its own outputs).
- Pin sources with hashes; never allow network access at build time.
- macOS apps are large; consult the README about generation retention before depending on many at once.
