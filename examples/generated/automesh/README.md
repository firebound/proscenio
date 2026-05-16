# automesh fixture (SPEC 013 Wave 13.1)

Workbench for the **SPEC 013 automesh from sprite** operator + future Wave 13.1 bind / weight paint / sidecar follow-ups. Four sprite planes with image-textured materials plus a 3-bone arm chain positioned over the hand sprite - feeds the smoke checklist in [`tests/MANUAL_TESTING.md` section 1.15](../../../tests/MANUAL_TESTING.md) end-to-end.

## Directory layout

```text
examples/generated/automesh/
├── automesh.blend       [SOURCE - built by build_blend.py]
└── pillow_layers/
    ├── hand.png                   200x200, stylized hand (palm + 4 fingers)
    ├── blob.png                   200x200, smooth ellipse blob
    ├── lshape.png                 200x200, concave L silhouette
    └── ring.png                   200x200, donut with alpha hole
```

No `.proscenio` expected output - this fixture is authoring-only; it never exports.

## Contents of the .blend

| Element | Detail |
| --- | --- |
| Armature `automesh.arm` | 3-bone chain `shoulder` -> `elbow` -> `wrist`, connected, along world +X from X=-4 to X=-2. Positioned so the chain crosses the hand sprite's bbox (SPEC 013 D15 density-under-bones smoke). |
| Sprite `hand` | 2.0x2.0 unit quad at world (-3, 0, 0), parented to `automesh.arm`. Image-textured with `pillow_layers/hand.png`. The density-under-bones smoke target. |
| Sprite `blob` | 2.0x2.0 unit quad at world (0, 0, 0), unparented. Smooth convex baseline. |
| Sprite `lshape` | 2.0x2.0 unit quad at world (3, 0, 0), unparented. Concave hull stress test. |
| Sprite `ring` | 2.0x2.0 unit quad at world (0, 0, -3), unparented. Alpha-hole edge case. |
| Materials | One per sprite (`<name>.mat`), Principled BSDF + ShaderNodeTexImage with `interpolation="Closest"` (pixel-art). |
| UVs | 0..1 rect on each quad's own texture (mirrored U so the PIL image reads unmirrored in Front Ortho). |
| Actions | None. |

## Why these four shapes

Each silhouette exercises a different aspect of the SPEC 013 pure-Python alpha contour walker + annulus geometry pipeline:

- **`hand`** is the canonical "real character part" - tapered finger tips + palm + gaps between fingers stress Moore Neighbour tracing on a non-trivial contour, and the 3-bone chain over it lets the user see D15 bone-aware density in action vs OFF (the density-under-bones triangle clusters near each bone segment).
- **`blob`** is the simplest possible convex silhouette - baseline regression target. Any future change that breaks blob automesh almost certainly broke the basics.
- **`lshape`** stresses concave hull handling - the contour walker has to follow the inward-pointing corner without giving up. Spine `Trace` documents concave support; this is the local regression guard.
- **`ring`** is a deliberate **anti-fixture** for the "no holes" contract Spine + Proscenio both ship. The outer contour walks the outside fine; the inner contour walker meets the alpha hole's silhouette and the resulting topology is degenerate. Smoke exists to confirm Proscenio degrades visibly (operator runs but produces a malformed mesh) rather than crashing - if a user violates the contract we want them to notice.

## Building from source

Two stages: PNG generation runs without Blender, `.blend` assembly runs in headless Blender.

```sh
# 1. Generate 4 PNGs under pillow_layers/.
python scripts/fixtures/automesh/draw_layers.py

# 2. Assemble the .blend.
blender --background --python scripts/fixtures/automesh/build_blend.py
```

Re-run both steps when smoke surfaces a need for an updated baseline (new shape, different bone layout, etc).

## Smoke usage

See [`tests/MANUAL_TESTING.md` section 1.15](../../../tests/MANUAL_TESTING.md) for the T1-T16 checklist. Quick reference:

1. Open `automesh.blend` in Blender.
2. Enable Proscenio addon (if not auto-loaded).
3. Select a sprite plane.
4. Open Sidebar (N key) > Proscenio tab > Skinning subpanel.
5. Tune props in the Automesh sub-box.
6. Click `Automesh from Sprite` button.

For density-under-bones smoke: Skeleton panel > set picker to `automesh.arm` > Skinning panel > select `hand` sprite > enable density-under-bones > Automesh. Compare visual against OFF.

**Important:** never `Ctrl+S` after smoke. The fixture is tracked + the smoke flow rewrites mesh geometry in place. If you accidentally save, regenerate via `build_blend.py`.
