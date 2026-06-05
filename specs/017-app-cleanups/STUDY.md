# App cleanups: Godot dedup, docs tidy

Status: **draft, pending review**. Decisions D1-D5 proposed; judgment call Q1 flagged with a lean. Collects the localized cleanup findings from the four-app organization audit for Godot and the docs site - the two apps that passed the structural audit as "Good" and need only bounded fixes. The Blender addon's system reorganization is [spec 016](../016-blender-app-system-organization/STUDY.md); the Photoshop plugin's web-app re-layout is [spec 018](../018-photoshop-web-app-layout/STUDY.md). This spec is deliberately not structural.

## Problem

The organization audit found Godot and docs structurally healthy: clean separation, single-responsibility files, self-explanatory locations. What it did find was a short list of localized issues - concrete duplication to consolidate, dead comments, and naming. None is a reorganization; each is a bounded fix. This spec gathers them so they have a tracked home and a size-appropriate plan rather than a restructure they do not need.

## Scope and non-goals

In scope: dedup into existing canonical homes, fixing stale comments, naming, and dropping dead assets, grouped by app. Out of scope: any structural reorganization (these apps passed); Photoshop (spec 018) and Blender (spec 016); behavior change; schema or `format_version` change. Each phase is behavior-preserving and proven by that app's existing gates.

## Findings and plan

Severity is the audit's. Location citations are `file:line` from the audit reads.

### Godot (`apps/godot/addons/proscenio/builders/`)

| Location | Issue | Severity | Fix |
| --- | --- | --- | --- |
| `polygon_builder.gd:8-29` vs `sprite_frame_builder.gd:12-29` | `_resolve_sprite_texture` duplicated verbatim (the second even comments "Mirror of polygon_builder._resolve_sprite_texture") | Med | Extract a shared `resolve_sprite_texture(...)` both builders call |
| `polygon_builder.gd:118-131` vs `sprite_frame_builder.gd:92-105` | Slot-routing parent-resolution block near-identical (slot_map lookup -> visibility, else bone-or-skeleton fallback) | Med | Extract a shared `resolve_sprite_parent(...)`; polygon's `is_skinned` branch stays in the caller |
| `slot_builder.gd:32-33` | `SlotBuilder.sanitize` is a pass-through shim over `NodeNameUtil.sanitize`; `animation_builder.gd:43,158` call the shim while the sprite builders call `NodeNameUtil` directly - two names for one function | Low | Point `animation_builder.gd` at `NodeNameUtil.sanitize`; drop the shim |
| `animation_builder.gd:120-123` | Comment claims cubic interpolation but code defaults to LINEAR, upgrading to CUBIC only for transform channels | Low | Reword the comment to match the code |
| `animation_builder.gd:142-144` | Dangling `#.` comment fragment | Low | Remove the stray line |

### Docs (`apps/docs/`)

| Location | Issue | Severity | Fix |
| --- | --- | --- | --- |
| `static/img/undraw_docusaurus_{mountain,react,tree}.svg`, `static/img/docusaurus.png` | Leftover Docusaurus starter assets; zero references anywhere | Low | Delete the four files (keep `favicon.ico`, `logo.svg`, `docusaurus-social-card.jpg` - the social card is still referenced) |
| `src/schema/withDefs.ts` | camelCase filename; layout.md reserves `kebab-case.ts` for modules | Low | Rename to `with-defs.ts`; update the 6 `@site/src/schema/withDefs` imports under `docs/content/**` (the exported function `withDefs` keeps its name) |

## Decisions (proposed)

- **D1.** Scope is localized cleanups only - dedup into existing canonical homes, fix stale comments, drop dead assets, fix naming. No structural reorganization; these two apps passed the structural audit.
- **D2.** Group by app; each app is an independent phase and PR.
- **D3 (Godot).** Extract the two duplicated builder blocks into shared helpers callable by both sprite builders; collapse the `SlotBuilder.sanitize` shim onto `NodeNameUtil.sanitize`.
- **D4 (Docs).** Delete the four unused starter assets; rename `withDefs.ts` to `with-defs.ts`.
- **D5 (explicit non-action).** Leave the Godot `reimporter.gd` empty Phase-2 stub in place: a harmless placeholder, not worth a churn. Recorded so a reviewer does not delete it reflexively.

## Judgment calls

Proceeding on the lean unless overridden in review.

- **Q1 (Godot `reimporter.gd`).** Empty `@tool extends RefCounted` Phase-2 placeholder. Lean: keep in place (harmless); optionally add a one-line backlog pointer. Alternative: move the intent to backlog and delete the stub.

## Related

- [system-organization spec](../016-blender-app-system-organization/STUDY.md): the Blender structural counterpart.
- [photoshop web-app layout](../018-photoshop-web-app-layout/STUDY.md): the Photoshop structural counterpart (its cleanup findings are absorbed into that move).
- [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md): GDScript typing, no-premature-abstraction.
- [`../../.ai/conventions/layout.md`](../../.ai/conventions/layout.md): file naming.
