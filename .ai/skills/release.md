---
name: release
description: Package and publish each component
---

# Release process

## Versioning

One product version in lockstep across the three apps. Tag format: `vX.Y.Z` (no per-component prefix). The Blender addon, Photoshop plugin, and Godot plugin all carry this same number.

- Bump by the highest severity across components (a breaking change in any app makes the product MAJOR); unchanged apps re-stamp and ride along.
- Pre-1.0: `0.MINOR.PATCH`, `-beta` suffix on the beta channel.
- One source of truth (the tag / a root `VERSION`) stamps all three manifests at release.

Full rationale and the carry-along rule are in [`../conventions/layout.md`](../conventions/layout.md) "Versioning" and the locked decision in [`../../specs/decisions.md`](../../specs/decisions.md).

`packages/models/schemas/proscenio.schema.json` carries its own integer `format_version`, **independent** of the product version. Bumping the schema version is a separate decision documented in the PR.

## Blender addon

Target distribution: the official **Blender Extensions Platform** (`extensions.blender.org`).

```sh
cd apps/blender
blender --command extension build
```

Output: `proscenio-X.Y.Z.zip`. Submit via the Extensions Platform. Also attach to the GitHub Release.

## Godot plugin

Target distribution: the **Godot Asset Library** plus GitHub Releases.

Zip the `apps/godot/addons/proscenio/` folder and submit via <https://godotengine.org/asset-library>.

## Photoshop UXP plugin

Target distribution: GitHub Releases (no Adobe Exchange marketplace). The plugin is a webpack bundle, not the legacy single-file JSX script.

```sh
cd apps/photoshop
pnpm install
pnpm run build       # webpack → apps/photoshop/dist/
(cd dist && zip -r ../../../dist/proscenio-photoshop-${version}.ccx .)
```

Output: `proscenio-photoshop-X.Y.Z.ccx` (rename to `.zip` if `.ccx` packaging is out of scope at release time). Attach to the GitHub Release. Users load the bundle via Adobe UXP Developer Tool (UDT) or by dropping the `.ccx` into Photoshop.

## CI release flow

1. Push a single tag matching `v*` (e.g. `v0.9.0-beta`).
2. The `release.yml` workflow builds all three zips and attaches them to the GitHub Release for the tag.
3. Manual final step: submit the changed artifacts to the Blender Extensions Platform and the Godot Asset Library (skip a store whose bundle did not change).

> The workflow's tag trigger still matches the retired per-component prefixes (`blender-v*` / `godot-v*` / `photoshop-v*`); retargeting it to a single `v*` and building all three zips per tag is the implementation follow-up tracked in the release plan.

## Pre-release checklist

- [ ] Schema validates against all examples and fixtures.
- [ ] All targeted Blender LTS versions pass tests.
- [ ] All targeted Godot versions pass tests.
- [ ] CHANGELOG.md updated.
- [ ] If `format_version` changed, migration documented and migrator implemented.
