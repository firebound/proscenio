---
name: release
description: Package and publish each component
---

# Release process

## Versioning

SemVer per component. Tag format: `<component>-vX.Y.Z`.

- `apps/blender-v0.1.0`
- `apps/godot-v0.1.0`
- `apps/photoshop-v0.1.0`

`packages/models/schemas/proscenio.schema.json` carries its own integer `format_version`, **independent** of component versions. Bumping the schema version is a separate decision documented in the PR.

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
pnpm run build       # webpack -> apps/photoshop/dist/
(cd dist && zip -r ../../../dist/proscenio-photoshop-${version}.ccx .)
```

Output: `proscenio-photoshop-X.Y.Z.ccx` (rename to `.zip` if `.ccx` packaging is out of scope at release time). Attach to the GitHub Release. Users load the bundle via Adobe UXP Developer Tool (UDT) or by dropping the `.ccx` into Photoshop.

## CI release flow

1. Push a tag matching `<component>-v*`.
2. The `release.yml` workflow builds the right zip(s) for that component.
3. The workflow attaches artifacts to the GitHub Release for the tag.
4. Manual final step: submit to the Blender or Godot platform store.

## Pre-release checklist

- [ ] Schema validates against all examples and fixtures.
- [ ] All targeted Blender LTS versions pass tests.
- [ ] All targeted Godot versions pass tests.
- [ ] CHANGELOG.md updated.
- [ ] If `format_version` changed, migration documented and migrator implemented.
