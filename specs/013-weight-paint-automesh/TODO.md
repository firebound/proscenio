# SPEC 013 - TODO

Weight paint ergonomics + automesh. See [STUDY.md](STUDY.md) for the full design + decisions D1-D16 (locked at planning time after 9-tool survey + 6-theme community-pain synthesis). Wave 13.1 = first cut (D1-D15 minus D16). Wave 13.2 = productivity polish (Animate soft/hard, Moho region painting, weight transfer between sprites, multi-mesh batch bind). Wave 13.3+ = aspirational (Auto-Patch, Glue equivalent).

## Decision lock-in

- [ ] D1 - automesh paradigm = alpha-trace one-shot (pure-Python, no OpenCV).
- [ ] D2 - mesh topology shape = annulus (outer + inner contour + `bmesh.ops.triangle_fill`).
- [ ] D3 - mesh data preservation anchor = `proscenio_base_sprite` vertex group; re-runs remove only verts NOT in this group.
- [ ] D4 - bone heat solver usage = explicit user opt-in only, NEVER default. No default-bind code path may call `parent_with_automatic_weights` blind.
- [ ] D5 - initial bind algorithm default = planar proximity falloff (custom, NOT bone heat); enum offers PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY (no BONE_HEAT in first cut).
- [ ] D6 - weight preservation through mesh regen = sidecar JSON keyed by UV anchors + auto-reproject on regen + visible provenance overlay.
- [ ] D7 - weight paint modal wrapper = one-button enter / exit, auto-restore on exit + crash; lift COA2 `COATOOLS2_OT_EditWeights` pattern (fixed: Bone Collections instead of `bone.hide` global, `try/finally` restore, ESC hard-exit).
- [ ] D8 - 2D paint preset = auto-apply on modal enter (`Front Faces Only=False`, `Falloff=Projected`, brush radius in screen px, `Auto Normalize=True`); header pill "2D paint preset: ON".
- [ ] D9 - GPU weight overlay viz = colorband discs per vertex (lift COA2 6-stop colorband, alpha 0 for zero-weight verts).
- [ ] D10 - ESC in any draw modal = hard exit + release pending stroke; no conditional behaviour.
- [ ] D11 - pre-flight diagnosis on auto-weight failure = structured guidance per failure cause; pre-flight detects unapplied scale / flipped normals / overlapping verts / isolated islands / bones outside mesh bbox; emits actionable message (never raw stack trace).
- [ ] D12 - tablet RELEASE detection = `event.pressure==0` + `WINDOW_DEACTIVATE` + timer-based fallback (synthesize RELEASE if no movement for N ms).
- [ ] D13 - subpanel placement = new `Skinning` subpanel parallel to `Skeleton` in the Proscenio sidebar.
- [ ] D14 - symmetry mirror axis source = picker armature mirror flag (single source of truth, parallel to SPEC 012 D16 contract).
- [ ] D15 - density-under-bones automesh = ON by default when picker has armature, OFF otherwise; reuse picker bone positions.
- [ ] D16 - soft vs hard bone toggle = defer to Wave 13.2 (first cut covers via `bind_init_mode` PROXIMITY vs SINGLE_NEAREST).

## Wave 13.1 - core surface (Blender)

Branch: `feat/spec-013-weight-paint-automesh` (or split into 13.1.a automesh + 13.1.b bind + 13.1.c paint per PR-size budget). Target: ship D1-D15 in ~5 commits + tests + docs + smoke.

**Goal:** make weight painting in Proscenio tractable for the average 2D cutout user. After this wave a user can take a PNG sprite + a Quick-Armature-authored rig and produce a bound, weighted, exportable mesh in under 5 minutes without leaving the addon's panel.

### 13.1.a - Pure-Python automesh (D1 + D2 + D3 + D15)

**Goal:** turn a sprite (image-textured plane OR imported `[mesh]` layer) into an annulus mesh whose density follows the picker armature's bones, without any third-party Python dependencies.

