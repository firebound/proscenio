# Blender UI/UX audit: reconcile, assess, and bucket the addon's tools

Status: **in progress - reconciliation pass first (D1 locked)**. This spec is the discovery step of the `apps/blender` UI/UX review that spec 019 opened. It designs nothing on its own: it reconciles the standing UX feedback against the shipped code, assesses every tool's current state, and sorts the findings into actionable buckets that become their own numbered specs.

## Status - reviewed 2026-06-09

Kept open: the discovery method is only partly run. Delivered and carried downstream - [`INVENTORY.md`](INVENTORY.md) and [`DESIGN-NOTES.md`](DESIGN-NOTES.md) drove spec 022 (IA restructure), spec 023 (help / docs / i18n), and spec 024 (preferences); the sprite-rigid-bind and atlas findings live in [`../backlog.md`](../backlog.md). Still open inside this spec:

- **Phase A reconciliation** - only "Cross-panel / general" tagged; ~15 areas remain under "Pending Phase A" in [`RECONCILE.md`](RECONCILE.md), much of it now overtaken by spec 022 shipping.
- **Phase B per-tool audit** - never produced; no per-tool sheets exist.
- **Buckets B + C** - cross-app per-asset PPU (Bucket B), and per-tool feature gaps (Bucket C: bone-collections management, richer bone-hierarchy editing) never spawned their own spec.

## Problem

The addon's sidebar grew tool by tool across many specs (authoring panel, slots, quick-armature, weight-paint-automesh, ...). It has never had a single holistic UX pass, and the standing feedback can no longer be trusted as a worklist.

1. **The feedback predates the code it describes.** [`backlog-ui-feedback.md`](../backlog-ui-feedback.md) was written before spec 019 (naming) and before spec 013's Skinning toolchain. So it mixes: items already shipped (the "'sprite' overloaded" rename, fully closed by spec 019 across all three apps), items about panels that were since renamed ("Active Sprite" is now "Active Element"), and it has zero coverage of the entire Skinning panel (automesh, bind, weights, edit-weights, interactive modal).
2. **A bare read re-litigates settled decisions.** Worked example: reading the "rename 'sprite'" item cold reads as open work; verifying against the enum (`ELEMENT_TYPE_ITEMS`), the models (`MeshElement` / `SpriteElement`), the Godot builders (`mesh_builder.gd` / `sprite_builder.gd`), and the PS tag parser (`kind: "mesh" | "sprite"`) shows it is done. Reconciliation has to test each item against current code AND shipped specs, not grep a string.
3. **No current map of the tools.** The UI/UX review series was deliberately sequenced naming-first (spec 019), with the panel / information-architecture work as the declared successor. That successor cannot design the grouping or the per-tool fixes without a trustworthy, current inventory of what each tool is, does, and lacks.

## What we want

- A **reconciled inventory**: every standing UX item tagged against current code + shipped specs, so the worklist reflects reality instead of history.
- A **per-tool assessment**: for each tool, what it is, the features and interactions it ships today (code-derived), and the maintainer's hands-on read of what is good, bad, and missing.
- Findings sorted into **three actionable buckets**, each of which promotes to its own numbered spec.

## Method

Three phases, gated so the slow hands-on work runs on a clean slate.

- **Phase A - Reconciliation (code-side; this spec, do first per D1).** Walk every item in [`backlog-ui-feedback.md`](../backlog-ui-feedback.md) and the UI-relevant entries in [`backlog-bugs-found.md`](../backlog-bugs-found.md). Tag each with a status (legend below) and cite file:line evidence. Output: [`RECONCILE.md`](RECONCILE.md). This kills the stale-noise problem globally before anyone opens Blender.
- **Phase B - Per-tool audit.** One sheet per tool, sidebar order. Code-side (I fill): current features + interactions. Hands-on (maintainer, in Blender, logged live): GOOD / BAD / MISSING. The Phase A `VERIFICAR` items fold into this session. Output: per-tool sheets under this folder.
- **Phase C - Bucket + spawn.** Sort the surviving items plus the new Phase B findings into the buckets below. Each bucket promotes to its own spec (022+), authored with the normal STUDY-then-TODO flow.

## Buckets

The three layers the maintainer named, mapped to deliverables.

