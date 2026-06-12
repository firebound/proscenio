# Backlogs summary

Verified index of every open backlog item, grouped by plugin and area. Each row: Type (`bug` defect / `ui` polish / `quality` toolchain / `feature`), a short slug, a <=10-word description, a code-verified Status, the Evidence (file:line) backing that status, and a Link to the canonical entry in the `specs/backlog-*` files. Statuses were audited 2026-06-10 against `main`: `open` = present / not started; `partial` = some sub-points resolved; `needs-retest` = code-fixed, only a GUI smoke can confirm; `upstream` = external (Blender) issue.

The 2026-06-11 reconciliation of specs 027-035 pruned this index hard: every row whose work shipped in PRs #104-#113 was removed (the locked calls live in [`decisions.md`](decisions.md)), and every not-now row moved to its new home - [`DEFERRED.md`](DEFERRED.md), [`GATED.md`](GATED.md), or [`DROPPED.md`](DROPPED.md). What remains is the work owned by the not-yet-started specs (ui-help-surfaces, storage-split, reach), the GUI-retest rows whose code fix shipped but await a verification-session smoke (tracked in [`EXECUTION_MAP.md`](EXECUTION_MAP.md) "Verification session"), and two newer backlogs (Photoshop performance, IK authoring ergonomics). Blocking items for the first release are called out in [PLAN.md](PLAN.md). Blender-6-gated work is excluded (see [backlog-blender-6.md](backlog-blender-6.md)).

## Blender Addon

