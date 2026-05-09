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

`schemas/proscenio.schema.json` carries its own integer `format_version`, **independent** of component versions. Bumping the schema version is a separate decision documented in the PR.

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

## Photoshop exporter

Just the `.jsx` file. Attach to the GitHub Release. No marketplace.

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
