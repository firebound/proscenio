# Spec 029: Mesh authoring

Fix and round out the mesh-generation tools - the interactive modal and the generation panel.

## Scope

- **Fix Automesh Interactive extend/cut** - the Stage 2 pen tools currently do nothing or spray artifacts.
- **Rename "Mesh resolution"** - the current label misleads about what the value does.
- **Default "Density follows bones" OFF** - flip the default that surprises users.
- **Group "Interior spacing"** with the other numeric controls.
- **Surface "preserve weights on regen"** where the regen actually runs, not only in the snapshot panel.
- **Action-oriented Automesh modal button** - rename the vague "Automesh (modal)" label.
- **Element-type gating** - warn (not silently run) when a mesh tool is used on a sprite, and keep the sprite a quad.
- **Sprite rigid single-bone bind** - a bind path for sprites, since weight paint is mesh-only.
- **Manual hull authoring** - a click-to-place pen tool for drawing a mesh by hand.

## Study

Surface read 2026-06-11 against `main`: the modal operator (`operators/automesh/automesh_authoring.py`), the stage dispatch (`core/bpy_helpers/automesh/authoring_pipeline.py`), the pure splice (`core/automesh/outer_splice.py`), the panel (`panels/mesh_generation.py`), and the scene props (`properties/scene_props.py`).

### Surface notes

**Not the brush-preset bug - cross-check closed.** The skinning-weight-paint failure mutates a live bpy RNA `CurveMapPoints` collection and throws; the automesh Stage 2 path contains no curve code at all. It is pure-Python polyline splice surgery fed by the toggle-pen dispatch state (`automesh_authoring.py:242-248`), and it fails without ever raising. The "curve rebuild" root-cause collapse in [EXECUTION_MAP.md](../EXECUTION_MAP.md) can close as two distinct bugs.

**Extend/cut root-cause hypothesis.** Four defects compound into exactly the reported "no-op OR artifacts":

1. **Snap-anchored extend strokes classify as fully outside and are silently dropped.** `_snap_pen_click` (`automesh_authoring.py:653-697`) snaps pen clicks onto exact outer-contour verts - the affordance invites anchoring the extend on the silhouette. `point_in_polygon` (`core/automesh/density.py:70-77`) is explicit that on-edge points count as outside. A stroke anchored on the contour at both ends with its middle outside therefore has an all-False inside mask, and `splice_extend_stroke` (`outer_splice.py:136-137`) returns None - the stroke is skipped. Symptom: extend does nothing.
2. **The APPLY-path no-op warning is dead code.** `_resolve_outer_override_local` (`authoring_pipeline.py:269`) detects a skipped splice with `spliced_world is outer_world_raw`, but `splice_extend_strokes` always returns a fresh list, so the identity test never trips and the "stroke ignored" warning never prints. The preview path already carries the value-equality fix with a comment naming this exact trap (`authoring_pipeline.py:350-353`); the apply path was never aligned. Symptom: the no-op stays silent.
3. **Arc selection conflates draw direction with seam wrap - the artifact generator.** When a stroke does splice, `_splice_outside_run` (`outer_splice.py:77-102`) anchors at the outer verts nearest to the last-inside / first-re-entry stroke samples and picks the replaced arc purely by comparing the two indices. Two failure modes: (a) with sparse pen clicks the inside anchors sit far from the actual boundary crossing, so the outside run is spliced into the wrong stretch of contour, producing self-intersections; (b) a stroke drawn against the contour winding, or across the walker's seam at index 0, hits the `exit < entry` branch (`outer_splice.py:99-101`), which keeps only `outer[exit..entry]` and throws away the rest of the silhouette. The artist cannot see the winding or the seam, so a large fraction of extend gestures mangle the contour. The existing unit file (`tests/automesh/test_outer_splice.py:40-56`) asserts only weak properties (one vert above the old top, length >= 6) and passes even when the bump splices into the bottom edge - in its own fixture the four outer verts are equidistant from the inside anchor, so the insert point is arbitrary.
4. **Stage 2 cut has no preview by design, reading as a no-op.** Cut strokes carve corridor holes at APPLY only - `compute_outer_preview` ignores them (`authoring_pipeline.py:334-342`) and `_outer_preview_relevant` skips refresh for cut-only commits (`automesh_authoring.py:818-825`). During the stage the only feedback is the red stroke line; the silhouette changes nothing until APPLY.

A dispatch trap feeds the same report: hold-Shift-and-click (the standard Blender modifier idiom) never enters draw mode, because any non-modifier press clears the pending tap (`automesh_authoring.py:443-449`), and a plain outer-stage click is a no-op by design (`automesh_authoring.py:534-538`). Only a clean tap-then-release toggles the pen, which the cursor tooltip states but deep habit fights.

**Fix is cheaper than narrowing Stage 2 - what the code says.** The toggle-pen machinery (dispatch, overlay, persistence, statusbar chords) is shared with Stage 4, which works; the broken part is ~165 lines of pure bpy-free geometry plus one dead identity check. Fix direction: anchor the splice at the actual stroke/contour segment crossings (unambiguous edge indices, winding-independent, no dependence on classifying snapped endpoints), treat on-boundary samples as inside for the extend mask, align the apply-path no-op check with the preview's value-equality fix, and harden the weak unit file - all headless-testable. Narrowing scope instead would rip the pen wiring, outer-stroke persistence, spliced preview, overlay kwargs and statusbar chords out of Stage 2 across more files than the fix touches, and would amputate the modal's main value - the bug entry itself calls extend/cut the point of the interactive modal. GUI cost of the fix is one re-run of scenarios already queued unchecked (backlog-manual-testing 1.23 T1, 1.25 T6/T9).

