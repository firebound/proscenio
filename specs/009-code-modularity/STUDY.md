# SPEC 009 — Code modularity audit

Audit of structural quality across the Proscenio codebase. Scope: identify god-modules, mixed-responsibility files, DRY/SRP violations, and pragmatic reorganizations that fit the project's actual constraints (Blender addon register cycle, mypy strict, GDScript typed).

Out of scope: reformatting (ruff handles it), behavioral changes, public API breaks, performance work. Goal is structure-only — tests pass before and after, every function lands in a more honest location.

This document analyses the current state. The accompanying TODO.md plans the reorganization in waves.

## 1. Codebase inventory

Top-level LOC by language, May 2026 snapshot:

| Area | Top files | LOC |
| --- | --- | --- |
| `apps/blender/operators/__init__.py` | 25 operator classes + 13 module-level helpers | 1755 |
| `apps/blender/panels/__init__.py` | 11 panels + 3 UILists + 19 draw helpers | 1002 |
| `apps/blender/exporters/godot/writer.py` | 4 TypedDicts + 33 functions | 869 |
| `apps/blender/core/help_topics.py` | 2 dataclasses + 13 topic dicts | 539 |
| `apps/blender/properties/__init__.py` | 3 PropertyGroups + 7 helpers + 2 handlers | 493 |
| `apps/blender/core/validation.py` | 1 dataclass + 22 functions | 361 |
| `apps/blender/core/sprite_frame_shader.py` | 1 dataclass + bpy graph builder | 337 |
| `apps/blender/core/atlas_io.py` | image collection + assembly | 308 |
| `apps/blender/core/psd_manifest.py` | manifest dataclass + reader | 239 |

Addon total: ~7480 LOC across 24 Python files.

Other languages:

| Area | Top files | LOC |
| --- | --- | --- |
| `apps/godot/addons/proscenio/` | 8 GDScript files (importer + 5 builders + plugin + reimporter) | 622 |
| `scripts/fixtures/` + `scripts/maintenance/` | 14 fixture builders + helpers | 2423 |
| `apps/photoshop/` | 2 JSX scripts (export, import) | 911 |

The size disparity is the headline. Two files (`operators/__init__.py` and `panels/__init__.py`) carry ~37% of all addon LOC. Every other file in the addon is under 540 LOC — most under 200. The two oversized ones are the immediate restructure target.

## 2. Package structure

Current addon layout:

```text
apps/blender/
  __init__.py             20 LOC — registers properties, operators, panels (clean)
  blender_manifest.toml
  pyproject.toml
  core/                   bpy-free helpers (mostly)
    __init__.py           3 LOC docstring only
    atlas_io.py           bpy-bound (Image plumbing)
    atlas_packer.py       bpy-free (MaxRects)
    feature_status.py     bpy-free (dispatch table)
    help_topics.py        bpy-free (content)
    hydrate.py            bpy-free
    mirror.py             bpy-free
    psd_manifest.py       bpy-free
    psd_naming.py         bpy-free
    psd_spritesheet.py    bpy-bound
    region.py             bpy-free
    slot_emit.py          bpy-free
    sprite_frame_shader.py  bpy-bound
    uv_bounds.py          bpy-free
    validation.py         bpy-free (lazy bpy import in one path)
  exporters/godot/
    writer.py             one file, 869 LOC
  importers/photoshop/
    __init__.py           ImportResult + import_manifest + 2 helpers
    armature.py           1 function
    planes.py             stamp + 7 helpers
  operators/
    __init__.py           god-module, 1755 LOC
    import_photoshop.py   1 operator
  panels/
    __init__.py           god-module, 1002 LOC
  properties/
    __init__.py           3 PGs + helpers + handlers
  tests/run_tests.py      Blender-driven round-trip
```

Strengths: `core/` has earned the bpy-free split for most files, and existing extractions (`hydrate.py`, `mirror.py`, `slot_emit.py`, `feature_status.py`, `help_topics.py`) prove the pattern works. The weakness is concentrated in three files: `operators/__init__.py`, `panels/__init__.py`, `exporters/godot/writer.py`.

## 3. Oversized modules

Three modules exceed reasonable sizing for the addon's complexity:

### 3.1 `operators/__init__.py` (1755 LOC, 25 operator classes, 13 helpers)

