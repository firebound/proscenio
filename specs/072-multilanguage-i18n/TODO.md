# Spec 072 TODO: Multilanguage i18n

Execution plan for [STUDY.md](STUDY.md). Two independent tracks (Blender addon, Docs) plus a shared close-out. The tracks share no code and can run in parallel; the only ordering inside each track is structure-before-content. Confirm the STUDY open calls (D3 tooling, completeness bar) before starting the content passes.

Locale codes: Blender `pt_BR`, Docusaurus `pt-BR`. English stays the canonical source on both - nothing English is moved or deleted.

## Track A - Blender addon

### A1. Locale-table structure (no translation yet)

- [ ] Create `apps/blender/core/i18n_locales/` package with an `__init__.py` exporting a `LOCALE_TABLES` aggregate (one module per locale).
- [ ] Add `apps/blender/core/i18n_locales/pt_BR.py` exporting `ROWS: tuple[TranslationRow, ...]` (empty to start).
- [ ] Rework [core/i18n.py](../../apps/blender/core/i18n.py) so `TRANSLATIONS` is assembled from `i18n_locales` rather than inline, keeping `iface()`, `_as_translations_dict`, `register`/`unregister` unchanged. `i18n.py` stays the thin assembler (STUDY D4).
- [ ] Headless test: the table registers, `_as_translations_dict` folds the per-locale modules into `{locale: {(ctxt, msgid): msgstr}}`, and a seeded sample `(ctxt, msgid) -> msgstr` round-trips through `pgettext_iface` under a forced `pt_BR` locale (STUDY D8).

### A2. Extraction + drift tooling

- [ ] Add the extraction script (e.g. `scripts/blender/extract_i18n.py`, bpy-free where possible) that walks `apps/blender/**` and collects translatable msgids in two buckets:
  - **static**: `bl_label`, `bl_description`, property `name=`/`description=`, enum item `(id, name, desc)` labels.
  - **dynamic**: `iface(...)` first-args, `layout.label(text=...)` / `row.label(text=...)` literals, `report_info/warn/error/debug` message args.
- [ ] Script emits/updates a catalog template (the full msgid set with empty pt-BR slots) for the translator to fill, and is re-runnable (stable ordering, no churn on unchanged source). Decide template format: a `pt_BR.py` skeleton vs a `.po`/JSON intermediate the build folds in. Recommend the `pt_BR.py` skeleton (no extra parser, matches D4).
- [ ] Reverse-coverage test (spec 064 precedent): every registered `(ctxt, msgid)` still exists in source, and every extracted translatable msgid is present in the catalog (fail on a new unregistered string or a stale registered one). This is the drift guard that keeps the table honest across future copy changes.

### A3. Dynamic-string wrapping (STUDY D5)

- [ ] Wrap the dynamic call sites so they resolve against the table:
  - `layout.label(text="...")` / `row.label(...)` computed labels across `panels/**` and operator draw code -> `iface("...")`.
  - `report_*` message arguments at the call sites -> wrap the message, keeping the `Proscenio: ` / `[Proscenio debug] ` prefix in [report.py](../../apps/blender/core/_shared/report.py) outside the translated msgid (prefix the translated string).
  - any f-string / computed label feeding a `bl_label`-equivalent draw.
- [ ] Static strings (`bl_label`, property `name`/`description`, enum items) get **no** code change - they auto-translate from the table once rows exist.
- [ ] Re-run the extraction script; confirm the dynamic strings now appear as `iface()` msgids and the reverse-coverage test stays green.

### A4. pt-BR content pass

- [ ] Fill `i18n_locales/pt_BR.py ROWS` from the catalog: machine-assisted first pass + human review (STUDY D9). PT-BR orthography (full accents); EN technical terms (slot, atlas, weight paint, skeleton, element) aportuguesados only where natural, otherwise kept.
- [ ] Priority order if shipping partial (STUDY open call): panel/operator labels -> report messages -> property descriptions -> help bodies.
- [ ] Manual walk: launch Blender with "Translate Interface" on under pt_BR, confirm panels/operators/reports render Portuguese and any unfilled string falls back to English cleanly. Log the walk in the QA Companion blender checklist.

## Track B - Docs (Docusaurus)

### B1. Declare the locale + chrome

- [ ] Add `pt-BR` to `i18n.locales` and a `localeConfigs` entry (label `Portugues (Brasil)`, `htmlLang: 'pt-BR'`, `direction: 'ltr'`) in [docusaurus.config.ts](../../apps/docs/docusaurus.config.ts:56).
- [ ] Run `pnpm --dir apps/docs write-translations --locale pt-BR` to generate the `apps/docs/i18n/pt-BR/` skeleton (navbar, footer, sidebar category, theme UI JSON).
- [ ] Translate the chrome JSON: navbar `Guides`/`Project`/`Tools`, footer titles + labels, sidebar category labels, copyright. (Docusaurus's own theme strings are seeded; review for tone.)
- [ ] Wire `@easyops-cn/docusaurus-search-local` `language: ['en', 'pt']` so pt-BR pages index with the Portuguese stemmer (STUDY D7).

### B2. Content tree + first pass

- [ ] Create the translated docs tree under `apps/docs/i18n/pt-BR/docusaurus-plugin-content-docs/current/` mirroring the **31 hand-authored** files (`00-guides/**`, `01-project/**`, `02-tools/**`, `docs/README.md`). Untranslated files fall back to English per-page, so partial is safe.
- [ ] **Exclude** `docs/content/**` (the 8 auto-generated schema `.mdx` + `content/README.md`) - they stay English-only this pass (STUDY D6); confirm they render under the pt-BR locale via fallback without a build error.
- [ ] Translate, prioritizing the guides (`00-guides/**`) then tools then project, machine-assisted + human review.
- [ ] Keep code blocks, repo-source links (`../apps`, `../packages`, `../specs`), admonition syntax, and heading-id anchors intact so the repo-links remark plugin and cross-links keep resolving.

### B3. Build verification

- [ ] `pnpm --dir apps/docs build` builds both locales clean (Docusaurus builds every declared locale); fix any pt-BR MDX/link breakage.
- [ ] `pnpm --dir apps/docs typecheck` green.
- [ ] Spot-check the locale dropdown switches en <-> pt-BR and the pt-BR search returns results.

## Track C - Close-out

- [ ] Update [gated.md](../gated.md) `i18n-locale-tables`: mark the trigger fired and the work landed under spec 072 (keep as record, per the gated convention).
- [ ] Update [decisions.md](../decisions.md) with the locked calls (canonical-English-source, per-locale module split, extraction-tooling-over-hand-author, schema-docs-excluded).
- [ ] QA Companion: add/extend the blender checklist for the "Translate Interface / pt_BR" walk; note the docs locale switch is a docs-site check, not a product walk.
- [ ] On ship, prune the `072-multilanguage-i18n/` folder per the spec lifecycle and record the summary + PR in [_index.md](../index.md). Docs/planning changes commit direct to main; the Blender addon code rides a branch + PR.

## Definition of done

- Both surfaces register a real pt-BR locale, English preserved as source/fallback, structure append-only for the next language.
- Blender: extraction + reverse-coverage test guard the table; dynamic strings wrapped; static strings translate from rows; a pt_BR interface walk passes.
- Docs: pt-BR locale declared, chrome + the 31 hand-authored pages translatable (auto-gen excluded), search localized, build + typecheck green.
- The locked calls are in `decisions.md`, the gate is marked in `gated.md`, and the QA walk is logged.
