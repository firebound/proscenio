# Spec 050: Blender authoring design decisions

Five authoring-side questions that surfaced alongside the [spec 049](../049-blender-ui-polish/STUDY.md) polish batch but cannot be coded until a design call is made. Each is framed below with its code anchors, concrete options, a recommendation, and the locked decision it must respect. **This spec is STUDY-first: it pauses here for the decisions. The TODO is written once each call is locked** - per item the implementation is small-to-medium, so the cost is the decision, not the code.

How to use this file: read each question, pick an option (or amend), and record the call. The chosen calls then move to [`decisions.md`](../decisions.md) and the implementable rows become [TODO.md](TODO.md).

## Scope

- **sprite-centered-vs-origin** - should `centered` derive from the imported PS `[origin]` tag, or stay a manual toggle?
- **qa-quickarm-interaction-revision** - the Quick Armature modal chords are saturated and unintuitive; what scheme replaces them, and where does viewport pick-parent fit?
- **qa-rotation-mode** - expose Euler vs quaternion authoring choice; how to keep a rotation-mode swap from silently breaking driven animations?
- **proscenio-y-depth-layers** - controllable Y depth to avoid plane z-fighting after import; auto from PS order or manual, and does it touch the schema?
- **incorporate-blender-mesh-as-element** - a button to adopt a hand-authored Blender mesh into the flow; what does it set and what are the preconditions?

## Open decisions

### 1. sprite-centered-vs-origin

**Code anchors:** `properties/object_props.py` (`centered` BoolProperty, sprite-only, default True); `exporters/godot/writer/sprites.py` (reads `centered`, also derives `Sprite2D.offset` from quad-bounds-vs-origin); `importers/photoshop/planes.py` (hardcodes `centered=True` on import, ignores PS origin); `packages/models/src/proscenio_models/psd_manifest.py` (`SpriteLayer.origin` from the `[origin:x,y]` tag).

**Question:** `centered` (manual bool) and the PS `[origin]` tag both concern where the sprite sits relative to its pivot, but they are disconnected - import ignores the tag and the user re-toggles by hand.

**Options:**
- **(A) Keep manual toggle.** No import coupling, two mental models persist.
- **(B) Derive from PS origin on import, with a manual override field.** Honors the authored intent by default; adds one override field.
- **(C) Compute at export from geometry, drop the field.** Pure derived appearance; no UI control, no way to force an intent that differs from geometry.

**Recommendation:** **(C) or (B).** `decisions.md` "Sprite appearance and orientation" locks that *appearance is derived from native Blender state, never new authoring props* and already derives `offset` from quad-bounds-vs-origin - which points at (C). (B) is friendlier (a visible toggle) but adds an authoring prop, mildly against that rule. **Decide (B) vs (C) by re-reading that locked rationale.** Size **S** either way.

### 2. qa-quickarm-interaction-revision

**Code anchors:** `operators/armature/quick_armature.py` (modal; `resolve_press_mode_label(shift, alt, default_chain)` binds Shift/Alt; bare X/Z axis lock; Ctrl grid snap; Ctrl+Z/Ctrl+Shift+Z undo/redo); `operators/armature/_status_bar.py` (the rendered chord cheatsheet); `core/armature/quick_armature_math.py` (`resolve_press_mode`). Locked: `decisions.md` "Quick Armature UX" (GPU preview line + real bone on click, tail tracks MOUSEMOVE; prefix = pref + F3; Front-Ortho auto-snap restores prior view on exit).

**Question:** Shift/Alt/Ctrl/X/Z are all bound and conflate chain modifiers (Shift/Alt) with standalone tools (undo, axis lock). Viewport pick-parent (hit-test a bone tip to reparent mid-sketch) has no home. What scheme replaces the taps before fitting pick-parent in? (Absorbs the old `qa-pick-parent-viewport`.)

**Options:**
- **(A) Mode-layer scheme.** A key (e.g. Tab) switches modal mode (chain / reparent); the status bar shows that mode's chords; pick-parent is its own mode. Frees the modifier taps; adds one mental step; preserves all locked promises.
- **(B) Alt+click as a direct parent-pick.** Alt+LMB near a bone tip picks parent, falls back to disconnected; minimal but overloads Alt and is ambiguous.
- **(C) Standalone Reparent operator outside the modal.** Leaves chords unchanged but breaks the one-session authoring flow.

**Recommendation:** **(A) mode-layer** - cleanest long-term home for pick-parent, no retraining of existing chords, fits the locked modal-UX promises. Size **M** (track `_mode`, swap status-bar + handlers per mode, Tab handler). This is the heaviest design of the five.

### 3. qa-rotation-mode

