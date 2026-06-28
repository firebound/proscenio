# Spec 070: Mesh pen authoring (from-blank + re-editable)

A pen tool that **creates** a mesh from nothing - the first click drops the first vert, the outline grows point by point until the loop closes, then it triangulates to a SIMPLE (non-dense) mesh - and lets the user **come back later** to a mesh they already applied and add or move points. The Illustrator / Spine pen, as the user framed it.

This is the open follow-on the spec 066 prune recorded: spec 066 added a Manual contour tool, but it edits the OUTER contour of an *existing* mesh element and ends at APPLY (a one-shot session). It is logged as `mesh-pen-authoring` in [backlog/ui-feedback.md](../backlog/ui-feedback.md). The two halves (create-from-blank and re-edit-after-apply) are one feature because both need the same missing piece: the authored outer ring as first-class, persisted state rather than a transient recompute of the alpha trace.

## Scope

- **In:** a from-blank entry that creates a Proscenio mesh element and authors its outline with the existing click-pen; persisting the authored outer ring so a re-launch reloads it instead of re-tracing; SIMPLE triangulation only.
- **Out (reuse 066 as-is):** the click-pen machine, the bare-Tab tool cycle, the interior point / fold / cut tools, the CDT triangulation, the APPLY commit. This spec adds an entry point and a persistence field; it does not rewrite the modal.
- **Out (later):** DENSE interior authoring from blank (the inner-loops stage); a standalone non-element scratch canvas (a pen mesh is always a real element).

## Open decisions

### 1. The from-blank entry: how does a pen session start with no element and no image?

**Code anchors:** `apps/blender/operators/automesh/automesh_authoring.py` (`PROSCENIO_OT_automesh_authoring.invoke`, the guards at ~213-229: requires `context.active_object` to be a MESH and `first_material_image(obj)` to return an image, rejects SPRITE elements; `self._output = StageOutput()` starts empty and `compute_outer()` ~313 fills `_output.outer` from the alpha trace); `apps/blender/operators/automesh/automesh_authoring.py` (`_handle_outer_contour_event` ~471, `_commit_contour` ~852 -> `contour_ring_from_pen` sets `self._output.outer`, the OUTER "contour" tool that already authors a fresh ring); `apps/blender/operators/incorporate.py` (`PROSCENIO_OT_incorporate_element.execute` ~101 - stamps `element_type="mesh"` via the idprop setter, the only "make an object a Proscenio element" path that is not PSD import); `apps/blender/importers/photoshop/planes.py` (`_build_quad` ~332, `_attach_material` ~405 - the textured-quad substrate import builds); `apps/blender/panels/mesh_generation.py` (`_authoring_button_enabled` ~249 - the MESH + TEX_IMAGE enable gate). Locked context: `decisions.md` "Weight paint + automesh" (automesh is alpha-trace one-shot) and the spec 066 "Mesh generation interaction" entries (the contour reuses the click-pen in the OUTER stage).

**Question:** The modal today refuses to launch without an existing MESH element that carries an image texture, and it seeds `_output.outer` from the alpha trace of that image. A from-blank pen has neither a mesh nor an image to trace. What creates the element, what stands in for the image (the modal, the overlay, and APPLY all read it), and how does the session arm straight into the contour pen with an empty outer?

**Options:**
- (A) A new operator (e.g. `proscenio.pen_mesh_new`) that creates an empty mesh object, stamps `element_type="mesh"`, attaches a material with a TEX_IMAGE node fed a user-chosen image (file picker / drag), then launches the existing modal pre-armed to OUTER with the "contour" tool active and `_output.outer` empty (no `compute_outer` because there is no alpha to trace). Reuses every downstream stage and APPLY unchanged.
- (B) Generalize `automesh_authoring.invoke` to accept a bare mesh / no element and a missing image (placeholder / checker texture), so one operator covers both alpha-trace and from-blank. Fewer operators, but it loosens the modal's invariants (the overlay, the silhouette validation, and APPLY all assume an image).
- (C) A fully separate pen operator that does not reuse the modal at all - its own draw/commit. Maximum control, maximum duplicate surface and test burden.

