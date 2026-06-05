# Blender app system organization - TODO

See [STUDY.md](STUDY.md) for the full evaluation and decisions D1-D6 (locked after the axis analysis; Q1 = `_shared/`, Q2 = god-module splits in-scope).

Each phase is one PR, behavior-preserving, proven by the existing gates (`ruff` + `mypy --strict` + pytest). A half-done migration is never in a broken state - every phase is a relocation plus an import-path update, with the package `__init__.py` re-exporting the public surface so external callers change one import line. This honors the "no big-bang reorganization" rule in [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md).

Recommended order: phases 1-5 are mechanical and low-risk (do first); phases 6-7 carry the god-module splits (D6) and get dedicated review; phase 8 is a low-risk move; phase 9 finalizes the record.

## Decision lock-in

- [x] D1 - keep layer-first top level; complete the feature-subpackage pattern. Reject per-system inversion.
- [x] D2 - cross-cutting infra lives in `core/_shared/` (pure) + `core/bpy_helpers/_shared/` (bpy-bound).
- [x] D3 - photoshop-import domain folder is `psd/`.
- [x] D4 - `panels/` and `properties/` stay layer-first; no per-system fragmentation.
- [x] D5 - no `format_version` bump, no schema change, no behavior change.
- [x] D6 - the two operator god-modules are split during this migration (phases 6, 7).
- [x] Q1 - shared tier = `_shared/`.
- [x] Q2 - god-module splits in-scope (not deferred).

## Phase 1 - `_shared/` infra tier + CP-key consolidation

Foundational; unblocks every later phase and lands the highest-value audit fix.

- [ ] Create `core/_shared/` (pure) and `core/bpy_helpers/_shared/` (bpy-bound), each with an `__init__.py` re-exporting the public surface.
- [ ] Move the pure infra into `core/_shared/` per the STUDY shared-infrastructure table: `cp_keys`, `report`, `props_access`, `pg_cp_fallback`, `feature_status`, `hydrate`, `geometry_2d`, `region`, `viewport_state`, `modal_overlay_geometry`.
- [ ] Move the bpy-bound infra into `core/bpy_helpers/_shared/`: `viewport_math`, `modal_overlay`, `select`, and relocate `_bpy_compat` here from the `core/` root (fixes its bpy-at-module-top violation of the "direct children of `core/` import nothing from `bpy`" rule).
- [ ] Update all import sites (mechanical, via the re-exporting facades where possible).
- [ ] Companion (audit, High): consolidate the leaked CP keys into `cp_keys.py` and replace literals with the imported constants - `proscenio_weight_sidecar` (9 source modules: `panels/skinning.py`, `operators/{edit_weights,restore_weight_snapshot,sidecar_io}.py`, `core/skinning/sidecar_schema.py`, `core/bpy_helpers/skinning/{stroke_diff,weight_overlay,automesh_hook,bind_apply}.py`), plus `proscenio_bone_modes`, `proscenio_envelope_radius`, `proscenio_mirror_x`, the automesh authoring stroke keys, and the photoshop import-tag keys.
- [ ] Companion (audit, Med): point `core/mirror.py` and `core/hydrate.py` at the `cp_keys` constants in their mapping tables instead of hardcoded literals.
- [ ] Gate: `ruff` + `mypy --strict` + pytest green.

## Phase 2 - atlas

- [ ] Create `core/atlas/` (move `atlas_packer.py` + atlas math) with re-exporting `__init__.py`.
- [ ] Create `core/bpy_helpers/atlas/` (move `atlas_collect.py`, `atlas_compose.py`, `atlas_manifest.py`).
- [ ] `operators/atlas_pack/` and `panels/atlas.py` stay; update their imports.
- [ ] Companion (audit, Med): move `scene_has_pre_pack_snapshot` out of `operators/atlas_pack/_paths.py` into `core/bpy_helpers/atlas/` so `panels/atlas.py` imports it from `core` - restores the `panels -> core` direction and stops crossing the underscore-private operator boundary.
- [ ] Gate.

