# SPEC 005 — Blender authoring panel

Status: **draft**, design phase. Implementation pending decision lock-in on the open questions below.

## Problem

The Blender side of Proscenio ships as a writer + a stub sidebar with two buttons: "Hello Proscenio" (smoke test) and "Export Proscenio". Everything else is **raw Custom Properties on the active object**:

- `proscenio_type = "sprite_frame"`
- `proscenio_hframes = 4`
- `proscenio_vframes = 1`
- `proscenio_frame = 0`
- `proscenio_centered = true`

Setting up a single `sprite_frame` sprite means typing five property keys exactly right, in a panel buried under Object Properties → Custom Properties. Skinning weights are authored through Blender's native vertex-group + weight-paint tooling (already good), but the user has no addon-side feedback that "this mesh has groups but they don't match any bone" until the exporter raises a `RuntimeError`. Validation happens at the worst possible moment — on export.

Real authoring iteration needs:

1. A **dedicated panel** in a discoverable place that surfaces every Proscenio-relevant knob for the active object.
2. **Typed widgets** instead of free-form Custom Property strings — a dropdown for sprite type, integer fields for `hframes`/`vframes`, a checkbox for `centered`.
3. **Inline validation** — red text or icons on rows that would break the export, before the user clicks Export.
4. **Sticky export path** — the file dialog is fine for first-export-of-a-document but punishes every subsequent iteration; the panel should remember where this `.blend` was last exported and one-click re-export there.
5. **Foundation for SPEC 004** — slots will need a list editor and default picker; the panel infrastructure built here should accommodate that without rework.

The goal of SPEC 005 is the panel, not every authoring helper imaginable. Atlas region helpers, ortho camera previewers, weight-painting visualizers stay in backlog and feed into 005.1 when real demand surfaces.

## Reference: COA Tools 2 + wider survey