**Recommendation:** **(A).** It reuses the part 066 already shipped (the contour tool authors a fresh outer ring with no alpha) and isolates the new surface to one thin create-then-launch operator, keeping the modal's image/element invariants intact. The image question is real and stands whether (A) or (B): a textured pen needs a texture, so the from-blank operator should require the user to pick the image up front (the texture defines the UV space the silhouette is drawn in) rather than inventing a placeholder that APPLY would bake. (B) is tempting for "one operator" but it weakens invariants the whole modal leans on; defer it. (C) duplicates the most intricate, least headless-testable code in the addon - rejected. **Decide whether the from-blank operator (A) requires an image at create time (recommended) or allows a textureless draft that gets an image later.** Size **M** for (A) (one create-and-launch operator + the empty-outer arm path + the panel entry + a headless test that the operator builds a valid element and the contour commit writes a mesh).

### 2. Persisting the authored outline so a re-launch is a re-edit, not a re-trace

**Code anchors:** `apps/blender/operators/automesh/authoring_pipeline.py` (`read_user_strokes` / `write_user_strokes` ~147/168, `read_user_outer_strokes` / `write_user_outer_strokes` ~172/182 - the existing persisted authoring state, JSON Custom Properties); `apps/blender/core/_shared/cp_keys.py` (`PROSCENIO_USER_STROKES`, `PROSCENIO_USER_OUTER_STROKES`, `PROSCENIO_USER_STEINERS` ~88-93 - the keys); `apps/blender/operators/automesh/automesh_authoring.py` (re-invoke reloads strokes ~1089/1095, but `_output.outer` is recomputed via `compute_outer` ~313 every invoke and the manual contour replaces it in-memory only ~852-869); `apps/blender/core/automesh/stroke_geometry.py` (`contour_ring_from_pen` ~43 - pure, the ring the modal commits). Locked context: spec 066 "Mesh generation interaction" (the contour commit is in-memory; nothing persists the outer ring).

**Question:** Interior and outline-edit strokes already persist to Custom Properties and reload on re-invoke, so re-entering re-applies them. The OUTER ring does not: it is recomputed from the alpha trace each launch, and a hand-authored contour replaces it only in memory, lost at APPLY. For "come back and add points in the middle of the outline" the modal must reload the *authored* ring as live, editable pen state, not re-trace it. Where does the authored outer ring live, and how is the re-launch told to load it instead of tracing?

**Options:**
- (A) A new Custom Property (e.g. `proscenio_authored_outer_contour`, JSON list of points, mirroring the existing `proscenio_user_*` keys) written on contour commit / APPLY; re-invoke, when present, loads it into `_output.outer` and arms the OUTER contour tool instead of calling `compute_outer`. The ring is editable as pen points again.
- (B) Infer the outer ring from the final mesh's boundary edges on re-invoke (no stored state). Zero new storage, but boundary-walk is lossy (subdivisions and interior cuts blur which verts were the authored anchors) and fragile under later manual Edit-Mode tweaks.
- (C) Persist nothing new; keep the current behavior (interior strokes reload, outer re-traces). Re-edit of the outline is simply unsupported. Cheapest, but it does not deliver the user's ask.

**Recommendation:** **(A).** It matches the precedent exactly - the authored outline becomes one more `proscenio_*` authoring field next to the stroke keys, so the same write-on-commit / read-on-invoke machinery carries it, and the anchors stay the user's actual clicked points rather than a guessed boundary. (B) reads clever but loses the authoring intent the moment subdivisions or a cut touch the boundary, which is most real meshes. (C) is the honest "we did not build it" and is what 066 left, so it is the thing this spec exists to change. **Decide whether the stored ring is the pre-subdivision anchor points (re-editable, recommended) or the post-subdivision baked ring (simpler to render, not re-editable).** Size **M** (one CP read/write pair + the re-invoke load branch + a from-blank-then-relaunch headless test asserting the ring round-trips).