## Phase 3 - slot

- [ ] Create `core/slot/` (move `slot_emit.py`).
- [ ] `operators/slot/` stays; update imports.
- [ ] Gate.

## Phase 4 - sprite_frame

- [ ] Create `core/sprite_frame/` (move `sprite_frame_math.py`).
- [ ] Create `core/bpy_helpers/sprite_frame/` (move `sprite_frame_shader.py`).
- [ ] Gate.

## Phase 5 - psd (photoshop import)

- [ ] Create `core/psd/` (move `psd_manifest.py`, `psd_naming.py`).
- [ ] Create `core/bpy_helpers/psd/` (move `psd_spritesheet.py`).
- [ ] `importers/photoshop/` stays; update imports.
- [ ] Companion (audit, Low): route `operators/import_photoshop.py` reports through `core.common.report` instead of raw `self.report` + inline `"Proscenio: "` strings.
- [ ] Optional (audit, Low): split `importers/photoshop/planes.py` (426 LOC, three concerns) into mesh stamping + `material.py` + `cp_tags.py` if it is being touched anyway.
- [ ] Gate.

## Phase 6 - armature (move + quick_armature split, D6)

Carries a real refactor; review on its own.

- [ ] Create `core/armature/` (move `quick_armature_math.py`, `skeleton_target.py`).
- [ ] Create `operators/armature/` subpackage (move `quick_armature.py`, `authoring_ik.py`, `authoring_camera.py`, `set_bone_mode.py`, `skeleton_target.py`).
- [ ] Split the `quick_armature.py` god-module: chord/header/preview draw helpers -> `operators/armature/_overlay.py`; pure view-pose math (`_view_pose_equal`, `_point_in_region_rect`, `_rv3d_is_front_ortho`) -> `core/armature/` or `core/_shared/viewport_state`.
- [ ] Gate.

## Phase 7 - automesh operators (move + automesh_authoring split, D6)

Carries a real refactor; review on its own.

- [ ] Create `operators/automesh/` subpackage (move `automesh.py`, `automesh_authoring.py`).
- [ ] Split the `automesh_authoring.py` god-module: statusbar/chord draw -> `operators/automesh/_statusbar.py`; screen-to-XZ-plane projection (`_region_to_world_xz*`) -> `core/bpy_helpers/_shared/viewport_math` (add the offset variant there); image resolution (`_resolve_image`, `_find_tex_image`) -> `core/bpy_helpers/automesh`.
- [ ] Companion (audit, Med): dedupe `_find_tex_image` / `_resolve_image` / `_resolve_pixels_per_unit` between `operators/automesh.py` and `automesh_authoring.py` - extract once into `core/bpy_helpers/automesh` and import in both.
- [ ] Gate.

## Phase 8 - skinning operators

- [ ] Create `operators/skinning/` subpackage (move `bind_mesh.py`, `edit_weights.py`, `copy_weights_to_selected.py`, `restore_weight_snapshot.py`, `brush_preset.py`, `sidecar_io.py`).
- [ ] Gate.

## Phase 9 - finalize the record

- [ ] Mirror D1-D6 into [`../decisions.md`](../decisions.md): a new per-feature section plus an update to the "Code modularity" / "Per-package import discipline" entries noting the `_shared/` tier and the completed system grouping.
- [ ] Update [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md) "Module organization (Blender addon)" to document the `_shared/` infra tier and that every system is a domain package.
- [ ] Drop a one-line pointer in [`../backlog.md`](../backlog.md) under "Blender addon" if any phase is deferred.

## Out of scope

Per STUDY non-goals: no per-system top-level inversion; no fragmenting `panels/` or `properties/`; no touching `schema_bindings/`; no reorganizing `apps/godot/examples/` (synced, edits do not persist); no behavior change or schema bump.