- [ ] `core/alpha_contour.py` (pure Python, bpy-free): walk the alpha channel via Moore neighbour contour tracing. Input = `list[list[int]]` alpha grid (0-255). Output = outer + inner contour as `list[tuple[int, int]]`. Configurable threshold + margin (pixel dilate / erode).
- [ ] `core/automesh_geometry.py` (pure Python, bpy-free): given outer + inner contours, build annulus topology vertex list + edge list ready for `triangle_fill`. Resampling via Laplacian smoothing (3 iterations) + arc-length resample to even spacing. Configurable interior subdivision density.
- [ ] `core/automesh_density.py` (pure Python, bpy-free): given bone segments (list of `(head_xz, tail_xz)`) + base interior vertex grid, return additional subdivision points clustered within configurable radius of each bone segment. Falls back to uniform density when no bones given.
- [ ] `core/bpy_helpers/automesh_bmesh.py` (bpy-bound): consumes pure-Python output from above; reads `bpy.types.Image.pixels` buffer (flat float array, 4 channels) into the alpha grid format; writes annulus topology via `bmesh.ops.triangle_fill`; tags the original quad's 4 verts in `proscenio_base_sprite` vertex group before any regen; re-runs delete only verts NOT in `proscenio_base_sprite`.
- [ ] `operators/automesh.py` - `PROSCENIO_OT_automesh_from_sprite`. `bl_options = {"REGISTER", "UNDO"}`. Reads `scene.proscenio.skinning.{automesh_resolution, automesh_alpha_threshold, automesh_margin, automesh_density_under_bones}`. F3 redo panel exposes overrides.
- [ ] Operator pre-flight: detect missing image texture, zero-area alpha (all-transparent sprite), oversized image (warn at >4096 dim per side), missing picker armature when `automesh_density_under_bones` is True (auto-fallback to uniform with INFO report).
- [ ] Operator integrates with SPEC 011 `[mesh]`-tagged imports: preserves `proscenio_psd_kind = "mesh"` custom property; merges with existing topology rather than replacing when the mesh already has non-base-sprite verts (warn + offer "Replace all" via redo).

**Tests** (pytest, bpy-free):

- [ ] `tests/test_alpha_contour.py` - synthetic 8x8 / 16x16 / 64x64 alpha grids covering: square sprite, L-shape, donut (validates outer-only since "no holes" follows Spine contract), single-pixel sprite (degenerate fallback), all-transparent (raises ValueError).
- [ ] `tests/test_automesh_geometry.py` - annulus vertex/edge count invariants, contour-smoothing convergence (3 iterations -> stable point positions), arc-length resample maintains expected vertex count.
- [ ] `tests/test_automesh_density.py` - bone-density subdivision adds verts within radius of bone segments, fallback to uniform when no bones, vertex count scales linearly with bone count.

### 13.1.b - Planar proximity bind (D4 + D5 + D11)

**Goal:** bind a mesh to a bone chain via a custom planar-distance algorithm that never hits the bone-heat solver, and surface structured diagnosis when something goes wrong.

- [ ] `core/planar_proximity.py` (pure Python, bpy-free): given vertex positions (`list[tuple[float, float]]` on XZ plane) + bone segments (`list[tuple[head_xz, tail_xz, name]]`), return per-vertex weights as `dict[bone_name, list[float]]`. Algorithm = `1 / distance_to_segment ^ falloff_power` normalized across bones, with hard cutoff at configurable max distance. Default falloff_power = 2.0.
- [ ] `core/bind_diagnosis.py` (pure Python + bpy boundary): pre-flight checks. Each check returns `BindDiagnosis(kind: Literal["scale", "normals", "overlap", "islands", "bone_bbox"], severity: Literal["error", "warn"], message: str, hint: str)`. Boundary helper `collect_diagnoses_for_object(obj, armature) -> list[BindDiagnosis]` wraps bpy reads.
- [ ] `core/skinning_modes.py` (pure Python, bpy-free): `BindMode = Literal["PROXIMITY", "ENVELOPE", "SINGLE_NEAREST", "EMPTY"]` + `bind_weights_for_mode(mode, vertex_positions, bone_segments) -> dict[str, list[float]]`. Dispatch by mode; PROXIMITY delegates to `planar_proximity`, SINGLE_NEAREST picks closest bone per vertex, ENVELOPE uses bone envelope radius, EMPTY returns all-zero dict.
- [ ] `operators/bind_mesh.py` - `PROSCENIO_OT_bind_mesh_to_armature`. Reads `scene.proscenio.skinning.bind_init_mode`. F3 redo override. Source of armature = picker (SPEC 012 D16); fails fast with structured guidance if picker is unset.
- [ ] Pre-flight runs before any weight calculation; severity `error` aborts with INFO report + suggested fixes; severity `warn` continues with WARNING. Each diagnosis kind has a documented remedy string.
- [ ] Bind writes vertex groups via `obj.vertex_groups.new` + `vertex_groups[name].add(index_list, weight, "REPLACE")`. Always normalizes per-vertex sums to 1 (matching SPEC 003 D1 writer contract; user gets canonical weights even before paint).
- [ ] Sidecar capture hook (per D6): immediately after bind, write `obj["proscenio_weight_sidecar"]` snapshot of the just-generated weights keyed by UV.
- [ ] Operator option `use_bone_heat: BoolProperty(default=False, description="Use Blender's heat-diffusion (legacy / experimental)")` for users who insist - per D4 this is opt-in only and ungated, including in panel UI (only F3 redo).