This file mixes every operator in the addon — export, validation, selection, IK, UV, slots, atlas pack, atlas apply, drivers, pose library, quick armature, sprite-frame preview shader, ortho camera — plus 13 file-private helpers that span four unrelated concerns (validation reporting, packed-atlas filesystem layout, mouse projection, material image inspection). Adding any new operator forces a reader to scroll past the others and gets caught in helper sprawl that might or might not apply.

The top-level `__init__.py` is also where `_classes` is defined and `register()` runs. That coupling between operator definition and registration is the only thing currently keeping the file together.

### 3.2 `panels/__init__.py` (1002 LOC, 11 panels + 3 UILists + 19 helpers)

The panel module mixes nine subpanels with overlapping concerns. Worse than operators, the helpers are not local to one panel — `_draw_region_box` is shared between active-sprite and active-slot, `_outliner_category_rank` serves only the outliner UIList but lives in the module body, and `_draw_subpanel_header` is the cross-cutting shared utility. UIList subclasses (bones, actions, sprite_outliner) are interleaved between panel definitions rather than grouped.

### 3.3 `exporters/godot/writer.py` (869 LOC, 33 functions)

The writer's structure is more disciplined — every function has a clear name and a docstring — but the file mixes seven distinct concerns: top-level export entry, scene discovery, slot emission, slot animation emission, skeleton building, sprite/weights building, action emission + fcurve helpers. Each concern is independently testable; bundled together they make the file hard to navigate when chasing a single bug.

## 4. Operators module audit

Map of `operators/__init__.py` content by lines:

| Lines | Class / helper | Concern |
| --- | --- | --- |
| 23–61 | `PROSCENIO_OT_status_info` | Help dispatch |
| 64–109 | `PROSCENIO_OT_help` | Help dispatch |
| 112–124 | `PROSCENIO_OT_smoke_test` | Diagnostics |
| 127–138 | `_populate_validation_results` | Validation export integration |
| 141–163 | `PROSCENIO_OT_validate_export` | Validation |
| 166–189 | `_run_writer` + `_gate_on_validation` | Export gating |
| 192–256 | `PROSCENIO_OT_export_godot`, `_reexport_godot` | Export |
| 258–283 | `PROSCENIO_OT_select_issue_object` | Selection |
| 286–349 | `PROSCENIO_OT_select_outliner_object`, `_toggle_outliner_favorite` | Selection / outliner |
| 352–396 | `PROSCENIO_OT_create_ortho_camera` | Authoring helper |
| 398–440 | `PROSCENIO_OT_toggle_ik_chain` | Authoring helper |
| 443–495 | `PROSCENIO_OT_reproject_sprite_uv` | UV authoring |
| 497–551 | `PROSCENIO_OT_snap_region_to_uv` | UV authoring |
| 553–656 | `PROSCENIO_OT_unpack_atlas` | Atlas authoring |
| 658–802 | `_ensure_single_driver`, `PROSCENIO_OT_create_driver` | Driver shortcut |
| 804–897 | `PROSCENIO_OT_create_slot` | Slot system |
| 899–959 | `_slot_bone_target`, `PROSCENIO_OT_add_slot_attachment` | Slot system |
| 961–1052 | `PROSCENIO_OT_setup_sprite_frame_preview`, `_remove_sprite_frame_preview` | Slot system / preview shader |
| 1054–1092 | `PROSCENIO_OT_set_slot_default` | Slot system |
| 1094–1166 | `PROSCENIO_OT_save_pose_asset`, `_default_pose_asset_name` | Pose library |
| 1168–1202 | `PROSCENIO_OT_bake_current_pose` | Pose helper |
| 1204–1387 | `_mouse_event_to_z0_point`, `PROSCENIO_OT_quick_armature` | Quick armature |
| 1390–1450 | `_first_texture_image_name`, `_duplicate_active_uv_layer`, `_pre_pack_snapshot_for`, `_scene_has_pre_pack_snapshot`, `_packed_atlas_paths` | Atlas pack helpers |
| 1452–1706 | `PROSCENIO_OT_pack_atlas`, `PROSCENIO_OT_apply_packed_atlas` | Atlas pack |
| 1708–1746 | `_swap_image_in_materials` | Atlas pack helper |
| 1748–1755 | `_classes`, `register`, `unregister` | Registration |