**Panel and props rows, verified open.** `automesh_resolution` is still named `Mesh resolution` with the inverted semantic spelled out in its own description (`scene_props.py:80-89`). `automesh_density_under_bones` still defaults True (`scene_props.py:171-179`), and the one-shot operator copies the PG at invoke (`automesh.py:181`), so flipping both defaults is the whole change. `Interior spacing` still sits in the dense-only greyed block (`mesh_generation.py:148-151`) even though the modal reads it in SIMPLE mode too - free-draw resample spacing and pick radius (`automesh_authoring.py:1224-1227`) and the fold-line snap radius (`authoring_pipeline.py:778`) - so the grouping move is semantically right, not just cosmetic. The regen entry points show only `preserve_base_quad` (`mesh_generation.py:146`) while `Preserve weights on regen` (`scene_props.py:273`) surfaces nowhere near the buttons that trigger regen. The button copy is still `Automesh (modal)` under a "Multi-stage modal preview" label (`mesh_generation.py:174,185`); renames must sync `help_topics.py:747,750` and `docs/02-blender-addon/05-mesh-generation.md` (the guide-page mention belongs to the guide-doc rename sweep owned by the ui-help-surfaces spec).

**Element gating, verified open.** The **Mesh Generation** panel polls any MESH (`_active_is_mesh`, `mesh_generation.py:31-34`) and the one-shot operator polls type-only (`automesh.py:165-168`), so both run on a `sprite` element and silently replace its quad - while the **Weight Paint** panel already gates correctly on `element_type == "mesh"` (`_is_mesh_element`, `weight_paint.py:25-31`). The gate is a copy of a shipped pattern plus a pure validation rule (sprite mesh = 4 verts, 1 face).

### Research notes

- **Spine** ([Mesh attachments](http://en.esotericsoftware.com/spine-meshes), [Mesh Tools view](http://esotericsoftware.com/spine-mesh-tools), [blog: vertex placement](https://esotericsoftware.com/blog/Mesh-creation-tips-vertex-placement)): ships manual and automatic as peers - `New` mode places hull verts click by click (close by clicking the first vert) and `Trace` auto-generates ("created slightly differently each time", re-run and pick), with `Generate` as the hybrid that auto-fills the interior after the artist hand-places the verts that matter. Manual placement is not the single primary path; it is the taught precision half of a standard hybrid, and the vertex-placement blog treats deliberate placement as the pro skill.
- **Live2D Cubism** ([Automatic Mesh generator](https://docs.live2d.com/en/cubism-editor-manual/mesh-edit/), [Edit Mesh manually](https://docs.live2d.com/en/cubism-editor-manual/mesh-edit-manual/)): the manual recommends auto-generation for bulk initial meshing and manual point-by-point meshing for the parts that deform hardest (eyebrows, eyelashes, mouth).
- **Moho** ([Moho 14 features](https://moho.lostmarble.com/pages/features), [quad-mesh tutorial](https://moho.lostmarble.com/blogs/news/moho-pro-tutorial-how-to-create-and-animate-quad-meshes)): meshes are hand-drawn with the vector tools (quads + triangles, sharp corners + auto-weld); automatic mesh creation arrived later, in Moho 14, as convenience on top of the manual base.
- Reading for Proscenio: manual mesh authoring is a standard capability in every comparable tool, so the demand class is real, not imagined. The host changes the cost-benefit though: Spine and Cubism are closed editors that must ship a pen tool, while Blender already has Edit Mode plus this addon's `Reproject UV` and weight reprojection - the missing piece here is gesture convenience, not capability.

### Assessment

Scores: flow-value (5 = core pipeline correctness/productivity), test-burden (5 = recurring manual GUI), bug-surface (5 = new modal/stateful surface), underuse-risk (5 = speculative).

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Fix Automesh Interactive extend/cut | 4 | 3 | 1 | 2 | now | Blocking; a shipped surface broken at its main stage; the fix is pure geometry + headless tests, one already-queued GUI re-run |
| Rename "Mesh resolution" | 3 | 1 | 1 | 1 | now | Deceptive label on a core knob steers artists the wrong way; rename + help/docs sync |
| Default "Density follows bones" OFF | 2 | 1 | 1 | 2 | now | Two-line default flip (PG + operator); only DENSE sessions read it |
| Group "Interior spacing" | 2 | 1 | 1 | 2 | now | Layout move the code already justifies - the prop is not dense-only |
| Surface "preserve weights on regen" | 3 | 1 | 1 | 2 | now | Mirror an existing prop where regen runs; protects trust in the weight-preserve contract |
| Action-oriented modal button copy | 2 | 1 | 1 | 2 | now | Label-only; sync help topic and addon doc page |
| Element-type gating | 4 | 2 | 2 | 2 | now | Contract protection against silent sprite_frame breakage; copies the shipped Weight Paint gate |
| Sprite rigid single-bone bind | 2 | 3 | 3 | 4 | drop | Native bone-parenting already is the rigid bind; one help sentence in the gate warn covers discovery - an operator wrapping a one-keystroke native action is bloat |
| Manual hull authoring | 3 | 5 | 5 | 4 | gate | Real demand class everywhere in the genre, but a new modal is maximum GUI burden and Edit Mode + `Reproject UV` is a workable fallback today |

### Verdict summary

7 now, 1 gate, 1 drop, 0 defer. The now set is one blocking pure-geometry bugfix plus six small panel/props rows that batch into two PRs; nothing in it adds interactive surface. The one big-capability row (manual hull) gates on a logged real-art failure of the alpha-trace plus Edit Mode fallback, and only after the extend/cut splice it would reuse has soaked. Sprite rigid bind is proposed for pruning: the element-gating warn plus a help line pointing at native bone-parenting covers the need with zero new operators.