**Tests** (pytest, bpy-free):

- [ ] `tests/test_planar_proximity.py` - 4-vertex square + 1 bone gives all 4 verts weight 1.0 to that bone; 2 bones equidistant give 0.5 / 0.5; bone outside max distance gives 0.
- [ ] `tests/test_skinning_modes.py` - each enum case produces expected shape; EMPTY returns zero-weights; SINGLE_NEAREST never emits weight on more than one bone per vertex.
- [ ] `tests/test_bind_diagnosis.py` - synthetic objects via SimpleNamespace exercise each diagnosis kind: unapplied scale, flipped normal (manually constructed face), overlapping verts (two verts at same coord), isolated islands (two disjoint face groups), bones outside bbox.

### 13.1.c - Weight paint modal wrapper (D7 + D8 + D9 + D10 + D12 + D14)

**Goal:** one-button entry into a 2D-safe weight paint context with custom overlay, with hard guarantees on exit cleanup and ESC handling.

- [ ] `core/paint_preset_2d.py` (pure Python, bpy-free): pure-data record of brush settings to apply / restore. `PaintPresetSnapshot` frozen dataclass with all 8 toggles (Front Faces Only, Falloff Shape, brush radius, Auto Normalize, Use Symmetry X/Y/Z, brush Strength). `apply_preset(snapshot) -> PaintPresetSnapshot` returns previous values for restore.
- [ ] `core/bpy_helpers/paint_preset_bind.py` (bpy-bound): reads brush settings from `context.tool_settings.weight_paint`, calls pure-Python apply, writes back. Mirror axis pulled from `scene.proscenio.active_armature` mirror flag (D14).
- [ ] `core/bpy_helpers/weight_overlay.py` (bpy-bound): GPU `draw_handler_add` callback drawing 6px filled discs per vertex coloured by the active vertex group weight via a 6-stop colorband (red->orange->yellow-green->green->cyan->blue). Alpha 0 for zero-weight verts. Optional toggle to draw provenance instead of value (D6 hook).
- [ ] `operators/edit_weights.py` - `PROSCENIO_OT_edit_weights_modal`. Modal flow:
  - `invoke`: snapshot brush + viewport + Bone Collections + active object + selection. Switch armature to POSE; mesh to WEIGHT_PAINT; apply 2D paint preset; auto-select vertex group matching first selected pose bone; register `weight_overlay` draw handler; register `STATUSBAR_HT_header.prepend` icon hint ("ESC exit | Mirror: ON | 2D preset: ON"); register `VIEW3D_HT_header.append` matching hint (lift SPEC 012 D6 pattern).
  - `modal`: ESC = hard exit (D10), pass-through for all paint events (Blender brush owns LMB/MOUSEMOVE), `WINDOW_DEACTIVATE` triggers a "release in-flight stroke" guard via `bpy.ops.paint.weight_paint('INVOKE_DEFAULT', stroke=[])` no-op to flush Blender's brush state. D12 tablet pressure release uses `event.pressure` introspection when available.
  - `_finish` / `cancel`: restore brush + viewport + Bone Collections + active + selection via `try/finally`. Unregister handlers + headers. Wraps cumulative paint in single `bpy.ops.ed.undo_push(message="Edit Weights: N strokes")`.
- [ ] `core/bone_collection_visibility.py` (bpy-bound): replace COA2's `bone.hide` global-flag approach with Blender 4.0+ Bone Collections visibility (`armature.data.collections[i].is_visible`). Snapshot + restore round-trip; undo-stack-aware.
- [ ] Header pill renders via `_draw_statusbar_edit_weights(self, context)` reused-pattern from SPEC 012 D6 refinement (`_emit_chord_layout` helper). Pill icons: `EVENT_ESC`, `MOD_MIRROR`, `BRUSHES_ALL` (or similar 2D-paint-indicating icon).
- [ ] Crash safety: any exception in modal body or in `invoke` body must hit `_finish` via `try/except/finally` so the user never wakes up with bones hidden or brush in wrong state. Log to console; report INFO with restoration message.