Eleven distinct concerns crammed into one file. Five concerns alone — slots, atlas pack, drivers, validation, quick armature — together dominate ~1100 of the 1755 LOC and could each ship as their own module without breaking anything.

## 5. Panels module audit

`panels/__init__.py` content map:

| Lines | Class / helper | Concern |
| --- | --- | --- |
| 17–34 | `PROSCENIO_PT_main` | Root panel |
| 36–39 | `_OBJECT_FRIENDLY_MODES`, `_POSE_FRIENDLY_MODES`, idname constants | Cross-cutting constants |
| 42–66 | `_draw_subpanel_header` | Shared header |
| 68–135 | `_draw_sprite_frame_readout`, `_draw_weight_paint_disabled_hint`, `_discover_atlas_size_for`, `_first_tex_image_size` | Active-sprite helpers |
| 138–202 | `_draw_region_box`, `_draw_active_sprite_body`, `_draw_sprite_frame_body` | Active-sprite helpers |
| 205–245 | `_draw_preview_shader_buttons`, `_material_has_slicer`, `_draw_polygon_body` | Active-sprite helpers |
| 247–280 | `_draw_weight_paint_brush` | Active-sprite helper |
| 282–323 | `PROSCENIO_PT_active_sprite` | Active-sprite panel |
| 325–359 | `_draw_driver_shortcut` | Active-sprite helper |
| 361–439 | `PROSCENIO_PT_active_slot` | Active-slot panel |
| 441–451 | `_attachment_kind_for`, `_attachment_icon_for` | Active-slot helpers |
| 453–519 | `PROSCENIO_PT_skeleton` | Skeleton panel |
| 521–542 | `PROSCENIO_UL_bones` | Bones list |
| 543–565 | `PROSCENIO_UL_actions` | Actions list |
| 567–593 | `_outliner_category_rank` | Outliner helper |
| 595–691 | `PROSCENIO_UL_sprite_outliner` | Outliner UIList |
| 693–725 | `PROSCENIO_PT_outliner` | Outliner panel |
| 727–757 | `PROSCENIO_PT_animation` | Animation panel |
| 759–781 | `PROSCENIO_PT_atlas` | Atlas panel |
| 783–834 | `_draw_packer_box`, `_scene_has_pre_pack_snapshot`, `_packed_manifest_exists`, `_discover_atlas_name` | Atlas-panel helpers |
| 836–879 | `PROSCENIO_PT_validation` | Validation panel |
| 881–918 | `PROSCENIO_PT_export` | Export panel |
| 920–959 | `PROSCENIO_PT_help` | Help panel |
| 961–989 | `PROSCENIO_PT_diagnostics` | Diagnostics panel |
| 991–1002 | `_classes`, `register`, `unregister` | Registration |

The active-sprite section alone (lines 68–360) is 290 LOC of helpers plus the panel — bigger than most standalone modules in the project. Slots, outliner, and atlas similarly cluster their own helper bundles. Each cluster is a candidate for its own module.

`_scene_has_pre_pack_snapshot` is duplicated as both an operator helper and a panel helper (operators line 1439 + panels line 806). Same logic, two homes.

## 6. Core subpackage audit

`core/` is the most mature part of the addon. Most modules already respect SRP and ship under 250 LOC. Two outliers:

- `help_topics.py` at 539 LOC. Of those, ~470 are dictionary literals for the 13 topic entries. The dispatch logic is small (~70 LOC). The file is long but cohesive — every line is content. This is acceptable for a content registry; an alternative is one-topic-per-file with a registry that imports them all, but the readability gain is marginal.
- `validation.py` at 361 LOC mixing four validators (active-sprite, active-slot, export, atlas). Each pair (active-X + private helpers) could land in its own submodule under `core/validation/`.

Also worth flagging: `core/` advertises itself as bpy-free in the package docstring, but `atlas_io.py`, `psd_spritesheet.py`, `sprite_frame_shader.py` all import `bpy` at module top. The inconsistency confuses readers who rely on the convention to decide where to add new code. Honest fix: rename `core/` to drop the bpy-free implication, OR move the bpy-bound modules to a sibling subpackage (`core/bpy_helpers/` or `engine/`).

## 7. Writer module audit

`exporters/godot/writer.py` content map:

