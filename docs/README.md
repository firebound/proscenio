# Proscenio docs

This is a top-level documentation index that pairs hand-authored workflow guides with an interactive JSON Schema reference so a reader can move from "how the pipeline works" to "what every field on a `.proscenio` document means" without leaving this directory.

## Workflow guides

- [Basic walkthrough](00-guides/00-basic/index.md): the end-to-end loop, one page per tool.
- [Advanced workflow](00-guides/01-advanced/index.md): deeper dives into the features of each tool, and how they fit together.

## Project documentation

- [Project architecture](01-project/01-architecture.md): the design goals, the dataflow, and how the tools and formats fit together.
- [Features](01-project/02-features.md): the current feature set, the rationale for each, and how they fit together.
- [Pipeline comparison](01-project/03-comparison.md): Proscenio against other 2D authoring stacks (Spine, DragonBones, COA Tools).
- [Deferred / out-of-scope](01-project/04-deferred.md): rationale for features explicitly not in the current iteration.

## Schema reference

Interactive reference for both wire formats, grouped by feature and rendered live from the JSON Schemas by the docs-site viewer, so it always reflects the models:

- [Schema reference](content/README.md): entry point for both formats.
- [Proscenio character](content/proscenio/document.mdx): the `.proscenio` document: skeleton, sprites, slots, animation.
- [PSD manifest](content/psd-manifest/manifest.mdx): the manifest the Blender importer reads from the Photoshop export.

The JSON Schemas are dumped from the pydantic source of truth at [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/). Regenerate the schemas and bindings after editing the models:

```pwsh
uv run python -m proscenio_codegen all
```

That emits the JSON Schema artifacts, the Godot Resource bindings, and the TypeScript bindings (or run `schemas` / `godot` / `ts` individually). The schema reference itself needs no regeneration step: the viewer reads the dumped schemas directly.

## Where the source-of-truth lives

| Surface                                        | File / package                                                                          |
| ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| Wire-format models (.proscenio + PSD manifest) | [`packages/models/src/proscenio_models/`](../packages/models/src/proscenio_models/)     |
| Codegen emitters (schemas / Godot / TS)        | [`packages/codegen/src/proscenio_codegen/`](../packages/codegen/src/proscenio_codegen/) |
| Blender addon                                  | [`apps/blender/`](../apps/blender/)                                                     |
| Photoshop UXP plugin                           | [`apps/photoshop/`](../apps/photoshop/)                                                 |
| Godot importer plugin                          | [`apps/godot/`](../apps/godot/)                                                         |

## Docs site

The docs site is a Docusaurus app in [`apps/docs/`](../apps/docs/) that serves this `docs/` folder as its content root.

Run it with `pnpm --dir apps/docs start` for dev, or `pnpm --dir apps/docs build` for a production bundle.

It deploys to GitHub Pages at [space-wizard-studios.github.io/firebound-proscenio](https://space-wizard-studios.github.io/firebound-proscenio/) via [`docs-deploy.yml`](../.github/workflows/docs-deploy.yml), on every push to `main` that touches `docs/`, `apps/docs/`, or the dumped schemas.