**Tests** (pytest, bpy-free):

- [ ] `tests/test_paint_preset_2d.py` - apply_preset returns prior values; round-trip via `apply_preset(apply_preset(snap).previous) == snap` (idempotent restore).
- [ ] `tests/test_bone_collection_visibility.py` - snapshot + restore via SimpleNamespace mocks; covers empty-collections edge case and Blender-3.x-fallback (when `data.collections` does not exist).
- [ ] Headless modal tests deferred - modal state is hard to exercise without booting Blender; manual smoke covers it. Document the smoke checklist in `tests/MANUAL_TESTING.md`.

### 13.1.d - Weight sidecar + reproject (D6) - **the differentiator**

**Goal:** make automesh regen non-destructive. Once a user has painted weights, regenerating the mesh at a different resolution preserves their work via UV-anchored re-projection.

- [ ] `core/weight_sidecar.py` (pure Python, bpy-free): `WeightSidecar` dataclass:
  - `vertex_group_names: list[str]`
  - `entries: list[WeightSidecarEntry]` where entry = `(uv_anchor: tuple[float, float], weights: dict[group_name, float], provenance: Literal["user_paint", "auto_seed", "reprojected"])`
  - `mesh_topology_hash: str` (sha1 of vertex count + face indices, used to detect topology change)
