# Spec 050: Blender authoring design decisions - TODO

Sequenced from the locked calls in [STUDY.md](STUDY.md). Three small PRs; all "now", none blocks another.

## PR 1 - rotation-mode guard + convert-to-Euler

- [ ] Add an export-validator check: warn when a bone that drives a sprite has a `rotation_mode` that does not match its driver's assumption (the driver reads ROT_* in `XYZ`). Lives with the other lazy checks in [`core/validation/`](../../apps/blender/core/validation/); warn-only, never blocks export.
- [ ] Add a **Convert rotation to Euler** operator that sets `rotation_mode = "XYZ"` (Blender converts the stored values), with a scope of the active bone or all bones in the armature. Surface it in the Skeleton panel ([`panels/skeleton.py`](../../apps/blender/panels/skeleton.py)); operator under [`operators/armature/`](../../apps/blender/operators/armature/).
- [ ] Headless tests: the validator fires on a mismatched driven bone and stays quiet otherwise; the convert operator rewrites `rotation_mode` for the active-bone and all-bones scopes.

## PR 2 - manual Y depth offset

- [ ] Add a `depth_offset` float to the element PropertyGroup ([`properties/object_props.py`](../../apps/blender/properties/object_props.py)) - authoring-only, no schema field.
- [ ] In the writer ([`exporters/godot/writer/sprites.py`](../../apps/blender/exporters/godot/writer/sprites.py) `_derive_z_index`), add `depth_offset` to the PSD-order-derived Y before negating into `z_index`.
- [ ] Surface the field in the element/outliner panel.
- [ ] Headless test: a non-zero `depth_offset` shifts the emitted `z_index` by the expected amount; zero keeps the PSD-order value.

## PR 3 - incorporate Blender mesh as element

- [ ] Add an **Incorporate as Element** button in [`panels/element.py`](../../apps/blender/panels/element.py), shown when the active object is a plain mesh with no Proscenio element data.
- [ ] Add the operator (under [`operators/`](../../apps/blender/operators/)): a Mesh / Sprite choice (redo/adjust dialog, the Create Slot pattern), defaulting Sprite for a 4-vert single-face quad and Mesh otherwise; set `element_type` + the sensible defaults the Element panel already controls.
- [ ] Headless tests: incorporate sets a valid mesh element; the quad heuristic picks Sprite and fills hframes/vframes; a non-quad picks Mesh.