### Cross-panel / general

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | subpanel-drag-reorder | Drag-and-drop reorder of subpanels | partial | sibling top-level panels get native header-drag free; `bl_parent_id` subpanels cannot (upstream Blender limit) | [backlog-ui-feedback.md](backlog-ui-feedback.md#cross-panel--general) |
| feature | panel-helper-consolidation | Panel-helper consolidation (cross-module dupes) | open | `_helpers.py:36-43` holds only the PR-#96 pair; scene-props getattr still inline in 5 panels | [backlog.md](backlog.md#panel-helper-consolidation-cross-module-dupes) |

### Format / schema

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | pg-cp-storage-split | Storage split PG-vs-CP by intent (target 1.0.0) | open | uniform mirror intact: `mirror.py:56-71` (14 rows) + `hydrate.py:17-29` (11 rows); `read_field` dual fallback in `writer/sprites.py:72` | [backlog.md](backlog.md#split-propertygroup-vs-custom-property-storage-by-intent-target-100) |

### Active Sprite panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | reproject-uv-orientation | Reproject UV: slow 2nd call + rotated/flipped result | partial | still `smart_project` (`uv_authoring.py:73`); limitation documented in docstring + tooltip; Edit-Mode start rejected; perf symptom unverified | [backlog-bugs-found.md](backlog-bugs-found.md#reproject-uv-segunda-chamada-lenta--uv-resultante-rotacionadaflipada) |
| ui | header-mesh-name | Show selected mesh name in header | open | `element.py:94` static `bl_label = "Active Sprite"`; no draw_header with obj.name | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | clamp-initial-frame | Clamp Initial frame to [0, hframes*vframes-1] | open | `object_props.py:95-102` frame has min=0 only, no max/soft_max | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | rename-initial-frame | Rename "Initial frame" to "Frame" | open | `object_props.py:96` still `name="Initial frame"` | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |
| ui | centered-vs-origin-help | Clarify centered-vs-origin distinction in help | partial | `help_topics.py:616-617` explains centered semantics (spec 023); no explicit vs-PS-origin contrast | [backlog-ui-feedback.md](backlog-ui-feedback.md#active-sprite-panel) |

### Mesh Generation panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | automesh-interactive-extend-cut | Automesh Interactive extend/cut broken or artifacts | needs-retest | code fix shipped in #106 (`outer_splice.py` crossing splice + tests); GUI smoke 1.23 T1 / 1.25 T6,T9 pending | [backlog-bugs-found.md](backlog-bugs-found.md#automesh-interactive-modal-ferramentas-extend--cut-quebradas) |

### Skeleton panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | skeleton-row-click-select | Row click does not select bone in viewport | needs-retest | `selection.py:79-93` select_bone_by_name wired per-row in `skeleton.py:51-57` (fix `dcd08f6`); no post-fix GUI log | [backlog-bugs-found.md](backlog-bugs-found.md#skeleton-panel-row-click-no-uilist-não-seleciona-bone-no-viewport) |

### Quick Armature

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | qa-gizmo-crash | Blender 5.1.1 gizmo crash post snap-cursor (upstream-suspect) | upstream | stack 100% Blender/AMD internals; defensive try/except shipped (`_handlers.py:82-100`) | [backlog-bugs-found.md](backlog-bugs-found.md#blender-511-crash-em-gizmo_button2d_draw-apos-view3dsnap_cursor_to_center-suspeito-upstream) |

### IK authoring ergonomics

Session feedback (2026-06-11) after the spec 031 IK target-wiring + bake gate shipped. Canonical entries in [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md).

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | ik-toggle-misnomer | "Toggle IK" is create/destroy, not a toggle | open | `authoring_ik.py` adds/removes the whole constraint + control bone; no influence on/off | [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md#entradas) |
| ui | ik-no-indication | No Proscenio signal that an IK chain exists | open | only the `.IK` control-bone suffix hints; Skeleton panel lists bones flat | [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md#entradas) |
| ui | ik-constraint-props-inaccessible | Chain length / influence / pole only via native Bone Constraints | open | no Proscenio surface exposes the constraint props | [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md#entradas) |
| bug | ik-control-bone-leaks-export | `.IK` control bone exports as a Bone2D | open | `build_skeleton` (`skeleton.py:92`) iterates `iter_bones` without filtering `use_deform=False` | [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md#entradas) |
| feature | ik-rigify-style-management | Rigify-style bone collections / colors / shapes for controls | open | no bone-collection/custom-shape/color set on the `.IK` control bone | [backlog-ik-ergonomics.md](backlog-ik-ergonomics.md#entradas) |

### Outliner panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| ui | indented-tree | Indented tree (armature > slots > attachments) | partial | category-rank sort + indent for slot attachments (`outliner.py:15-32,120`); no bone-parent nesting | [backlog-ui-feedback.md](backlog-ui-feedback.md#outliner-panel) |
| ui | left-align-names | Left-align mesh names | open | `outliner.py:70-77` operator labels without alignment; text centers | [backlog-ui-feedback.md](backlog-ui-feedback.md#outliner-panel) |

### Validation panel

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | slot-transform-keys | Does not detect transform keys on slot attachments | needs-retest | shared `action_fcurves` reader wired via `active_slot.py` + `export.py` (#104), unit-tested; original GUI failure unexplained, re-run on `slot_swap` pending | [backlog-bugs-found.md](backlog-bugs-found.md#validator-não-detecta-keyframes-de-transform-em-slot-attachments) |
| ui | frame-unhide-on-click | Frame + unhide offending object on issue click | open | `selection.py:31-37` select only; no unhide/frame-view | [backlog-ui-feedback.md](backlog-ui-feedback.md#validation-panel) |

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

### Other / proposed

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | onion-skin-overlay | Onion-skin overlay for animators | open | no onion-skin code in tree | [backlog.md](backlog.md#onion-skin-overlay) |
| feature | joystick-slider-blend | Joystick / slider multi-pose blend widget | open | no joystick/BlendSpace code | [backlog.md](backlog.md#joystick--slider-authoring) |
| feature | materials-panel | Materials panel (interpolation, blend-mode, bulk path fix) | open | panel registry lacks Materials module | [backlog-ui-feedback.md](backlog-ui-feedback.md#materials-panel-proposed---doesnt-exist-yet) |
| feature | validator-element-rename | Validator internal naming sprites-vs-elements rename | open | `_types.py:74` SpritePayload; `measurement.py:177` + `report.py:63` report.sprites unchanged | [backlog.md](backlog.md#validator-internal-naming-sprites-vs-elements) |

## Photoshop Plugin

### Performance (UXP panel)

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | dom-api-ipc-walks | Layer-tree walks pay one sync IPC per property; convert to batchPlay multiGet | open | `adapt-document.ts:28,60-75` recursive DOM-API walk (`.name`/`.visible`/`.bounds` per layer) | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#dom-api-layer-walks-pay-one-synchronous-ipc-call-per-property) |
| bug | double-adapt-per-tick | Each document event runs adaptDocument twice + export dry-run + ajv | open | `ProscenioTagsPanel.tsx:38-42` preview.refresh + `useTagTree.ts:44-58` syncOnce, same version bump | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#every-document-event-triggers-two-full-layer-tree-adaptations-plus-an-export-dry-run) |
| bug | busy-defeats-memo | Global busy flag re-renders every TagRow twice per rename | open | `Row.tsx:204-228` tagRowEqual compares `busy`; `useTagTree.ts:95-110` flips it per rename | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#the-global-busy-flag-defeats-reactmemo-across-the-whole-tag-list) |
| bug | unstable-react-keys | Keys from raw layerPath remount whole subtree on rename | open | `TagsSection.tsx:81` `key={node.layerPath.join("/")}`; rename shifts descendants' keys | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#react-keys-derive-from-raw-layer-names-remounting-subtrees-on-rename) |
| bug | idle-poll-tree-walks | 1.5s full-tree IPC poll + 300ms selection poll always on | open | `useTagTree.ts:23-24` ACTIVE_POLL_MS=1500; `useActiveLayerPath.ts:15` POLL_MS=300 | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#polling-cadence-runs-full-tree-ipc-reads-even-when-idle) |
| feature | tags-list-virtualization | No virtualization; 500+ layer PSDs mount thousands of UXP controls | open | `TagsSection.tsx:69-90` renders every visible node; no cap or windowing | [backlog-photoshop-performance.md](backlog-photoshop-performance.md#large-documents-render-every-row-with-no-virtualization) |

### Exporter / roundtrip

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| bug | waist-1px-drift | waist height drifts -1px on PS round-trip | needs-retest | JSX reader retired; drift measured against JSX era, never re-measured through UXP png-writer trim path | [backlog-bugs-found.md](backlog-bugs-found.md#jsx-exporter-waist-size-difere-1px-entre-blender-bbox-e-photoshop-layerbounds) |

### Other DCC exporters

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | krita-exporter | Krita exporter (Phase 2) | open | no Krita code in apps/ | [backlog.md](backlog.md#krita-exporter) |
| feature | gimp-exporter | GIMP exporter (lower priority) | open | no GIMP code anywhere | [backlog.md](backlog.md#gimp-exporter) |

## Cross-cutting

### Architecture revisits (not slated)

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| feature | gdextension-escape-hatch | GDExtension / C# escape hatch (documented, gated on triggers) | open | entry stands; AGENTS.md hard rule #3 intact; no apps/godot-csharp | [backlog.md](backlog.md#gdextension--c-escape-hatch) |

### Code quality

| Type | Item | Description | Status | Evidence | Link |
| --- | --- | --- | --- | --- | --- |
| quality | wheel-staleness-gate | Bundled proscenio_models wheel has no staleness gate | open | `apps/blender/wheels/README.md` "When to bump" omits model shape changes; no `tests/codegen/` check rebuilds the wheel | [backlog-code-quality.md](backlog-code-quality.md#the-bundled-proscenio_models-wheel-has-no-staleness-gate) |

## Reconciliation note (2026-06-11)

The 027-035 reconciliation removed the rows whose work shipped (PRs #104-#113) and relocated the not-now rows. To find where a former row went:

- **Resolved** (shipped): gone from here; the locked design call, if any, is in [`decisions.md`](decisions.md); the code is in git history under the PR.
- **Gated** (held behind a trigger): [`GATED.md`](GATED.md).
- **Deferred** (sequenced second-stage): [`DEFERRED.md`](DEFERRED.md).
- **Dropped** (value below cost): [`DROPPED.md`](DROPPED.md).
- **Retest** (code-fixed, GUI smoke pending): retained above with `needs-retest` status; the smoke runs in the [`EXECUTION_MAP.md`](EXECUTION_MAP.md) verification session.

The earlier audit tables (2026-06-10 prune of 26 bugs + 15 features) live in this file's git history.
