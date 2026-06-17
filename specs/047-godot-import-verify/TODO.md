# Spec 047: Godot importer verification and docs - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): four rows, all now, in one code+test PR plus a docs follow-up. The with-texture region scaling is a confirming test (a code read says it already works); the no-texture region is a real fix.

## Now (done - one PR)

Code, tests, and docs shipped together (the docs document the same import behavior the code fix changes, so they ride one PR rather than a follow-up).

### Region verification + no-texture fix

- [x] With-texture region test: a `Sprite2D` resolving a known-size `ImageTexture` (64x32) and a normalized `texture_region` asserts `region_rect` equals the region scaled to texture pixels. It went into a **new** [`test_sprite_region.gd`](../../apps/godot/tests/test_sprite_region.gd) rather than `test_importer.gd`, because adding it there pushed the file past gdlint's 500-line cap. The element is routed through `ProscenioDocument.from_dict` so the builder gets the same typed `Array[ProscenioElement]` the importer does; the atlas is passed straight in (no fixture PNG plumbing). The runtime run confirmed the scaling - the study's one unverified finding is now verified.
- [x] Fixed the no-texture region edge case in [`sprite_builder.gd`](../../apps/godot/addons/proscenio/builders/sprite_builder.gd): `region_enabled` / `region_filter_clip_enabled` now sit with the `region_rect` assignment inside `if ... and sprite_tex != null`, so a texture-less sprite ships region-disabled instead of an enabled empty region that draws nothing. Matches `mesh_builder.gd` leaving UVs raw without a texture.
- [x] Replaced the stale "filled in by the importer's real load" comment (no such pass exists in `importer.gd:_import`) with a note on the rect-only-when-texture behavior.
- [x] No-texture region test: a `texture_region` with no resolvable texture comes out `region_enabled == false`. Covered in `test_sprite_region.gd` (synthetic, atlas `null`) and pinned on the real `effect` fixture in `test_importer.gd` (the harness builds with a `null` atlas, so `glint` is already on the no-texture path; its assertions flipped from enabled to disabled).
- [x] Ran the headless suite green: `test_importer.gd` 84 assertions pass, `test_sprite_region.gd` 5 checks pass. Added a CI step so `test_sprite_region.gd` runs alongside the importer test.

### Docs

- [x] Documented the `_001` name-collision suffix convention on [`docs/04-godot-plugin/index.md`](../../docs/04-godot-plugin/index.md): Godot's automatic `add_child` suffix, never a kind prefix, because animation tracks resolve targets by leaf name via `find_child`.
- [x] Added the multi-frame sprite preview caveat to the same page, pointing at the authoring rule (`quad_units = frame_px / ppu`) already written in [`packages/fixtures/README.md`](../../packages/fixtures/README.md) "Sprite quads (multi-frame)". Left `00-basic/03-godot.md` as-is (the plugin page is the import-side home for the caveat).
