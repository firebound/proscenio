---
name: photoshop-uxp-dev
description: UXP plugin for Photoshop - layer slicing and manifest JSON via TypeScript + React
---

# Photoshop UXP plugin

## Stack

- **UXP** (Unified Extensibility Platform). Adobe's modern plugin runtime.
- **TypeScript** for all source. `tsconfig.json` ships in `apps/photoshop/` with `strict: true`.
- **React** for the panel UI; Spectrum web components for native theming.
- **webpack + babel** bundle into the UXP plugin format (per SPEC 010 D15).
- **pnpm** as the package manager (per SPEC 010 D14).
- **ajv** for runtime schema validation against `schemas/psd_manifest.schema.json` (Ajv2020 build; the schema declares draft 2020-12).
- **vitest** for unit tests covering the pure planner / validator.
- **Photoshop CC 2024 (PS 25+)** minimum requirement. UXP `xmp` module support and modern panel APIs require this floor.

## Folder layout

```text
apps/photoshop/
|-- package.json         # pnpm; webpack + babel + react + TypeScript + ajv + vitest
|-- tsconfig.json        # strict TypeScript
|-- webpack.config.js    # build config; @babel/preset-typescript
|-- plugin/              # UXP package source (copied by webpack into dist/)
|   |-- manifest.json    # plugin manifest (host, entrypoints, permissions)
|   |-- index.html       # panel root
|   `-- icons/
|-- src/
|   |-- domain/          # pure logic + types (planner, layer, manifest)
|   |-- adapters/        # PS DOM -> domain mappers
|   |-- io/              # UXP filesystem + ajv + manifest IO
|   |-- controllers/     # orchestrators (export-flow, import-flow) + PanelController
|   |-- hooks/           # React state-management hooks
|   |-- panels/          # panel + section components
|   |-- types/           # ambient type shims (uxp.d.ts, spectrum.d.ts)
|   |-- index.tsx        # plugin entry
|   `-- styles.css
`-- uxp-plugin-tests/    # vitest unit tests; excluded from tsconfig include
```

## Output format

The plugin emits a manifest JSON conforming to [`schemas/psd_manifest.schema.json`](../../schemas/psd_manifest.schema.json) v2, alongside per-layer PNGs under `images/`. v1 is still accepted by the Blender side for legacy fixtures - the parser at [`apps/blender/core/psd_manifest.py`](../../apps/blender/core/psd_manifest.py) reads both, rejecting v2-only fields on a v1 document.

```json
{
  "format_version": 2,
  "doc": "doll.psd",
  "size": [1024, 1024],
  "pixels_per_unit": 100,
  "anchor": [512, 768],
  "layers": [
    {
      "kind": "polygon",
      "name": "torso",
      "path": "images/torso.png",
      "position": [120, 340],
      "size": [180, 240],
      "z_order": 0,
      "origin": [200, 460],
      "blend_mode": "multiply",
      "subfolder": "body/torso"
    }
  ]
}
```

Schema v2 deltas (SPEC 011):

| Field | Where | Source tag(s) |
| --- | --- | --- |
| `anchor` | root | document-level horizontal + vertical PSD guides |
| `kind: "mesh"` | per layer | `[mesh]` tag |
| `origin` | per layer | `[origin]` marker inside a `[spritesheet]` / `[merge]` group, or explicit `[origin:X,Y]` |
| `blend_mode` | per layer | `[blend:multiply]` / `[blend:screen]` / `[blend:additive]` |
| `subfolder` | per layer | accumulated path from enclosing `[folder:NAME]` groups |

This JSON is consumed by [`apps/blender/importers/photoshop/__init__.py`](../../apps/blender/importers/photoshop/__init__.py) (orchestrator) + `planes.py` (stamper).

## Tag parser internals

The bracket-tag taxonomy is parsed in TypeScript at [`apps/photoshop/src/domain/tag-parser.ts`](../../apps/photoshop/src/domain/tag-parser.ts). The parser walks the PSD layer / group name once, lexing every `[tag]` or `[tag:value]` token; the residual string after every recognised tag is stripped becomes the display name surfaced to the manifest.

- **Token grammar**: `[` `IDENT` (`:` `VALUE`)? `]`. `IDENT` is alphanumeric + underscore; `VALUE` is any non-`]` chars (allows spaces / commas / floats).
- **Unknown tags pass through**: an unrecognised `[foo]` stays in the display name so the artist's typo or future tag is still visible. The Tags tab in the panel flags unknown tags with a warning chip.
- **Tag bag**: parser returns `{ name: string, tags: Tag[] }`. Downstream consumers read `tags.find(t => t.kind === "blend")` etc.; ordering inside the bag matches lexical order in the source string.
- **Rewrite path**: the Tags tab uses `writeLayerName(name, tags)` from `apps/photoshop/src/domain/tag-writer.ts` to deterministically reconstruct a layer name from the tag bag - keeps the round-trip stable when toggling tags via the UI.

## XMP storage

Tags are stored in **two places** for resilience:

1. **Inside the layer name** (`arm.R [folder:body] [origin:10,20]`) - the artist-visible canonical form. Round-trippable in any PSD without plugin support.
2. **In the document's XMP metadata** under the `proscenio:` namespace - keyed by the layer's sanitised path. Used by the planner to survive layer renames without losing the tag bag.

The namespace URI is `https://proscenio.dev/spec-011/v1` (prefix `proscenio`), registered via UXP's `xmp` module at plugin load. Both live as exported constants in `apps/photoshop/src/io/xmp.ts` (`PROSCENIO_XMP_NAMESPACE_URI`, `PROSCENIO_XMP_PREFIX`). Property names are **NCName-safe**: the layer's full sanitised path (with `/` and other illegal NCName chars replaced by `_`) is used so each layer has a stable XMP key even when its display name changes.

