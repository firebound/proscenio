# Blender addon: organize by system (layer-first hybrid)

Status: **decisions locked, ready for TODO**. D1-D5 locked; Q1 resolved (shared tier = `_shared/`) and Q2 resolved (god-module splits are in-scope, see D6). Restructure proposal for `apps/blender/`, completing the started-but-partial system organization under `core/`. Extends the locked "Code modularity" and "Per-package import discipline" entries in [`../decisions.md`](../decisions.md). No runtime behavior change, no `format_version` bump - a file-organization refactor proven by the existing behavior tests, exactly as the prior code-modularity refactor was.

## Problem

A system-by-system organization was started under `core/` - `automesh/`, `skinning/`, and `validation/` are proper domain packages with re-exporting `__init__.py` facades - but only for a few systems. The rest of the addon's systems (atlas, slot, sprite_frame, psd, armature) are still laid flat as loose files. The open question is whether the top-level `core/ exporters/ importers/ operators/ panels/ properties/` layer split is the right axis at all, or whether the addon should instead group everything per system (`automesh/panel`, `automesh/operators`, ...). The goal is that each file is self-explanatory from its location alone, grouped by both common interest and single responsibility, without clean-arch ceremony. This study maps the systems and the shared code, evaluates the two axes, and locks a direction so the TODO can sequence an incremental migration.

## Current state

### Systems

Each system already crosses the layers. OK means the system is grouped into a domain package on that axis today; FLAT means it is loose files.

| System | core/ (pure) | bpy_helpers/ (bpy-bound) | operators/ | panels/ |
| --- | --- | --- | --- | --- |
| automesh | OK `automesh/` | OK `automesh/` | FLAT `automesh.py`, `automesh_authoring.py` | shared sections |
| skinning / weights | OK `skinning/` | OK `skinning/` | FLAT `bind_mesh`, `edit_weights`, `copy_weights_to_selected`, `restore_weight_snapshot`, `brush_preset`, `sidecar_io` | `skinning.py` |
| validation | OK `validation/` | - | - | `validation.py`, `diagnostics.py` |
| export (godot) | `validation/export.py` | - | `export_flow.py` | `export.py` + `exporters/godot/writer/` OK |
| atlas | FLAT `atlas_packer.py` | FLAT `atlas_collect/compose/manifest.py` | OK `atlas_pack/` | `atlas.py` |
| slots | FLAT `slot_emit.py` | - | OK `slot/` | `active_slot.py` |
| import (photoshop) | FLAT `psd_manifest.py`, `psd_naming.py` | FLAT `psd_spritesheet.py` | FLAT `import_photoshop.py` | + `importers/photoshop/` OK |
| armature / IK / skeleton | FLAT `quick_armature_math.py`, `skeleton_target.py` | - | FLAT `quick_armature`, `authoring_ik`, `authoring_camera`, `set_bone_mode`, `skeleton_target` | `skeleton.py` |
| sprite_frame | FLAT `sprite_frame_math.py` | FLAT `sprite_frame_shader.py` | - | `_draw_sprite_frame.py` |
| help | FLAT `help_topics.py` | - | `help_dispatch.py` | `help.py` |
| uv / mirror / selection / driver / pose / outliner | FLAT singles | `select.py` | FLAT singles | various |

The pattern works where applied (automesh, skinning, validation, the godot writer) and is absent where not. The inconsistency, not the axis, is the problem.

### Shared infrastructure

These modules belong to no single system. The import graph confirms each is pulled by operators, exporters, panels, or properties across several systems. Today they sit as loose files at the root of `core/`, visually indistinguishable from system code.

| Module | Responsibility | Pulled by |
| --- | --- | --- |
| `core/cp_keys.py` | Custom Property key registry (single source of truth) | atlas, slots, export |
| `core/report.py` | The `"Proscenio: "` report prefix helper | nearly every operator |
| `core/props_access.py` | Typed PropertyGroup access | driver, export, selection, uv, camera, atlas |
| `core/_bpy_compat.py` | bpy iteration / collection shims | importers, every writer submodule |
| `core/pg_cp_fallback.py` | PropertyGroup / Custom Property read fallback | writers |
| `core/feature_status.py` | Feature gating + status badges | help, panels |
| `core/hydrate.py` | Custom Property hydration on file load | properties |
| `core/region.py`, `core/geometry_2d.py` | 2D region + geometry math | export writer, several |
| `core/viewport_state.py`, `core/modal_overlay_geometry.py`, `bpy_helpers/viewport_math.py`, `bpy_helpers/modal_overlay.py` | Viewport state + modal overlay drawing | automesh, quick_armature |

