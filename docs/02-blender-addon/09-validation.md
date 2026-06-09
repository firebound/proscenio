# Validation

Walks the scene and reports issues that would block an export: a missing armature when sprites carry vertex groups, bone references that no longer exist on the armature, atlas image files missing from disk, and `sprite_frame` meshes without `hframes` / `vframes`.

Errors block the export; warnings are informational. Click a row to select the offending object.
