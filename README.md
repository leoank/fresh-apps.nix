# fresh-apps.nix

A curated set of Nix packages for desktop applications, refreshed daily by
GitHub Actions. Targets one thing nixpkgs is intentionally slow at: shipping
the *latest* upstream release within hours instead of days.

The current focus is chat (Signal, WhatsApp), but the architecture is
general — anything with a stable upstream channel and a sensible update
script belongs here.

## Available Packages

<!-- BEGIN GENERATED PACKAGE DOCS -->

### Chat

<details>
<summary><strong>signal-desktop</strong> - Private messenger for iOS, Android, macOS, Windows, and Linux</summary>

- **Source**: binary
- **License**: AGPL-3.0-only
- **Homepage**: https://signal.org/
- **Platforms**: aarch64-darwin
- **Usage**: `nix run github:leoank/fresh-apps.nix#signal-desktop -- --help`
- **Nix**: [packages/signal-desktop/package.nix](packages/signal-desktop/package.nix)

</details>
<details>
<summary><strong>whatsapp</strong> - WhatsApp Messenger desktop client (macOS native)</summary>

- **Source**: binary
- **License**: unfree
- **Homepage**: https://www.whatsapp.com/
- **Platforms**: aarch64-darwin
- **Usage**: `nix run github:leoank/fresh-apps.nix#whatsapp -- --help`
- **Nix**: [packages/whatsapp/package.nix](packages/whatsapp/package.nix)

</details>
<!-- END GENERATED PACKAGE DOCS -->

## Status

| Package | x86_64-linux | aarch64-darwin |
| ---------------- | :----------: | :------------: |
| `signal-desktop` | yes | yes |
| `whatsapp` | — | yes |

Intel macOS (`x86_64-darwin`) is no longer targeted: nixpkgs-unstable (26.11+)
has dropped support for that platform.

WhatsApp on Linux is intentionally not packaged. Meta does not ship a Linux
client; any "WhatsApp for Linux" available elsewhere is a third-party Electron
wrapper, not WhatsApp.

## Usage

```nix
{
  inputs.fresh-apps.url = "github:leoank/fresh-apps.nix";
}
```

Either consume the packages directly:

```nix
environment.systemPackages = [
  inputs.fresh-apps.packages.${pkgs.system}.signal-desktop
];
```

…or apply the overlay and reach them as `pkgs.freshApps.*`:

```nix
nixpkgs.overlays = [ inputs.fresh-apps.overlays.default ];
# then
environment.systemPackages = [ pkgs.freshApps.signal-desktop ];
```

## How updates work

Every package owns its version under `packages/<name>/hashes.json`. A
package-specific `update.py` fetches the upstream version + hashes and
rewrites that file. The daily GitHub Actions workflow (`update.yml` → the
reusable `update-flake.yml`) discovers all packages with a `version`
attribute, fans out one job per package, runs the updater, and opens an
auto-mergeable PR if anything changed.

- **Signal macOS** — `latest-mac.yml` (electron-updater) → version; the
  universal `.dmg` is downloaded and hashed (its manifest SHA512 describes the
  pre-notarization file and does not match the stapled dmg that is served).
- **Signal Linux** — Debian apt `Packages` file → matching `.deb` for the macOS
  version, SHA256 already present. If the Linux build lags the macOS release,
  the updater defers until both match.
- **WhatsApp macOS** — Sparkle appcast at `mac_native/updates/` → newest
  enclosure's versioned `.zip` URL (the same scheme nixpkgs uses). The pinned
  `?version=` URL is deterministic; the zip is hashed once and reused for both
  Intel and Apple Silicon (WhatsApp ships a universal binary).

## Manual update

```bash
nix develop                                       # devshell with nix-update, pyyaml, gh
python packages/signal-desktop/update.py
python packages/whatsapp/update.py
nix build .#signal-desktop                        # on linux or darwin
nix build .#whatsapp                              # darwin only
```

Regenerate the README package section:

```bash
./scripts/generate-package-docs.py
```

## Repository checks

- `nix flake check` — runs the formatter check + `meta-maintainers`
  evaluation. Every package's `meta.maintainers` is forced so a missing or
  typoed maintainer reference fails at eval time, not later in CI.
- `nix fmt` — treefmt (nixfmt, deadnix, shfmt, shellcheck, mdformat, yamlfmt,
  taplo, ruff, mypy).
- `.github/workflows/check-maintainers.yml` — fails any PR introducing a new
  package without a maintainer.
- `.github/workflows/check-readme.yml` — fails any PR whose package metadata
  doesn't match the generated README block.
- `.github/workflows/flake-check.yml` — runs `nix flake check` on every PR
  across `ubuntu-latest` and `macos-latest`, so the format check, the
  `meta-maintainers` eval, and the actual package builds (Signal on Linux,
  Signal + WhatsApp on darwin) are all exercised before merge.

## Caveats

- Sources are unfree binary blobs. Set `nixpkgs.config.allowUnfree = true` (the
  flake already does this for its own outputs).
- macOS builds are `.app` bundles installed into `$out/Applications/`. Use
  [`mac-app-util`](https://github.com/hraban/mac-app-util) in your
  `nix-darwin` config to get them registered with Spotlight and Dock.
- These store paths are large (Signal ~200 MB, WhatsApp ~250 MB). Keeping many
  generations adds up — see your GC policy.

## Layout

```
flake.nix                  blueprint-discovered packages + overlays.default
devshell.nix               dev shell (nix-update, pyyaml, gh, treefmt)
pyproject.toml             ruff + mypy config for update scripts
lib/default.nix            custom maintainers (exposed as flake.lib.maintainers)
checks/
  meta-maintainers.nix     force-evaluates meta.maintainers for every package
packages/
  signal-desktop/          .deb (linux) and .dmg (darwin)
  whatsapp/                .zip only, universal (darwin)
  formatter/               treefmt config (passthru.hideFromDocs)
scripts/
  updater/                 vendored http / hash / json helpers
  generate-package-docs.*  regenerate README block
  check.sh                 mypy entry point
.github/
  ci/                      discovery + update + create_pr + check_maintainers
  workflows/               update + update-flake + auto-merge + check-* + ...
```

## Credits

Repository architecture, updater layout, and CI scripts are adapted from
[numtide/llm-agents.nix](https://github.com/numtide/llm-agents.nix) (MIT).
