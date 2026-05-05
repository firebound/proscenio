# Effect example

Worked example for [SPEC 002](../../specs/002-spritesheet-sprite2d/STUDY.md) — a `sprite_frame` (Godot `Sprite2D`) sprite with frame-by-frame animation, the alternative path to the `Polygon2D` cutout used by the [`dummy`](../dummy/) fixture.

## Files

| File | Purpose | LFS |
| --- | --- | --- |
| `effect.proscenio` | hand-authored — 1 root bone, 1 `sprite_frame` sprite, 1 looping `play` animation | text |
| `atlas.png` | 64×16 horizontal strip — four 16×16 frames | yes |
| `generate_atlas.py` | regenerates `atlas.png` from scratch (Pillow required) | text |
| `Effect.tscn` + `Effect.gd` | wrapper scene + script — see the Wrapper scene pattern in [`examples/dummy/README.md`](../dummy/README.md) | text |

## Three files, three roles

Same model as the dummy fixture:

| File | Who writes it | Survives reimport? |
| --- | --- | --- |
| `effect.proscenio` | Blender / DCC — source of truth | rewritten by exporter |
| `effect.scn` (generated) | Godot importer regenerates from `effect.proscenio` | **clobbered** every reimport |
| `Effect.tscn` + `Effect.gd` | you — wraps the imported scene | **untouched** by reimport |

## Anatomy

- One bone (`root`) at origin.
- One sprite (`glint`) of `type: "sprite_frame"`, `hframes=4`, `vframes=1`, attached to `root`.
- One animation (`play`, 0.4 s, looping) — a single `sprite_frame` track stepping `frame: 0 → 1 → 2 → 3` every 0.1 s.

The atlas's four frames are color-coded (red, yellow, green, blue) with the inner shape growing then shrinking, so a misordered import is visible at a glance.

## Validate the fixture

```sh
python -m check_jsonschema --schemafile schemas/proscenio.schema.json examples/effect/effect.proscenio
```

Should print `ok -- validation done`.

## Why this fixture exists

Validates the SPEC 002 path end-to-end:

- Schema accepts `type: "sprite_frame"` with `hframes`/`vframes` and rejects nothing real.
- Importer dispatches to `sprite_frame_builder.gd` and produces a `Sprite2D` with the right frame metadata.
- Animation builder wires the `sprite_frame` track to `:frame` with `INTERPOLATION_NEAREST`.
- Wrapper-scene pattern from SPEC 001 holds identically for `Sprite2D`-backed sprites.
