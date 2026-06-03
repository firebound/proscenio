# Proscenio docs

Top-level documentation index. Pairs hand-authored workflow guides with the auto-generated JSON Schema reference so a reader can move from "how the pipeline works" to "what every field on a .proscenio document means" without leaving this directory.

## Workflow guides (hand-authored)

- [End-to-end walkthrough](WALKTHROUGH.md) - the full Photoshop -> Blender -> Godot loop in one linear pass.
- [Blender workflow](BLENDER-WORKFLOW.md) - addon panels + per-feature recipes the artist follows while authoring.
- [Photoshop workflow](PHOTOSHOP-WORKFLOW.md) - UXP exporter / tag system / round-trip authoring flow.
- [Godot workflow](GODOT-WORKFLOW.md) - importer behaviour at editor time + how the generated `.scn` plugs into a Firebound project.
- [Pipeline comparison](COMPARISON.md) - Proscenio against other 2D authoring stacks (Spine, DragonBones, COA Tools).
- [Deferred / out-of-scope](DEFERRED.md) - rationale for features explicitly not in the current iteration.

## API reference (codegen)

- [Schemas index](content/api/schemas/README.md) - top-level entry to the JSON Schema reference for both supported wire formats.
- [proscenio.schema.json](content/api/schemas/proscenio.md) - `.proscenio` v1 document shape (the Godot importer's input).
- [psd_manifest.schema.json](content/api/schemas/psd_manifest.md) - PSD manifest v2 shape (the Blender importer's input).

The schema markdown is generated from the pydantic source of truth at [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/). Regenerate after editing the models:

```pwsh
uv run python -m proscenio_codegen docs
```

The same workspace command emits the JSON Schema artifacts (`uv run python -m proscenio_codegen schemas`) and the Godot Resource bindings (`uv run python -m proscenio_codegen godot`) / TypeScript bindings (`uv run python -m proscenio_codegen ts`). Run `uv run python -m proscenio_codegen all` to refresh every artifact at once.

## Where the source-of-truth lives

| Surface | File / package |
| --- | --- |
| Wire-format models (.proscenio + PSD manifest) | [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/) |
| Codegen emitters (docs / schemas / Godot / TS) | [`packages/codegen/src/proscenio_codegen/`](../packages/codegen/src/proscenio_codegen/) |
| Blender addon | [`apps/blender/`](../apps/blender/) |
| Photoshop UXP plugin | [`apps/photoshop/`](../apps/photoshop/) |
| Godot importer plugin | [`apps/godot/`](../apps/godot/) |

## Docs site

The auto-generated markdown is ready for a static site generator (Docusaurus / VitePress / mdBook). No deploy target is wired today; the rendered HTML lives downstream of whichever site framework picks up `docs/content/`. The relative-link style matches Docusaurus's default routing so the existing markdown drops into a fresh site without rewriting cross-references.
