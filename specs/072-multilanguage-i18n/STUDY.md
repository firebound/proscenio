# Spec 072: Multilanguage i18n (docs + Blender addon, first locale pt-BR)

Make the product speak more than one language. Two surfaces carry user-facing text: the Docusaurus documentation site (`docs/`) and the Blender addon's editor UI (`apps/blender/`). Both already have the i18n *mechanism* in place but neither has a single non-English string registered. This spec fires the gated `i18n-locale-tables` item ([gated.md](../gated.md)) - its copy-churn prerequisite was met by spec 064, and the request for Brazilian Portuguese is the trigger. The English strings stay as the canonical source on both surfaces; pt-BR is added as the first translated locale, and both systems are left structured so a second language is append-only.

This is a translation-*enablement* spec, not a translate-everything spec. The engineering deliverable is: the wiring, the extraction/maintenance tooling, the locale scaffolding, the drift guards, and a complete first pt-BR pass. The ongoing per-string translation copy is a content task that rides on top of the structure this lands.

## Why now

- The user (Brazilian, Space Wizard Studios) asked for Portuguese and explicitly wants the result to be multilanguage, with English preserved.
- Spec 064 already routed every Blender help-topic body through `core/i18n.py` `iface()` under a per-topic context, so the bulk of the multi-line copy is translation-stable - no second copy pass is needed to localize it.
- Docusaurus 3.10 ships native i18n; the config already declares an `i18n` block (`locales: ['en']`) and the `write-translations` script already exists in [apps/docs/package.json](../../apps/docs/package.json). Nothing structural blocks adding a locale.

## Current state

### Blender addon

- [apps/blender/core/i18n.py](../../apps/blender/core/i18n.py) registers Blender's `bpy.app.translations` table under the addon key at register time. `TRANSLATIONS` is an empty tuple; `iface(msgid, msgctxt)` wraps `pgettext_iface` for draw-time strings. The module docstring already documents the "append rows to grow a locale" model.
- Two string classes exist:
  - **Static** - `bl_label`, `bl_description`, property `name` / `description`, enum item labels. Blender auto-translates these from the registered table whenever "Translate Interface" is on and a `(msgctxt, msgid)` entry exists. No call-site change needed; they only need table rows.
  - **Dynamic** - strings assembled at draw time (f-strings, computed `layout.label(text=...)`, `report_info/warn/error` message arguments in [core/_shared/report.py](../../apps/blender/core/_shared/report.py) call sites). These translate only if looked up through `iface()` first. Today only the help-topic bodies (spec 064) go through `iface()`; the rest are raw literals.
- Rough scale (from a read-only audit): ~570 distinct user-facing strings - ~50 operator labels, ~280 property `name`/`description`, ~100 enum item labels, ~100 inline `layout.label()`, ~50 report messages. Concentrated in `properties/` (~280), `panels/` (~150-200), `operators/` (~100-120), `core/_shared/report.py` call sites (~50).

### Docs (Docusaurus 3.10.1)

- Site app: [apps/docs/](../../apps/docs/); content served from repo-root `docs/` (`path: '../../docs'`, `routeBasePath: '/'`).
- `i18n: { defaultLocale: 'en', locales: ['en'] }` in [docusaurus.config.ts](../../apps/docs/docusaurus.config.ts:56). No `i18n/` directory, no translated content.
- Content inventory (from `docs/**/*.{md,mdx}`):
  - **31 hand-authored files** (~25k words): `00-guides/**` (11), `01-project/**` (4), `02-tools/**` (13 incl. blender-addon 01-11, photoshop-plugin, godot-plugin, the index pages), `docs/README.md`.
  - **8 auto-generated files**: `docs/content/**` (the proscenio + psd-manifest schema reference `.mdx` plus `content/README.md`), emitted by `proscenio_codegen all` from the JSON schemas. **Excluded from this pass** per the request.