### 3. Relationship to 066 and the "simple, not dense" guarantee

**Code anchors:** `apps/blender/core/skinning/authoring_stages.py` (`AuthoringStage` ~20-30: OUTER / EDIT_OUTLINE / INNER_LOOPS / EDIT_INTERIOR_POINTS / PREVIEW_INTERIOR / APPLY; `stage_tools` / `default_tool` ~52-57 - the per-stage tool sets); `apps/blender/operators/automesh/automesh_authoring.py` (`_active_stages` per interior mode; the INNER_LOOPS stage is DENSE-only); `apps/blender/core/bpy_helpers/automesh/cdt.py` (`build_mesh_via_delaunay` ~130 - the triangulation APPLY runs). Locked context: spec 066 "Mesh generation interaction" (bare Tab cycles the per-stage tool; the contour lives in OUTER).

**Question:** The user wants "simple mesh generation (not dense)". The interior-mode toggle already drives whether the INNER_LOOPS / dense stages run. A from-blank pen mesh - does it force SIMPLE, expose the same interior-mode choice, or skip the interior stages entirely (outline-only triangulation)?

**Options:**
- (A) Force SIMPLE for a from-blank pen mesh: the session runs OUTER (contour) -> EDIT_OUTLINE -> EDIT_INTERIOR_POINTS (optional point drops) -> APPLY, skipping the DENSE inner-loops stage. Matches "not dense" literally and keeps the stage list short.
- (B) Expose the existing interior-mode toggle so a pen mesh can still go dense if the user wants it later. More flexible, but contradicts the stated "simple" intent and adds the dense stages to a tool meant to be lightweight.
- (C) Outline-only: APPLY triangulates the bare contour with no interior points at all (a fan / minimal CDT). Simplest mesh, but loses the interior-point tool the user may want for a few deformation anchors.

**Recommendation:** **(A).** "Simple, not dense" is explicit, and the from-blank flow should default to the SIMPLE stage list (contour + optional interior points + apply), which is the lightest path that still lets the user drop a handful of interior anchors for skinning. (C) is too austere - a few interior points are cheap and often wanted. (B) re-introduces the density the user asked to avoid; leave dense to the existing alpha-trace authoring on imported art. **Decide whether the from-blank pen still offers the interior-point tool (recommended) or is outline-only.** Size **S** (reuse the SIMPLE stage list; the only work is defaulting the from-blank session to it).

## Verdict summary

A new from-blank operator (decision 1A) creates a real mesh element with a user-chosen image and launches the existing 066 modal armed to the OUTER contour pen with an empty outer - reusing the click-pen, the tool cycle, the triangulation, and APPLY unchanged. A new `proscenio_authored_outer_contour` Custom Property (decision 2A) persists the authored ring next to the existing stroke keys, so a re-launch reloads the outline as editable pen state instead of re-tracing - the single change that turns the one-shot session into a re-editable one and serves both halves of the feature. The from-blank session defaults to the SIMPLE stage list (decision 3A). Open locks for the user: image-at-create vs textureless draft (1), pre- vs post-subdivision stored ring (2), interior points vs outline-only (3). Total size **M** - the heavy machinery already shipped in 066; this is an entry point plus a persistence field.

## Sources

- Spec 066 (mesh-generation-interaction), pruned 2026-06-27 (PR #162) - the contour pen + tool cycle this builds on; see `_index.md` and `decisions.md` "Mesh generation interaction".
- `backlog/ui-feedback.md` - the `mesh-pen-authoring` entry this STUDY drives.
- Code anchors above, current as of 2026-06-27 (`apps/blender/operators/automesh/`, `core/skinning/authoring_stages.py`, `core/automesh/`, `operators/incorporate.py`, `importers/photoshop/planes.py`).