- **Bucket A - cross-all-tools (information architecture).** Subpanel grouping + order, the version-banner nesting (every subpanel currently nests under "Pipeline v0.1.0"), the header + help-button convention, list alignment, status badges, drag-reorder. This is the panel/IA spec that spec 019 declared as its successor.
- **Bucket B - cross-app (pipeline-wide).** Concepts that span Blender + Photoshop + Godot, surfaced by the audit. Seed: per-asset PPU end-to-end (today a single global PPU).
- **Bucket C - per-tool.** Each panel's own feature and interaction gaps that do not generalize.

## Tool inventory

Sidebar order, anchored on `PROSCENIO_PT_main`. Loose operators are mapped to the panel that owns them.

| # | Tool (panel) | Owns / loose operators |
| --- | --- | --- |
| 0 | `PROSCENIO_PT_main` (root) | version banner + root help |
| 1 | Active Element | element-type body (`_draw_mesh` / `_draw_sprite`), texture region, Drive-from-Bone shortcut, Reproject UV |
| 2 | Active Slot | slot create (Path A/B), attachment add, preview shader |
| 3 | Skeleton | Quick Armature, Toggle IK, Ortho Camera, Pose Library, active-armature picker |
| 4 | Skinning | Automesh (one-shot + interactive modal), Bind, Edit Weights modal, weight snapshot/restore, copy weights, debug stages |
| 5 | Outliner | favorites, filter, select-on-click |
| 6 | Animation | action list / selector |
| 7 | Atlas | pack / apply / unpack |
| 8 | Validation | validate, select-issue |
| 9 | Export | export Godot, re-export, PPU |
| 10 | Help | help popups, status legend |
| 11 | Diagnostics | smoke test |
| - | Export-adjacent | Photoshop manifest import |

## Legend

Reconciliation status (Phase A) and hands-on tags (Phase B).

| Tag | Meaning |
| --- | --- |
| **FEITO** | Done. Cite the code / spec that closed it. |
| **REAL** | Still valid, confirmed against current code. |
| **MUDOU** | Partially addressed or the context shifted (panel renamed, sub-part shipped); the residual is restated. |
| **OBSOLETO** | No longer applies - the feature was removed or redesigned past the item. |
| **VERIFICAR** | Cannot be settled from code alone (pure runtime behavior); folds into the Phase B hands-on session. |
| GOOD / BAD / MISSING | Phase B hands-on verdict per tool. |

## Decisions

- **D1 - reconcile-first.** Run the global reconciliation pass (Phase A) before the per-tool hands-on audit, so the audit starts from a trustworthy worklist. Locked.
- **D2 - record in this spec folder.** [`backlog-ui-feedback.md`](../backlog-ui-feedback.md) stays as the source being reconciled (not deleted, not rewritten in place); the audit's structured output lives here. Locked.
- **D3 - discovery scope only.** This spec reconciles, assesses, and buckets. It changes no UI and writes no implementation. The bucket specs (022+) do the design and the work. Mirrors how spec 019 scoped itself to the rename alone.

## Open questions

- **Q1 (hands-on owner).** Phase B's GOOD/BAD/MISSING layer needs the maintainer in Blender; Phase A is code-side and proceeds solo. Confirm the Phase B cadence (one tool at a time vs a batched session).
- **Q2 (skinning depth).** The Skinning panel has no prior feedback at all and is the largest tool (5 operators + a modal). Its Phase B sheet likely needs the most time; consider splitting it from the lighter panels.

## Related

- [`../019-naming-consistency/STUDY.md`](../019-naming-consistency/STUDY.md): the first spec in this UI/UX review (naming), whose non-goal explicitly defers the panel/IA work to this successor.
- [`../backlog-ui-feedback.md`](../backlog-ui-feedback.md): the standing UX feedback this spec reconciles (the source for Phase A).
- [`../backlog-bugs-found.md`](../backlog-bugs-found.md): UI-relevant behavior bugs (panel selectors that do not drive the viewport, validator noise, orphan help) folded into the reconciliation.
- [`../backlog.md`](../backlog.md): the rolling backlog whose `Blender addon` section carries feature-level items the buckets cross-reference.
- [`../013-weight-paint-automesh/STUDY.md`](../013-weight-paint-automesh/STUDY.md): the Skinning toolchain that postdates all UX feedback and needs a from-scratch sheet.
