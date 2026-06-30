# Spec 073 STUDY: Edit Weights panel cheatsheet mirror

## Why

The repo codified a reusable interactive-tool gesture cheatsheet pattern (spec 069): a modal's status-bar chords are also mirrored on its N-panel in a collapsible section, gated on the modal being live. Quick Armature, Automesh Authoring, and Manual Mesh (spec 070) all carry both the status-bar cheatsheet and the panel mirror. **Edit Weights** is the last interactive tool with only the status-bar half - no panel mirror. This closes the `interactive-cheatsheet-cross-tool` backlog item so the pattern is uniform across every interactive tool.

## Scope

One quick-win: add the panel mirror to the Edit Weights subpanel, matching the canonical pattern. No behavior change to the modal itself.

- The Edit Weights modal (`PROSCENIO_OT_edit_weights_modal`) already appends a status-bar draw (`_draw_statusbar_edit_weights`) and tracks a live flag (`_statusbar_appended`). Its chords: ESC exit, and the mirror-source read-out (`mirror = target.proscenio_mirror_x`).
- The status-bar draw currently builds raw rows in the old split-icon/text style the convention warns against; fold it onto the shared `chord` primitive so the status bar and the mirror render identically.

## Decision (locked)

- **Extract the chord vocabulary into `operators/skinning/_status_bar.py`** (`emit_edit_weights_chords(layout)`), mirroring `operators/armature/_status_bar.py` and `operators/automesh/_status_bar.py` - the operator owns the registered header callback, the module owns the chord vocabulary. The status-bar draw and the panel mirror both call it.
- **Mirror gated on `_statusbar_appended`** (the operator class flag), drawn in a `layout.panel("proscenio_edit_weights_shortcuts", default_closed=True)` section on the Edit Weights subpanel - the convention's `_statusbar_appended` gate, not an `is_running` helper (Edit Weights has none).
- No new test: the cheatsheet emitters are UI-draw helpers with no unit coverage today (Quick Armature / Automesh / Manual Mesh mirrors have none either); coverage is the in-Blender operator suite exercising the modal.

## Code anchors

- `apps/blender/operators/skinning/edit_weights.py` - `_draw_statusbar_edit_weights`, `_statusbar_appended`.
- `apps/blender/operators/_status_bar.py` - the shared `chord` primitive.
- `apps/blender/panels/weight_paint.py` - `PROSCENIO_PT_edit_weights.draw`.
- `apps/blender/panels/mesh_generation.py` `_draw_manual_draw_cheatsheet`, `panels/skeleton.py` `_draw_quick_armature_shortcuts` - the sibling mirrors to match.
- `.ai/conventions/code.md` "Interactive-tool gesture cheatsheet" - the canonical pattern.

## Open items

None - the pattern and the gate are settled; this is a uniformity fill.