## What we want

Open `apps/blender/` and read systems, not a flat wall of 30 mixed files. Cross-cutting infrastructure should be visibly distinct from system code. The `core/` (bpy-free) versus `core/bpy_helpers/` (bpy-bound) test boundary must survive untouched. No premature abstraction, no Repository/Service ceremony - just consistent grouping of what already exists.

## Design space

### Axis A - outer organization axis

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A1.** Layer-first top level, feature subpackages within (extend the current pattern) | Matches Blender's type-ordered registration; preserves the `core/` vs `bpy_helpers/` test boundary; already proven in the repo (`operators/atlas_pack/`, `core/skinning/`, `exporters/godot/writer/`) | Two axes to hold in mind (layer, then feature); shared infra still needs a home (Axis B) | **Lock.** |
| **A2.** Per-system top level / vertical slice (`automesh/operators.py`, `automesh/panels.py`, `automesh/props.py`) | One folder per feature reads cohesively | `register()` is type-ordered (properties -> operators -> panels), so the root must still walk every system in layer order - re-introduces the layers at the root, less legibly; forces the pure-vs-bpy test split to be recreated inside every system; fragments the shared N-panel tree | Reject. |
| **A3.** Status quo (leave the flat systems flat) | Zero work | The started migration stalls half-applied; the inconsistency is exactly the reported pain | Reject. |

The three Blender-specific reasons A2 loses: (1) registration is type-ordered not feature-ordered; (2) the bpy-free vs bpy-bound split is the test boundary and is orthogonal to feature; (3) panels are one shared N-panel tree, inherently cross-system. The idiomatic way to get "see systems" in a Blender addon is feature subpackages inside the layer directories, which A1 codifies.

### Axis B - shared-infrastructure home

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **B1.** `core/_shared/` (pure) + `core/bpy_helpers/_shared/` (bpy-bound) | Underscore signals "module-internal", matching the existing `_helpers.py` convention; sorts to the top of an alphabetical listing so the infra tier sits above the systems instead of buried among them | A leading-underscore package name | **Lock (Q1).** |
| **B2.** `core/common/` (pure) + `core/bpy_helpers/common/` (bpy-bound) | Common monorepo idiom | No underscore signal; sorts into the middle of the system folders alphabetically, burying the infra tier | Considered (Q1 chose B1). |
| **B3.** Leave flat at `core/` root with a doc comment | No moves | The reported pain is precisely that infra and system code look identical at the root | Reject. |

### Axis C - psd domain folder name

`psd/` versus `import/`. `import` reads ambiguously (close to the keyword, collides with the `importers/` layer concept). **Lock `psd/`.**

### Axis D - operator god-module split timing

The audit flagged two god-modules (`operators/automesh_authoring.py` ~1412 LOC, `operators/quick_armature.py` ~1246 LOC) mixing operator logic with drawing, projection, and image-resolution helpers. Splitting them is real refactor work, not a move. **Option D-now** (split during this migration) versus **D-defer** (move the files into feature subpackages now; split the internals when the next feature touches them, per the "migrate when next touched" rule). **Lock D-now (Q2):** split the two god-modules during this migration. Phases 6 and 7 carry the refactor and get dedicated review rather than riding a mechanical move.

## Decisions (proposed)

ADR-light, to mirror back into [`../decisions.md`](../decisions.md) once locked.

- **D1 (Axis A).** Keep the layer-first top level; complete the feature-subpackage pattern in `core/`, `core/bpy_helpers/`, and `operators/`. Reject the per-system top-level inversion. Revisit trigger: a future where registration stops being type-ordered (Blender API change) or the addon splits into independently-registered sub-addons.
- **D2 (Axis B).** Carve a `_shared/` package on both the pure and bpy-bound sides for cross-cutting infrastructure. The leading underscore sorts it to the top of the directory listing (above the system folders) rather than into the middle. Revisit trigger: `_shared/` itself grows past a handful of modules and needs its own sub-grouping.
- **D3 (Axis C).** The photoshop-import domain folder is named `psd/`.
- **D4.** `panels/` and `properties/` stay layer-first; no per-system fragmentation. The per-feature panel files already map close to one-per-system. Revisit trigger: a single panel file absorbs two unrelated systems.
- **D5.** No `format_version` bump, no schema change, no user-facing behavior change. Each phase is behavior-preserving; the existing behavior tests carry the proof. Same contract as the prior "Refactor into packages without behavior change" decision.
- **D6 (Axis D).** The two god-modules (`operators/automesh_authoring.py` ~1412 LOC, `operators/quick_armature.py` ~1246 LOC) are split during this migration, not deferred. Their phases carry a real refactor (drawing, projection, and image-resolution helpers extracted out of the operator) and get reviewed on their own.

