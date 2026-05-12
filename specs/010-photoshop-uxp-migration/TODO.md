# SPEC 010 - TODO

UXP plugin replaces ExtendScript JSX. Schema unchanged. See [STUDY.md](STUDY.md).

## Decisions to lock

- [x] D1 - cut-over vs coexistence (locked: cut over; JSX retires at parity)
- [x] D2 - Photoshop minimum version (locked: PS 22 / CC 2021+)
- [x] D3 - TypeScript vs plain JS (locked: TypeScript; `tsconfig.json` shipped)
- [x] D4 - React vs Adobe Spectrum UXP (locked: React; Spectrum revisitable later)
- [x] D5 - schema validation library (locked: `ajv` consuming `schemas/psd_manifest.schema.json`)
- [x] D6 - file system flow (locked: pick folder once per session; cached in `localStorage`)
- [x] D7 - roundtrip parity (locked: yes -- port `proscenio_import.jsx` semantics too)
- [x] D8 - schema bump (locked: no bump -- v1 contract preserved byte-for-byte)
- [x] D9 - CI integration (locked: new `lint-photoshop` job; gates 5 -> 6)
- [x] D10 - test fixtures (locked: reuse `examples/generated/simple_psd/`)
- [x] D11 - JSX retirement trigger (locked: manual-roundtrip parity on `simple_psd/`)
- [x] D12 - distribution channel (locked: `.ccx` via UDT for releases; UDT direct-load for dev)
- [x] D13 - live reload (locked: yes via `pnpm run uxp:watch`)
- [x] D14 - package manager (locked: pnpm)
- [x] D15 - bundler (locked: webpack; Vite rejected)

## Pre-implementation

- [ ] Confirm `examples/generated/simple_psd/source.psd` exists and exports a valid v1 manifest (use as parity oracle).
- [ ] Verify the React scaffold builds: `cd apps/photoshop && npm install && npm run build`.
- [ ] Verify `uxp plugin load` works against a real Photoshop install via UDT.
- [ ] Capture current JSX output for `examples/generated/simple_psd/source.psd` as the byte-equality target.

## Wave 10.1 - TypeScript foundation

- [x] `tsconfig.json` with `strict: true` (allowJs for the scaffold transition).
- [x] `@types/react`, `@types/react-dom`, `typescript`, `@babel/preset-typescript` in `package.json`.
- [x] Webpack config handles `.ts` / `.tsx` / `.js` / `.jsx` via `@babel/preset-typescript`.
- [x] `pnpm run typecheck` script (`tsc --noEmit`).
- [x] Replace deprecated `@babel/plugin-proposal-object-rest-spread` with `@babel/plugin-transform-object-rest-spread`.
- [ ] Add UXP types (Adobe ships a typings package - confirm exact name).
- [ ] Rename `src/index.jsx` → `src/index.tsx`.
- [ ] CI: `lint-photoshop` job stub running typecheck only.

## Wave 10.1.x - Adobe scaffold modernization (follow-up)

The Adobe React UXP starter pinned several plugins to old majors. After Wave 10.1 lands, sweep these:

- [x] `babel-loader` 8 → 10
- [x] `clean-webpack-plugin` 2 → 4
- [x] `copy-webpack-plugin` 5 → 14 (large API change; rewrite the `CopyPlugin` block in `webpack.config.js`)
- [x] `css-loader` 6 → 7
- [x] `style-loader` 1 → 4
- [x] `nodemon` 2 → 3
- [x] Replace `file-loader` with webpack 5 asset modules (file-loader is deprecated)
- [x] Audit `resolutions` for `acorn-with-stage3`: webpack 5.88+ ships modern acorn natively; the override may be obsolete and removable. Convert to `pnpm.overrides` if still needed. (Removed - no longer needed.)
- [x] Declare `node:os` external alongside `os` so webpack 5's URI scheme handling does not break the build.

## Wave 10.2 - Layer walk + manifest builder

- [ ] Port `proscenio_export.jsx` layer recursion to TypeScript in `src/controllers/exporter.ts`.
- [ ] Manifest builder produces shape matching `psd_manifest.schema.json` v1.
- [ ] Sprite-frame group detection: numeric children primary + `<name>_<index>` fallback.
- [ ] Hidden layers skipped; `_` prefix excluded.
- [ ] Unit tests in `uxp-plugin-tests/` for pure functions (recursion, name sanitization, manifest builder against fixtures).

## Wave 10.3 - File system + PNG export

- [ ] UXP storage API: pick folder once, cache in component state + `localStorage`.
- [ ] Per-layer PNG export via `saveAs.png` writing into `<folder>/layers/`.
- [ ] Manifest JSON written at `<folder>/manifest.json`.
- [ ] Schema validation with `ajv` before write; surface errors in panel UI.
- [ ] Manual test: byte-equality check against captured JSX output for `examples/generated/simple_psd/source.psd`.

## Wave 10.4 - React panel

- [ ] Panel layout: doc info, folder picker, export button, validation result, roundtrip button.
- [ ] React state for export progress, errors, last-export summary.
- [ ] Plugin manifest entrypoints in `plugin/manifest.json` register the panel.
- [ ] Live reload via `npm run uxp:watch` documented in skill.

## Wave 10.5 - Roundtrip (manifest → PSD)

- [ ] Port `proscenio_import.jsx` to `src/controllers/importer.ts`.
- [ ] Reads manifest JSON, opens PSD if absent, recreates layers.
- [ ] Manual test: roundtrip on `examples/generated/simple_psd/` produces structurally identical PSD.

## Wave 10.6 - CI completion

- [ ] `lint-photoshop` job runs typecheck + unit tests + manifest schema check on fixtures.
- [ ] Document `lint-photoshop` in [`docs/DECISIONS.md`](../../docs/DECISIONS.md) "Validation gates" (5 → 6).
- [ ] Update README "Predictable contract" pillar to mention typed Photoshop side.

## Wave 10.7 - JSX retirement

- [ ] Confirm parity manually on `examples/generated/simple_psd/` and any other PSD fixtures.
- [ ] Delete `apps/photoshop/proscenio_export.jsx`.
- [ ] Delete `apps/photoshop/proscenio_import.jsx`.
- [ ] Remove JSX porting notes from `photoshop-uxp-dev` skill.
- [ ] Bump README minimum Photoshop version note.

## Wave 10.8 - Documentation polish

- [ ] `apps/photoshop/README.md` updated with UXP install + dev loop.
- [ ] [`CONTRIBUTING.md`](../../CONTRIBUTING.md) end-to-end usage walkthrough mentions the UXP plugin path (currently mentions JSX in step 1).
- [ ] [`docs/DECISIONS.md`](../../docs/DECISIONS.md) gains "SPEC 010 - Photoshop UXP migration" subsection capturing locked decisions and the JSX retirement.
- [ ] [`STATUS.md`](../../STATUS.md) flips SPEC 010 row to shipped.

## Risks

- **UXP API drift across PS versions.** Mitigation: pin minimum at PS 22; smoke-test on latest stable + minimum version manually.
- **Webpack + Babel + tsc interaction.** Scaffold uses Babel; layering tsc on top can introduce config friction. Keep tsc as type-only check (`--noEmit`); let Babel keep transpiling.
- **Sandbox file permissions.** UXP requires user to grant folder write each session unless cached. Document the one-time pick UX clearly so users do not assume the plugin is broken.
- **Roundtrip layer reconstruction.** PSD format is rich; the import path must not corrupt source PSDs. Always work on a copy; never overwrite the source.
