# Spec 030: Skinning and weight paint

Make the weight-paint domain solid and productive - fix the bind defects, clean the panel, and add the advanced skinning tools.

## Scope

- **Fix brush-curve presets** throwing on click.
- **Fix per-bone Soft/Hard** being inert under the default Bone Heat mode.
- **Surface Weight Transfer max distance** in the panel.
- **Warn on out-of-range Weight Transfer** - flag silent zero-coverage targets.
- **Name the target armature** in the Bind subpanel.
- **Flat-mesh weight display** that does not hide the texture.
- **Clear a per-bone override** - add the missing clear path.
- **Reorder the Bind button** after the overrides box.
- **Sidecar Import applies to live weights** - not just write Custom Properties.
- **Unify "Snapshot" and "Sidecar IO"** naming.
- **Weight-preserving PSD re-import** - snapshot and restore weights around a re-import.
- **Soft/Hard runtime per-bone toggle**.
- **Bone-strength region painting** - a Moho-style influence gizmo.
- **Live pose-mode preview** inside weight paint.
- **Auto-patch joint cover** at articulations.
- **Cubism-style glue seam-bind**.
- **Smart-bone corrective drivers**.
- **Mirror humanoid binding** in one operator.
- **Bezier brush stroke** for alpha-boundary tracing.

## Study

### Surface notes

The domain spans the **Weight Paint** panel family (`apps/blender/panels/weight_paint.py`: parent plus **Bind**, **Edit Weights**, **Snapshot**, **Sidecar IO**, **Weight Transfer** subpanels), the bind engine (`core/bpy_helpers/skinning/bind_apply.py`), the per-bone mode store (`core/skinning/bone_modes.py` + `operators/skinning/set_bone_mode.py`), the transfer operator (`operators/skinning/copy_weights_to_selected.py`), sidecar IO (`operators/skinning/sidecar_io.py`, `operators/skinning/restore_weight_snapshot.py`), and - for the re-import item - the Photoshop importer (`importers/photoshop/planes.py`).

- **Brush presets throw on click.** `operators/skinning/brush_preset.py:40-45` mutates the live RNA `CurveMapPoints` collection: truncate to the 2-point floor via repeated `points.remove(points[-1])`, set `.location` in place on indices 0-1, then `points.new(x, y)` for the rest, then `update()`. `CurveMapPoints` reallocates on `remove` and re-sorts by x on `new`, so in-place writes and held proxies are fragile across the mutation sequence; the exact traceback was never captured (the bug entry asks for it first). The robust shape proposed in the bug entry stands: rebuild in ascending-x order, refetch proxies after every collection mutation, and wrap in try/except that downgrades to a `WARNING` report instead of propagating a RuntimeError.
- **Curve-rebuild cross-check (automesh extend/cut, owned by the mesh-authoring spec): not one root cause.** The automesh splice is `core/automesh/outer_splice.py` - a pure-Python polyline list surgery (`_splice_outside_run` slices and concatenates point lists; no bpy import in the module), fed by the toggle-pen event dispatch in `operators/automesh/automesh_authoring.py:242-247` (`_mod_tap_kind` / `_pen_kind` state). Its failure modes are silent: wrong nearest-anchor indices, degenerate runs, or taps never reaching the pen state machine - producing no-ops or mesh artifacts. The brush-preset failure is a bpy RNA collection mutation raising an exception on click. Same superficial truncate/set/new shape, but different layers, zero shared code, and opposite failure modes (exception vs silent geometry). Two independent bugs; neither fix informs the other.
- **Per-bone Soft/Hard is inert in the default mode, and the code half-knows.** `apply_bind` early-returns into `_apply_bone_heat` for `BONE_HEAT` (`bind_apply.py:207-208`) before `_apply_bone_mode_overrides` (`:231`); `_merge_per_bone_weights`'s own docstring documents that bones absent from the hard matrix "(e.g. BONE_HEAT path) keep the soft column unconditionally" (`:62-69`). Meanwhile `_draw_bind` draws the overrides box unconditionally (`weight_paint.py:204-223`) and `BONE_HEAT` is the recommended default (`properties/scene_props.py:226-228`). The honest fix is UI gating: show the box only under the planar modes, with a hint label under Bone Heat. A post-pass that recomputes overridden bone columns planar-side and splices them into the heat result is possible (the merge machinery exists) but is new capability on the default path - gate it on someone actually asking for per-bone control without switching to `Proximity`.
- **Soft/Hard runtime toggle is the same item.** The toggle, store, and rebind path all exist and work under the planar modes (`bind_apply.py:231`, `bone_modes.py`); the only gap is the inert default plus the missing clear path. Fixing those completes the backlog row - no standalone work remains.
- **No clear path for an override, by construction trivial to add.** `set_bone_mode.py:36-43` enums only `SOFT`/`HARD`; `write_bone_modes` (`bone_modes.py:37-39`) serializes a whole dict, so clearing is popping the key and rewriting - a third enum item plus a button per row.
- **Weight Transfer hides its one parameter and its one failure mode.** `max_distance` is an F9-only operator property (`copy_weights_to_selected.py:24-30`); the panel draws a bare button (`weight_paint.py:168-169`). `_apply_to_target` counts only verts that received weights; targets fully beyond the radius silently get `{}` per vert and the INFO line still reads as success (`:44-51`). Per-target `X/Y verts` coverage plus a `WARNING` at zero coverage is pure counting logic, headless-testable.
- **Sidecar Import stores but never applies.** `sidecar_io.py:80-85` validates the JSON and writes the Custom Property only; pushing to live vertex groups requires `Reset to Last Saved Weights`, which hard-aborts on topology-hash mismatch (`restore_weight_snapshot.py:75-85`). Import can safely chain the apply when the file's topology hash matches the live mesh, and report "stored only - topology differs" when it does not.
- **PSD re-import is the one real data-loss pit in the domain.** `planes.py:_ensure_mesh` unconditionally runs `clear_geometry()` plus a fresh quad (`:246-259`); the module docstring documents that painted weights and automesh densification are lost (`:12-19`). Two code facts sharpen the fix. First, object-level Custom Properties survive re-import - including `proscenio_weight_sidecar`, so the UV-anchored painted weights are still sitting on the object after the wipe, with no code path able to reapply them (restore aborts on the hash mismatch). Second, the exact snapshot/reproject pair this needs already shipped for automesh regen (`core/bpy_helpers/skinning/automesh_hook.py`: `maybe_pre_regen_snapshot` / `maybe_post_regen_reproject`, UV-anchor reprojection, no-op-safe when `preserve_on_regen` is off). Cheapest loss-free path for the common case: short-circuit the rebuild when the layer's placement size and offset are unchanged (art retouch, same bounds - mesh and weights untouched). For changed bounds, wire the hook pair around `_ensure_mesh`: weights reproject onto the fresh quad (degraded to 4 anchors; a follow-up automesh regen with preserve on redistributes them). This is flow protection on the PSD -> Blender leg, not new capability, and it is headless-coverable end to end (import, bind, paint, re-import, assert).
- **What Blender natively covers that the aspirational items duplicate.** Posing bones while weight painting is native mixed mode (bone select and rotate, timeline scrub, live deformation - no modal needed). Viewport Overlays expose a weight-paint opacity slider (texture shows through the gradient) and a zero-weights display option - the cheap answer to the flat-mesh display item, with the upstream caveat that opacity 0 does not fully hide the overlay (Blender issue 145603). Bone envelopes (display plus <kbd>Ctrl+Alt+S</kbd> radius scaling) are the native influence-region surface; the addon's `ENVELOPE` bind already consumes a per-bone radius (`proscenio_envelope_radius`, read in `bind_apply.py:108-116`, today CP-only with no UI).