**Code anchors:** `operators/driver.py` (sets `target.rotation_mode = "XYZ"` when wiring a bone driver; reads ROT_* axis); the writer collapses Euler/quaternion for export, so the export is already correct both ways; `packages/fixtures/*/build_blend.py` set `rotation_mode="XYZ"` on driven bones. Locked: `decisions.md` "Rigging, drivers, IK" (Drive-from-Bone assumes the XYZ Euler read).

**Question:** A bone's `rotation_mode` is not controllable from Quick Armature. The export handles both modes, so the value is authoring clarity - but swapping mode on a *driven* bone can silently change how the driver expression reads the rotation. How to expose the choice safely?

**Options:**
- **(A) Lock new Quick Armature bones to Euler-XYZ, no UI.** Safest for drivers; removes flexibility.
- **(B) A scene-level "rotation mode" choice applied on bone creation.** Visible, but does not stop a post-creation manual swap.
- **(C) Validate on export: warn when a driven bone's rotation_mode does not match its driver's assumption.** Fits the lazy-validation pattern; prevention is post-hoc.

**Recommendation:** **(C) export validation warn** - matches `decisions.md` "Validation is lazy + inline" and targets the actual risk (a driven bone whose mode drifted) instead of over-restricting authoring. Size **S** (a validator check over the export armature's driven bones).

### 4. proscenio-y-depth-layers

**Code anchors:** `importers/photoshop/planes.py` (`_layer_placement` sets object Y = `z_order * Z_EPSILON`, 0.001 per layer, to avoid viewport z-fight); `exporters/godot/writer/sprites.py` (`_derive_z_index` reads `obj.location.y`, negates it, emits `z_index`). Locked: `decisions.md` "Sprite appearance" (`z_index` from PSD Y depth; appearance derived from native state).

**Question:** Today Y is PSD-driven and read back as `z_index`. Should Y depth be controllable in Blender (manual offset, or auto-grouped layers), and does it enter the schema or stay authoring-only?

**Options:**
- **(A) Keep current.** PSD-driven, immutable after import; to reorder, re-import with a different PS order. Simplest.
- **(B) A manual "Depth Offset" PropertyGroup float, added to the derived Y at export.** Blender-authoring-only, no schema change; export already reads Y. Adds one field.
- **(C) Auto-layer from collections / subfolders** (a "Depth mode" enum + an "Auto-layer" button). More power, couples to hierarchy.
- **(D) Promote `depth_layer` to the schema.** Round-trips authored depth; semantically overlaps `z_index`; a schema field decision.

**Recommendation:** **(B) manual depth offset (authoring-only)** - minimal, transparent, no schema/writer change beyond adding the offset before negating. Note the "appearance derived from native state" rule: `z_index` is already a derived appearance, so an offset is a derivative of a derivative - **confirm against that rationale before building** (it may argue for (A) or (D) instead). Size **S** ((B)) to **M** ((D)).

### 5. incorporate-blender-mesh-as-element

**Code anchors:** `panels/element.py` (the `element_type` selector); `properties/object_props.py` (`ELEMENT_TYPE_ITEMS`; sprite-only fields hframes/vframes/frame/centered); `importers/photoshop/planes.py` (`_tag_element_type` sets `element_type`, copies frame fields, defaults sprite centered); `core/validation/active_element.py` (a valid element is a MESH with a known `element_type`, sprites need hframes/vframes >= 1). Locked: none beyond lazy validation.

**Question:** A user authors a mesh directly in Blender and wants it in the flow. What does an "incorporate" button set, and what are the preconditions?

**Options:**
- **(A) Plain "Make Proscenio Element" button.** Sets `element_type="mesh"`, defaults the rest; precondition: active object is MESH with >= 1 face. Quick; sprite case needs follow-up field entry.
- **(B) Smart dialog (Mesh / Sprite) with geometry hint.** A quad (4 verts / 1 face) defaults to Sprite (hframes=vframes=1, centered) else Mesh; same precondition; mirrors the existing "Create Slot" modal pattern.
- **(C) Full on-boarding** (type + spritesheet dims + material/placeholder image). Higher polish, over-scoped for now.

**Recommendation:** **(B) smart dialog** - matches the codebase's existing modal-dialog pattern and pre-fills the same PG fields the Element panel already controls; no schema impact. Size **M** (operator + modal + geometry heuristic + property set).

## Verdict summary

**5 decisions, 0 ready to code.** Each carries a recommendation and a size estimate; none is built before its call is locked. Heaviest design: qa-quickarm-interaction-revision (option A, mode-layer). Two calls (sprite-centered, y-depth) hinge on the same "appearance derived from native state" locked rationale and should be decided together. Once decided, the locked calls move to [`decisions.md`](../decisions.md) and the implementable rows become [TODO.md](TODO.md).
