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

## Architectural patterns + tradeoffs

These patterns surfaced during 005 + 005.1.x implementation. Captured here so successor SPECs (004 slots, 005.1.c.2 packer, 006 Photoshop importer) can reuse them without re-deriving the rationale.

### PropertyGroup canonical, Custom Property as legacy mirror

PropertyGroup is the editor-side source of truth — typed, validated, surfaced in panels. Custom Properties (`proscenio_type`, `proscenio_hframes`, etc.) are legacy fallback so `.blend` files authored before SPEC 005 still load cleanly. Writer reads PropertyGroup-first, Custom Property as fallback. Hydration on `load_post` + script-reload copies CPs back into PG.

**Tradeoff.** Requires a one-way mirror (PG → CP) on every PG edit, plus complete-snapshot semantics (every field, not just the touched one). Editing a CP directly does **not** update the PG until the next reload. Documented as expected behavior; users who want bidirectional must edit through the panel.

**Why not drop CPs entirely.** Pre-SPEC-005 fixtures (and any user `.blend` from before 2026-05-04) have CPs and no PG. Deleting CP support would make those files break silently — sprite_type defaults to polygon, frame counts reset, etc. Cost of keeping the fallback is one `getattr(props, field, default)` call per field per export. Negligible.

### Mirror-all on any update + `save_pre` handler

Per-field PropertyGroup update callbacks only fire when the user actually edits that field. Defaults never trigger a callback, so a partial CP set was the norm in early 005.1.c.1. Reload Scripts then rehydrated PG from incomplete CPs and lost untouched fields.

**Fix pattern.** All field update callbacks delegate to `mirror_all_fields(props, obj)` (in `core/mirror.py`) which writes the entire 10-field map. A `@bpy.app.handlers.persistent save_pre` handler additionally walks every object in `bpy.data.objects` and flushes PG → CP before the `.blend` is saved, covering the case where values were authored programmatically without going through the panel.

**Tradeoff.** 10 dict writes per panel edit instead of 1. Sub-microsecond cost; user does not perceive it. `save_pre` walks every object on every save — O(N) where N is the scene's object count. For ~100 objects it's <1 ms; not a concern.

### Timer-deferred hydration

PropertyGroup wiring is **not** stable when `register()` returns. Setting PG fields inline writes to a transient stub that gets dropped before the data block is committed.

**Fix pattern.** `bpy.app.timers.register(hydrate, first_interval=0.0)` schedules hydration for the next event tick. Plus a `@bpy.app.handlers.persistent load_post` handler covers `.blend` opens after register has already run.

**Tradeoff.** First panel render of a freshly-opened `.blend` may show defaults for one tick before hydration fires. Imperceptible (sub-frame). The alternative — synchronous hydration in register — silently loses data on first load.

### Core extracted bpy-free

Logic that does not strictly require Blender (validation, region resolution, hydration, mirror) lives under `blender-addon/core/` and imports zero `bpy`. Tests under `tests/` import these modules directly via `sys.path` munging and exercise them with `SimpleNamespace` mocks.

**Tradeoff.** Slightly awkward import shape — `from ...core import region as region_core` from `exporters/godot/writer.py` (3-dot relative). Plus `# type: ignore[import-not-found]` on relative imports because mypy with the addon-as-non-package setup gets confused. In exchange, every meaningful code path runs in `pytest` without spinning up Blender. CI lint-python runs in <1 second instead of needing the test-blender headless job to validate the logic.

### Mode-aware subpanel polls

Each child panel of `PROSCENIO_PT_main` defines `poll(cls, context)` filtering by `context.mode`. Active Sprite hides outside object/edit-mesh/weight-paint/vertex-paint. Skeleton hides outside object/pose/edit-armature. Sidebar stops cluttering with subpanels that can't do anything in the active mode.

**Tradeoff.** User entering an unexpected mode loses access to features they expect. Mitigated by keeping the parent banner always visible — the subpanel disappears, not the whole tab. Documented intent: "subpanel polls true only if its operations are valid in the active mode."

### Marker-based toggle pattern

`PROSCENIO_OT_toggle_ik_chain` stamps a constraint named exactly `Proscenio IK`. Toggle removes it by name. Constraints with any other name (user-authored, third-party addon) are left untouched.

**Tradeoff.** Renaming our constraint manually breaks the toggle behavior — second click adds another instead of removing. Documented in the operator's `bl_description`.

**Reusable.** Same pattern for any add/remove operator that should not stomp user state: pick a marker name, only act on objects matching it. SPEC 004 slot system can reuse for slot-attachment shortcuts.

### Two-stage destructive operators

5.1.c.2 (atlas packer) splits the destructive flow: `pack_atlas` generates `atlas_packed.png` next to the `.blend` without touching materials; `apply_packed_atlas` is a separate button that rewrites UVs and relinks materials.

**Tradeoff.** Two clicks instead of one. In exchange, an accidental click does not destroy hand-tuned UVs. Pattern reusable for any operator whose effect is irreversible without source backup.

### Vendor over pip

Atlas packer (5.1.c.2) ships a vendored MaxRects implementation (`core/atlas_packer.py`, ~150 LOC, zero deps) instead of adding `pytexturepacker` to `pyproject.toml`.

**Why.** `pip install` inside Blender's bundled Python is fragile cross-platform: paths differ Win/Mac/Linux, permissions vary, future Blender 6 may break ABI. Single-file pure-Python is portable, auditable, offline-installable.

**Tradeoff.** ~150 LOC of code we own and must maintain. Acceptable: bin-packing is a stable algorithm, MaxRects has decades of literature, no security surface.

### F3-searchable label prefix

All operators prefix `bl_label` with `Proscenio:` so Blender's F3 search matches the addon namespace. Cheat-sheet panel still shows the raw idname for power users who want to wire keymaps.

**Tradeoff.** Labels are 11 characters longer in any context that uses them (search popup, keymap editor, operator history). Inside the Proscenio sidebar the panel buttons override `text=` to drop the prefix and show the short label only.

### Weight paint inline brush only for polygon

`sprite_frame` meshes render as Sprite2D in Godot — no Polygon2D.skeleton, no per-vertex bone weights. Weight painting on a sprite_frame mesh has no export effect. Active Sprite panel acknowledges this with an info hint when the user enters PAINT_WEIGHT mode on a sprite_frame mesh, instead of silently showing the polygon weight controls.

**Tradeoff.** Inconsistency between sprite kinds — polygon meshes get the brush controls inline, sprite_frame meshes don't. Mitigated by the explicit "(Sprite2D is not deformed by bones)" hint so the user understands the why.

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