| Lines | Functions | Concern |
| --- | --- | --- |
| 53–82 | TypedDicts (`BoneDict`, `RestLocal`, `SpriteFrameDict`, `WeightDict`) | Schema shape |
| 84–131 | `export` | Top-level entry |
| 134–169 | `_find_armature`, `_find_sprite_meshes`, `_find_atlas_image`, `_doc_name` | Scene discovery |
| 172–232 | `_build_slots`, `_is_slot_empty`, `_read_slot_default` | Slots |
| 235–333 | `_build_slot_animations`, `_build_slot_attachment_track`, `_merge_slot_animations_into` | Slot animation |
| 336–426 | `_world_to_godot_xy`, `_godot_world_angle_from_dir`, `_compute_bone_world_godot`, `_build_skeleton`, `_wrap_pi` | Skeleton |
| 441–656 | `_read_proscenio_field`, `_build_sprite`, `_build_sprite_frame`, `_resolve_known_groups`, `_vertex_bone_weights`, `_build_sprite_weights`, `_resolve_sprite_bone` | Sprites + weights |
| 672–862 | `_build_animations`, `_action_fcurves`, `_collect_bone_keys`, `_absolute_position` / `_rotation` / `_scale`, `_build_bone_track`, `_build_animation`, `_resolve_pose_entry`, `_quat_to_screen_angle`, `_parse_bone_data_path` | Bone animations |

Seven concerns. The four lower-level concerns (skeleton, sprites, animations, slots) are independently meaningful. Splitting them into `writer/` subpackage with one module per concern would keep the top-level `export` function as the only orchestrator and let each sub-emitter be tested in isolation.

The TypedDicts at the top double as the output schema's typed shape; they belong with the writer for now, but a future schema-typed module could host them once SPEC 008 lands `texture_region` track.

## 8. DRY violations

### 8.1 Select-only-this pattern

Reproduced verbatim in 5+ places (operators 279, 311, 385, 474, 878):

```python
for other in context.scene.objects:
    other.select_set(False)
obj.select_set(True)
context.view_layer.objects.active = obj
```

The doll panel select-issue, outliner row-click, ortho camera focus, reproject UV, and create-slot all reproduce this. One helper `select_only(context, obj)` is the obvious extraction.

### 8.2 Scene-props lookup pattern

`getattr(scene, "proscenio", None)` appears ~12 times across panels and operators with identical fallback handling. Same for `getattr(obj, "proscenio", None)`. A typed pair `scene_props(context)` and `object_props(obj)` returning `ProscenioSceneProps | None` / `ProscenioObjectProps | None` would keep the access pattern explicit without each call site re-implementing the guard.

### 8.3 `self.report({"…"}, "Proscenio: …")`

39 calls in operators. The `"Proscenio: "` prefix is duplicated on every one. Other calls differ only in severity strings. A small reporter helper (`report_info(op, msg)`, `report_warn(op, msg)`, `report_error(op, msg)`) would centralize the prefix and sever the visual noise.

### 8.4 Duplicated helpers across files

- `_scene_has_pre_pack_snapshot` defined in both `operators/__init__.py` and `panels/__init__.py`. Identical body.
- `_packed_atlas_paths` (operators) vs `_discover_atlas_name` (panels) read the same `.atlas.json` filename but compute it independently.
- `_first_texture_image_name` (operators 1390) vs `_first_tex_image_size` (panels 126) walk the same `mat.node_tree.nodes` looking for `TEX_IMAGE`; difference is which property they return.

### 8.5 Slot Empty detection

`writer.py::_is_slot_empty` and `validation.py::_is_active_slot` both implement "is this Empty flagged as a Proscenio slot". The writer version handles CP fallback; the validation version does not. Both should defer to a single helper.

### 8.6 PG/CP fallback pattern

`writer.py` reads PropertyGroup first then falls back to Custom Properties. The pattern is encoded inline in `_read_proscenio_field`, `_is_slot_empty`, `_read_slot_default`. Three independent implementations of the same protocol.

## 9. SRP violations

### 9.1 Operators that do too much

- `PROSCENIO_OT_pack_atlas` (200+ LOC) collects images, runs the packer, writes PNG, writes manifest, snapshots UVs into Custom Properties, reports. Five responsibilities.
- `PROSCENIO_OT_apply_packed_atlas` (320+ LOC) reads manifest, mutates UV layers per object, swaps materials, restores from snapshot if re-applied, reports. The flow control is dense.
- `PROSCENIO_OT_quick_armature` (185 LOC) is a modal operator with five helpers (mouse projection, ensure-armature, create-bone, finish, and the modal dispatch itself). The helpers are operator-internal but testable independently.