### Research notes

- **Moho manual (Bone Tools) + Lost Marble forum threads**: flexi-binding (per-bone strength falloff over all points) is Moho's default; region binding (per-bone cutoff radius) is the cleaner-movement refinement that "requires a little extra setup". The pair maps one-to-one onto the shipped `Proximity` and `Envelope` bind modes - the Moho influence concept already exists here, minus a gizmo.
- **Moho features page + Anime Studio Tutor webinar**: smart bones are genuinely central to Moho rigging (joint correction, face and body turns) - the demand inside Moho is real, not imagined.
- **Digital Production on Moho 14.4 game-engine export**: smart bones export as morph targets / shape keys - they presuppose a vertex-morph track in the target runtime. The Proscenio schema has no morph track and Godot's Polygon2D has no blendshape, so a Blender-side corrective would author data with no export path.
- **Live2D Cubism editor manual (Glue)**: glue binds vertices of two ArtMeshes with a 0-100 weight bias, used for neck and shoulder seams; it is honored by the Cubism runtime and carries an editing caveat (unbind before editing the mesh or shapes corrupt). Godot has no vertex-stitch runtime constraint, so an authoring-side glue cannot round-trip.
- **Blender Studio Fundamentals 4.5 (weight painting) + Blender 5.1 manual**: posing bones inside Weight Paint mode is the documented native workflow, including playback while painting; Viewport Overlays carry the weight-paint opacity and zero-weights options. Upstream issue 145603 notes the opacity slider never reaches fully invisible.
- **Blender tracker T54526 + Blender Artists data-transfer threads**: Blender's own Data Transfer max-distance has a silent-failure history (stale nearest-index false positives, "weights will not transfer" reports) - precedent that max distance must be visible and zero coverage must warn.
- **Spine User Guide (Weights view) + Esoteric blogs (Mesh binding, Automatic skinning weights)**: the Spine loop is bind selected bones, auto weights, then adjust against test poses in animate mode; the documented workflow has no mirror-weights surface; seams are handled by overlapping per-limb attachments weighted across the joint.
- **Cutout art-prep guides (Animation and Video / Cartoon Animator series, Unity 2D rigging courses)**: characters are split into per-limb layers with rounded overlap caps drawn at the joints; left and right limbs are separate drawings, and the standard 3/4-view presentation makes them non-congruent. The "most cutout characters are asymmetric" claim holds for the typical case: there is usually no symmetric mesh for a mirror-bind to act on, and no Proscenio fixture exercises a symmetric rig end to end.