## Open questions (resolved)

- **Q1 - shared-tier name.** Resolved: `_shared/` over `common/` - the leading underscore sorts the infra tier to the top of an alphabetical listing instead of burying it among the system folders. D2 and Axis B updated.
- **Q2 - operator god-module split timing.** Resolved: split in-scope over defer. D6 and Axis D updated; phases 6 and 7 carry the refactor.

## Target layout

After the phased migration the addon reads as systems. The pure `core/` root drops from ~22 mixed modules to four single-file features plus domain folders; `_shared/` leads each listing (the underscore sorts above the system folders).

```text
apps/blender/
  __init__.py                       registration orchestrator (unchanged)
  core/
    _shared/                        NEW - cross-cutting infra (pure)
      cp_keys  report  props_access  pg_cp_fallback
      feature_status  hydrate  geometry_2d  region
      viewport_state  modal_overlay_geometry
    automesh/  skinning/  validation/      (unchanged - already domain packages)
    atlas/                          NEW <- atlas_packer
    slot/                           NEW <- slot_emit
    sprite_frame/                   NEW <- sprite_frame_math
    psd/                            NEW <- psd_manifest, psd_naming
    armature/                       NEW <- quick_armature_math, skeleton_target
    help_topics.py  mirror.py  uv_bounds.py      stay flat (single-module features)
    bpy_helpers/
      _shared/                      NEW - cross-cutting infra (bpy-bound)
        _bpy_compat  viewport_math  modal_overlay  select
      automesh/  skinning/          (unchanged)
      atlas/                        NEW <- atlas_collect, atlas_compose, atlas_manifest
      sprite_frame/                 NEW <- sprite_frame_shader
      psd/                          NEW <- psd_spritesheet
  operators/
    atlas_pack/  slot/              (unchanged - already subpackages)
    automesh/                       NEW <- automesh, automesh_authoring (+ _statusbar split)
    skinning/                       NEW <- bind_mesh, edit_weights, copy_weights_to_selected,
                                          restore_weight_snapshot, brush_preset, sidecar_io
    armature/                       NEW <- quick_armature (+ _overlay split), authoring_ik,
                                          authoring_camera, set_bone_mode, skeleton_target
    driver.py  export_flow.py  help_dispatch.py  import_photoshop.py
    pose_library.py  selection.py  uv_authoring.py      stay flat (single-operator features)
  panels/  properties/              unchanged (layer-first; files already ~1:1 per system)
  exporters/godot/writer/           unchanged (already a package)
  importers/photoshop/              unchanged (already a package)
  tests/                            unchanged
```

Single-module features stay flat by design - putting a one-file feature in its own folder is the ceremony this spec avoids; they become packages only on growing a second module. Registered classes stay layer-first (Blender registration order); each new package `__init__.py` re-exports its public surface so external callers change one import line, not many. The full phased breakdown lives in [`TODO.md`](TODO.md).

## Non-goals

- No per-system top-level inversion (Axis A2, rejected).
- No fragmenting `panels/` or `properties/` into per-system folders (D4).
- No touching `schema_bindings/` (auto-generated, header-marked, drift-tested) - this addon is a producer and has none, but the rule stands.
- No reorganizing `apps/godot/examples/` (synced from `examples/generated/*/godot/`; edits do not persist).
- No behavior change, no schema bump (D5).

## Related

- [`../decisions.md`](../decisions.md): "Code modularity", "Per-package import discipline".
- [`../../.ai/conventions/code.md`](../../.ai/conventions/code.md): "Module organization (Blender addon)", the ~300 LOC smell threshold, no-premature-abstraction, domain-package rule.
- [`../../.ai/conventions/layout.md`](../../.ai/conventions/layout.md): repository layout, file naming.
- [`../../.ai/skills/architecture.md`](../../.ai/skills/architecture.md): component boundaries and dependency direction.
