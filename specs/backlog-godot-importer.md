# Godot importer backlog

Code-read gaps in the Godot import builders (`apps/godot/addons/proscenio/builders/`), from the QA Companion audit (2026-06-15), re-verified against current `main`. Found by reading, not yet reproduced. The doc-coverage half is in [backlog-docs.md](backlog-docs.md).

## Import-builder hardening (future STUDY)

One area pass: the builders trust the document shape with no validation, so malformed, duplicate, or unresolved data silently corrupts the rig or aborts the import. Candidate fixes, each cited:

- **Malformed polygon/UV point aborts the whole import** (med). `mesh_builder.gd:60-61,83-84` index `p[0]/p[1]` and `u[0]/u[1]` with no length guard, unlike the bone path's `_vec2_from_packed` (`skeleton_builder.gd:47`). One shared length-guarded helper closes both.
- **Skinned mesh with all-missing bones binds undeformed** (med). `mesh_builder.gd:15-29` sets `poly.skeleton` + `clear_bones` before any weight resolves; if every weight references a missing bone the Polygon2D is skeleton-bound with zero weights. Resolve weights first; only bind when one resolves.
- **Empty/mismatched slot default hides every attachment, silently** (low). `sprite_attach_util.gd` `resolve_sprite_parent` sets `visible = name == default` with no warning when nothing matches. Warn, or fall back to the first attachment.
- **Animation target resolves first same-named node across the whole tree** (low). `animation_builder.gd:53,80` `find_child(target, true, false)` can bind a track to an unrelated subtree (the `sprite_frame` path already narrows by `Sprite2D` type). Scope the lookup.
- **Duplicate bone names overwrite the lookup dict** (low, defense). `skeleton_builder.gd:30` keys by raw name with no collision check; the writer avoids collisions (a fixture rename shipped in #128), so this is defense-in-depth. Warn or disambiguate.
- **Per-key `interp` is parsed but never honored** (low, dead field). `animation_builder.gd:148-154` hardcodes interpolation per property; the authored `key.interp` is ignored. Honor it or drop it from the schema.

## Non-destructive reimporter is an empty stub (decision needed)

`reimporter.gd` is an empty `RefCounted`; its own header and the docs promise a diff/merge reimport that preserves user edits, but none is performed (every reimport overwrites the `.scn` wholesale - wrapper scenes survive only as a side effect of instancing). Product call: build the diff/merge reimporter, or drop the non-destructive claim and document the wrapper-scene pattern as the supported path. Tied to the Blender "re-import rebuilds the armature" item in [backlog-bugs-found.md](backlog-bugs-found.md).
