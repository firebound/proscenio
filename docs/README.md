# Proscenio docs

Top-level documentation index. Pairs hand-authored workflow guides with an interactive JSON Schema reference so a reader can move from "how the pipeline works" to "what every field on a .proscenio document means" without leaving this directory.

## Workflow guides (hand-authored)

- [End-to-end walkthrough](WALKTHROUGH.md) - the full Photoshop -> Blender -> Godot loop in one linear pass.
- [Blender workflow](BLENDER-WORKFLOW.md) - addon panels + per-feature recipes the artist follows while authoring.
- [Photoshop workflow](PHOTOSHOP-WORKFLOW.md) - UXP exporter / tag system / round-trip authoring flow.
- [Godot workflow](GODOT-WORKFLOW.md) - importer behaviour at editor time + how the generated `.scn` plugs into a Firebound project.
- [Pipeline comparison](COMPARISON.md) - Proscenio against other 2D authoring stacks (Spine, DragonBones, COA Tools).
- [Deferred / out-of-scope](DEFERRED.md) - rationale for features explicitly not in the current iteration.

## Schema reference

Interactive reference for both wire formats, grouped by feature and rendered live from the JSON Schemas by the docs-site viewer, so it always reflects the models:

- [Schema reference index](content/README.md) - entry point for both formats.
- [Proscenio character](content/proscenio/document.mdx) - the `.proscenio` document: skeleton, sprites, slots, animation.
- [PSD manifest](content/psd-manifest/manifest.mdx) - the manifest the Blender importer reads from the Photoshop export.

The JSON Schemas are dumped from the pydantic source of truth at [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/). Regenerate the schemas and bindings after editing the models:

```pwsh
uv run python -m proscenio_codegen all
```

That emits the JSON Schema artifacts, the Godot Resource bindings, and the TypeScript bindings (or run `schemas` / `godot` / `ts` individually). The schema reference itself needs no regeneration step - the viewer reads the dumped schemas directly.

## Where the source-of-truth lives

| Surface | File / package |
| --- | --- |
| Wire-format models (.proscenio + PSD manifest) | [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/) |
| Codegen emitters (schemas / Godot / TS) | [`packages/codegen/src/proscenio_codegen/`](../packages/codegen/src/proscenio_codegen/) |
| Blender addon | [`apps/blender/`](../apps/blender/) |
| Photoshop UXP plugin | [`apps/photoshop/`](../apps/photoshop/) |
| Godot importer plugin | [`apps/godot/`](../apps/godot/) |

## Docs site

The docs site is a Docusaurus app in [`apps/docs/`](../apps/docs/). It serves this `docs/` folder as its content root: the hand-authored guides plus the schema reference (the latter rendered by an interactive JSON Schema viewer that reads the dumped schemas directly). Run it with `pnpm --dir apps/docs start` for dev or `pnpm --dir apps/docs build` for a production bundle. No deploy target is wired yet.
