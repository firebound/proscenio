# Photoshop UXP plugin

Source for the Proscenio Photoshop plugin. Built on Adobe's React UXP starter; will be ported to TypeScript per [SPEC 010](../specs/010-photoshop-uxp-migration/STUDY.md). Schema target: [`schemas/psd_manifest.schema.json`](../schemas/psd_manifest.schema.json) v1.

For deeper context see [`.ai/skills/photoshop-uxp-dev.md`](../.ai/skills/photoshop-uxp-dev.md) and [`docs/PHOTOSHOP-WORKFLOW.md`](../docs/PHOTOSHOP-WORKFLOW.md).

## Install dependencies

`npm` (or `yarn`) is required. From the root of this folder:

```sh
npm install
```

If you prefer `yarn`, after `package-lock.json` exists, run:

```sh
yarn import
```

## Build

Two modes:

- `npm run watch` (or `yarn watch`) builds a development version into `dist/` and rebuilds on source changes. Use during dev with UDT in watch mode.
- `npm run build` (or `yarn build`) builds a production version into `dist/`. No live reload.

You **must** run either `watch` or `build` before loading the plugin in Photoshop.

## Load in Photoshop via UDT

Use the [UXP Developer Tool](https://developer.adobe.com/photoshop/uxp/2022/guides/getting-started/) to load the plugin:

1. Click **Add Plugin...** in UDT.
2. Pick the `manifest.json` from `dist/` (built output) or from `plugin/` (source manifest).
3. If you point UDT at `plugin/manifest.json`, set the plugin build folder to `dist/` via **... → Options → Advanced**.
4. Click **Load** on the plugin row. Switch to Photoshop; the plugin panels appear.

During development, the recommended flow is `npm run watch` plus loading the `dist/` manifest in UDT.

## What this plugin does today

Adobe React UXP starter with two demo panels and a Spectrum UXP color picker. Proscenio-specific functionality (PSD layer walk, manifest emission, schema validation, roundtrip) lands as part of [SPEC 010](../specs/010-photoshop-uxp-migration/STUDY.md).

## Common issues

- **`npm install` errors**: delete `node_modules/`, `package-lock.json`, and `yarn.lock` (if present), then `npm install` again.
- **`yarn import` says "Lockfile already exists"**: an existing `yarn.lock` is in the way. Delete it to regenerate, or skip `yarn import` and use `npm` directly.

## Compatibility

- Photoshop: 23.2.0 or higher.
- UXP: 5.6 or higher.
- Target after SPEC 010 lands: Photoshop CC 2021+ (PS 22+) with TypeScript source and React UI.
