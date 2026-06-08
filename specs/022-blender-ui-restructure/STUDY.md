# Blender addon UI restructure: sibling panels, accordion subpanels, warn-not-hide

Status: **decisions locked, ready for TODO**. This is the information-architecture spec the spec 019 naming work declared as its successor and that the spec 021 audit prepared. It reshapes the `Proscenio` sidebar from one nested god-panel into a set of sibling top-level panels with collapsible subpanels, relocates the operators the audit found in the wrong place, renames the overloaded tools, and splits weight painting into its own panel. It is structure only: the help / doc-link / i18n system (spec 023) and the full addon preferences (spec 024) are separate, and feature-level gaps (Bucket C) are out.

The current-state baseline this spec edits against is [`../021-blender-ui-audit/INVENTORY.md`](../021-blender-ui-audit/INVENTORY.md); the decision trail (plan, critical evaluation, resolved forks) is [`../021-blender-ui-audit/DESIGN-NOTES.md`](../021-blender-ui-audit/DESIGN-NOTES.md); the interactive mockup of the target tree is [`../021-blender-ui-audit/ia-mockup.html`](../021-blender-ui-audit/ia-mockup.html).

## Problem

The sidebar grew tool by tool across many specs and never had a holistic pass. The audit (spec 021) surfaced the structural debt:

1. **One god-panel nests everything.** `PROSCENIO_PT_main` draws the version line `Pipeline v0.1.0`, and every tool is a `bl_parent_id` child of it, so all eleven tools visually indent under the version banner as if they were a submenu of the version number. Native Blender tabs (View, Item) instead hold several sibling top-level panels, each collapsible and reorderable.
2. **Contextual panels vanish, which breaks workflows.** Active Element, Active Slot, and Skinning poll on the selection and disappear when it is wrong. The worst case: you cannot select a mesh to add to a slot, because the Active Slot panel vanishes the moment you select the mesh.
3. **Operators live where the user does not look.** Create Slot is in Skeleton, the Validate button is in Export, Preview Camera and Import Photoshop are in Export, and the weight-paint brush controls are inline in Active Element.
4. **Skinning is overloaded.** Eight sub-boxes (automesh, interactive automesh, bind, edit weights, weight transfer, snapshot, sidecar IO, debug) in one panel, named "Skinning" though half of it is mesh generation. Its status badge is wrong: `skinning` is absent from `feature_status`, so the header falls back to blender-only even though Bind produces weights that export.
5. **Affordances are inconsistent.** Some sub-boxes carry a status badge and a `?`; many do not (Texture region, every Skinning box, Help, Diagnostics). The version banner owns the only root `?`.

## What we want

A sidebar where every tool is a sibling top-level panel, its internal groups are collapsible accordion subpanels (the native `View > View Lock` pattern), nothing hides on the wrong selection (it warns instead), every operator lives where its concept lives, and every panel and subpanel carries a consistent status badge plus help button. Weight painting becomes its own panel, distinct from mesh generation. The overloaded and misnamed tools are renamed to read as what they do.

## Target structure

Thirteen sibling top-level panels in the `Proscenio` category, in this default order. `iso` = an isolated selector drawn at the panel top (not inside a subpanel). `warn` = renders an inline warning instead of hiding when its context is absent. Subpanels are accordion (collapsible) children, two levels deep at most.