These are not blockers — they work — but each is a candidate for a small dedicated module that extracts the pure logic and leaves the operator as a thin shell.

### 9.2 Panels that orchestrate too much

`PROSCENIO_PT_active_sprite.draw` calls 5 different `_draw_*` helpers based on conditional branches (sprite_type, mode). The helpers belong together but their dispatch is inline in the draw method. A single-entrypoint helper module under `panels/active_sprite/` would isolate this logic.

### 9.3 Validation aggregation

`validate_export` in `core/validation.py` sequentially calls four different validators in one body. Acceptable for now, but as more SPECs add validators the aggregation logic grows. A registry pattern (`@validator` decorator + iterator) is overkill today; flag for revisit when validator count exceeds 8.

## 10. Coupling and import direction

### 10.1 Direction adherence

The intended dependency order is:

```text
panels -> operators -> core -> schema
properties -> core
```

Verified by grep: panels do not import operators directly (good — operators are invoked via bl_idname strings). Operators import from core. Core does not import from operators or panels. Properties imports from core. No cycles.

### 10.2 bpy-free claim drift

`core/` advertises itself as bpy-free. `core/atlas_io.py`, `core/sprite_frame_shader.py`, `core/psd_spritesheet.py` import bpy at module level. This isn't broken — they're useful helpers — but it weakens the "bpy-free core" rule that the rest of `core/` follows. Two paths to honesty: (a) move the bpy-bound modules elsewhere; (b) update the package docstring to acknowledge the mixed nature.

### 10.3 Lazy-import pattern

`operators/__init__.py` lazy-imports `..exporters.godot.writer` (line 168) and `..core.atlas_io` / `atlas_packer` (line 1497) inside `execute()` to dodge Blender reload-cycle issues. This is intentional and works; document it once as a rule rather than rediscover per file.

## 11. Naming conventions

### 11.1 Class prefixes

`PROSCENIO_OT_*` for operators, `PROSCENIO_PT_*` for panels, `PROSCENIO_UL_*` for UILists, `Proscenio*` for PropertyGroups. Consistent with Blender convention.

### 11.2 Module-private helpers

Underscore-prefixed (`_draw_*`, `_build_*`, `_resolve_*`). Consistent. The convention breaks only at `core/help_topics.py::_section` which is private to the module but nothing else.

### 11.3 Constant naming

`_PRE_PACK_CP_KEY`, `_PACKED_ATLAS_MAT_NAME`, `_PREVIEW_CAM_NAME`, `_IK_CONSTRAINT_NAME`, `_QUICK_RIG_NAME`, `_HELP_OP_IDNAME`, `_STATUS_OP_IDNAME` — module-private constants, underscore-prefixed SCREAMING_CASE. Consistent. Their scattering across operator and panel modules suggests a shared `constants.py` or per-feature submodule constants block.

### 11.4 Idname / bl_idname strings

`"proscenio.<verb>_<noun>"` consistently. No drift detected.

## 12. Public API surface

`apps/blender/__init__.py` re-exports nothing — only `register()` / `unregister()`. Submodule `__init__.py` files behave inconsistently:

- `operators/__init__.py`, `panels/__init__.py`, `properties/__init__.py` define everything in the file itself (god-modules).
- `core/__init__.py` is empty.
- `importers/photoshop/__init__.py` defines `import_manifest` + helpers inline AND has sibling files (`armature.py`, `planes.py`) — mixed pattern, the package's main API lives in `__init__.py`.

For test imports, the addon exposes via `from core.help_topics import ...` and `from core.validation import ...`. The split between "what is imported by tests" and "what is internal" is currently informal.

## 13. Type discipline

Consistent: every function and class is type-annotated. Mypy strict runs clean across 27 source files (verified).

`# type: ignore` density:

- `operators/__init__.py`: 26 (mostly `valid-type` on `StringProperty` / etc descriptors and `import-not-found` on relative imports — both are bpy stub limitations, not user errors)
- `properties/__init__.py`: 38 (same pattern, denser because PropertyGroups have many descriptor fields)
- `panels/__init__.py`: 3
- `writer.py`: 2

The ignores are concentrated where bpy descriptor magic forces them. A small helper module exposing typed wrappers could eliminate the `valid-type` ignores at the cost of an indirection — likely not worth the trade today.