- [ ] `core/weight_reproject.py` (pure Python, bpy-free): `reproject(sidecar, new_vertex_uvs) -> dict[group_name, list[float]]`. For each new vertex, find the 3 nearest UV anchors in the sidecar (KD-tree or simple sort for small meshes), barycentric-interpolate weights, mark as `reprojected` provenance. Verts with no close-enough anchor fall back to fresh proximity seed and are marked `auto_seed`.
- [ ] `core/bpy_helpers/sidecar_io.py` (bpy-bound): serialize WeightSidecar to JSON, write to `obj["proscenio_weight_sidecar"]` Custom Property (raw CP, not PG - survives addon disable per SPEC 005 storage rules). Read back on demand.
- [ ] `operators/automesh.py` (13.1.a above): when `scene.proscenio.skinning.preserve_on_regen` is True and the object has an existing sidecar with non-zero entries, automatically: (a) snapshot current weights into sidecar refresh, (b) regenerate mesh, (c) call `reproject` to seed weights on new topology, (d) report INFO with counts ("Restored 187 user-paint vertices, seeded 42 new vertices from proximity").
- [ ] `operators/restore_weight_snapshot.py` - `PROSCENIO_OT_restore_weight_snapshot`. Re-applies the sidecar to the current mesh without regen (useful when user's last automatic reproject went wrong).
- [ ] Provenance hooks: bind operator (13.1.b) tags all vertices `auto_seed` after first bind; edit weights modal (13.1.c) tags any vertex the user paints `user_paint` via a pre/post-modal diff. Provenance pill in the panel: "187 paint / 42 seed / 0 reprojected."
- [ ] Vertex provenance overlay: weight overlay (13.1.c) gains a toggle to recolour discs by provenance instead of weight value (user_paint = white outline, auto_seed = gray, reprojected = cyan).

**Tests** (pytest, bpy-free):

- [ ] `tests/test_weight_sidecar.py` - serialize/deserialize round-trip, topology hash detects changes, JSON shape stable.
- [ ] `tests/test_weight_reproject.py` - identical-topology reproject = no-op (every vert matches its own UV anchor); coarser-to-finer mesh reproject interpolates correctly; verts with no close anchor fall back to auto_seed; provenance counters match expected.

### 13.1.e - PropertyGroup + panel + integration (D13)

- [ ] `properties/scene_props.py` extend with `ProscenioSkinningProps` PropertyGroup (per STUDY Design surface > Property model). Pointer wired on `ProscenioSceneProps.skinning`.
- [ ] `panels/skinning.py` - new `PROSCENIO_PT_skinning` subpanel parallel to `PROSCENIO_PT_skeleton`. Layout:
  - "Picker armature" row (mirror of Skeleton picker, read-only view + jump-to-Skeleton-panel button if unset).
  - "Automesh" sub-box: resolution / alpha threshold / margin / density-under-bones toggle + `Automesh from Sprite` button.
  - "Bind" sub-box: `bind_init_mode` dropdown + `Bind to Picker Armature` button.
  - "Edit Weights" sub-box: 2D preset toggle + `Edit Weights` button (launches modal).
  - "Snapshot" sub-box: preserve-on-regen toggle + `Restore Snapshot` button + sidecar provenance counts ("187 paint / 42 seed / 0 reprojected" if sidecar exists, else "no snapshot").
- [ ] Panel polling: only show subpanel when active object is mesh-type. Show "Pick an armature in Skeleton panel" warning when picker is unset.
- [ ] Operator buttons disabled with explanatory tooltip when prerequisites unmet (e.g. `Edit Weights` disabled with "Bind to picker armature first" when no vertex groups exist).
- [ ] F3 search discoverability: all 5 operators registered with descriptive `bl_label`. `bl_description` short and links to the panel.

### 13.1.f - Docs + smoke

**Docs:**

- [ ] [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) gains "Weight paint modal pattern" subsection (companion to SPEC 012's "Modal overlay pattern" and "Modal operator hint placement"). Covers the snapshot + apply + restore pattern + try/finally crash safety + Bone Collections visibility approach.
- [ ] [`.ai/skills/blender-dev.md`](../../.ai/skills/blender-dev.md) gains "Pure-Python contour walking" subsection documenting why automesh does not use OpenCV (constraint reasoning + COA2 adoption lesson).
- [ ] [`.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md) - "Skinning weights" section already covers the wire format (SPEC 003). Cross-reference SPEC 013 as the authoring story.
- [ ] [`tests/MANUAL_TESTING.md`](../../tests/MANUAL_TESTING.md) - new section 1.15 "SPEC 013 weight paint + automesh" with smoke checklist (T1 invoke automesh on a hand sprite, T2 verify annulus topology, T3 bind to picker chain, T4 enter edit weights modal, T5 paint a few strokes, T6 regen automesh at higher resolution, T7 verify weights restored + provenance counts).

**Smoke fixture:**

- [ ] Reuse `examples/generated/atlas_pack/atlas_pack_workbench.blend` (SPEC 012 smoke fixture). Add a hand-sized sprite + 3-bone arm chain if not already present; the existing rig should already exercise the flow.
- [ ] Manual smoke per checklist above, before merge. Log results in MANUAL_TESTING.md per the live-logging convention.

**Manual verification** (logged in `tests/MANUAL_TESTING.md` 1.15):

- [ ] Reload-Scripts safety smoke - re-run "Reload Scripts" after entering Edit Weights modal; verify no orphan draw handlers, no panel crash, brush state restored.
- [ ] Cross-armature smoke - bind mesh to one armature, change picker to another, re-bind; verify sidecar persists and reprojects.
- [ ] Headless Blender script via `--background --python` to confirm registration / unregister cycle clean.

## Wave 13.2 - productivity polish (deferred)

Productivity layer on top of first cut. Each item is a self-contained refinement; ship in a follow-up PR or fold into iteration of an existing wave when the trigger lands.

- **Soft vs Hard bone toggle (D16, Animate lift).** Per-bone enum on the vertex group's metadata (`group.proscenio_bone_mode = "SOFT" | "HARD"`); rebind operator re-derives weights respecting the mode. Soft = proximity falloff; Hard = single-nearest. Trigger: user complains that proximity bleed between adjacent bones is too soft on a specific limb.
- **Bone strength region painting (Moho lift).** Per-bone elliptical/capsule influence widget. Drag a handle along the bone in the viewport to grow / shrink radius. Region drives initial weight map procedurally; weight paint becomes fix-up. Couples to a custom viewport draw + gizmo handle. Trigger: user feedback that the proximity default doesn't give enough control for shapes like long hair or tails.
- **Multi-mesh batch bind.** Bind operator takes selected meshes (not just active); applies the same algorithm to each against the picker armature. Useful for character imports with N sprites + 1 rig. Trigger: imported-character workflow stresses this.
- **Weight transfer between sprites.** `proscenio.copy_weights_to_selected` operator. Takes source mesh (active) + N target meshes (selected); for each vertex in each target, look up nearest source vertex by world position + copy its weight dict. Solves COA2 issues [#18](https://github.com/Aodaruma/coa_tools2/issues/18) + [#73](https://github.com/Aodaruma/coa_tools2/issues/73). Foundational for Live2D-style line / colour / shadow layered sprites.
- **Live pose-mode preview in weight paint.** "Scrub the bone to a posed angle, see how the mesh deforms, scrub back" without leaving Edit Weights modal. Adds a pose-scrub overlay + a hotkey to toggle rest pose. Trigger: user wants to verify weight changes against a deformed pose without exiting the modal.
- **Sidecar import / export.** Operator to dump the weight sidecar JSON to a file + load from a file. Enables version-controlled weight backups outside the .blend. Trigger: user asks to back up weight work to git.
- **Brush settings curve presets.** Quick-select brush curve presets named for common 2D tasks ("Hard edge", "Soft falloff", "Crease", "Smooth blend") via dropdown in the Edit Weights modal status pill. Saves a 6-click trip to the brush curve editor per session.

## Wave 13.3 - aspirational (deferred further)

- **Auto-Patch joint cover at articulations (Toon Boom Harmony lift).** One-click joint-cover operator: given two child meshes sharing a parent bone, generate the seam geometry + weight blend that hides the inner-elbow hole as the joint bends. Requires both child-mesh detection (which sprites are on which side of the articulation) and a custom seam generator (boundary-following triangulation). Trigger: humanoid fixture lands + user complains about inner-elbow gap.
- **Cubism Glue equivalent.** Operator that seam-binds overlapping vertices of two meshes with a weight slider biasing which side dominates. Different surface than Auto-Patch (covers any seam, not just articulations). Trigger: layered-sprite use case stresses this.
- **Smart-Bone-style corrective drivers.** Per-bone shape key driven by bone rotation; user records a corrective pose at a specific angle and the addon emits a driver. Goes into SPEC 014 (animation system) not SPEC 013 (authoring).
- **Mirror humanoid binding.** One mesh on one side, click to mirror to the other. Couples to symmetric rigs. Trigger: first humanoid fixture lands.

## Refinement log (post-Wave-13.1 iterative feedback)

Empty at SPEC creation time. Populate as manual-smoke feedback rounds + post-merge polish land.

| Commit | Change | Why |
| --- | --- | --- |
| _-_ | _Wave 13.1 not shipped yet; log opens on first refinement commit_ | _-_ |

## Out of scope (deferred to Wave 13.2 / 13.3 / successor SPECs / backlog)

Per [STUDY out-of-scope](STUDY.md#out-of-scope-deferred-to-successor-specs-or-backlog), still deferred:

- Auto-attach mesh to slot (couples to SPEC 004 maturity).
- Bezier brush stroke for alpha-boundary trace (Wave 13.2 if D1.B free-draw is added; first cut ships D1.A one-shot only).
- GPU-accelerated weight sampling (no consumer until 5000+ vertex meshes show perf complaint).
- Live2D-style deformer paradigm (different SPEC entirely; Proscenio is bone-based).
- Smart-Bone-style corrective drivers (SPEC 014+, couples to animation).
- Cubism Glue equivalent (Wave 13.3).
- Mirror humanoid binding (Wave 13.3 + needs symmetric humanoid fixture).
- Multi-mesh batch bind (Wave 13.2).
- Weight transfer between sprites (Wave 13.2).
- Live pose-mode preview in weight paint (Wave 13.2).
- Sidecar import / export to external file (Wave 13.2).
- Soft vs Hard bone toggle as runtime per-bone flag (Wave 13.2 per D16).
- Bone strength region painting (Wave 13.2 per Moho lift).
- Auto-Patch joint cover (Wave 13.3 per Harmony lift).

Permanently rejected:

- OpenCV / numpy as install-time dependency (COA2 adoption lesson per Constraints + D1).
- Bone-heat solver as default bind algorithm (D4).
- Per-brush mirror as the source of truth (D14).
- ESC as deselect-only inside any draw modal (D10).

## Successor SPECs

- **SPEC 014 (planned: animation polish)** - inherits weight-aware vertex-group machinery from this SPEC; Smart-Bone-style driver-based correctives would land there.
- **SPEC 004 (slots)** maturity unlocks auto-attach mesh to slot + per-slot weight variations.
- **A future "Quick Mesh" operator** (mentioned in SPEC 012 successor list) is the direct sibling to automesh - lift the modal scaffold from this SPEC's `13.1.c` Edit Weights wrapper if pursued.
