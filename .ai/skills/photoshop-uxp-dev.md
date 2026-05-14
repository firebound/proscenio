---
name: photoshop-uxp-dev
description: UXP plugin for Photoshop - layer slicing and manifest JSON via TypeScript + React
---

# Photoshop UXP plugin

## Stack

- **UXP** (Unified Extensibility Platform) - Adobe's modern plugin runtime.
- **TypeScript** strict for all source.
- **React** for the panel UI; Spectrum web components for native theming.
- **webpack + Babel** to bundle into the UXP plugin format.
- **pnpm** as the package manager.
- **ajv** for runtime validation against the PSD manifest schema (Ajv2020 build).
- **vitest** for unit tests on the pure planner / validator.
- **Photoshop CC 2024 (PS 25+)** minimum - UXP `xmp` and modern panel APIs require it.

## Source layout

```text
src/
|-- domain/        pure logic + types (planner, layer, manifest, tag parser/writer)
|-- adapters/      PS DOM -> domain mappers
|-- io/            UXP filesystem, ajv, manifest IO, XMP, PNG writes
|-- controllers/   orchestrators (export-flow, import-flow, PanelController)
|-- hooks/         React state hooks (one per useXxx file)
|-- panels/        panel + section components
|-- types/         ambient type shims (uxp.d.ts, spectrum.d.ts)
|-- index.tsx      plugin entry
```

Layer direction: `panels` -> `hooks` / `controllers` -> `domain` + `io` -> `adapters`. `domain/` never imports UXP APIs.

## Output format

The plugin emits a manifest JSON conforming to `schemas/psd_manifest.schema.json` alongside per-layer PNGs. The manifest is the only contract with the Blender importer - any new field must land in the schema first, then in the writer and the consumer in the same PR.

Key fields on each entry: `kind` (`polygon` | `mesh` | `sprite_frame`), `name`, `path`, `position`, `size`, `z_order`, and optional `origin`, `blend_mode`, `subfolder`. Document-level optionals: `anchor` (set from PSD guides).

## Bracket-tag taxonomy

Layer / group names carry `[tag]` or `[tag:value]` tokens that drive the manifest shape (kind selection, blend mode, subfolder routing, ignore, origin, ...). The tag parser:

- walks the name once and lexes every recognised token.
- strips recognised tokens from the residual display name.
- leaves unknown tokens in place so artist typos and future tags stay visible; the Tags tab surfaces them as warnings.
- returns a `{ name, tags[] }` bag in lexical order.

The writer (`tag-writer`) reconstructs a name deterministically from the bag, so toggling tags via the UI round-trips cleanly.

## XMP storage

Tags live in two places for resilience:

1. **Inside the layer name** - artist-visible canonical form, round-trippable in any PSD.
2. **In the document's XMP metadata** under a `proscenio` namespace, keyed by the layer's sanitised path - survives renames.

XMP serialises the tag bag as compact JSON per property. Read-back falls back to parsing the layer name when the XMP entry is missing (fresh-from-Blender PSDs have no XMP yet). Keys are NCName-safe.

## File system in UXP

UXP sandboxes file system access. Use `require("uxp").storage`:

- `localFileSystem.getFolder()` to pick an output folder.
- `localFileSystem.getFileForOpening({ types: ["json"] })` to pick a manifest for import.
- `localFileSystem.createPersistentToken(entry)` + `localStorage` to survive plugin reloads.
- `entry.createFile(name, { overwrite: true })` to write PNG or JSON.

Required permission: `"localFileSystem": "request"` is enough as long as every write happens inside the user-picked folder. Do not request `"fullAccess"`.

## Dev loop

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm run test        # vitest run
pnpm run build       # webpack into dist/
pnpm run uxp:load    # load plugin into Photoshop via UDT
pnpm run uxp:watch   # rebuild + reload on src changes
pnpm run uxp:debug   # Chrome DevTools attached to the plugin
```

Adobe UXP Developer Tool (UDT) must be installed and connected. Point UDT at the built `dist/manifest.json`, not the source manifest - the source references files webpack only produces after the build runs.

## UXP gotchas

- `app.documents.add({ mode, fill })` rejects bare strings - pass `constants.NewDocumentMode.RGB` and `constants.DocumentFill.TRANSPARENT`.
- `Document.trim(trimType, top, bottom, left, right)` takes positional args, not an options bag.
- `file.write(string)` defaults to utf8. Passing `{ format: "utf8" }` errors - drop the option.
- Declaring `manifestVersion: 5` permissions the plugin does not actually use makes it Validate but fail Load. Declare only what is used.
- The `<script>` injection at the top of `plugin/index.html` (`globalThis.screen = {}`, `WebSocket.prototype.OPEN`) is required by the React + UXP combination - do not remove.

## Testing

Unit tests for the pure planner + validator + tag parser run via vitest. PS DOM operations stay manual. The smoke loop is: load the plugin in UDT, run the exporter against a hand-authored PSD, diff the output against the captured oracle baseline for that fixture.

## Reference

- Adobe UXP guide: <https://developer.adobe.com/photoshop/uxp/2022/guides/>
- UXP Photoshop API reference: <https://developer.adobe.com/photoshop/uxp/2022/ps_reference/>
- UXP storage (file system): <https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/>