`ClassVar` usage: every operator uses `bl_options: ClassVar[set[str]]` correctly. `_drag_head: ClassVar[...]` on the modal operator is a workaround for Blender re-creating operator instances per modal session — flagged as deviation in a comment, acceptable.

## 14. Cross-cutting concerns

### 14.1 Error reporting

39 `self.report({"...", ...})` calls duplicate the `"Proscenio: "` prefix. See section 8.3.

### 14.2 Logging

`print_verbose("[Proscenio] ...")` in `panels` and `operators` ad-hoc. No centralized logger. For the addon's size this is fine, but a single `core/log.py` with `info(msg)` / `warn(msg)` would normalize.

### 14.3 Magic strings

Several string constants are duplicated:

- `"proscenio_slot_index"` in writer + slot operators
- `"proscenio_is_slot"` / `"proscenio_slot_default"` in writer + fixture script + slot operators
- `_PRE_PACK_CP_KEY` constant present, but the literal `"proscenio_pre_pack"` is also used in panels via direct lookup (`obj` indexed access)

A `core/cp_keys.py` (Custom Property keys) registry would centralize.

### 14.4 Validation message strings

Validation messages are constructed inline at each issue site. No template registry. For ~30 messages this is fine; flag if it grows.

## 15. Test coverage shape

121 pytest assertions across 13 test files. All run without bpy via `SimpleNamespace` mocks or pure-Python entry points. The Blender round-trip lives in `apps/blender/tests/run_tests.py` (5 fixture goldens).

Test imports follow a pattern:

```python
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))
from core.help_topics import HELP_TOPICS, ...
```

Re-modularization must preserve every existing import path. Because tests target `core.<module>`, splitting `core/validation.py` into `core/validation/<sub>.py` requires a re-export shim or test edits.

## 16. Blender addon practices

Sources:

- [Blender Add-on Guidelines — Code Structure](https://jlampel.github.io/blender_add-on_guidelines/06_code-structure.html)
- [Multi-File addon for Blender — B3D Interplanety](https://b3d.interplanety.org/en/creating-multifile-add-on-for-blender/)
- [Multi-File Packages — BlenderWiki archive](https://archive.blender.org/wiki/2015/index.php/Dev:Py/Scripts/Cookbook/Code_snippets/Multi-File_packages/)
- [Tips for Coding Scalable Addons — Superhive](https://superhivemarket.com/posts/tips-for-coding-scalable-addons)

Consensus across sources:

1. Multi-file from day one. Single-file addons are discouraged even for trivial ones (limits updater compatibility and IDE tooling).
2. `__init__.py` is for metadata + module-import + register dispatch only. Implementation belongs in submodules.
3. Each module owns its own `register()` / `unregister()` for the classes it defines. The package `__init__.py` calls them in order.
4. One operator class per file when the operator is non-trivial; a small operator module (e.g. `ops/select.py` containing 3 small selection operators) is also acceptable.
5. UI panels group differently from operators. A panel module per subpanel is reasonable when each subpanel has its own helpers; a shared `_panel_helpers.py` for cross-panel utilities (header drawing, mode-aware predicates) is encouraged.
6. Folder names like `ops/`, `ui/`, `props/` (or longer: `operators/`, `panels/`, `properties/`) are both common; pick one and stay consistent.

Proscenio already follows (1), (2) at the addon root, and (3) at the submodule level. The gap is in (4) and (5): `operators/__init__.py` and `panels/__init__.py` are still single files when they should be packages with one module per concern.

## 17. Python packaging conventions

Sources:

- [Hitchhiker's Guide to Python — Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [Real Python — Application Layouts](https://realpython.com/python-application-layouts/)
- [Real Python — SOLID Principles](https://realpython.com/solid-principles-python/)
- [God Object Anti-Pattern in Python](https://softwarepatternslexicon.com/patterns-python/11/2/4/)

Consensus:

1. `__init__.py` minimal unless code-sharing across submodules demands otherwise. Avoid putting executable code there.
2. Single Responsibility Principle: a module has one reason to change. When file size grows past a few hundred LOC, ask whether it has absorbed multiple concerns.
3. God-object / god-module is named explicitly as an anti-pattern. Splitting by concern (one concern per module) is the canonical refactor.
4. Private/public split via underscore prefix is the convention; for a package-level public API, expose via the package `__init__.py`.

Proscenio's `core/` follows these rules. The other directories don't yet.

## 18. Patterns worth preserving

Several existing patterns are working well and should be preserved by the restructure:

- bpy-free helpers extracted from bpy walkers. `slot_emit.py` is the canonical pattern: the bpy walker (`writer._build_slots`) builds `SlotInput` dataclasses and hands them to a bpy-free projection (`build_slot_dict`). Tests exercise the projection with pure Python.
- `hydrate.py` extraction. Same shape: bpy-free pure logic, bpy glue lives in the caller (`properties/__init__.py`).
- Dispatch tables. `feature_status.py` `FEATURE_STATUS` and `help_topics.py` `HELP_TOPICS` show how to centralize lookup logic with one source of truth + tests that walk every entry.
- Mode-friendly predicates. `_OBJECT_FRIENDLY_MODES` / `_POSE_FRIENDLY_MODES` as module-private sets that panel `poll()` uses. Cleaner than scattered string comparisons.
- `draw_header_preset` over `draw_header`. The right hook for status badges + help buttons (preserved in 5.1.d.5).
- Custom Property fallback in the writer. Lets headless contexts without registered PropertyGroups still produce valid output. This pattern needs to land in a single helper rather than be re-derived per call site.

## 19. Anti-pattern catalogue

The recurring shapes in the codebase that warrant a name:

1. God module (`operators/__init__.py`, `panels/__init__.py`).
2. Sequential helper sprawl. `panels/__init__.py` lines 68–280 contain 19 module-level helpers in declaration order with no visible grouping. Reader has to mentally tag each as belonging to active-sprite vs active-slot vs cross-cutting.
3. Mixed-concern file (`exporters/godot/writer.py`).
4. Repeated small idioms (select-only-this, getattr-proscenio, self.report-with-prefix). Section 8.
5. Inline magic strings across files for the same Custom Property.
6. Duplicated helpers across modules (section 8.4).
7. Mixed bpy-bound and bpy-free in the same package (`core/`).

## 20. GDScript plugin side

`apps/godot/addons/proscenio/`:

| File | LOC | Concern |
| --- | --- | --- |
| `importer.gd` | 154 | Import entry, format_version gate, builders dispatch |
| `builders/animation_builder.gd` | 154 | Animation tracks |
| `builders/polygon_builder.gd` | 99 | Polygon2D builder |
| `builders/slot_builder.gd` | 82 | Slot Node2D builder |
| `builders/sprite_frame_builder.gd` | 62 | Sprite2D builder |
| `builders/skeleton_builder.gd` | 43 | Skeleton2D builder |
| `plugin.gd` | 17 | EditorPlugin entry |
| `reimporter.gd` | 11 | Stub |

Already factored. No file exceeds 160 LOC. The builder pattern is clean: `builders/<kind>.gd` per node kind, dispatched from `importer.gd`. No structural changes needed here.

## 21. Photoshop JSX side

`apps/photoshop/`:

| File | LOC | Concern |
| --- | --- | --- |
| `proscenio_export.jsx` | 513 | Export everything |
| `proscenio_import.jsx` | 398 | Import everything |

Two large monoliths, each one concern (export, import). ExtendScript doesn't support modern module systems, so multi-file is awkward. The existing structure is acceptable given the language constraint, but internal sectioning via top-of-file commentary plus consistent helper naming would help readability. Not a SPEC 009 priority — flag for a separate housekeeping pass if the JSX grows further.

---

Sources used:

- [Blender Add-on Guidelines — Code Structure](https://jlampel.github.io/blender_add-on_guidelines/06_code-structure.html)
- [B3D Interplanety — multi-file addon](https://b3d.interplanety.org/en/creating-multifile-add-on-for-blender/)
- [Hitchhiker's Guide — Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [Real Python — SOLID Principles](https://realpython.com/solid-principles-python/)
- [Real Python — Application Layouts](https://realpython.com/python-application-layouts/)
- [God Object Anti-Pattern in Python](https://softwarepatternslexicon.com/patterns-python/11/2/4/)
- [Single Responsibility Principle in Python](https://renanmf.com/single-responsibility-principle-in-python/)
- [Tips for Coding Scalable Addons](https://superhivemarket.com/posts/tips-for-coding-scalable-addons)
