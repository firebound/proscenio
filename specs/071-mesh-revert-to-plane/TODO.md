# Spec 071 TODO: Revert a mesh element to its original plane

Drives [STUDY](STUDY.md). Decisions LOCKED via Q&A (build it now, alongside spec 070): rebuild the quad from `PROSCENIO_IMPORT_PLACEMENT` (1A), wipe skinning + automesh authoring strokes while keeping import identity / element_type / material (2A), restrict to PSD-imported mesh elements with a warn-no-op fallback for no-placement (3A), and REPORT a cleared summary.

## 1. Operator

- [ ] `PROSCENIO_OT_revert_to_plane` (`proscenio.revert_to_plane`) in `operators/` (mesh-element op, `REGISTER`/`UNDO`).
- [ ] poll: `_is_mesh_element` + a `PROSCENIO_IMPORT_PLACEMENT` tag present; warn-no-op otherwise ("no original plane recorded for this element").
- [ ] Rebuild: call `_build_quad(obj, (width, height), (offset_x, offset_z))` from the placement tag; the image material rides along (untouched).
- [ ] Wipe: every deform vertex group + `proscenio_base_sprite`; `PROSCENIO_WEIGHT_SIDECAR`, bone-mode / envelope / mirror keys; the automesh authoring strokes (`PROSCENIO_USER_*`) and the manual contour CP (`proscenio_manual_contour`, spec 070 C2).
- [ ] Keep: `PROSCENIO_IMPORT_PLACEMENT` / `_ORIGIN` / `_MANIFEST`, `element_type`, the material.
- [ ] Report a summary of what was cleared (N weights / vgroups / strokes) so the destructive scope is visible.

## 2. Panel

- [ ] A "Revert to plane" button (TRASH/LOOP_BACK icon) on the Mesh Generation panel (or Element panel) - mesh-element only; shown when the element has a placement tag.

## 3. Tests + gates

- [ ] Headless operator test: an automeshed + weighted element reverts to 4 verts / 1 face, image material intact, placement/origin/element_type kept, deform groups + sidecar gone.
- [ ] No-placement (incorporated) element: warn-no-op, mesh untouched.
- [ ] ruff + mypy + repo-root pytest + `run_operator_tests.py`.

## 4. Post-merge cleanup (ONLY after squash-merge)

- [ ] QA Companion: a revert-to-plane walk (next free `BL-MESH-...` id).
- [ ] Lock the call in [`decisions.md`](../decisions.md); remove `mesh-revert-to-plane` from [`backlog/ui-feedback.md`](../backlog/ui-feedback.md).
- [ ] Prune this spec folder; index in [`_index.md`](../_index.md) with the PR number.

## Follow-on (logged, not now)

- [ ] (3B) Bounding-box quad rebuild for no-placement / incorporated elements - gated behind a real request.