The XMP write helpers live at `apps/photoshop/src/io/xmp.ts`. They serialise the tag bag to a compact JSON string per property; reading back is a `JSON.parse` of the property value, falling back to a parse of the layer name when the XMP entry is missing (a fresh-from-Blender PSD has no XMP yet).

## Conventions (legacy, pre-SPEC 011)

- Layer groups become folders in the output structure (names join with `__`) when no `[folder:NAME]` tag is present.
- Hidden layers are skipped (toggleable).
- Layer name prefix `_` excludes the layer (toggleable). **Retired in v2**: use `[ignore]`. The plugin reads both for one cycle, then the shortcut drops.
- Sprite-frame group detection: `<name>_<index>` flat-naming fallback. **Retired in v2**: use `[spritesheet]` group tags. The fallback stays for a release to ease migration.

## File system in UXP

UXP sandboxes file system access. Use the `require("uxp").storage` API:

- `localFileSystem.getFolder()` opens the user-picked output folder.
- `localFileSystem.getFileForOpening({ types: ["json"] })` opens a single file (used for the manifest import path).
- `localFileSystem.createPersistentToken(entry)` + `localStorage` lets the folder survive plugin reloads.
- `entry.createFile(name, { overwrite: true })` writes a PNG or the manifest JSON.

Required permission: `"localFileSystem": "request"` in `plugin/manifest.json` is sufficient as long as every write happens inside a folder the user picked. `"fullAccess"` is not needed for this plugin.

## Dev loop

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit
pnpm run test        # vitest run
pnpm run build       # webpack into dist/
pnpm run uxp:load    # load plugin into Photoshop via UDT
pnpm run uxp:watch   # rebuild + reload on src changes
pnpm run uxp:debug   # open Chrome DevTools attached to the plugin
```

Adobe UXP Developer Tool (UDT) must be installed and connected. Documentation: <https://developer.adobe.com/photoshop/uxp/2022/guides/>.

When pointing UDT at the plugin, target the built `dist/manifest.json`, not the source `plugin/manifest.json` - the source manifest references files that only exist after webpack runs (the bundled `index.js`, the copied `index.html`).

## UXP gotchas (collected during the SPEC 010 port)

- `app.documents.add({ mode, fill })` rejects bare strings - pass `constants.NewDocumentMode.RGB` and `constants.DocumentFill.TRANSPARENT` (uppercase keys).
- `Document.trim(trimType, top, bottom, left, right)` takes positional args, not an options bag.
- `file.write(string)` defaults to utf8. Passing `{ format: "utf8" }` errors with "Format must be storage.formats.utf8 or storage.formats.binary" - drop the option.
- `manifestVersion: 5` with `launchProcess` declared but unused makes the plugin Validate but fail Load. Declare only the permissions the plugin actually uses.
- The HTML `<script>` injection at the top of `plugin/index.html` (`globalThis.screen = {}` and `WebSocket.prototype.OPEN`) is required by the React + UXP combination; do not remove.

## Testing

Unit tests for the pure planner + validator live under `uxp-plugin-tests/` and run via vitest. PS DOM operations stay manual.

Manual smoke test: load the plugin in UDT, run the exporter against `examples/authored/doll/02_photoshop_setup/doll_tagged.psd`, diff the output against the captured oracle baseline under `examples/authored/doll/02_photoshop_setup/uxp_export/` (gitignored; regenerable per the SPEC 010 Wave 10.3 procedure).

## Reference prior art

- Adobe UXP guide: <https://developer.adobe.com/photoshop/uxp/2022/guides/>
- UXP Photoshop API reference: <https://developer.adobe.com/photoshop/uxp/2022/ps_reference/>
- UXP storage (file system): <https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/>
- Adobe UXP plugin samples (React starter): <https://github.com/AdobeDocs/uxp-photoshop-plugin-samples>
