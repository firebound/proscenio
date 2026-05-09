# Photoshop UXP plugin

Source for the Proscenio Photoshop plugin. Built on Adobe's React UXP starter; ported to TypeScript per [SPEC 010](../specs/010-photoshop-uxp-migration/STUDY.md). Schema target: [`schemas/psd_manifest.schema.json`](../schemas/psd_manifest.schema.json) v1.

For deeper context see [`.ai/skills/photoshop-uxp-dev.md`](../.ai/skills/photoshop-uxp-dev.md) and [`docs/PHOTOSHOP-WORKFLOW.md`](../docs/PHOTOSHOP-WORKFLOW.md).

## Stack

- **pnpm** as package manager (locked, SPEC 010 D14).
- **webpack + Babel** as bundler (locked, SPEC 010 D15).
- **TypeScript** for source code; `tsconfig.json` is strict, with `allowJs` so the scaffold's `.jsx` files compile alongside new `.ts` / `.tsx` during the migration.
- **React 16** for the panel UI.

## Install dependencies

`pnpm` is the canonical package manager. Install pnpm if you do not have it (<https://pnpm.io/installation>), then from this folder:

```sh
pnpm install
```

`npm install` works as a fallback if pnpm is unavailable.

## Build

Two modes:

- `pnpm run watch` builds a development version into `dist/` and rebuilds on source changes. Use during dev with UDT in watch mode.
- `pnpm run build` builds a production version into `dist/` once. No live reload.

Run either before loading the plugin in Photoshop.

## Type checking

```sh
pnpm run typecheck
```

Runs `tsc --noEmit` against `tsconfig.json`. Emits no output - webpack handles the actual transpile via `@babel/preset-typescript`.

## Load in Photoshop via UDT

Use the [UXP Developer Tool](https://developer.adobe.com/photoshop/uxp/2022/guides/getting-started/) to load the plugin:

1. Click **Add Plugin...** in UDT.
2. Pick the `manifest.json` from `dist/` (built output) or from `plugin/` (source manifest).
3. If you point UDT at `plugin/manifest.json`, set the plugin build folder to `dist/` via **... → Options → Advanced**.
4. Click **Load** on the plugin row. Switch to Photoshop; the plugin panels appear.

During development, the recommended flow is `pnpm run watch` plus loading the `dist/` manifest in UDT.

## What this plugin does today

Adobe React UXP starter with two demo panels and a Spectrum UXP color picker. Proscenio-specific functionality (PSD layer walk, manifest emission, schema validation, roundtrip) lands as part of [SPEC 010](../specs/010-photoshop-uxp-migration/STUDY.md).

## Common issues

- **`pnpm install` errors**: delete `node_modules/` and any lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`), then `pnpm install` again.
- **Build picks up the wrong loader on a `.tsx` file**: confirm `webpack.config.js` includes `.ts` / `.tsx` in the resolve extensions and the babel rule.

## Compatibility

- Photoshop: 23.2.0 or higher (the scaffold floor; SPEC 010 will bump to PS 22 / CC 2021+).
- UXP: 5.6 or higher.
- Node: 20 or higher recommended for pnpm + tsc tooling.
