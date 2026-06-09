# Code duplication audit - summary

One-page overview of what the audit found. Full detail in [FINDINGS-TYPE4.md](FINDINGS-TYPE4.md); coverage accounting in [COVERAGE.md](COVERAGE.md); the original token-pass (PMD CPD) in [STUDY.md](STUDY.md).

## Scope

`apps/blender` only (Python). The Godot side (GDScript) has no cheap clone tool; the Photoshop TS app got the token pass but not the semantic one. The goal was type-4 duplication: logic that performs the same operation through different syntax, so a future refactor never has to change identical reasoning in more than one place.

## Method, in three layers

1. **PMD CPD (token)** - caught exact and renamed copy-paste. Surfaced ~15 structural clusters at minimum-tokens 35.
2. **AST scan v1 + v2** (`tools/ast_scan.py`, `tools/ast_scan2.py`) - exact skeleton, k-gram near-skeleton similarity, call-set overlap, cross-file name collisions, and data-schema comparison. Covers 100% of the 902 production functions.
3. **Hand read** - every logic-bearing file in `apps/blender` read line-by-line to separate real duplication from coincidental rhyme. Only register/UI boilerplate tails left un-read.

## The headline

The codebase is **well-factored** - it already has canonical helpers for almost every recurring operation (`scene_props`, `object_props`, `select_only`, `from_json`, `iter_shader_nodes`, `read_field`, `remap_uv_into_slot`, `point_in_polygon`, `_cyclic_loop_edges`). The duplication that exists is almost entirely **call sites that reimplement the operation inline instead of calling the helper that already exists**. That is the good kind of problem: the fix is mechanical (replace the inline copy with an import), not a new abstraction.

## Real duplications, by tier

### Tier 1 - large fan-out, canonical helper bypassed (highest payoff)

- **N1. Find the texture image on a material** - the `for node in material.node_tree.nodes: if node.type == "TEX_IMAGE"` walk is hand-written in ~10 places. Helper `iter_shader_nodes` exists; most sites ignore it. Single largest drift surface.
- **N2. PropertyGroup-first / Custom-Property-fallback read** - reimplemented ~5 times despite `read_field` / `read_bool_flag`, and the backing `_CPLookup` Protocol is defined 5 times. Already drifting in null/presence semantics.
- **N3. `point_in_polygon`** - two ray-cast implementations (one boundary-excluding canonical, one rogue) that disagree on edge points.

### Tier 2 - verbatim copies (will drift)

- **D1** `_resolve_image` + `_find_tex_image` copied between automesh.py and automesh_authoring.py (docstring admits the reuse but copied anyway).
- **D2** `_restore_selection` byte-identical across 2-3 files.
- **D3** `_resolve_pixels_per_unit` identical x2.
- **D4** `_image_filename` (Godot writer) near-identical x2 ("Mirrors..." in the comment).

### Tier 3 - shared block / parallel logic (medium)

GPU shader-draw tail (D6, ~8-10 sites), bmesh delete with inverted predicate (D7), cyclic edge-loop construction (D8/N6), PSD stamp tail (D9), JSON-Custom-Property codec (D10/N7), deform-bone world projection (N4, 3 sites), viewport ray-plane projection (N5), `scene.proscenio` accessor bypassed (N8), arc-length resamplers (N9), select-by-name operator body (N10), statusbar + chord renderers (D11/N11), Issue schema dataclass vs PropertyGroup (N12), nearest-vertex linear scan (N13, 4 sites), numpy image compositors (N17), tag-VIEW_3D-redraw (N18), "is slot Empty" predicate (N19), UV-remap-to-slot reimplemented (N20), UV-bounds bbox (N21), reparent-into-empty (N22), invoke-prefills-props (N23), selection save/restore inline (N24), picker-readout UI block (N25), issue-list render block (N26).

### Tier 4 - trivial

`_name_of` x3, armature poll x2, cp_key map table x2, `Point2D` alias x5, zero-matrix init x4, read-vertex-group-weights x5.

## Top 3 by payoff

1. **N1** - one `iter_material_images(obj)` collapses ~10 sites.
2. **N2** - one decision on the presence rule, then every site routes through one helper + one Protocol.
3. **D6** - one `_draw_batch(prim, verts, color, width)` primitive collapses the whole overlay-draw cluster.

## Evaluated and rejected (looked like duplication, is not)

`mirror._as_int/_as_float/_as_bool` (coercion rules genuinely differ), `contour._dilate_once/_erode_once` (already share their loop via `_apply_morphology`), `PoseDelta` / `BoneRestLocal` / `_KeyKwargs` (same field names, different meaning), `draw_body` / `draw_box` per-mode dispatch (intentional polymorphism), the `math.hypot` distance-loop idiom (coincidental), `_bpy_compat` thin compat shims (deliberate single acknowledged place).

## What was NOT covered

GDScript (`apps/godot`) - no tool exists. Type-4 twins that reach the same output through entirely different APIs (call-set overlap near zero) - only a same-domain hand read catches those, and that read is now done for `apps/blender`. Register/UI panel boilerplate tails were confirmed by pattern, not read line-by-line.
