# Photoshop UXP plugin

UXP plugin that exports PSD layers to a Proscenio manifest + per-layer PNGs, and re-imports a manifest back into a PSD. Schema target: [`schemas/psd_manifest.schema.json`](../schemas/psd_manifest.schema.json) v1.

Deeper context: [`.ai/skills/photoshop-uxp-dev.md`](../.ai/skills/photoshop-uxp-dev.md) and [`docs/PHOTOSHOP-WORKFLOW.md`](../docs/PHOTOSHOP-WORKFLOW.md). Design lives in [SPEC 010](../specs/010-photoshop-uxp-migration/STUDY.md).

## Stack

- **TypeScript** strict; ajv runtime validation against the v1 schema.
- **React** for the panel; Spectrum web components (`<sp-checkbox>`, `<sp-action-button>`, `<sp-heading>`, `<sp-body>`) for native theming.
- **webpack + Babel** as bundler (locked, SPEC 010 D15).
- **pnpm** as package manager (locked, SPEC 010 D14).
- **vitest** for unit tests on the pure planner + validator.

## Install dependencies

```sh
pnpm install
```

`npm install` works as a fallback, but the committed lockfile is pnpm.

## Dev loop

```sh
pnpm run typecheck   # tsc --noEmit; gates the typed surface
pnpm run test        # vitest run; covers the pure planner + ajv validator
pnpm run build       # webpack into dist/; one-shot
pnpm run watch       # webpack + nodemon rebuild on src change
pnpm run uxp:load    # load dist/ via UDT (`uxp plugin load`)
pnpm run uxp:reload  # reload the running plugin
pnpm run uxp:watch   # auto-reload UDT on dist/ changes
pnpm run uxp:debug   # attach Chrome DevTools to the plugin
```

The `uxp:*` scripts assume the [UXP Developer Tool (UDT)](https://developer.adobe.com/photoshop/uxp/2022/guides/devtool/) is running and connected.

## Load in Photoshop via UDT

1. `pnpm run build` (or `pnpm run watch`).
2. UDT > **Add Plugin** > target `apps/photoshop/dist/manifest.json` (the BUILT manifest, not the source `plugin/manifest.json` - the source references files that only exist after webpack runs).
3. UDT > **Load** on the plugin row. Switch to Photoshop; the **Proscenio Exporter** panel appears under **Plugins**.

## What the plugin does

| Direction | Trigger | Behaviour |
| --- | --- | --- |
| Export | Active PSD + chosen output folder | Walks the layer tree, builds a v1 manifest, validates it against the schema, writes the JSON + per-layer PNGs under the folder's `images/` subdirectory. One core.executeAsModal banner per export. |
| Import | Picked manifest JSON | Reads the manifest, ajv-validates it, creates a fresh PSD at the manifest size, places every layer at its declared position, names sprite_frame groups as LayerSets with one child per frame. Saves as `photoshop/<doc>.psd` next to the manifest. |

The output folder is persisted across plugin reloads via UXP's `createPersistentToken` + `localStorage`; pick it once.

## Compatibility

- **Photoshop**: CC 2024 / PS 25.0 or newer. `plugin/manifest.json` `host.minVersion` enforces.
- **UXP**: ships with PS - no separate install.
- **UDT**: latest; some UXP APIs only appear in recent UDT builds.
- **Node**: 20 or newer for pnpm + tsc.

## Common issues

- **UDT Load fails after Validate passes.** Almost always means UDT is pointed at `plugin/manifest.json` rather than `dist/manifest.json`. Re-add the plugin with the dist path.
- **Export fails with "Format must be storage.formats.utf8 or storage.formats.binary".** UXP rejected a bare `{ format: "utf8" }` option; the code drops the option entirely (string content defaults to utf8). If this error reappears in a future PS version, propagate `storage.formats.utf8` as the value.
- **Export PNGs land opaque.** The temp doc was created with the wrong fill enum. `documents.add({ fill })` requires `constants.DocumentFill.TRANSPARENT` (UPPERCASE), not the lowercase string.

## Folder layout

See [.ai/skills/photoshop-uxp-dev.md](../.ai/skills/photoshop-uxp-dev.md) for the canonical map (domain / adapters / io / controllers / hooks / panels / types).