### Assessment

Flow value: 5 = protects the core PSD -> Blender -> export -> Godot flow. Test burden: 1 = pure unit, 5 = recurring manual GUI. Bug surface: 1 = bugfix, 5 = new modal/stateful surface. Underuse risk: 1 = universal, 5 = speculative lift.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| Fix brush-curve presets | 3 | 2 | 1 | 1 | now | Blocking; shipped affordance throws on click; robust rebuild is contained and headless-coverable |
| Fix per-bone Soft/Hard inert under Bone Heat | 4 | 2 | 1 | 1 | now | Blocking; the default mode lies; honesty gate in the panel, post-pass override engine gated on demand |
| Surface Weight Transfer max distance | 3 | 2 | 1 | 2 | now | One hidden parameter controls the whole operator; pull-forward tagged |
| Warn on zero-coverage Weight Transfer | 4 | 1 | 1 | 1 | now | Silent failure on a shipped path; Blender's own data transfer has the same documented pitfall; pure counting logic |
| Name the target armature in Bind | 2 | 2 | 1 | 1 | now | One label; restores context lost from the parent readout |
| Flat-mesh weight display | 3 | 2 | 1 | 2 | now | Native overlay opacity + zero-weights display already solve it; expose the lever, do not build a custom overlay (that part gated) |
| Clear a per-bone override | 3 | 2 | 1 | 1 | now | UX trap - state is currently irreversible; third enum item plus dict-key pop |
| Reorder the Bind button | 2 | 2 | 1 | 1 | now | Draw-order swap riding the same `_draw_bind` pass |
| Sidecar Import applies to live weights | 3 | 2 | 2 | 2 | now | Import that visibly does nothing erodes trust; apply-when-hash-matches reuses `apply_sidecar` |
| Unify Snapshot / Sidecar IO naming | 2 | 2 | 1 | 1 | now | Copy change; "sidecar" stays internal-only per the UI feedback |
| Weight-preserving PSD re-import | 5 | 3 | 3 | 1 | now | Closes the domain's one data-loss pit on the core iteration loop; sidecar already survives the wipe and the snapshot/reproject hooks already shipped for automesh regen |
| Soft/Hard runtime per-bone toggle | 3 | 2 | 1 | 2 | now | Merged: toggle + rebind already work under planar modes; the inert-default fix plus the clear path complete it |
| Bone-strength region painting | 2 | 5 | 5 | 4 | drop | Duplicates the shipped Envelope bind + native bone envelopes with a new gizmo surface; Moho itself treats region binding as the non-default refinement |
| Live pose-mode preview | 2 | 5 | 4 | 4 | drop | Native Blender already poses bones live inside Weight Paint mode; document the native combo instead of rebuilding it in a modal |
| Auto-patch joint cover | 2 | 4 | 5 | 5 | gate | Art-prep convention (overlap caps at joints) plus seam weighting covers the need; trigger: a humanoid fixture ships end to end AND the artist reports articulation gaps that overlap art plus weight blending cannot hide |
| Cubism-style glue seam-bind | 1 | 4 | 5 | 5 | drop | Cannot round-trip: Godot has no vertex-stitch runtime constraint, so glue would author data the export must discard |
| Smart-bone corrective drivers | 2 | 4 | 5 | 4 | drop | Requires a morph/vertex track the schema does not have and Polygon2D cannot play; re-propose only inside a future schema-level morph feature |
| Mirror humanoid binding | 1 | 3 | 3 | 5 | drop | Cutout limbs are separate asymmetric drawings (3/4-view standard); no symmetric mesh to mirror, no symmetric fixture, and brush X-mirror already covers the single-mesh case |
| Bezier brush stroke | 2 | 5 | 4 | 5 | drop | Silhouette authoring belongs to the mesh-authoring spec; polyline strokes + arc-length resample already smooth contours; highest-burden test class (stroke feel) with zero demand signal |

### Verdict summary

12 now, 1 gate, 6 drop. The now set is two blocking bind bugfixes, eight small panel and operator corrections (one of which, the runtime toggle, is completed by the bugfix rather than new work), and one flow-protection item (weight-preserving PSD re-import) promoted because it closes a real data-loss pit with machinery that already shipped. The aspirational cluster lifted from the tool survey does not survive contact with the export contract or with native Blender: one item gates on a concrete humanoid-fixture trigger, five drop. Two now items carry explicitly gated extensions (the Bone Heat per-bone post-pass; a Spine-style custom weight overlay) so the cheap fix cannot silently grow into the expensive one. Recommendation: land the two blocking fixes first, batch the panel corrections into two small PRs, close with the re-import protection - and prune the dropped rows from the backlog files in the same pass.
