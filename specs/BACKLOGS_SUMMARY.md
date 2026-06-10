# Backlogs summary

Verified index of every open backlog item, grouped by plugin and area. Each row: Type (`bug` defect / `ui` polish / `quality` toolchain / `feature`), a short slug, a <=10-word description, a code-verified Status, the Evidence (file:line) backing that status, and a Link to the canonical entry in the `specs/backlog-*` files. Statuses audited 2026-06-10 against `main` by reading the current code: `open` = present / not started; `partial` = some sub-points resolved; `needs-retest` = code-fixed, only a GUI smoke can confirm behavior; `upstream` = external (Blender) issue, watch only. Items verified `fixed`/`shipped` in that audit (26 bugs + 15 features) were pruned from this file and from the source backlogs in the same pass - the audit tables with their evidence live in this file's git history. Blocking items for the first release are called out in [PLAN.md](PLAN.md). Blender-6-gated work is excluded (see [backlog-blender-6.md](backlog-blender-6.md)).

## Blender Addon

### Cross-panel / general

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | subpanel-drag-reorder | Drag-and-drop reorder of subpanels | partial | sibling top-level panels get native header-drag free; `bl_parent_id` subpanels cannot (upstream Blender limit) | [backlog-ui-feedback.md](backlog-ui-feedback.md#cross-panel--general) |

### Writer / exporter

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | writer-ignores-picker | Writer exports armatures[0], ignoring active-armature picker | open | `scene_discovery.py:14-17` returns first ARMATURE; never reads the picker PointerProperty (found by 2026-06-10 audit) | [backlog-bugs-found.md](backlog-bugs-found.md#writer-exporta-armatures0-e-ignora-o-active-armature-picker) |
| feature | multi-polygon-truncation | Multi-polygon mesh truncated to first polygon only | open | `writer/sprites.py:94` `first_poly = polygon_at(mesh, 0)`; no validation warning | [backlog.md](backlog.md#multi-polygon-mesh-meshes) |
| feature | rig-orientation-detection | General rig-orientation detection (XZ vs XY plane) | open | `animations.py:220-221` docstring defers to future spec; writer hardcodes XZ | [backlog.md](backlog.md#general-rig-orientation-detection) |
| feature | auto-detect-2d-vs-3d | Auto-detect 2D rig vs 3D mesh | open | no detection in writer or validation; flat-quad assumption stated unchecked | [backlog.md](backlog.md#auto-detect-2d-rig-vs-3d-mesh) |
| feature | blender-43-legacy-actions | Blender 4.3 legacy-actions fcurves compatibility, untested | open | fallback exists (`animations.py:38-39`) but CI pins Blender 5.1.1 only | [backlog.md](backlog.md#blender-43-legacy-actions-compatibility) |

### Format / schema

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | bezier-curve-preservation | Bezier curve handles not transmitted to Godot | open | `proscenio.py:217` interp only linear/constant; no tangent fields | [backlog.md](backlog.md#bezier-curve-preservation) |
| feature | multi-atlas-pages | Multiple atlases per character (atlas_pages array) | open | `proscenio.py:266` atlas is a single optional str | [backlog.md](backlog.md#multiple-atlases-per-character) |
| feature | animation-event-tracks | Animation events / method tracks (audio, particles) | open | `proscenio.py:227` Track literal has no event variant | [backlog.md](backlog.md#animation-events-method-tracks) |
| feature | per-key-interp-mixing | Per-key interpolation mixing in one track | open | `animation_builder.gd:115-121` one track-level interpolation; `key.interp` never read | [backlog.md](backlog.md#per-key-interpolation-mixing) |
| feature | format-migration-path | Format detection + v1-to-v2 migration path | open | no `migrations/` in tree; `importer.gd:136-140` errors with no migrator pointer | [backlog.md](backlog.md#format-detection--migration) |
| feature | bone-physics-export | Bone physics joint-chain export (cape, hair) | open | no joint/stiffness/damping fields in models | [backlog.md](backlog.md#bone-physics-joint-chain-export) |
| feature | path-constraint-export | Path-constraint export (PathFollow2D) | open | no path-geometry fields in models | [backlog.md](backlog.md#path-constraint-export) |
| feature | texture-region-track | Continuous UV animation (texture_region track) | open | Track literal = bone_transform/sprite_frame/slot_attachment/visibility only | [backlog.md](backlog.md#continuous-uv-animation-texture-region-track) |
| feature | sprite-frame-export-path | sprite_frame track: Blender export path missing | open | grep sprite_frame in exporters: zero hits; writer emits bone_transform + slot_attachment only | [backlog.md](backlog.md#sprite_frame-animation-track---blender-export-path) |
| feature | visibility-track-both-sides | visibility track: implement both sides or retire | open | `animation_builder.gd:86` still `push_warning("not implemented yet")`; no Blender emission | [backlog.md](backlog.md#visibility-animation-track---blender-export-path) |
| feature | sprite-appearance-passthrough | Sprite appearance: modulate / z_index / flip / blend_mode passthrough | open | MeshElement/SpriteElement carry none; blend_mode exists only on PSD-manifest side | [backlog.md](backlog.md#sprite-appearance-fields---modulate--draw-order--flip--blend-mode-passthrough) |
| feature | sprite-pivot-offset | Sprite pivot / Sprite2D.offset from Blender origin | partial | schema field exists (`proscenio.py:155`) + importer stamps it (`sprite_builder.gd:48-49`); writer never computes offset from the Blender origin | [backlog.md](backlog.md#sprite-pivot--sprite2doffset-from-the-blender-origin) |
| feature | ik-round-trip | IK constraints round-trip Blender to Godot | open | raw bone keyframes only; no SkeletonModification in Godot addon; no bake-at-export | [backlog.md](backlog.md#ik-constraints-round-trip-blender---godot) |
| feature | nla-strips-to-actions | NLA strips flattened to baked Actions | open | `animations.py:162` iterates `bpy.data.actions`; no NLA/bake handling | [backlog.md](backlog.md#nla-strips-to-actions) |
| feature | per-asset-ppu | Per-asset PPU end-to-end (per-layer pixels-per-unit) | open | PPU single global: `scene_props.py:398` one FloatProperty, one writer param, one root field | [backlog-ui-feedback.md](backlog-ui-feedback.md#pipeline-cross-tool) |
| feature | pg-cp-storage-split | Storage split PG-vs-CP by intent (target 1.0.0) | open | uniform mirror intact: `mirror.py:56-71` (14 rows) + `hydrate.py:17-29` (11 rows); `read_field` dual fallback in `writer/sprites.py:72` | [backlog.md](backlog.md#split-propertygroup-vs-custom-property-storage-by-intent-target-100) |

### Active Sprite panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | reproject-uv-orientation | Reproject UV: slow 2nd call + rotated/flipped result | partial | still `smart_project` (`uv_authoring.py:73`); limitation documented in docstring + tooltip; Edit-Mode start rejected; perf symptom unverified | [backlog-bugs-found.md](backlog-bugs-found.md#reproject-uv-segunda-chamada-lenta--uv-resultante-rotacionadaflipada) |
| ui | header-mesh-name | Show selected mesh name in header | open | `element.py:94` static `bl_label = "Active Sprite"`; no draw_header with obj.name | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | clamp-initial-frame | Clamp Initial frame to [0, hframes*vframes-1] | open | `object_props.py:95-102` frame has min=0 only, no max/soft_max | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | rename-initial-frame | Rename "Initial frame" to "Frame" | open | `object_props.py:96` still `name="Initial frame"` | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | centered-vs-origin-help | Clarify centered-vs-origin distinction in help | partial | `help_topics.py:616-617` explains centered semantics (spec 023); no explicit vs-PS-origin contrast | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |

### Drive from Bone

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | expression-two-ranges | Replace raw expression with two editable ranges | open | `_draw_driver_shortcut.py:23` raw driver_expression string; no range fields | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | driver-readout-inspect-reset | Inline driver-value readout + Inspect/Reset buttons | open | `_draw_driver_shortcut.py:14-28` picker fields + create operator only | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | sticky-panel | Sticky/pinned panel while editing pose bone | open | panels poll on active MESH; no pin/lock affordance | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| feature | drive-slot-from-bone | Drive slot attachment from a bone | open | no slot driver code in `operators/slot/` | [backlog.md](backlog.md#drive-slot-attachment-from-a-bone-slot-analog-of-drive-from-bone) |

### Active Slot / Slots panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | create-slot-parented-seed | Create-slot Empty misplaced when seed has parent | open | `slot/create.py:81-85` still assigns world translation into parent-local location, no matrix_parent_inverse | [backlog-bugs-found.md](backlog-bugs-found.md#create-slot-path-b-novo-empty-fica-em-posição-errada-quando-seed-já-tem-parent) |
| bug | create-slot-origin-unapplied | Create-slot Empty misplaced when origin unapplied | open | `slot/create.py:85` positions at object translation, not geometry bbox center | [backlog-bugs-found.md](backlog-bugs-found.md#create-slot-por-seleção-de-mesh-empty-em-posição-aparentemente-aleatória-quando-origin-da-mesh-não-foi-aplicada) |
| ui | slots-native-uilist | Standardize slots list to native UIList | open | `panels/slots.py:61-72` still row buttons, no template_list | [backlog-ui-feedback.md](backlog-ui-feedback.md#slots-panel-lista-de-slots-do-projeto) |
| ui | path-a-b-affordance | Clarify Path A vs Path B affordance | open | `create.py:62` poll always-enabled, no inline hint/context disable | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-slot-panel) |
| ui | slot-no-bone-warning | Warn when slot has no parent bone | open | `panels/slots.py:113-116` plain "(unparented)" label; no validation check or fix button | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-slot-panel) |
| ui | keyframe-active-attachment | Keyframe-active-attachment authoring button | open | grep keyframe in `operators/slot/` = 0 hits | [backlog-ui-feedback.md](backlog-ui-feedback.md#slots-panel-lista-de-slots-do-projeto) |

### Mesh Generation panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | automesh-interactive-extend-cut | Automesh Interactive extend/cut broken or artifacts | open | `automesh_authoring.py:243-245` pen state + `authoring_pipeline.py:266` splice unchanged; post-report PRs #101-#103 dedup-only | [backlog-bugs-found.md](backlog-bugs-found.md#automesh-interactive-modal-ferramentas-extend--cut-quebradas) |
| ui | mesh-resolution-rename | Rename deceptive "Mesh resolution" field | open | `scene_props.py:81` name still "Mesh resolution", default 0.25 | [backlog-ui-feedback.md](backlog-ui-feedback.md#mesh-generation-panel-spec-022) |
| ui | density-follows-bones-default-off | Default "Density follows bones" OFF | open | `scene_props.py:179` automesh_density_under_bones default=True | [backlog-ui-feedback.md](backlog-ui-feedback.md#mesh-generation-panel-spec-022) |
| ui | interior-spacing-grouping | Group "Interior spacing" with other numeric values | open | `mesh_generation.py:151` interior_spacing still in dense-only block | [backlog-ui-feedback.md](backlog-ui-feedback.md#mesh-generation-panel-spec-022) |
| ui | preserve-weights-readout | Surface "preserve weights on regen" where regen runs | open | `mesh_generation.py:146` only preserve_base_quad; toggle lives only in Weight Paint Snapshot | [backlog-ui-feedback.md](backlog-ui-feedback.md#mesh-generation-panel-spec-022) |
| ui | automesh-modal-copy | Rename "Automesh (modal)" to action-oriented copy | open | `mesh_generation.py:185` button "Automesh (modal)"; `:174` "Multi-stage modal preview" | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| feature | element-type-gating | Element-type gating: warn on sprite, validate quad | open | `mesh_generation.py:31-34` accepts any MESH; `automesh.py:166-168` poll type-only; no quad check | [backlog.md](backlog.md#element-type-gating-mesh-only-tools-warn-on-sprite--sprite-stays-a-quad) |
| feature | sprite-rigid-single-bone-bind | Sprite rigid single-bone bind (weight-paint is mesh-only) | open | `weight_paint.py:25-31` mesh-only gate shipped; no rigid-bind control/operator exists | [backlog.md](backlog.md#sprite-rigid-single-bone-bind-weight-paint-is-mesh-only) |

### Weight Paint panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | brush-curve-presets-error | Brush-curve presets throw on click | open | `brush_preset.py:40-45` same suspect truncate/set/new sequence; #103 comment-only | [backlog-bugs-found.md](backlog-bugs-found.md#edit-weights-brush-curve-presets-disparam-erro) |
| bug | per-bone-overrides-inert-bone-heat | Per-bone Soft/Hard inert under Bone Heat default | open | `bind_apply.py:207-208` BONE_HEAT early-returns before overrides (`:231`); box drawn ungated (`weight_paint.py:204`) | [backlog-bugs-found.md](backlog-bugs-found.md#per-bone-softhard-overrides-são-inertes-no-modo-bone_heat-o-default) |
| bug | weight-transfer-no-coverage-warning | Weight Transfer: no warning when targets out-of-range | open | `copy_weights_to_selected.py:48-51` reports total copied only; no zero-coverage warning | [backlog-bugs-found.md](backlog-bugs-found.md#weight-transfer-sem-warning-quando-targets-ficam-fora-do-alcance-cobertura-zero-silenciosa) |
| ui | bind-shows-target-armature | Bind subpanel does not show target armature | open | `weight_paint.py:172-223` `_draw_bind` never names picker | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | flat-mesh-weight-display | Flat-mesh weight display hides texture | open | no display-mode code; only provenance overlay | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | clear-per-bone-override | Cannot clear a per-bone override | open | `set_bone_mode.py:36-43` enum SOFT/HARD only, no clear path | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | bind-button-after-overrides | Reorder Bind button after overrides box | open | `weight_paint.py:190` Bind drawn before overrides box (`:204`) | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | sidecar-import-live-apply | Sidecar Import does not apply to live weights | open | `sidecar_io.py:85` import writes CP only; no vertex-group apply | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | snapshot-sidecar-naming | Unify "Snapshot" + "Sidecar IO" naming | open | `weight_paint.py:106,129` labels unchanged; operator labels "Weight Sidecar" | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| ui | weight-transfer-max-distance-panel | Surface Weight Transfer max_distance in panel | open | draw button-only; max_distance F9-only (`copy_weights_to_selected.py:24`) | [backlog-ui-feedback.md](backlog-ui-feedback.md#weight-paint-panel-spec-022) |
| feature | weight-preserving-psd-reimport | Weight-preserving PSD re-import (snapshot around reimport) | open | `planes.py:247` `_ensure_mesh` still clear_geometry + fresh quad; no snapshot hook | [backlog.md](backlog.md#weight-preserving-psd-re-import) |
| feature | soft-hard-runtime-toggle | Soft/Hard runtime per-bone toggle (Adobe Animate lift) | partial | toggle + rebind respect overrides (`bind_apply.py:231`) but inert in default BONE_HEAT (`:207`) | [backlog.md](backlog.md#weight-paint-productivity-follow-up-candidates) |
| feature | bone-strength-region-painting | Bone strength region painting (Moho lift) | open | no capsule/influence-gizmo code in tree | [backlog.md](backlog.md#weight-paint-productivity-follow-up-candidates) |
| feature | live-pose-preview | Live pose-mode preview in weight paint | open | native POSE+WPAINT combo only; no pose-scrub/rest-pose hotkey in modal | [backlog.md](backlog.md#weight-paint-productivity-follow-up-candidates) |
| feature | auto-patch-joint-cover | Auto-Patch joint cover at articulations | open | no joint-cover/seam-generator code | [backlog.md](backlog.md#weight-paint-aspirational-candidates) |
| feature | cubism-glue-seam-bind | Cubism Glue seam-bind equivalent | open | no glue/seam-bind code | [backlog.md](backlog.md#weight-paint-aspirational-candidates) |
| feature | smart-bone-corrective-drivers | Smart-Bone corrective drivers | open | no corrective/shape-key driver code | [backlog.md](backlog.md#weight-paint-aspirational-candidates) |
| feature | mirror-humanoid-binding | Mirror humanoid binding | open | only brush X-mirror flag; no mirror-bind operator | [backlog.md](backlog.md#weight-paint-aspirational-candidates) |
| feature | bezier-brush-stroke | Bezier brush stroke for alpha-boundary trace | open | strokes are polyline pen only | [backlog.md](backlog.md#weight-paint-aspirational-candidates) |

### Skeleton panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | skeleton-row-click-select | Row click does not select bone in viewport | needs-retest | `selection.py:79-93` select_bone_by_name wired per-row in `skeleton.py:51-57` (fix `dcd08f6`); no post-fix GUI log | [backlog-bugs-found.md](backlog-bugs-found.md#skeleton-panel-row-click-no-uilist-não-seleciona-bone-no-viewport) |
| ui | skeleton-inline-rename | Inline bone rename | open | rows are emboss=False operator buttons; no editable prop | [backlog-ui-feedback.md](backlog-ui-feedback.md#skeleton-panel) |
| ui | skeleton-armature-picker | Name which armature the writer uses; selector | partial | picker shipped (`scene_props.py:473-486` + `skeleton.py:93-95`); the writer-ignores-picker half is now its own bug (Writer / exporter above) | [backlog-ui-feedback.md](backlog-ui-feedback.md#skeleton-panel) |
| feature | skeleton-bone-collections | Bone-collections management from the panel | open | no bone-collection ops in panels/operators | [backlog.md](backlog.md#spec-021-follow-up-unfinished-discovery--buckets-bc) |
| feature | skeleton-hierarchy-editing | Richer bone-hierarchy editing (beyond read-only readout) | open | read-only connected/relative readout shipped; no editing operators | [backlog.md](backlog.md#spec-021-follow-up-unfinished-discovery--buckets-bc) |

### Quick Armature

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | qa-gizmo-crash | Blender 5.1.1 gizmo crash post snap-cursor (upstream-suspect) | upstream | stack 100% Blender/AMD internals; defensive try/except shipped (`_handlers.py:82-100`) | [backlog-bugs-found.md](backlog-bugs-found.md#blender-511-crash-em-gizmo_button2d_draw-apos-view3dsnap_cursor_to_center-suspeito-upstream) |
| ui | qa-preview-clamp-color | Clamp/color preview line under panel overlays | partial | option B shipped: red invalid color + tooltip (`_overlay.py:36,114-115,144-167`); clamp (option A) not implemented | [backlog-ui-feedback.md](backlog-ui-feedback.md#quick-armature-operator) |
| feature | qa-rotation-mode | Rotation-mode choice (Euler-Y vs quaternion) + safe swap | open | no rotation_mode authoring surface; only driver targets set XYZ | [backlog.md](backlog.md#bone-rotation-mode-authoring-surface-quaternion-vs-euler) |
| feature | qa-pick-parent-viewport | Pick-parent-in-viewport during modal | open | no bone-tip parent retarget chord | [backlog.md](backlog.md#quick-armature-follow-up-candidates) |
| feature | qa-chain-naming-suffixes | Chain-aware bone naming suffixes | open | `quick_armature.py:547` flat counter naming | [backlog.md](backlog.md#quick-armature-follow-up-candidates) |
| feature | qa-mirror-suffix | Mirror auto-suffix _L/_R with X-Mirror | open | no X-mirror handling in `_create_bone` | [backlog.md](backlog.md#quick-armature-follow-up-candidates) |
| feature | qa-numeric-length | Numeric length input (Tab to type) | open | modal handles no TAB entry | [backlog.md](backlog.md#quick-armature-follow-up-candidates) |
| feature | qa-local-axis-lock | Local-axis lock (press axis twice) | open | second press clears lock; global X/Z only | [backlog.md](backlog.md#quick-armature-follow-up-candidates) |
| feature | qa-defaults-help-topic | Help topic for quick_armature_defaults | open | `help_topics.py:304` only quick_armature topic | [backlog.md](backlog.md#quick-armature-follow-ups-deferred-polish) |
| feature | qa-headless-undo-axis-tests | Headless undo / axis-lock interaction tests | open | helper math covered only; no operator-suite file | [backlog.md](backlog.md#quick-armature-follow-ups-deferred-polish) |

### Atlas panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | unpack-material-rename | Material rename breaks Unpack restoration silently | partial | `unpack.py:99-104` warns + summarizes partial restores (`bd64989`); lookup still by name, pointer-based snapshot not done | [backlog-bugs-found.md](backlog-bugs-found.md#atlas-unpack-rename-de-material-entre-apply-e-unpack-quebra-restauração-silenciosamente) |
| ui | packing-controls | Add packing controls (strip whitespace, edge padding, rotation) | open | `scene_props.py:424-444` only padding/max_size/pot; no edge-extend/strip/rotation | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| ui | ppu-visibility | Show PPU through the pipeline | open | no PPU readout in `panels/atlas.py`; PPU only on Export panel | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| ui | discovered-vs-packed-label | Clarify discovered-source vs packed atlas label | open | `atlas.py:32-36` single undifferentiated label | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| ui | per-object-pack-state | Per-object pack/unpack state visibility | open | `atlas.py:59` scene-wide snapshot check; no per-object badge | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| ui | document-material-identity | Document material-identity-by-name limitation | open | `help_topics.py:203-227` atlas topic has no rename caveat | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| feature | atlas-region-helper | Atlas region authoring helper (snap UV by name) | open | only reproject + region-from-UV ops exist | [backlog.md](backlog.md#atlas-region-authoring-helper) |
| feature | exclude-from-atlas | Exclude sprites from shared atlas pack | open | no exclude_from_atlas flag; `pack.py:50` packs every textured mesh | [backlog.md](backlog.md#exclude-sprites-from-the-shared-atlas-pack) |
| feature | validate-spriteframe-uv | Validate sprite_frame UV covers full sheet | open | no UV-bounds check in core/validation | [backlog.md](backlog.md#validate-sprite_frame-uv-covers-the-full-sheet) |
| feature | export-bundle | Export bundle: gather .proscenio + textures into folder | open | no bundle/gather option in writer or export_flow | [backlog.md](backlog.md#export-bundle-gather-the-proscenio-and-its-textures-into-one-folder) |
| feature | maxrects-heuristics | MaxRects: try multiple heuristics for density | open | `atlas_packer.py:130-146` BSSF only | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |
| feature | shrink-start-size | Shrink-to-fit / configurable start_size | open | `atlas_packer.py:65` start_size=256 param never passed, no scene prop | [backlog-ui-feedback.md](backlog-ui-feedback.md#atlas-panel) |

### Outliner panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | indented-tree | Indented tree (armature > slots > attachments) | partial | category-rank sort + indent for slot attachments (`outliner.py:15-32,120`); no bone-parent nesting | [backlog-ui-feedback.md](backlog-ui-feedback.md#outliner-panel) |
| ui | left-align-names | Left-align mesh names | open | `outliner.py:70-77` operator labels without alignment; text centers | [backlog-ui-feedback.md](backlog-ui-feedback.md#outliner-panel) |

### Validation panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | slot-transform-keys | Does not detect transform keys on slot attachments | needs-retest | `active_slot.py:31,83-112` check wired via `export.py:57`, unit-tested; check predates the bug report - original GUI failure unexplained, re-run needed | [backlog-bugs-found.md](backlog-bugs-found.md#validator-não-detecta-keyframes-de-transform-em-slot-attachments) |
| bug | slot-no-parent-bone | Flags slot attachments as "no parent bone" (false positive) | open | `export.py:61-78` walks all meshes with no is_slot-parent skip | [backlog-bugs-found.md](backlog-bugs-found.md#validator-flagga-slot-attachments-como-no-parent-bone-false-positive) |
| bug | validator-pg-only | Reads PG only, ignores raw Custom-Property edits | partial | `validation/_shared.py:21,33` element fields route through writer's read_field; `active_slot.py:40-41` slot_default still PG-only getattr | [backlog-bugs-found.md](backlog-bugs-found.md#validator-lê-pg-só-ignora-edits-direto-em-custom-properties) |
| ui | frame-unhide-on-click | Frame + unhide offending object on issue click | open | `selection.py:31-37` select only; no unhide/frame-view | [backlog-ui-feedback.md](backlog-ui-feedback.md#validation-panel) |

### IK workflow

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | ik-toggle-no-target | Toggle IK creates constraint without target | open | `authoring_ik.py:49-55` no target/subtarget wiring | [backlog-ui-feedback.md](backlog-ui-feedback.md#toggle-ik--ik-workflow) |
| ui | ik-bake-gate | No bake-action gate before export | open | no IK check in core/validation; no nla.bake wrapper | [backlog-ui-feedback.md](backlog-ui-feedback.md#toggle-ik--ik-workflow) |
| feature | ik-fk-switch | IK/FK runtime switch (Rigify-style) | open | no switch/driver code; ik_constraint_export OUT_OF_SCOPE | [backlog-ui-feedback.md](backlog-ui-feedback.md#toggle-ik--ik-workflow) |
| feature | ik-chain-helper | IK chain helper (one-click constraint stack) | open | only the toggle exists; no target/pole scaffolding | [backlog.md](backlog.md#ik-chain-helper) |

### Help / status badges

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | sprite-frame-preview-help-orphan | sprite_frame_preview help topic orphan (regressed by #96) | open | topic exists (`help_topics.py:417`); `_draw_sprite.py:17-28` has no help button; `draw_subbox_header` has zero callers | [backlog-bugs-found.md](backlog-bugs-found.md#help-topic-sprite_frame_preview-é-orphan---sem-entry-point-na-ui) |
| ui | see-also-clickable | Local-path see-also refs not clickable | partial | `help_dispatch.py:89-97` http(s) refs render as url_open buttons + doc_url button; 3 local-path refs still plain labels | [backlog-ui-feedback.md](backlog-ui-feedback.md#help--status-badges) |
| ui | help-panel-popup-button | Replace Help panel with single popup button | open | `help.py:32-52` Help panel persists (DEFAULT_CLOSED cheat-sheet) | [backlog-ui-feedback.md](backlog-ui-feedback.md#help--status-badges) |
| ui | merge-diagnostics-help | Merge Diagnostics into Help panel | open | `diagnostics.py:13-33` still separate panel (now behind debug_mode pref, spec 024) | [backlog-ui-feedback.md](backlog-ui-feedback.md#diagnostics-panel) |
| feature | i18n-locale-tables | i18n: populate per-locale translation tables | open | `i18n.py:32` TRANSLATIONS empty tuple - mechanism wired, tables empty by design | [backlog.md](backlog.md#spec-023-follow-up-i18n-tables-see-also-urls-docs-depth) |
| feature | see-also-online-urls | Migrate inline see-also refs to online URLs | open | `help_topics.py:182,334,512` still local paths | [backlog.md](backlog.md#spec-023-follow-up-i18n-tables-see-also-urls-docs-depth) |
| feature | addon-docs-screenshots | Expand addon reference pages with screenshots | open | docs/02-blender-addon/ 13 pages, ~14 lines each, no screenshots | [backlog.md](backlog.md#spec-023-follow-up-i18n-tables-see-also-urls-docs-depth) |
| feature | docs-url-preference | Docs-URL as a preference (when second target appears) | open | `help_topics.py:837` `_DOCS_BASE` hardcoded; deferred by design, trigger not hit | [backlog.md](backlog.md#spec-024-follow-up-docs-url-preference-d3--overrides-d4---none) |
| feature | guide-doc-rename-sweep | Guide-doc rename sweep (Element + panel-name vocabulary) | open | `docs/00-guides/00-basic/02-blender.md:55` + advanced still say "Automesh from Sprite" / "Skinning" | [backlog.md](backlog.md#spec-022-follow-up-in-editor-smoke--guide-doc-rename-sweep) |

### Pose library

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | pose-save-library-precheck | Save Pose fails without writable asset library; no guidance | needs-retest | `pose_library.py:68-85` writable-library pre-check + actionable error + asset_library_reference (fix `7d10f69`); no post-fix GUI log | [backlog-bugs-found.md](backlog-bugs-found.md#save-pose-to-library-unexpected-library-type-sem-orientação-ao-usuário) |
| feature | pose-apply-to-selection | One-click apply-pose-to-selection | open | only save_pose_asset + bake_current_pose exist | [backlog.md](backlog.md#pose-library-evolution) |
| feature | pose-auto-categorise | Auto-categorise poses by armature name | open | no catalog/categorise code | [backlog.md](backlog.md#pose-library-evolution) |
| feature | pose-thumbnails | Pose-asset thumbnails via Proscenio preview camera | open | no thumbnail render; preview camera not wired to assets | [backlog.md](backlog.md#pose-library-evolution) |

### Other / proposed

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | onion-skin-overlay | Onion-skin overlay for animators | open | no onion-skin code in tree | [backlog.md](backlog.md#onion-skin-overlay) |
| feature | joystick-slider-blend | Joystick / slider multi-pose blend widget | open | no joystick/BlendSpace code | [backlog.md](backlog.md#joystick--slider-authoring) |
| feature | materials-panel | Materials panel (interpolation, blend-mode, bulk path fix) | open | panel registry lacks Materials module | [backlog-ui-feedback.md](backlog-ui-feedback.md#materials-panel-proposed---doesnt-exist-yet) |
| feature | validator-element-rename | Validator internal naming sprites-vs-elements rename | open | `_types.py:74` SpritePayload; `measurement.py:177` + `report.py:63` report.sprites unchanged | [backlog.md](backlog.md#validator-internal-naming-sprites-vs-elements) |
| feature | panel-helper-consolidation | Panel-helper consolidation (cross-module dupes) | open | `_helpers.py:36-43` holds only the PR-#96 pair; scene-props getattr still inline in 5 panels | [backlog.md](backlog.md#panel-helper-consolidation-cross-module-dupes) |

## Photoshop Plugin

### Tags panel / tag system

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | tag-form-clear | Advanced-fields form cannot clear a set tag | open | `tag-form.ts:97-99` `delete changes[key]` still drops clear signal; zero clear cases in tag-form.test.ts | [backlog.md](backlog.md#tags-advanced-fields-form-cannot-clear-a-set-tag) |
| feature | nested-merge-warning | Nested [merge] collapses silently (revisit with warning) | open | `planner.ts:189-213` emitTagConflicts has no merge-nested entry (by design) | [backlog.md](backlog.md#nested-merge-collapses-silently) |
| feature | name-pattern-rewrite | [name:pre*suf] parsed but planner does not rewrite | open | `tag-parser.ts:28` parses namePattern; planner has zero references | [backlog.md](backlog.md#namepresuf-parsed-but-planner-does-not-rewrite) |
| feature | kind-mesh-vs-polygon | kind:"mesh" equals "polygon" downstream until mesh-deformation ships | open | `planes.py:403` stamps CP; no deformation branch anywhere | [backlog.md](backlog.md#kind-mesh-semantically-equal-to-kind-polygon-downstream) |
| feature | slice-9slice-tag | [slice] Cocos-style 9-slice tag | open | tag-parser has no slice tag | [backlog.md](backlog.md#sliceltrb---cocos-style-9-slice) |
| feature | head-turner-groups | Head-turner view groups (Character Animator) | open | no view-group code in src | [backlog.md](backlog.md#head-turner-view-groups-adobe-character-animator) |
| feature | pseudo-keyword-tagging | Pseudo-keyword auto-tagging (Head, Mouth, Eye) | open | bracket-tags only (`tag-parser.ts:115-119`) | [backlog.md](backlog.md#pseudo-keyword-auto-tagging-head-mouth-eye_open-) |
| feature | isolated-flag | [isolated] warp-independent flag | open | TagBag lacks the field | [backlog.md](backlog.md#isolated-warp-independent-flag-character-animators--prefix) |

### Exporter / roundtrip

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | ppu-roundtrip | PPU not round-tripped; defaults to 100 (waived) | open | `manifest.ts:18` DEFAULT_PIXELS_PER_UNIT=100; import-flow never reads manifest PPU, no XMP plumb | [backlog-bugs-found.md](backlog-bugs-found.md#jsx-exporter-pixels_per_unit-não-roundtripa-hardcoded-100) |
| bug | waist-1px-drift | waist height drifts -1px on PS round-trip | needs-retest | JSX reader retired; drift measured against JSX era, never re-measured through UXP png-writer trim path | [backlog-bugs-found.md](backlog-bugs-found.md#jsx-exporter-waist-size-difere-1px-entre-blender-bbox-e-photoshop-layerbounds) |
| feature | stable-layer-identity | Stable layer identity in PngWrite.layerPath (dup names) | open | `planner.ts:60` layerPath string[] - no {name, index} tie-break | [backlog.md](backlog.md#stable-layer-identity-in-pngwritelayerpath) |
| feature | doll-oracle-v2 | Doll-roundtrip oracle re-run against schema v2 | open | v2 structure pinned by pytest only; no byte-equal v2 capture (deferred by design) | [backlog.md](backlog.md#doll-roundtrip-oracle-re-run-against-schema-v2) |
| feature | origin-pivot-fixture | Dedicated origin/pivot fixture | open | no origin fixture in packages/fixtures; doll oracle stands in | [backlog.md](backlog.md#dedicated-origin--pivot-fixture-a-photoshop-tag-system-follow-up) |
| feature | spectrum-shadow-dom | Spectrum web-component shadow-DOM init cost | open | sp-action-button/sp-textfield in 5 panel files; trigger (>100-layer lag) not hit | [backlog.md](backlog.md#spectrum-web-component-shadow-dom-init-cost) |
| feature | flat-fixture-buckets | Migrate flat fixtures into psd_to_blender/blender_to_godot buckets | open | 8 flat fixtures remain; buckets hold only tag_smoke + README | [backlog.md](backlog.md#migrating-flat-fixtures-into-psd_to_blender-and-blender_to_godot) |

### Other DCC exporters

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | krita-exporter | Krita exporter (Phase 2) | open | no Krita code in apps/ | [backlog.md](backlog.md#krita-exporter) |
| feature | gimp-exporter | GIMP exporter (lower priority) | open | no GIMP code anywhere | [backlog.md](backlog.md#gimp-exporter) |

## Godot Plugin

### Importer / builders

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | node-name-collision-polish | Node-name collision polish (Bone2D vs Polygon2D) | open | `node_name_util.gd:13` only sanitizes punctuation; no prefix, no convention doc | [backlog.md](backlog.md#node-name-collision-polish) |
| feature | plugin-uninstall-warning | Plugin-uninstall warning UI / CI guard | open | tests exercise builders directly; no plugin-disabled scene assert in CI | [backlog.md](backlog.md#plugin-uninstall-warning-ui) |
| quality | sprite2d-region-filter-clip | Sprite2D region_filter_clip for packed sprite_frame | open | `sprite_builder.gd:53-60` sets region_enabled + region_rect only; repo grep region_filter_clip: zero | [backlog.md](backlog.md#sprite2d-region_filter_clip-for-packed-sprite_frame) |

## Cross-cutting

### Fixtures

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | simple-psd-slot-cycle-abs-paths | Audit simple_psd / slot_cycle for absolute image paths | open | `slot_cycle/build_blend.py:146-149` no relpath rewrite before save; simple_psd delegates to importer (no relpath there) | [backlog-bugs-found.md](backlog-bugs-found.md#fixtures-simple_psd--slot_cycle-provável-path-absoluto-de-imagem-bakeado-no-blend) |

### Tests / CI

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| quality | run-coverage-ci | Wire run_coverage.py + combine into CI | open | ci.yml test-blender has no run_coverage step; sonar-project.properties documents local pre-scan | [backlog.md](backlog.md#spec-020-follow-up-coverage-deferrals) |
| quality | drop-bpy-coverage-exclusions | Drop bpy-bound coverage exclusions when units comprehensive | open | `sonar-project.properties:38` still excludes operators/panels/properties/bpy_helpers | [backlog.md](backlog.md#spec-020-follow-up-coverage-deferrals) |
| quality | edge-polish-pure-modules | Edge-polish ~8 pure modules at 89-93% | open | no coverage work since PR #95 | [backlog.md](backlog.md#spec-020-follow-up-coverage-deferrals) |
| quality | blender-multi-version-matrix | Blender headless multi-version matrix (4.2 LTS + latest) | open | `ci.yml:107` single pin blender-5.1.1 | [backlog.md](backlog.md#blender-headless-test---multi-version-matrix) |
| quality | godot-editor-reimport-test | Godot full editor-reimport test (plugin-disabled assertion) | open | apps/godot/tests has only test_importer.gd (builders-direct) | [backlog.md](backlog.md#godot-importer-test---full-editor-reimport) |
| quality | ci-matrix-expansion | Godot/Blender CI matrix expansion | open | `ci.yml:158` pins godot-4.6.2; `:107` blender-5.1.1; no matrix | [backlog.md](backlog.md#ci-matrix-expansion) |
| feature | mixed-feature-fixture | End-to-end mixed-feature fixture (atlas+sprite_frame+slots+drive) | open | examples/generated still single-feature; buckets near-empty | [backlog.md](backlog.md#end-to-end-mixed-feature-fixture) |

### Code quality

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| quality | eslint-not-in-ci | ESLint never runs in CI or pre-commit | open | `ci.yml:34-52` lint-photoshop runs typecheck + vitest only; no eslint hook in pre-commit | [backlog-code-quality.md](backlog-code-quality.md#eslint-never-runs-in-ci-or-pre-commit) |
| quality | models-codegen-no-mypy | packages/models + packages/codegen have no mypy gate | open | zero [tool.mypy] in both pyproject.toml; CI mypy only blender + validator | [backlog-code-quality.md](backlog-code-quality.md#packagesmodels-and-packagescodegen-have-no-mypy-gate) |
| quality | mypy-ignore-errors-subtrees | mypy ignore_errors exempts large bpy-bound subtrees | open | `apps/blender/pyproject.toml:119` + validator overrides intact | [backlog-code-quality.md](backlog-code-quality.md#mypy-ignore_errors--true-exempts-large-bpy-bound-subtrees) |
| quality | bpy-stubs-override-sweep | Drop remaining bpy ignore_errors overrides (stubs adopted) | partial | fake-bpy-module-latest adopted (`pyproject.toml:21`, PR #80); the module-by-module override sweep is pending | [backlog.md](backlog.md#bpy-stubs-drop-the-remaining-ignore_errors-overrides) |

### Repo / packaging

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | release-photoshop-stale | Release workflow Photoshop job stale (.jsx -> UXP dist) | open | `release.yml:39` still cp's proscenio_export.jsx; no .jsx exists - a photoshop-v* tag would fail | [backlog.md](backlog.md#release-workflow-photoshop-job-stale-jsx--uxp-dist) |
| feature | issue-pr-templates | Issue + PR templates | open | .github/ contains only workflows/ | [backlog.md](backlog.md#issue-and-pr-templates) |
| feature | install-dev-script | scripts/install-dev.ps1 to automate dev junctions | open | scripts/ holds only debug/godot/maintenance | [backlog.md](backlog.md#statusline--dev-loop-polish) |

### Architecture revisits (not slated)

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | gdextension-escape-hatch | GDExtension / C# escape hatch (documented, gated on triggers) | open | entry stands; AGENTS.md hard rule #3 intact; no apps/godot-csharp | [backlog.md](backlog.md#gdextension--c-escape-hatch) |

## Audit notes (2026-06-10)

What the verification + cleanup pass did and what stays actionable:

- **Pruned as verified-fixed (26 bugs)** from `backlog-bugs-found.md` and this file: the 3 writer output bugs (`3e15758`, `b2eacbf`), the Drive-from-Bone triad (`4ce3df9`/`8196e9d`, `7f6e178`), slot PG/CP mirror (`d6ff6a9`), snap-to-UV-bounds (`dece00a`), Animation/Outliner row-click + filter (`dcd08f6`), Quick Armature Z=0 (`800e80f`) + empty-rig sweep + PEP 563 post-mortem (rule promoted to `.ai/conventions/code.md` + `.ai/skills/blender-dev.md`), the 2 atlas Apply bugs (`27f7640`, `15fc634`), mouth_drive bone orientation, wrapper-.tscn paths (`8e5155a`), and the Godot-side duplicates of the writer fixes. Re-verified by direct code reads + 621 repo pytest + 226 vitest green.
- **Pruned as shipped (15 features)** from `backlog.md` / `backlog-ui-feedback.md`: element-vocab rename, version-line footer + GitHub link, accordion subpanels, per-subpanel help topics, Validate button in panel, multi-mesh batch bind, weight-transfer operator, sidecar IO, brush-presets row, ortho preview camera, png-writer findLayerByPath, JSX exporter port (obsolete - UXP supersedes), Docusaurus docs site, LICENSE full body, project.godot warning tuning + :Variant annotations (resolved via typed schema_bindings).
- **Promoted to a new bug:** writer exports `armatures[0]` and ignores the active-armature picker (found by the audit; see Writer / exporter above).
- **Regression on record:** sprite_frame_preview help orphan was fixed (`6749412`) then regressed by the #96 restructure - `draw_subbox_header` has zero callers; noted in the bug entry.
- **Needs-retest queue (GUI session):** skeleton row-click select, save-pose pre-check, validator slot-transform-keys (check predates the logged failure - root cause unexplained), PS waist 1px drift (re-measure through UXP). `backlog-manual-testing.md` markers flipped to `[~]` with commit pointers.