- Theme/chrome strings (navbar `Guides`/`Project`/`Tools`/`GitHub`, footer titles + link labels, copyright, sidebar category labels, plus Docusaurus's own UI strings) are translated through the `i18n/<locale>/` JSON files that `write-translations` generates.
- Search: `@easyops-cn/docusaurus-search-local` is configured single-language. It supports a `language` array (lunr stemmers, `pt` included) - needs per-locale indexing wired or pt-BR search degrades.

## Decisions

| # | Question | Call |
|---|----------|------|
| D1 | Which language, and what stays canonical | Brazilian Portuguese. English remains the default locale and the msgid source on both surfaces (nothing English is moved or deleted). Locale codes differ by tool: Blender `pt_BR`, Docusaurus `pt-BR` (BCP-47). |
| D2 | One language or a multilanguage frame | Multilanguage. Both systems are N-locale capable already; pt-BR is added as the first non-English locale and the structure stays append-only so a second language is data + content, not re-architecture. |
| D3 | How Blender msgids are extracted and kept from drifting | Build a small repo script that walks the addon source and collects translatable msgids (static: `bl_label`/`bl_description`/property `name`+`description`/enum items; dynamic: `iface()` args, `layout.label(text=...)`, `report_*` args), emits a catalog template, and backs a reverse-coverage test (spec 064 / spec 036 help-topic precedent) that fails if a registered msgid no longer exists in source or a new translatable string is unregistered. Hand-authoring ~570 rows is rejected - it drifts on the first copy change. |
| D4 | Where the Blender locale tables live | Split per-locale tables out of `i18n.py` into a `core/i18n_locales/` package (one module per locale, e.g. `pt_BR.py`); `i18n.py` stays the thin assembler that folds them into the `{locale: {(ctxt, msgid): msgstr}}` dict. Keeps `i18n.py` readable and makes "add a language" = add a file. |
| D5 | Dynamic-string wrapping scope | Wrap the dynamic call sites (`layout.label(text=...)`, computed labels, `report_*` message args) with `iface()` so they resolve against the table. The `Proscenio: ` / `[Proscenio debug] ` prefixes in `report.py` stay outside the translated msgid (prefix the *translated* message). Static strings get zero code change - rows only. |
| D6 | Auto-generated schema docs | Excluded this pass. `docs/content/**` regenerates from schemas; localizing it needs a locale-aware codegen pass, logged as a follow-on (see Out of scope / gated). The site still builds with those pages English-only under a pt-BR locale. |
| D7 | Docs search under a second locale | Wire `@easyops-cn/docusaurus-search-local` `language: ['en', 'pt']` so pt-BR pages are indexed with the Portuguese stemmer. |
| D8 | Build/CI | Docs: `docusaurus build` builds every declared locale - the existing build/typecheck check covers regressions once pt-BR is declared. Blender: a headless test that the table registers, folds, and round-trips a sample `(ctxt, msgid) -> msgstr`, plus the D3 reverse-coverage guard. |
| D9 | Who produces the pt-BR copy | Machine-assisted first pass + human review by the team (the user is a native pt-BR speaker). This is a content dependency, not an engineering blocker; the structure ships regardless of how much copy is done. PT-BR orthography rules apply (full accents; aportuguesamento of EN technical terms acceptable but not preferred). |

## Open calls (confirm before TODO execution)

- **D3 tooling vs hand-author** - recommend tooling. If the team would rather hand-curate a smaller high-value subset first (panel labels + report messages only, deferring property descriptions), that is a smaller TODO; flag if preferred.
- **Translation completeness bar for v1** - does pt-BR need 100% coverage to ship, or is partial acceptable (Blender shows English for any unregistered msgid; Docusaurus falls back per-string to English)? Recommend: ship the structure + chrome + guides at 100%, allow per-string fallback for the long tail, track the gap.

## Out of scope / follow-ons

- **Localized schema-reference docs** - `docs/content/**` codegen would need a locale-aware emit. Gated until pt-BR demand for the schema pages is real.
- **Third+ languages** - the structure supports them; each is a new locale file (Blender) + `i18n/<locale>/` tree (docs) + a content pass. Not built here.
- **Addon screenshots / docs captures** - already gated (`addon-docs-screenshots`); localized captures inherit that gate.
- **In-product locale picker beyond Blender's native "Translate Interface" toggle and Docusaurus's locale dropdown** - both ship native switchers; no custom UI.

## Sources

- Fires the gated `i18n-locale-tables` item ([gated.md](../gated.md)); its copy-churn prerequisite was satisfied by spec 064 ([_index.md](../_index.md) row 064).
- Mechanism precedent: spec 023 (i18n mechanism), spec 064 (help bodies routed through `iface()` under per-topic context).
- Reverse-coverage-test precedent: spec 036 / spec 064 (`_DOC_PATHS` mirror, help-topic reverse coverage).
