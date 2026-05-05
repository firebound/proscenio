# Dummy example

Hand-written end-to-end fixture for SPEC 000 Phase 1. Bypasses the Blender exporter (which does not exist yet) and exercises the Godot importer in isolation.

## Files

| File | Purpose | LFS |
| --- | --- | --- |
| `dummy.proscenio` | hand-authored character — 3 bones, 3 sprites, 1 idle animation | text |
| `dummy.blend` | minimal Blender source matching the hand-written `.proscenio` | yes |
| `atlas.png` | 256×256 placeholder texture with three labeled 80×80 regions | yes |
| `generate_atlas.py` | regenerates `atlas.png` from scratch (Pillow required) | text |
| `Dummy.tscn` + `Dummy.gd` | wrapper scene + script — see the Wrapper scene pattern section below | text |

## Three files, three roles

When you drop this folder into a Godot project, you end up with three layers — keep them straight:

| File | Who writes it | Survives reimport? |
| --- | --- | --- |
| `dummy.proscenio` | Blender (or your DCC) — source of truth | rewritten by exporter |
| `dummy.scn` (generated) | Godot importer regenerates from `dummy.proscenio` | **clobbered** every reimport |
| `Dummy.tscn` + `Dummy.gd` | you — wraps the imported scene | **untouched** by reimport |

The instance/inherit pattern in `Dummy.tscn` is the canonical way to add scripts and extra nodes (collisions, particles, AI controllers) without losing them when the DCC re-exports. See [SPEC 001](../../specs/001-reimport-merge/STUDY.md) for the full rationale.

## Anatomy

```text
root          legs sprite (parented to root, polygon extends below the bone)
 │
 └─ torso     torso sprite (centered on the torso bone)
     │
     └─ head  head sprite (centered on the head bone)
              animated: head bobs ±15° on the rotation axis, 1.0 s loop
```

The atlas is 256×256. Three vertical 80×80 regions on the left edge, top to bottom: head (red), torso (blue), legs (green). Anything magenta is "off the atlas" and indicates a UV bug.

## Validate the fixture

```sh
python -m check_jsonschema --schemafile schemas/proscenio.schema.json examples/dummy/dummy.proscenio
```

Should print `ok -- validation done`.

## Wrapper scene pattern

`Dummy.tscn` instances the imported `dummy.scn` and attaches `Dummy.gd` to the wrapper root. This is the recommended way to customize an imported character:

- Scripts live on the wrapper. Reimport never touches the wrapper file.
- Extra nodes (collision shapes, particle emitters, AI state machines) parent to the wrapper, not to bones inside the imported scene.
- The imported scene's `AnimationPlayer` is reachable via `find_child("AnimationPlayer")`. To add Godot-authored animations, give the wrapper its *own* `AnimationPlayer` with a second `AnimationLibrary`, and play across both libraries.

If you rename a bone in Blender, any `NodePath` in the wrapper that referenced the old name (`$DummyCharacter/Skeleton2D/old_name`) breaks on the next reimport. Plan renames as cross-DCC operations.

## Next steps in the spec

This dummy is the input to the Godot importer smoke test (TODO §"Godot importer — make MVP work end-to-end" in [`specs/000-initial-plan/TODO.md`](../../specs/000-initial-plan/TODO.md)) and the worked example for [SPEC 001](../../specs/001-reimport-merge/STUDY.md).
