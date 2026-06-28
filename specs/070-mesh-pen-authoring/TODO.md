# Spec 070 TODO: Mesh pen authoring (from-blank + re-editable)

Drives the locked [STUDY](STUDY.md). All three decisions locked to (A) on the Spine / Moho precedent: D1 a from-blank operator that requires an image at create and launches the 066 contour pen over it; D2 persist the user's clicked anchor points (`proscenio_authored_outer_contour`) so a re-launch re-edits them; D3 the from-blank session runs the SIMPLE stage list with the interior-point tool.

Reuses the spec 066 machinery wholesale (the click-pen, the OUTER contour tool, the bare-Tab cycle, the CDT triangulation, APPLY). The new surface is one create-and-launch operator, one persistence field, and two branches in the modal's invoke. Dependency-first: the pure / persistence layer and its tests land before the operator and the modal wiring that consume them.

## 1. Persistence field for the authored outer contour (D2)

- [ ] `apps/blender/core/_shared/cp_keys.py`: add `PROSCENIO_AUTHORED_OUTER_CONTOUR` (the JSON anchor-points key), next to the existing `PROSCENIO_USER_*` keys.
- [ ] `apps/blender/operators/automesh/authoring_pipeline.py`: `read_authored_outer_contour(obj) -> list[Point2D] | None` and `write_authored_outer_contour(obj, points)` mirroring `read_user_strokes` / `write_user_strokes` (JSON round-trip, missing/malformed degrades to None).
- [ ] In-Blender test (`apps/blender/tests/operators/`): the anchor points round-trip through the object idprop; a missing key reads None; a malformed value degrades to None (the test-quality posture: assert the real read path, not a mock).

## 2. Persist the anchors on author (D2)

- [ ] `apps/blender/operators/automesh/automesh_authoring.py` `_commit_contour`: capture the pre-subdivision `_pen_points` (the user's clicked anchors) and `write_authored_outer_contour(obj, anchors)` so the ring survives the session. The subdivided ring still feeds `_output.outer` via `contour_ring_from_pen` unchanged.
- [ ] APPLY: ensure the authored anchors persist on commit too (re-write from the live anchors if the OUTER tool was used this session), so a post-APPLY re-launch finds them.
- [ ] Test: after a contour commit + APPLY, `read_authored_outer_contour` returns the clicked anchors (not the subdivided ring).

## 3. Re-edit branch in invoke (D2)

- [ ] `automesh_authoring.py` `invoke`: before `compute_outer`, if `read_authored_outer_contour(obj)` is present, load it into `self._output.outer` and arm the OUTER stage with the "contour" tool and those anchors as live pen points (skip the alpha trace). Otherwise keep the existing `compute_outer` path.
- [ ] Test: an element carrying `proscenio_authored_outer_contour` re-invokes with the contour tool armed and `_output.outer` equal to the stored ring (no alpha trace ran).

## 4. From-blank session mode (D1, D3)

- [ ] `automesh_authoring.py`: a class-level `_launch_from_blank: ClassVar[bool]` signal (set by the new operator, read-and-cleared in `invoke`). When set: skip `compute_outer` (there is no alpha), start `_output.outer` empty, force the SIMPLE `_active_stages` (D3), and arm the OUTER "contour" tool so the first click drops the first vert.
- [ ] Guard interaction: the from-blank flag and the re-edit branch (step 3) are mutually exclusive - re-edit wins if both somehow hold (a re-launch on an already-authored element is a re-edit, not a fresh blank).
- [ ] Test: with `_launch_from_blank` set on a fresh element, invoke arms the contour tool, `_output.outer` is empty, and `_active_stages` is the SIMPLE list.

## 5. The from-blank create-and-launch operator (D1)

- [ ] `apps/blender/operators/automesh/pen_mesh_new.py` (new) `PROSCENIO_OT_pen_mesh_new`:
  - File-select invoke (`StringProperty(subtype="FILE_PATH")` + `context.window_manager.fileselect_add`).
  - `execute`: load the image (`bpy.data.images.load`), read its pixel dimensions, derive the quad extent from the scene pixels-per-unit (mirror import), create a fresh MESH object (empty geometry), attach the unlit image material via the shared `_attach_material` (refactor it out of `planes.py` to a reusable home if it is private), stamp `element_type="mesh"` and the `PROSCENIO_IMPORT_PLACEMENT` extent (so UVs at APPLY map into real texture space), link + activate the object, set `_launch_from_blank`, and launch `bpy.ops.proscenio.automesh_authoring("INVOKE_DEFAULT")`.
  - Guard: a missing / unreadable image reports and cancels; report the created element on success.
- [ ] `operators/automesh/__init__.py`: register the new operator.
- [ ] Test: the operator builds a valid Proscenio mesh element (element_type="mesh", an image material with a TEX_IMAGE node, the placement tag) from an image path; a bad path cancels.

## 6. UV correctness for a from-blank mesh

- [ ] Verify APPLY assigns UVs to the contour-authored mesh from the stamped placement / image extent the same way an imported element gets them (read how `build_automesh` / the bridge maps world XZ to UV). If the existing UV path keys on the base quad (which a from-blank mesh lacks until APPLY), seed the placement-derived extent so the UVs land. Add a headless assertion that a from-blank APPLY produces a mesh with a UV layer covering the image.

## 7. Panel entry (D1)

- [ ] `apps/blender/panels/mesh_generation.py`: a "New Pen Mesh" button on the Mesh Generation panel (or its Automesh Interactive subpanel) that runs `proscenio.pen_mesh_new`. Unlike the existing "Author Mesh (interactive)" button it is NOT gated on an active mesh element (it creates one), so it shows when no mesh element is active - the empty-state entry point.
- [ ] Help / docstring: note it creates an element from an image and opens the pen.

## 8. Tests + gates

- [ ] Pure / persistence tests (steps 1-4) green in the repo-root `tests/` where bpy-free, in `apps/blender/tests/operators/` where they need Blender.
- [ ] `run_operator_tests.py` (full) + `run_tests.py` goldens (8/8 - from-blank authoring does not touch the writer's fixtures, so goldens are byte-unchanged).
- [ ] `ruff check` + `ruff format --check` (pinned 0.8.4) on `apps/blender`; `mypy --config-file apps/blender/pyproject.toml` from repo root; repo-root `uv run pytest tests/`.

## 9. Post-merge cleanup (ONLY after the maintainer squash-merges the PR)

- [ ] QA Companion: a from-blank pen walk (create-from-image -> draw contour -> APPLY) and a re-edit walk (re-open an applied pen mesh -> add a point), next free `BL-MESH-...` ids.
- [ ] Lock the calls in [`decisions.md`](../decisions.md) under a "Mesh pen authoring" subsection; note the `mesh-pen-authoring` backlog item shipped (remove it from [`backlog/ui-feedback.md`](../backlog/ui-feedback.md)).
- [ ] Prune this spec folder, index in [`_index.md`](../_index.md) with the PR number (flip 070 from planned to pruned).
