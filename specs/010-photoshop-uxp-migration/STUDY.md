# SPEC 010 — Photoshop UXP migration

**Status**: scaffolded. UXP plugin template already in [`apps/photoshop/`](../../apps/photoshop/) (React + webpack + Babel). Decisions to lock + implementation pending.

## Problem

The Photoshop side ships as ExtendScript JSX (`proscenio_export.jsx`, `proscenio_import.jsx`). ExtendScript is:

- Adobe-deprecated; UXP is the recommended runtime since Photoshop 22 (CC 2021).
- ES3-ish (no `let`, no arrow, no template strings, no native modules).
- Untyped beyond `@ts-check` JSDoc, which never reached parity with TypeScript.
- Untestable in CI (no headless harness; no `npm` toolchain).
- Slow to iterate (no live reload, no Chrome DevTools, dialog-based debug).

This blocks the **Predictable contract** pillar: the Photoshop side is the only component without real type-checking and the only component CI cannot lint. The schema is validated, but the writer that produces it is the weak link.

## Solution

Replace the JSX exporter with a UXP plugin written in TypeScript + React. Schema (`psd_manifest.schema.json` v1) does not change — the wire format stays byte-identical. Only the implementation moves.

The scaffold is already in [`apps/photoshop/`](../../apps/photoshop/):

```text
apps/photoshop/
├── package.json          # webpack + babel + react
├── webpack.config.js
├── plugin/
│   ├── manifest.json     # UXP host + entrypoints
│   ├── index.html        # panel root
│   └── icons/
├── src/
│   ├── index.jsx         # plugin entry (today JSX)
│   ├── components/
│   ├── controllers/
│   ├── panels/
│   └── styles.css
├── uxp-plugin-tests/
├── proscenio_export.jsx  # legacy ExtendScript (retire when parity reached)
└── proscenio_import.jsx  # legacy ExtendScript
```

## Stack choice

| Layer | Choice | Rationale |
| --- | --- | --- |
| Runtime | UXP | Adobe's modern, supported plugin platform |
| Source language | TypeScript | Aligns with Proscenio's strong-typing pillar; ESLint + tsc gates in CI |
| UI library | React (already in scaffold) | UXP supports React natively; alternative is Adobe Spectrum UXP. React keeps scaffold intact |
| Bundler | webpack + babel (in scaffold) | Stock UXP starter; mature, well-documented |
| Test runner | Jest or Vitest for pure functions | Manual UI / DOM still required (no headless Photoshop) |
| Schema validation | `ajv` (npm) + the existing `psd_manifest.schema.json` | Pulls schema as single source of truth |
| Distribution | `.ccx` package + UDT loader for dev | Standard UXP pipeline |
| Photoshop minimum | PS 22 / CC 2021 | UXP availability cut |

## Decisions to lock when SPEC opens

| ID | Decision | Default lean |
| --- | --- | --- |
| **D1** | Cut-over vs coexistence with JSX | **Cut over** (already chosen). JSX retires when UXP reaches parity. |
| **D2** | Photoshop minimum version | **PS 22 / CC 2021+**. Documented in README. Older versions fall off support. |
| **D3** | Source language: TypeScript vs plain JS via Babel | **TypeScript**. Aligns with strong-typing pillar; scaffold can keep webpack/Babel for transpile, add `tsc --noEmit` for type gate. |
| **D4** | UI library: React vs Adobe Spectrum UXP | **React** (scaffold already). Spectrum UXP optional later if more native PS look is wanted. |
| **D5** | Schema validation library | **`ajv`** consuming the existing `schemas/psd_manifest.schema.json` directly. No duplication. |
| **D6** | File system: pick-folder-once vs prompt-each-export | **Pick folder once per session**. Plugin caches the user's chosen output folder. |
| **D7** | Roundtrip (manifest → PSD) parity | **Yes**, port `proscenio_import.jsx` semantics. Same scope as exporter cut-over; required for closing the JSX retirement. |
| **D8** | Schema bump | **No bump**. `psd_manifest.schema.json` v1 unchanged. Implementation-only migration. |
| **D9** | CI integration | **`npm test` + `tsc --noEmit` + `check-jsonschema` in `lint-photoshop` job**. Adds a 6th gate. |
| **D10** | Test fixtures | Reuse `examples/generated/simple_psd/`. Add `examples/generated/simple_psd/source.psd` if not present so the UXP plugin has a fixture to run against. |
| **D11** | JSX retirement trigger | **Feature parity confirmed** by manual roundtrip on `examples/generated/simple_psd/` and `examples/authored/doll/` (when its PSD source ships). Then delete `proscenio_export.jsx` + `proscenio_import.jsx`. |
| **D12** | Distribution channel | **`.ccx` packaged via UDT** for releases; UDT direct-load for dev. Adobe Marketplace optional later. |
| **D13** | Live reload during dev | **Yes** via `pnpm run uxp:watch` (already in scaffold). Documented in `photoshop-uxp-dev` skill. |
| **D14** | Package manager | **pnpm (locked)**. `package.json` declares `packageManager: pnpm@9.x`. `package-lock.json` and `yarn.lock` ignored; pnpm-lock.yaml is the canonical lock when committed. |
| **D15** | Bundler | **webpack (locked)**. Adobe officially supports webpack for UXP; the React starter ships with it. Vite was evaluated and rejected: ESM-first defaults fight UXP's CommonJS runtime, no Adobe support, community plugins immature. Revisit only if Adobe ships first-class Vite tooling. |

