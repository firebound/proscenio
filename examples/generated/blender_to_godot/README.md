# blender_to_godot fixtures

End-to-end inputs + goldens for the **Blender -> Godot** half of the Proscenio pipeline. Each fixture starts from a `.blend` and produces a `.proscenio` scene file (plus a Godot wrapper `.tscn`) that downstream consumers diff against.

The existing procedural fixtures under `examples/generated/<name>/` (atlas_pack, blink_eyes, mouth_drive, shared_atlas, simple_psd, slot_cycle, slot_swap) all belong to this direction. They predate the categorization and stay at the flat top level for now; this bucket exists so new `blender_to_godot` fixtures can land beside the existing ones without disturbing the doc / script ripple chain.

> Migration of the flat-layout fixtures into this subdirectory is intentionally deferred. The blast radius spans `scripts/fixtures/`, every SPEC TODO, and the per-fixture wrapper paths in Godot - not worth one big refactor commit. New fixtures land here directly; legacy fixtures move when the next reason to touch them coincides with the rename.

## Pattern (reference: existing flat fixtures)

```text
<fixture_name>/
+- <fixture_name>.blend                   [SOURCE - built by scripts/fixtures/<name>/]
+- <fixture_name>.expected.proscenio      [GOLDEN]
+- pillow_layers/  or  atlas.png          [INPUT - drawn by Pillow]
+- godot/
   +- <FixtureName>.tscn
   +- <FixtureName>.gd
```

See [`scripts/fixtures/README.md`](../../../scripts/fixtures/README.md) for the build-script conventions.
