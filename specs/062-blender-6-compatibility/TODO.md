# Spec 062: Blender 6 compatibility - TODO

One PR, gated on the Blender 6.0 trigger. The `mat.use_nodes = True` writes in `importers/photoshop/planes.py` and `operators/atlas_pack/apply.py` set the flag rather than gate on it, so they are a separate concern and stay as-is.

## PR 1 - use_nodes read sweep (gated on Blender 6.0)

- [ ] `panels/mesh_generation.py`: convert the raw `use_nodes` read to `getattr(material, "use_nodes", True)`.
- [ ] `panels/atlas.py:93` (`if not mat.use_nodes or ...`): convert to the `getattr` form.
- [ ] `panels/_draw_sprite.py` (`_material_has_slicer`): convert to the `getattr` form.
- [ ] `operators/atlas_pack/_paths.py:64` (`swap_image_in_materials`): convert to the `getattr` form.
- [ ] `core/bpy_helpers/spritesheet/spritesheet_shader.py`: convert to the `getattr` form.
- [ ] Confirm `core/_shared/material_images.py:45` already uses the canonical form (the reference), and that all sites now match it.
