# SPEC 010 - TODO

UXP plugin replaces ExtendScript JSX. Schema unchanged. See [STUDY.md](STUDY.md).

## Decisions to lock

- [x] D1 - cut-over vs coexistence (locked: cut over; JSX retires at parity)
- [x] D2 - Photoshop minimum version (originally locked: PS 22 / CC 2021+; bumped during Wave 10.7 to PS 25 / CC 2024+ - the floor where every UXP API the plugin uses is documented stable. Older PS versions fall off support.)
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

- [x] Verify the React scaffold builds: `cd apps/photoshop && pnpm install && pnpm run build`. (Build green on Wave 10.1.x.)
- [ ] Verify `uxp plugin load` works against a real Photoshop install via UDT. (Manual; needs the user's PS.)
- [x] Capture JSX baseline for the parity oracle: run `apps/photoshop/proscenio_export.jsx` against `examples/authored/doll/02_from_photoshop/doll.psd`, diff `02_from_photoshop/export/doll.photoshop_exported.json` against `01_to_photoshop/doll.photoshop_manifest.json`. 22/22 layers, names match. 2 legacy JSX bugs surfaced (logged in `tests/BUGS_FOUND.md`): `pixels_per_unit` not round-tripped (defaults to 100), `waist.size` off by 1 px. UXP exporter target = current JSX output (B); the PPU bug rides along until Wave 10.5 fixes the import path.

## Wave 10.1 - TypeScript foundation

- [x] `tsconfig.json` with `strict: true` (allowJs for the scaffold transition).
- [x] `@types/react`, `@types/react-dom`, `typescript`, `@babel/preset-typescript` in `package.json`.
- [x] Webpack config handles `.ts` / `.tsx` / `.js` / `.jsx` via `@babel/preset-typescript`.
- [x] `pnpm run typecheck` script (`tsc --noEmit`).
- [x] Replace deprecated `@babel/plugin-proposal-object-rest-spread` with `@babel/plugin-transform-object-rest-spread`.
- [x] Add UXP types. (Adobe does not publish to npm; local shim in `src/types/uxp.d.ts` covers what the plugin consumes - tighten member-by-member as the surface grows.)
- [x] Rename `src/index.jsx` -> `src/index.tsx`.
- [x] CI: `lint-photoshop` job runs typecheck (and, since Wave 10.2, vitest).

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

- [x] Port `proscenio_export.jsx` layer recursion to TypeScript in `src/controllers/exporter.ts`.
- [x] Manifest builder produces shape matching `psd_manifest.schema.json` v1. (Schema file lands with ajv in Wave 10.3; types in `src/types/manifest.ts` encode the contract.)
- [x] Sprite-frame group detection: numeric children primary + `<name>_<index>` fallback.
- [x] Hidden layers skipped; `_` prefix excluded.
- [x] Unit tests in `uxp-plugin-tests/` for pure functions (recursion, name sanitization, manifest builder against fixtures). 24 tests via vitest; wired into `lint-photoshop` CI job.

## Wave 10.3 - File system + PNG export

- [x] UXP storage API: pick folder once. (Module-level in-memory cache via `cachedFolder` in `export-flow.ts`; survives within plugin session. Persistent token across reloads parked for Wave 10.4 alongside panel polish.)
- [x] Per-layer PNG export via `saveAs.png` writing into `<folder>/images/<name>.png` (folder layout matches JSX exporter, not the originally-spec'd `<folder>/layers/`, so the same parity oracle works).
- [x] Manifest JSON written at `<folder>/<doc>.photoshop_exported.json` (filename matches JSX exporter for byte-equality comparisons).
- [x] Schema validation with `ajv` before write; surface errors in panel UI.
- [x] Manual test: byte-equality check against captured JSX output for `examples/authored/doll/02_from_photoshop/doll.psd`. Ran UXP exporter in UDT against doll.psd; output landed in `02_from_photoshop/uxp_export/`. Manifest JSON: 22/22 entries semantically identical to the JSX baseline (only CRLF -> LF byte diff). PNGs: 22/22 pixel-byte-equal (SHA256 of decompressed IDAT matches; outer SHA differs only in zlib encoder flavour). Parity oracle PASSED.

## Wave 10.4 - React panel

- [x] Panel layout: doc info section + folder picker section + export button + validation result. Roundtrip button parked for Wave 10.5 (lands with the importer port).
- [x] React state for export progress, errors, last-export summary. Folder is persisted across plugin reloads via `storage.localFileSystem.createPersistentToken` + `localStorage`.
- [x] Plugin manifest entrypoints in `plugin/manifest.json` register the panel. (Wired in Wave 10.3.)
- [ ] Live reload via `pnpm run uxp:watch` documented in skill.

## Wave 10.5 - Roundtrip (manifest -> PSD)

- [x] Port `proscenio_import.jsx` semantics to TypeScript. Lives as `src/controllers/import-flow.ts` (orchestrator) + `src/io/manifest-reader.ts` (file-pick + ajv) + `src/io/png-placer.ts` (per-layer placement) + `src/io/psd-writer.ts` (PSD save).
- [x] Reads manifest JSON, creates a fresh transparent doc at the manifest size, stamps every entry in z_order descending. Sprite_frame entries land as LayerSets with one child per frame.
- [x] PPU roundtrip fix (BUGS_FOUND entry): parked as part of SPEC 011 (the tag system landing post-10.7 owns the PSD-side metadata story).
- [ ] Manual test: roundtrip on `examples/authored/doll/01_to_photoshop/doll.photoshop_manifest.json` produces a structurally identical PSD to the existing `02_from_photoshop/doll.psd`.

## Wave 10.6 - CI completion

- [x] `lint-photoshop` job runs typecheck + unit tests. PSD manifest schema check on fixtures landed in `validate-schema` (covers `*.photoshop_manifest.json` and `*.photoshop_exported.json` under `examples/`).
- [x] Document `lint-photoshop` in [`docs/DECISIONS.md`](../../docs/DECISIONS.md) "Validation gates" (5 -> 6).
- [x] Update README "Predictable contract" pillar to mention typed Photoshop side.

## Wave 10.7 - JSX retirement

- [x] Confirm parity manually. Wave 10.3 ran the doll roundtrip oracle (`examples/authored/doll/02_from_photoshop/doll.psd`): manifest 22/22 semantic-equal, PNGs 22/22 pixel-byte-equal vs the JSX baseline. `examples/generated/simple_psd/` has no PSD source (manifest-first fixture), so doll is the canonical retirement gate.
- [x] Delete `apps/photoshop/proscenio_export.jsx`.
- [x] Delete `apps/photoshop/proscenio_import.jsx`.
- [x] Remove JSX porting notes from `photoshop-uxp-dev` skill.
- [x] Bump README minimum Photoshop version note (PS 22 -> PS 25 / CC 2024+). `plugin/manifest.json` `host.minVersion` also bumped.

## Wave 10.8 - Documentation polish

- [x] `apps/photoshop/README.md` updated with UXP install + dev loop.
- [x] [`CONTRIBUTING.md`](../../CONTRIBUTING.md) end-to-end usage walkthrough mentions the UXP plugin path (replaced the step 1 JSX reference).
- [x] [`docs/DECISIONS.md`](../../docs/DECISIONS.md) gains "SPEC 010 - Photoshop UXP migration" subsection capturing locked decisions and the JSX retirement.
- [x] [`STATUS.md`](../../STATUS.md) flips SPEC 010 row to shipped.

## Risks

- **UXP API drift across PS versions.** Mitigation: pin minimum at PS 25 (post-Wave 10.7 bump); smoke-test on latest stable + minimum version manually.
- **Webpack + Babel + tsc interaction.** Scaffold uses Babel; layering tsc on top can introduce config friction. Keep tsc as type-only check (`--noEmit`); let Babel keep transpiling.
- **Sandbox file permissions.** UXP requires user to grant folder write each session unless cached. Document the one-time pick UX clearly so users do not assume the plugin is broken.
- **Roundtrip layer reconstruction.** PSD format is rich; the import path must not corrupt source PSDs. Always work on a copy; never overwrite the source.
