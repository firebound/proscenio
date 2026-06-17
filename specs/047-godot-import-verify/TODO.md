# Spec 047: Godot importer verification and docs - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): four rows, all now, in one code+test PR plus a docs follow-up. The with-texture region scaling is a confirming test (a code read says it already works); the no-texture region is a real fix.

## Now

### PR 1 - region verification + no-texture fix (one headless run verifies both)

- [ ] Add a with-texture region test to [`test_importer.gd`](../../apps/godot/tests/test_importer.gd): a `Sprite2D` fixture whose sprite resolves a real texture of a known size and carries a normalized `texture_region`, asserting `region_rect` equals the region multiplied by the texture size (mirrors the scaling at [`sprite_builder.gd`](../../apps/godot/addons/proscenio/builders/sprite_builder.gd) lines 60-72). This needs a fixture whose sprite gets a texture - the harness passes `null` as the atlas in `_build_character`, so either point the sprite at a per-sprite / by-name PNG the harness can load, or extend `_build_character` to pass a real `Texture2D`.
- [ ] Fix the no-texture region edge case in [`sprite_builder.gd`](../../apps/godot/addons/proscenio/builders/sprite_builder.gd): move `region_enabled = true` and `region_filter_clip_enabled = true` (lines 61, 64) together with the `region_rect` assignment inside the `if sprite_tex != null` branch, so a texture-less sprite ships as a plain region-disabled sprite rather than an enabled empty region that draws nothing. Keep parity with [`mesh_builder.gd`](../../apps/godot/addons/proscenio/builders/mesh_builder.gd) lines 79-85, which already leaves UVs raw without a texture.
- [ ] Delete the stale comment at [`sprite_builder.gd`](../../apps/godot/addons/proscenio/builders/sprite_builder.gd) lines 54-59 claiming the rect is "filled in by the importer's real load" - `importer.gd:_import` has no such pass. Replace it with a one-line note on the new (rect-only-when-texture) behaviour.
- [ ] Add the no-texture region test: a sprite with a `texture_region` but no resolvable texture must come out with `region_enabled == false` (the decided behaviour), not an enabled zero rect.
- [ ] Run the headless suite once and confirm green: `godot --headless --script apps/godot/tests/test_importer.gd` (the with-texture rect assertion is the one finding not yet runtime-verified in the study).

### PR 2 - docs (after PR 1 lands)

- [ ] Document the `_001` name-collision suffix convention on [`docs/04-godot-plugin/index.md`](../../docs/04-godot-plugin/index.md): colliding node names get Godot's automatic numeric suffix on `add_child`, never a kind prefix, because animation tracks resolve targets by name (`animation_builder.gd` `find_child(target, ...)` at lines 53, 62, 80) - a prefix would break the lookup.
- [ ] Add a one-line multi-frame sprite preview caveat to [`docs/04-godot-plugin/index.md`](../../docs/04-godot-plugin/index.md) (and optionally the slice line at [`00-basic/03-godot.md`](../../docs/00-guides/00-basic/03-godot.md) line 25): a multi-frame `Sprite2D` shows one frame at native pixel size while Blender shows the whole quad; this is inherent to the model. Point to the authoring rule already written at [`packages/fixtures/README.md`](../../packages/fixtures/README.md) lines 135-136 (`quad_units = frame_px / ppu`) rather than re-deriving it.
