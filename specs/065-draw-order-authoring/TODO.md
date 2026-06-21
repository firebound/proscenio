# Spec 065 TODO

Single PR (code). Order follows the dependency chain.

## Field rename + storage

- [ ] `core/_shared/cp_keys.py`: `PROSCENIO_DEPTH_OFFSET` -> `PROSCENIO_Y_DRAW_ORDER` (`proscenio_y_draw_order`); add `DEFAULT_Y_LOCATION_SPACING = 0.001`.
- [ ] `properties/object_props.py`: drop `depth_offset` FloatProperty; add `y_draw_order` IntProperty + `_y_draw_order_update` (writes `Y = order * spacing`, then mirrors).
- [ ] `core/_shared/hydrate.py` + `core/mirror.py`: map `y_draw_order` (int caster).

## Preference

- [ ] `addon_prefs.py`: `y_location_spacing` FloatProperty (default `DEFAULT_Y_LOCATION_SPACING`, `min` > 0); `y_location_spacing(context)` reader with headless fallback; draw it in the prefs panel.

## Writer

- [ ] `exporters/godot/writer/sprites.py`: `_derive_z_index` reads `y_draw_order` (PG/CP), returns `-order or None`; drop `_DEPTH_EPSILON`.

## Import

- [ ] `importers/photoshop/planes.py`: `_layer_placement` takes `spacing` (drops `Z_EPSILON`); `_place_and_tag` reads the preference, sets `y_draw_order = z_order` (CP + idprop), positions Y for non-slot meshes.

## Panels + operator

- [ ] `panels/element.py`: prop `y_draw_order`.
- [ ] `panels/helpers.py`: viewport `clip_start` + `clip_end`; `Re-space planes` button.
- [ ] `operators/armature/` (or a new helpers op module): `PROSCENIO_OT_respace_planes` - `Y = order * spacing` over every element.
- [ ] `panels/outliner.py`: editable `y_draw_order` column on mesh / attachment rows.

## Validation

- [ ] `core/validation/active_element.py`: `_validate_draw_order_position(obj, name, spacing)` - warn when `round(Y/spacing) != order`; thread `layer_spacing` param.
- [ ] `core/validation/export.py`: same divergence sweep across the scene.
- [ ] panel callers pass `y_location_spacing(context)`.

## Fixture + tests

- [ ] `packages/fixtures/slot_swap/build_blend.py`: rename `depth_offset` -> `draw_order` (int -1, -2), stamp `proscenio_y_draw_order`, keep `Y = order * 0.001`. Golden `z_index` 1 / 2 unchanged.
- [ ] `tests/writer/test_sprites.py`: rewrite the z_index tests onto `y_draw_order` (PG + CP fallback, net-zero -> None).
- [ ] New tests: import sets order (first vs re-import), update callback writes Y, re-space op, outliner column draws, validation divergence warning (pure, parametrized spacing).

## Gates

- [ ] operator tests, goldens 8/8, mypy strict, repo-root pytest.
