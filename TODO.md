# TODO

Concrete steps required before `fresh-apps.nix` is functional. Items are
roughly in the order they should be done.

## 1. Identity and metadata

- [ ] Replace the stub maintainer in `lib/default.nix`.
  - Set `github` to your real GitHub handle.
  - Set `githubId` to the integer from
    `curl -s https://api.github.com/users/<you> | jq -r .id`.
  - Set `name` to a display name (or remove the field).
- [ ] Update the `REPO` constant in `scripts/generate-package-docs.py` from
  `<owner>/fresh-apps.nix` to the real `owner/repo` slug.
- [ ] Update README links that reference `github:<you>/fresh-apps.nix` once you
  know the final repo URL.

## 2. Lock the flake on a machine with Nix

These cannot be done on the current sandbox; they require a working `nix`.

- [ ] `cd fresh-apps.nix && nix flake lock` to produce `flake.lock`.
- [ ] `nix flake check` — expect failures the first time:
  - The `meta-maintainers` check evaluates fine immediately.
  - The `formatter` check (`packages/formatter/default.nix → passthru.tests.check`)
    will likely demand a first-pass `nix fmt` to normalize everything.
- [ ] `nix fmt` and commit the formatting diff.

## 3. Populate real version + hashes

The `hashes.json` files ship with dummy `0.0.0` versions and all-zero SRI
hashes. Run each updater on its target platform to populate real values:

- [ ] On Linux (or any platform with `nix store prefetch-file`):
  ```bash
  nix develop -c python packages/signal-desktop/update.py
  ```
  Verify both `x86_64-linux` and the two darwin hashes get written.
  If `latest-mac.yml` is reachable from CI on Linux this also works on macOS.
- [ ] On macOS:
  ```bash
  nix develop -c python packages/whatsapp/update.py
  ```
  Confirm the WhatsApp **Sparkle appcast URL**
  (`https://www.whatsapp.com/desktop/mac_native/sparkle/appcast.xml`)
  actually responds — Meta has changed this path before. If 404, find the
  current appcast URL (DevTools network tab while WhatsApp Mac auto-updates)
  and substitute it in `packages/whatsapp/update.py`.

## 4. Verify each package builds

- [ ] `nix build .#signal-desktop` on `x86_64-linux`.
- [ ] `nix build .#signal-desktop` on `aarch64-darwin` (and `x86_64-darwin` if
  you have one).
- [ ] `nix build .#whatsapp` on `aarch64-darwin`.

If the Signal Linux build fails on a missing shared library, add it to
`buildInputs` in `packages/signal-desktop/package.nix` and re-run.

## 5. Generate the README block

- [ ] Run `./scripts/generate-package-docs.py` and commit the filled-in
  section between the `<!-- BEGIN GENERATED PACKAGE DOCS -->` markers.

## 6. Decide on the bot identity

Pick one of the two paths and apply it.

### Option A — GitHub App (matches llm-agents.nix exactly)

- [ ] Create a GitHub App with `contents:write` + `pull-requests:write`
  permissions; install it on the repo.
- [ ] Add repo secrets `CLIENT_ID` (the App's client ID) and
  `APP_PRIVATE_KEY` (the App's private key).
- [ ] No workflow edits needed.

### Option B — Plain `GITHUB_TOKEN` (simpler, no App)

- [ ] In `.github/workflows/update.yml`: drop the `secrets:` block.
- [ ] In `.github/workflows/update-flake.yml`: drop the
  `actions/create-github-app-token` steps and replace every
  `steps.app-token.outputs.token` reference with `secrets.GITHUB_TOKEN`.
- [ ] Disable auto-merge by setting `auto-merge: false` in
  `update.yml` (workflows triggered by `GITHUB_TOKEN`-authored commits
  don't run subsequent workflows; auto-merge would never resolve).
- [ ] Note in the README that contributors will need to push a manual
  no-op commit to trigger CI on bot PRs.

## 7. Tighten the `auto-merge.yml` pin

- [ ] Pin `Mic92/auto-merge@main` to a commit SHA once you've reviewed the
  action's behavior. `@main` is a supply-chain risk.

## 8. CI verification round-trip

- [ ] Push a branch, open a PR, confirm:
  - `check-maintainers` runs and passes (no new packages to flag).
  - `check-readme` passes (your generated block is up to date).
  - The format-check derivation under `nix flake check` is green.
- [ ] Manually fire `workflow_dispatch` on `update.yml` and confirm:
  - `discover` finds `signal-desktop` and `whatsapp`.
  - `update` runs without error on a no-op day ("Already up to date").
  - On an actual update day, a PR appears with the right title format.

## 9. Optional but recommended

- [ ] Set up a binary cache (Cachix or Numtide's cache) so consumers of
  this flake don't re-extract `.dmg`s. Without it, every consumer pays
  the full unpack cost. Update `flake.nix → nixConfig.extra-substituters`
  to point at your cache, mirroring llm-agents.nix.
- [x] Add a `nix flake check` workflow that runs on PRs
  (`.github/workflows/flake-check.yml`, matrix `ubuntu-latest` +
  `macos-latest`).
- [x] Add a per-platform smoke build workflow that actually `nix build`s each
  package on its target OS on PR. Covered by `flake-check.yml`: `nix flake check` builds every buildable derivation for the runner's system, so
  `ubuntu-latest` builds Signal (Linux) and `macos-latest` builds Signal +
  WhatsApp (darwin).
- [x] Require the flake-check contexts as branch protection on `main` so
  auto-merge gates on them: `flake-check (ubuntu-latest)` +
  `flake-check (macos-latest)` required, `strict` off (bot PRs merge
  independently), `enforce_admins` off (admins can still push directly).
- [ ] Add an `aarch64-linux` build of `signal-desktop`. Signal publishes
  ARM `.deb`s; the apt Packages file at
  `updates.signal.org/desktop/apt/dists/xenial/main/binary-arm64/Packages`
  is the source. The current `signal-desktop` updater only reads the
  `binary-amd64` file.

## 10. Things to revisit after first deployment

- [ ] If WhatsApp ever splits its dmg per architecture, replace the
  duplicate hash write in `packages/whatsapp/update.py` with a real
  per-arch lookup.
- [ ] If Signal Mac ever publishes ahead of Mac Linux for more than a day,
  reconsider the "defer until both match" policy in
  `packages/signal-desktop/update.py` — you may want to release them
  independently with two `hashes.json` files.
- [ ] Consider whether `mac-app-util` integration belongs in this flake
  (via an exposed `darwinModules.default`) or stays in the consumer's
  config.