## Implementation surface

### Source language migration

- Configure `tsconfig.json` with strict mode (`strict: true`, `noImplicitAny: true`).
- Rename `src/*.jsx` → `src/*.tsx` / `src/*.ts` per file responsibility.
- Add `@types/react`, `@types/react-dom`, UXP type definitions if available.
- Add `tsc --noEmit` to the `npm run build` pipeline so type errors block bundling.

### Photoshop DOM access

UXP uses `require("photoshop")` instead of ExtendScript's global `app`:

```ts
import { app } from "photoshop";

const doc = app.activeDocument;
for (const layer of doc.layers) {
  // walk recursive
}
```

`require("photoshop").action` exposes batchPlay for low-level operations not in the new DOM. Most layer-walk + export use cases stay in the typed DOM.

### File system

ExtendScript `File` constructor is unavailable. Replace with:

```ts
import { storage } from "uxp";

const folder = await storage.localFileSystem.getFolder();
const manifestFile = await folder.createFile("manifest.json", { overwrite: true });
await manifestFile.write(JSON.stringify(manifest, null, 2));
```

Per-layer PNG export uses `app.activeDocument.saveAs.png()` writing into a sub-folder created via `folder.createFolder("layers")`.

### React panel

Single panel with:

- Source file display (active document name).
- Output folder picker (one-time per session).
- Export button.
- Roundtrip / re-import button (D7).
- Validation result display (manifest validates against schema).

Panel state is local React state plus `localStorage` for the cached folder path.

### Schema validation

```ts
import Ajv from "ajv";
import schema from "../../schemas/psd_manifest.schema.json";

const ajv = new Ajv({ strict: false });
const validate = ajv.compile(schema);

if (!validate(manifest)) {
  throw new Error(`Manifest invalid: ${ajv.errorsText(validate.errors)}`);
}
```

Same validation runs in CI via `check-jsonschema` on the produced JSON.

### CI gate

Add `lint-photoshop` job to `.github/workflows/ci.yml`:

```yaml
lint-photoshop:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with: { node-version: '20' }
    - run: npm ci
      working-directory: apps/photoshop
    - run: npm run typecheck
      working-directory: apps/photoshop
    - run: npm test
      working-directory: apps/photoshop
```

Brings the validation count from 5 gates to 6.

## Reference

- Adobe UXP guide: <https://developer.adobe.com/photoshop/uxp/2022/guides/>
- UXP Photoshop API reference: <https://developer.adobe.com/photoshop/uxp/2022/ps_reference/>
- UXP storage (file system): <https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/>
- Adobe UXP plugin samples (React starter): <https://github.com/AdobeDocs/uxp-photoshop-plugin-samples>
- Skill: [`.ai/skills/photoshop-uxp-dev.md`](../../.ai/skills/photoshop-uxp-dev.md)
- Companion contract: [`schemas/psd_manifest.schema.json`](../../schemas/psd_manifest.schema.json)
- Predecessor SPEC: [SPEC 006 - Photoshop importer](../006-photoshop-importer/STUDY.md) (manifest v1 contract)

## Out of scope

- Schema bump. v1 contract is preserved byte-for-byte.
- Krita / GIMP UXP-equivalents. Tracked in [`docs/DEFERRED.md`](../../docs/DEFERRED.md). Krita has its own plugin SDK; GIMP is Python — different surfaces.
- Adobe Marketplace publication. Distributable via UDT load + `.ccx` direct install for now.
- Photoshop versions before CC 2021. Documented bump.

## Successor considerations

- Once shipped, the JSX files are deleted. SPEC 006 docs reference UXP as the live impl.
- A future SPEC may add **batch export** (multiple PSDs at once) once the single-file path is stable.
- A future SPEC may revisit **roundtrip parity** for advanced PSD features (smart objects, adjustment layers) which the JSX importer never handled.