1. **Outliner** - promoted to first; the scene navigator. Search + favorites + the categorized object list.
2. **Element** (was Active Element) - `warn` when the active object is not a mesh/sprite. `iso` Element type selector. Subpanels: **Active Mesh / Active Sprite** (title and body swap by `element_type`; the mesh body is poly/vg count + Reproject UV + Isolated material, the sprite body is hframes/vframes/frame/centered + readout + Setup/Remove Preview), **Texture Region**, **Drive from Bone**. The old inline weight-paint box is dropped; in paint-weight mode the panel shows a warning that the element type cannot change there.
3. **Slots** (was Active Slot) - always visible. Lists every slot in the project (clickable) and the **Create Slot** button (moved from Skeleton). Subpanel: **Active Slot** (the selected slot's attachments + Add Selected Mesh).
4. **Skeleton** - `iso` project-wide Active Armature selector. Subpanels: **Armature** (indented bone hierarchy + connected / relative-parent flags, length dropped), **Pose Mode** (always visible, warns outside pose mode; Bake Pose / Toggle IK / Save Pose), **Quick Armature** (defaults + run; the no-rig bug is fixed so it creates an armature when the scene has none).
5. **Mesh Generation** (was Skinning) - `warn` when the active object is not a mesh. `iso` Interior Mode selector. Subpanels: **Automesh from Alpha** (was "from Sprite"), **Automesh Interactive** (was "authoring" / the "(modal)" button), **Debug Pipeline** (debug-gated). Bind and every weight operator move out to Weight Paint.
6. **Weight Paint** (new) - `warn`; mesh-only (`element_type == "mesh"`). Subpanels: **Bind** (moved from Skinning), **Edit Weights**, **Snapshot**, **Sidecar IO**, **Weight Transfer**. Sprites are not weight-painted; they bind rigidly to a single bone (tracked in [`../backlog.md`](../backlog.md)).
7. **Animation** - actions list.
8. **Atlas** - atlas readout + the **Atlas packer** subpanel. (Packing-feature additions are Bucket C.)
9. **Validation** - issues list + the **Validate** button (moved here from Export).
10. **Pipeline** (was Export) - subpanels **Import** (Import Photoshop Manifest) and **Export** (PPU + last path + Export + Re-export).
11. **Helpers** - **Preview Camera** (moved from Export); the home for future authoring utilities.
12. **Help** - the operator reference (the per-operator tooltips and doc links are spec 023).
13. **Diagnostics** - Run Smoke Test; debug-gated.

Footer: a slim row with `Pipeline v0.1.0`, a GitHub link, and the root `?` (moved out of the panel tree). Debug-gated panels (Diagnostics) and subpanels (Debug Pipeline) appear only when a debug flag is on.

## Design space

The forks the audit raised, with the locked verdict. Full reasoning lives in [`../021-blender-ui-audit/DESIGN-NOTES.md`](../021-blender-ui-audit/DESIGN-NOTES.md).

### Axis A - root panel

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A1.** Sibling top-level panels; no god-parent; version in a footer | Matches native tabs; panels collapse and reorder independently; kills the "submenu of the version" look | Touches every panel's `bl_parent_id` + registration | **Lock** (user choice). |
| **A2.** Keep `PROSCENIO_PT_main` as parent, just reorganize children | Smaller diff | Preserves the nesting-under-version problem the user called out | Reject. |

### Axis B - contextual panels

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **B1.** Always render; warn when the context is wrong | Discoverable; fixes the "cannot add mesh to slot" bug; one code path per panel | Each panel grows a warning branch | **Lock.** |
| **B2.** B1 plus an addon preference to re-enable hiding | Power users can hide | A toggle every panel must honor, for a need nobody has yet | Reject (YAGNI). |
| **B3.** Keep hiding | No work | The bug stays | Reject. |

### Axis C - Element subpanel depth

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **C1.** Element > {Active Mesh/Sprite, Texture Region, Drive from Bone} as sibling subpanels (two levels) | Matches native depth; each section collapses independently | Texture Region / Drive read as siblings of the type body, not children of it | **Lock** (user choice). |
| **C2.** Element > Active Element > {Texture Region, Drive} (three levels) | Strict containment | Three-level nesting is cramped in the narrow N-panel | Reject. |

### Axis D - the type body

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **D1.** Two poll-gated subpanels - **Active Mesh** (polls `element_type == "mesh"`) and **Active Sprite** (polls `"sprite"`) - so exactly one renders | Reads as the thing selected; no dead "Body" wrapper; static labels, idiomatic poll | Two subpanel classes instead of one | **Lock** (user choice). |
| **D2.** A static "Body" subpanel that swaps content | Fixed label | "Body" is a meaningless title | Reject. |

### Axis E - weight painting

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **E1.** A dedicated Weight Paint panel holding Bind + Edit + Snapshot + Sidecar IO + Transfer; Mesh Generation keeps only automesh | Two coherent tools; mesh-only poll for the weight panel | Bind moves away from the automesh that feeds it | **Lock.** Bind creates the weights you then paint, so it belongs with painting. |
| **E2.** Keep everything in one "Skinning" panel | No move | The overload the audit flagged | Reject. |

## Decisions

- **D1 (Axis A).** Flatten the root. Every tool is a top-level `Panel` in the `Proscenio` category; sections inside a tool are accordion subpanels (one `bl_parent_id` level, two levels total). The version banner moves to a footer; the root `?` rides with it.
- **D2 (Axis B).** Warn, do not hide. Element, Slots' Active Slot, Skeleton's Pose Mode, Mesh Generation, and Weight Paint render an inline warning when their context is absent. No contextual-hide preference.
- **D3 (Axis C + D).** Element panel: rename Active Element -> Element; isolated Element type selector; the type body as two poll-gated subpanels (**Active Mesh** / **Active Sprite**, one renders per `element_type`); **Texture Region** and **Drive from Bone** as sibling subpanels; drop the inline weight-paint box for a paint-mode warning.
- **D4.** Slots panel: rename Active Slot -> Slots; always visible; project slot list + **Create Slot** (moved from Skeleton); **Active Slot** as a contextual subpanel.
- **D5.** Skeleton: isolated project-wide Active Armature selector; **Armature** subpanel (hierarchy + connected / relative parent, drop length); **Pose Mode** subpanel always visible (warn outside pose); **Quick Armature** subpanel. The no-rig bug is fixed (create when the scene has no armature).
- **D6 (Axis E).** Mesh Generation: rename Skinning -> Mesh Generation; isolated Interior Mode; **Automesh from Alpha** (was "from Sprite"); **Automesh Interactive** (was authoring / modal); **Debug Pipeline** (debug-gated). Bind + all weight operators leave for Weight Paint.
- **D7 (Axis E).** Weight Paint (new): mesh-only poll; **Bind**, **Edit Weights**, **Snapshot**, **Sidecar IO**, **Weight Transfer**.
- **D8.** Outliner is the first panel.
- **D9.** Pipeline panel: rename Export -> Pipeline with **Import** and **Export** subpanels; the **Validate** button moves to the Validation panel; **Preview Camera** moves to a new **Helpers** panel.
- **D10.** Header convention: every panel and every subpanel carries the status badge + `?` (fill the gaps on Texture Region, every Mesh Generation / Weight Paint box, Help, Diagnostics). `feature_status` gains correct bands for the renamed and new panels (Element, Slots, Mesh Generation, Weight Paint, Pipeline, Helpers); the `skinning` fallback is removed. This uses the existing badge icons; the custom Godot icon, the tooltips, and the doc links are spec 023.
- **D11.** Debug gating. The Diagnostics panel and the Debug Pipeline subpanel render only when `debug_mode` is on. Phase 5 introduces a minimal `ProscenioAddonPreferences` (`bpy.types.AddonPreferences`, `bl_idname` = the addon package) carrying a single `debug_mode: BoolProperty`, registered by the addon root; spec 024 expands that preferences surface (log level, and the rest). A user-level preference, not a per-file scene flag, because debug mode is an author/developer toggle, not document state.
- **D12 (scope).** This spec is structure, relocations, renames, the new Weight Paint panel, the badge / `?` header convention, and the Quick Armature bugfix. The help-popup doc links, per-field tooltips, custom Godot badge icon, and i18n string isolation are spec 023. The addon preferences (log level, and the larger prefs surface) are spec 024. Bone-collections management and Atlas packing features are Bucket C.

## Ride-alongs

Behavior fixes that travel with the structural work because they touch the same panels:

- **Quick Armature no-rig bug.** `panels/skeleton.py` returns early with "no Armature in scene" before drawing the Quick Armature button, so the operator that creates a rig is unreachable when the scene has none. The Quick Armature subpanel must stay reachable with zero armatures.
- **Skinning badge fallback.** Adding the correct `feature_status` bands for Mesh Generation and Weight Paint removes the blender-only fallback the audit flagged.

## Phasing

Each phase is one PR, gated by the Blender gate set (ruff check, ruff format --check, mypy, repo-root `uv run pytest tests/`, the fixture suite 7/7, the operator suite, the whole-addon import sweep) plus an in-editor smoke for the panels that phase touches.

- **Phase 1 - flatten + reorder + footer.** Drop `PROSCENIO_PT_main` as the parent; panels become top-level siblings in the `Proscenio` category; the version line and root `?` move to a footer panel registered last; Outliner registers first. Panel internals unchanged. Smoke: the sidebar shows sibling panels, none nested under the version.
- **Phase 2 - renames + isolated selectors + accordion subpanels.** Element (+ Active Mesh/Sprite, Texture Region, Drive subpanels, iso type), Skeleton (Armature / Pose Mode / Quick Armature subpanels, iso armature), Mesh Generation (rename, iso Interior Mode, Automesh from Alpha / Interactive / Debug subpanels), Pipeline (rename, Import / Export subpanels). Smoke: each panel renders its accordions and the type body swaps.
- **Phase 3 - relocations.** Slots panel (project list + Create Slot moved from Skeleton + Active Slot subpanel); Validate moved to Validation; Preview Camera moved to a new Helpers panel. Smoke: add-mesh-to-slot works without the panel vanishing; Validate runs from Validation.
- **Phase 4 - Weight Paint panel.** New panel; move Bind / Edit Weights / Snapshot / Sidecar IO / Weight Transfer out of Mesh Generation; mesh-only poll; sprite rigid-bind warning. Smoke: weight panel hidden-with-warning on a sprite, full on a mesh.
- **Phase 5 - warn-not-hide + header convention + prefs flag + ride-alongs.** Warning branches on every contextual panel; status badge + `?` on every panel and subpanel; corrected `feature_status` bands; a minimal `ProscenioAddonPreferences` with `debug_mode`; debug gating on Diagnostics + Debug Pipeline; the Quick Armature no-rig fix. Smoke: panels warn instead of vanishing; every header shows a badge + `?`; toggling `debug_mode` shows or hides Diagnostics + Debug Pipeline.

## Open questions

- **Q1 (in-panel reorder expectation).** Top-level panels are user-drag-reorderable; subpanels are not (their order is registration / `bl_order`). The default order above is the shipped order; document that subpanels collapse but do not reorder, so the expectation is set.

## Non-goals

- No help-popup doc links, no per-field tooltips, no custom Godot badge icon, no i18n string isolation - spec 023.
- No addon-preferences surface beyond the minimal debug flag Q1 may land - spec 024.
- No new features: bone-collections management, Atlas packing options, richer bone-relation editing are Bucket C.
- No `.proscenio` or schema change; this is editor UI only. The writer and importer are untouched.
- No behavior change to the operators themselves beyond the Quick Armature no-rig fix and their relocation.

## Related

- [`../021-blender-ui-audit/INVENTORY.md`](../021-blender-ui-audit/INVENTORY.md): the current-state baseline this spec edits against.
- [`../021-blender-ui-audit/DESIGN-NOTES.md`](../021-blender-ui-audit/DESIGN-NOTES.md): the plan, critical evaluation, and the resolved forks behind every decision here.
- [`../021-blender-ui-audit/ia-mockup.html`](../021-blender-ui-audit/ia-mockup.html): the interactive mockup of the target tree.
- [`../019-naming-consistency/STUDY.md`](../019-naming-consistency/STUDY.md): the naming work that opened this UI/UX series and sequenced this spec after it.
- [`../backlog.md`](../backlog.md): the sprite rigid single-bone bind entry (Weight Paint is mesh-only) and the Bucket C features this spec defers.
- Successors: spec 023 (help + docs + i18n) and spec 024 (addon preferences).