The user explicitly named the [COA Tools 2 Blender panel](https://github.com/Aodaruma/coa_tools2) as the spiritual model:

- Sidebar tab on the 3D Viewport.
- Per-active-object section with inline widgets for sprite-relevant fields.
- Buttons for common operations (export, duplicate, attach, etc).

We are not porting any code from `coa_tools2` — we adopt the *shape* of the UX, not the implementation.

A wider survey of the field — Spine, DragonBones, Live2D Cubism, Spriter, DUIK Ángela / Joysticks 'n Sliders, plus Blender-native and addon tooling — lives in [`RESEARCH.md`](RESEARCH.md). The addendum classifies each observed feature as **first cut**, **5.1**, **SPEC 004**, **future**, or **out of scope** so the panel layout that ships with this SPEC has its long-term shape on record. The matrix at the end of `RESEARCH.md` is the practical takeaway.

## Constraints

- **Plugin runs at editor time only** (current rule). The panel is `bpy.types.Panel` code; it has access to the full `bpy` API at draw time.
- **Schema is authoritative.** Every widget maps to a schema field (or an authoring property the writer reads). Adding a widget for something the writer ignores is a bug.
- **Coexistence with raw Custom Properties.** Power users may still edit raw if they want — the panel must round-trip cleanly with manual edits. SPEC 005 does not break the current authoring contract; it adds a UI layer over it.
- **Strict typing.** PropertyGroup definitions use Blender's typed properties (`EnumProperty`, `IntProperty`, `BoolProperty`); no free-form `StringProperty` for things that have a closed value set.
- **No new format features.** SPEC 005 is purely UX — the `.proscenio` shape does not change. Schema bump = nope.

## Design surface

### Layout

The current addon ships `PROSCENIO_PT_main` in the 3D View N-key sidebar under a "Proscenio" tab. SPEC 005 keeps that anchor and adds **subpanels** under it:

```text
N-key sidebar
└── Proscenio tab
    ├── Active sprite (subpanel — visible when a mesh is selected)
    │   ├── Sprite type dropdown (polygon | sprite_frame)
    │   ├── [if sprite_frame] hframes / vframes / frame / centered
    │   ├── [if polygon] vertex-group summary (read-only count)
    │   └── inline validation hints
    ├── Skeleton (subpanel — visible when an armature is selected or in scene)
    │   └── (placeholder — bone count + warning if no armature)
    ├── Slots (subpanel — placeholder for SPEC 004)
    │   └── (renders only after SPEC 004 lands)
    └── Export (subpanel — always visible)
        ├── Last export path (sticky)
        ├── Pixels-per-unit field
        ├── [Validate] button (dry-run, surfaces issues without writing)
        └── [Export] button (uses sticky path, falls back to file dialog)
```

The layout has room to grow — atlas region helpers, ortho preview, weight-painting toggles can all dock as new subpanels later.

### Property model

A single `PropertyGroup` per attachable surface — primarily on `bpy.types.Object` for sprite metadata. The PropertyGroup mirrors the current Custom Properties one-to-one; the panel writes through it transparently. Writer-side reads stay the same (`obj.get("proscenio_type", "polygon")`) so legacy `.blend` files using raw Custom Properties continue to export without migration.

A second PropertyGroup attaches to `bpy.types.Scene` for export-level settings:

- `proscenio_last_export_path: StringProperty(subtype="FILE_PATH")`
- `proscenio_pixels_per_unit: FloatProperty(default=100.0)`

### Validation strategy

Two parallel paths:

1. **Inline (every redraw of the panel).** Cheap structural checks: required fields present, value ranges sane, sprite type matches mesh shape. Surfaced as red text + icon next to the offending row.
2. **Lazy (Validate button + Export button).** Full check including bone-name resolution against the armature, vertex-group sanity, atlas existence. Reports through a popup or a console block; gates the Export button when a hard error is found.

The schema validator (`check-jsonschema`) is **not** invoked from inside Blender — that runs in CI and in the test runner. The panel's validation is structural-and-semantic, not schema-formal.

## Design decisions to lock

### D1 — Panel anchor

Where does the panel live?

- **D1.A — 3D View N-key sidebar (current location).** Extends `PROSCENIO_PT_main`.
- **D1.B — Properties Editor → Object Properties subpanel.** Shows when the active object is selected.
- **D1.C — Both A and B.**

**Recommendation: D1.A.** The current addon already lives there; users find it via the same N-key shortcut they use for the rest of Blender's add-on ecosystem. The Properties Editor placement is a backlog item if real demand surfaces; doing both creates two sources of truth for the same UI state.

### D2 — Custom Properties: replace, wrap, or pure-UI?

Current authoring contract is raw Custom Properties on the Object. The panel is new; what does it do to existing data?

- **D2.A — Wrap.** PropertyGroup mirrors Custom Properties; both stay in sync. Power users can edit raw, panel users go through the dropdowns.
- **D2.B — Replace.** Panel writes its own data structure; Custom Properties become deprecated. Migration script needed.
- **D2.C — Pure UI.** PropertyGroup is the only source; Custom Properties are removed entirely from the contract.

**Recommendation: D2.A.** No data migration. No breakage for users mid-project. The writer continues to read via `obj.get("proscenio_type", "polygon")`. The PropertyGroup's `update` callback writes the same Custom Property the user would type by hand, and the panel reads from it.

### D3 — Validation timing

- **D3.A — Inline only.** Every panel redraw runs cheap checks; expensive checks (atlas exists on disk, all vertex groups resolve) deferred until export.
- **D3.B — Lazy only (Validate button).** No redraw cost; user must click to learn anything.
- **D3.C — Both — inline cheap, lazy expensive.**

**Recommendation: D3.C.** Inline catches the obvious mistakes (missing `hframes` on a `sprite_frame` sprite) at zero ceremony; lazy covers the I/O-touching checks. Each lives where its cost is paid.

### D4 — Severity levels

- **D4.A — Error / warning only.** Errors block export, warnings inform.
- **D4.B — Error / warning / info.** Info for non-actionable observations.

**Recommendation: D4.A.** Two levels are easier to reason about. Info-level rows clutter the panel for marginal value.

### D5 — Sticky export path scope

- **D5.A — Per-document.** Stored on `bpy.types.Scene`'s PropertyGroup; saved with the `.blend`.
- **D5.B — Per-Blender-session.** Stored in addon prefs; resets on Blender restart.
- **D5.C — Per-user-default + per-document override.** Power-user setting.

**Recommendation: D5.A.** Authoring is document-centric. The `.blend` is the "project" artifact and carries the export destination. Restarts of Blender preserve the path. Per-user-default is a backlog feature.

### D6 — Validate button output channel

When the user clicks Validate, where do issues appear?

- **D6.A — Toast + console.** Blender's `self.report` shows a one-line popup; full details go to the system console.
- **D6.B — Dedicated panel section that lists issues.** Persistent until next Validate run.
- **D6.C — Both — toast for last result, panel section for full list.**

**Recommendation: D6.B.** The panel section is the authoring tool; ephemeral toasts disappear. Every issue gets a click-target ("Select offending object") in a future polish round.

### D7 — Slots subpanel: stub or skip?

SPEC 004 is the slot system. Should SPEC 005 ship a stub Slots subpanel now?

- **D7.A — Stub it.** Empty subpanel with "SPEC 004 — slot system not yet implemented" message. Reserves the layout slot.
- **D7.B — Skip.** Add the subpanel only when SPEC 004 lands.

**Recommendation: D7.B.** Stub UI is noise. SPEC 004 will introduce its own subpanel as part of its implementation. SPEC 005 panel infrastructure makes this trivial — one new `Panel` subclass with the right `bl_parent_id`.

### D8 — Atlas region helper, ortho camera helper, vertex-group inspector

These are common COA-Tools-style panel features that user productivity benefits from but are scope creep for first-cut SPEC 005.

- **D8.A — All in 005.** Big, slow first ship.
- **D8.B — None in 005.** First-cut panel ships with sprite type + export only.
- **D8.C — Vertex-group inspector in 005 (read-only count + warning), atlas + ortho helpers in 005.1.**

**Recommendation: D8.C.** The vertex-group summary is essentially free — read-only data display, no write logic. Atlas region snapping and ortho preview deserve their own Q&D pass; defer.

## Out of scope (deferred to 005.1 or backlog)

- Atlas region authoring helper (button: "Snap UV bounds → texture_region rectangle").
- Camera ortho preview helper (matches `pixels_per_unit`).
- Vertex weight visualization (color-by-dominant-bone overlay).
- Skinning toggle / preset (e.g. "rigid attach", "fully weighted to active bone").
- Drag-and-drop attachment ordering (SPEC 004 territory).
- Per-user default export-path preference (D5).
- Properties Editor placement (D1).
- A "Reset to defaults" button per subpanel.

## Successor considerations

- SPEC 004 (slots) plugs in as a Slots subpanel under the same `PROSCENIO_PT_main` parent. Property model, validation framework, and the "selected-object subpanel" pattern carry over.
- A future SPEC for "live link Blender ↔ Godot" (backlog) would dock as a Live Link subpanel.
- Atlas region helper (out-of-scope above) becomes a sub-feature of the Active sprite subpanel, not a standalone tool.
- Localization: every label currently English. If the project ever localizes, the panel becomes the largest string surface — keep `i18n_id` discipline from day one (Blender's translation API).
