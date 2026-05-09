---
name: photoshop-uxp-dev
description: UXP plugin for Photoshop - layer slicing and manifest JSON via TypeScript + React
---

# Photoshop UXP plugin

## Stack

- **UXP** (Unified Extensibility Platform). Adobe's modern plugin runtime; replaces ExtendScript.
- **TypeScript** for source code - real type checking end-to-end, not `@ts-check` JSDoc. `tsconfig.json` ships in `photoshop-exporter/` with `strict: true`; `allowJs: true` lets the existing `.jsx` scaffold continue to import while the port to `.tsx` proceeds.
- **React** for the panel UI.
- **webpack + babel** bundle into the UXP plugin format. Webpack is **locked** as the bundler (per [SPEC 010](../../specs/010-photoshop-uxp-migration/STUDY.md) D15) — Adobe's officially supported path. Vite was evaluated and rejected; UXP runtime needs CommonJS output and Vite's ESM-first defaults fight it.
- **pnpm** as the package manager (per SPEC 010 D14). `package.json` declares `packageManager: pnpm@9.x`.
- **Photoshop CC 2021+ (PS 22+)** minimum requirement.

ExtendScript / JSX is no longer the target. Legacy `proscenio_export.jsx` and `proscenio_import.jsx` stay as historical reference until the UXP plugin reaches feature parity, then retire.

## Folder layout

```text
photoshop-exporter/
├── package.json          # pnpm; webpack + babel + react + TypeScript devDeps
├── tsconfig.json         # strict TypeScript config; allowJs for the JSX scaffold
├── webpack.config.js     # build config; @babel/preset-typescript handles .ts/.tsx + .jsx
├── plugin/               # UXP package output target
│   ├── manifest.json     # plugin manifest (host, entrypoints, permissions)
│   ├── index.html        # panel root
│   └── icons/
├── src/
│   ├── index.jsx         # plugin entry (will become index.tsx)
│   ├── components/       # React UI
│   ├── controllers/      # PS DOM operations (layer walk, export)
│   ├── panels/           # panel registrations
│   └── styles.css
└── uxp-plugin-tests/
```

## Output format

The plugin emits a manifest JSON that conforms to [`schemas/psd_manifest.schema.json`](../../schemas/psd_manifest.schema.json) v1, alongside per-layer PNGs in a sibling folder. Schema is unchanged from the JSX era - only the implementation moves.

```json
{
  "format_version": 1,
  "doc": "dummy.psd",
  "size": [1024, 1024],
  "pixels_per_unit": 100,
  "layers": [
    {
      "kind": "polygon",
      "name": "torso",
      "path": "dummy/torso.png",
      "position": [120, 340],
      "size": [180, 240],
      "z_order": 0
    }
  ]
}
```

This JSON is consumed by [`blender-addon/importers/photoshop_json.py`](../../blender-addon/importers/photoshop_json.py).

## Conventions

- Layer groups become folders in the output structure.
- Hidden layers are skipped.
- Layer name prefix `_` excludes the layer (artist annotation).
- Trim alpha by default; configurable via the panel.
- Sprite-frame group detection: numeric children inside a layer group (primary) + `<name>_<index>` flat-naming fallback.

## File system in UXP

UXP sandboxes file system access. Use the `require("uxp").storage` API:

- `localFileSystem.getFolder()` opens the user-picked output folder.
- `entry.createFile(name, { overwrite: true })` writes a sibling PNG or the manifest JSON.
- Direct `File` constructor from ExtendScript is **not** available.

The user picks an export folder once per session; the plugin writes the manifest + PNGs as siblings inside it.

## Dev loop

```sh
pnpm install
pnpm run typecheck   # tsc --noEmit; gates IDE + CI before bundling
pnpm run build       # webpack into dist/
pnpm run uxp:load    # load plugin into Photoshop via UDT
pnpm run uxp:watch   # rebuild + reload on src changes
pnpm run uxp:debug   # open Chrome DevTools attached to the plugin
```

`npm run ...` works as a fallback if a contributor has not installed pnpm; the lockfile shape will diverge but the build is the same.

Adobe UXP Developer Tool (UDT) must be installed and connected. Documentation: <https://developer.adobe.com/photoshop/uxp/2022/guides/>.

## Testing

Headless plugin testing is limited. Manual flow:

1. Open a sample `.psd` (use `examples/simple_psd/source.psd`).
2. Run the plugin.
3. Verify the manifest JSON validates against `psd_manifest.schema.json` (use `check-jsonschema` from CI).
4. Verify PNG sidecars exist with expected names and sizes.

Add unit tests under `uxp-plugin-tests/` for pure functions (layer-tree walk, name sanitization, manifest builder). DOM operations stay manual.

## Migration from JSX (historical)

`proscenio_export.jsx` and `proscenio_import.jsx` implement the v1 manifest contract. The port forward:

- Layer walk recursion: TypeScript with proper types.
- `app.activeDocument.layers`: `require("photoshop").app.activeDocument.layers` (UXP DOM).
- `File` writes: UXP storage API.
- Dialogs: React panel.

The schema does not change. A successful port produces byte-identical manifest output for the same `.psd`.

## Reference prior art

- Adobe UXP guide: <https://developer.adobe.com/photoshop/uxp/2022/guides/>
- UXP Photoshop API reference: <https://developer.adobe.com/photoshop/uxp/2022/ps_reference/>
- UXP storage (file system): <https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/>
- Adobe UXP plugin samples (React starter): <https://github.com/AdobeDocs/uxp-photoshop-plugin-samples>
- `coa_tools2/Photoshop/coa_export.jsx` historical JSX prior art only - do not port forward; schema target differs.
