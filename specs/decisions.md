# Decisions

Locked architectural and per-feature calls. ADR-light: the call, the rationale, and the revisit trigger. Open work lives in the per-domain backlogs indexed from [`backlog.md`](backlog.md); this is the consolidated home for settled calls - the hand-written planning docs were retired once each feature shipped, so the rationale worth keeping was mirrored back here. One clause per rationale; impl detail stays in the code it cites.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension / native runtime** | GDScript-only plugin; generated `.scn` is native nodes, runs on plain Godot 4 with the plugin uninstalled. | Deep Firebound integration, `Polygon2D` skinning perf ceiling, Blender <-> Godot live-link, binary `.proscenio`, in-Godot round-trip. |
| **Conversion one-time, at editor import** | Heavy work at import; runtime is Godot core (C++), no GDScript perf ceiling. | Same as GDExtension. |
| **Strong typing everywhere** | GDScript `untyped_declaration=2`, Python `mypy --strict`, TS `strict`. | Baseline rule. |
| **Schemas are the contract (pre-launch: no bump)** | Pre-launch shape changes happen in place at the current `format_version`, no migration code, proven by regenerating fixtures + goldens; the number freezes at first public release. CI validates fixtures every stage. | First public release flips to bump-plus-migration for every later cross-component shape change. |
| **Storage split by field intent** | Editor-only fields are PropertyGroup-canonical; animatable / driver-target fields (`frame`, slot index) are Custom-Property-canonical (Blender cannot keyframe a PG-nested field). Locked, not yet implemented - code still mirrors uniformly. | Implement before 1.0.0; gated on the migration-path enabler + the 1.0.0 window. |
| **Addon preferences user-global, no per-project** | The scene PropertyGroup already carries per-`.blend` state. | A real need for per-project preference values. |
| **Wrapper-scene reimport, full overwrite** | Importer overwrites `.scn`; the user wrapper `.tscn` survives with scripts / extras. Marker-based merge would lose scripts on a bone rename (no stable IDs) and double the code paths. | Concrete pain the wrapper pattern cannot serve. |
| **One component per PR** | PS / Blender / Godot ship independent PRs; schema bumps cross all by definition. | None. |
| **Lockstep product versioning** | Three apps are one coupled pipeline (the addon emits a `format_version` the importer reads), so one SemVer `vX.Y.Z` bumped by the highest severity; unchanged apps re-stamp and ride along. Per-app detail in the CHANGELOG; `format_version` stays independent. Detail in [`.ai/conventions/layout.md`](../.ai/conventions/layout.md). | A component gains an independent consumer or release cadence. |
| **C# / GDExtension = documented escape hatch** | Maintainer prefers typing but stays in GDScript for 2D-community reach; Firebound itself stays C#. | Same as GDExtension. |
| **`apps/` + `packages/` + `scripts/` + `tools/` split** | apps ship; packages are shared building blocks; scripts are dependency-free one-offs; tools are standalone packages (own deps / build / tests), not shipped. Own manifest / build means tools or packages, never scripts. Detail in [`.ai/conventions/layout.md`](../.ai/conventions/layout.md). | A third standalone pnpm package warrants a root pnpm workspace alongside uv. |
| **Manual-test surface owned by QA Companion** | The walkable `checklist/` is living data round-tripped by the tool in `tools/qa-companion/`; the seeding `findings.md` audit was triaged + retired 2026-06-15 (code issues to bug backlogs, doc gaps to [`backlog-docs.md`](backlog-docs.md), rest dropped). | The checklist block format changes shape, or the tool is replaced. |
| **Codegen artifacts checked in per-app `schema_bindings/`** | Detailed home below (Typed-models codegen); `tests/codegen/` reproduces + fails on drift. | Renaming the binding folder, or moving JSON Schema off `packages/models/schemas/`. |

## Validation gates

Layered defenses, cheapest first:

1. **Editor / IDE.** Live diagnostics (Pylance, gdtoolkit, TypeScript LSP) + a shared spell-checker.
2. **Pre-commit.** Per-language formatters / linters, schema validation of staged JSON, spell-checker.
3. **CI - Python.** `ruff` + `mypy --strict` + pytest against the typed addon surface.
4. **CI - TypeScript.** `tsc --noEmit` + `vitest` against the Photoshop plugin.
5. **CI - GDScript.** `gdformat --check` + `gdlint` against the Godot plugin.
6. **CI - schemas.** Every fixture under `examples/` and per-app `tests/fixtures/` validated against the cross-component schemas.

Schemas are enforced at four points: producer output (writer / exporter validates before any diff), consumer input (PS runtime check, Godot format-version guard), CI fixture validation, and the migration path on any future bump.

## Feature decisions and studies

The calls made while building each feature that crossed a component boundary or shaped a contract. Every feature here has shipped; a few carry a follow-up not yet implemented.

### Animation tracks

- **Tracks ship resolved absolute values, not rest+delta.** Simpler importer; the cost is bigger payloads.

### Spritesheet Sprite2D discriminator

- **`type` discriminator is additive, no `format_version` bump.** `sprite_frame` lives beside `polygon` under a `type` field defaulting to `"polygon"` - pre-discriminator fixtures stay compatible.

### Skinning weights export

- **Skinned polygons parent to `Skeleton2D`, rigid sprites stay bone-parented.** Two parenting strategies coexist by design.
- **Skinning quality validation is user-driven** (paint, observe deformation) - no programmable visual check.

### Slot system

- **Hard cut, NEAREST interp on `slot_attachment` tracks.** Crossfade is a future extension.
- **Sprites stay in top-level `sprites[]`; `slots[].attachments[]` is a name list the importer cross-references.** Flat schema, no `slot:` field on `Sprite`.
- **Slots fit `format_version=1`** (already part of v1) and are **kind-agnostic** (polygon + sprite_frame compose in one slot).

### Blender authoring panel

- **Validation is lazy + inline.** Heavy scene walk behind the Validate button; per-subpanel status badges are O(1) per redraw. (Storage split: see Core architecture.)

### Blender N-panel layout and help surface

- **`bl_order` fixes the panel order and every panel (top-level and subpanel) opens `DEFAULT_CLOSED` except the About footer** - Pipeline leads (Import / Validate / Export subpanels), then Element, Slots, Skeleton, Mesh Generation, Weight Paint, Outliner, Animation, Atlas, Helpers; a panel-chrome test pins the collapsed invariant across the whole tree (subpanels included, so a section never spills its primary subpanel open) so a panel never ships expanded by accident. Revisit: a panel earns always-open status.
- **Help is one `Open help` popup in the About footer, not a panel** - the unusable Help cheat-sheet and the Diagnostics panel were removed (the smoke test rides the footer behind `debug_mode`), ending the Helpers / Help clash; every `HELP_TOPICS` id must have a caller in `panels/` or `operators/`, pinned by a reverse-coverage test so a restructure cannot orphan a topic silently.
- **The Element and Skeleton panels title themselves "<Panel>: <name>" via `draw_header`** (blank `bl_label`, the name dropped wholesale below a width threshold) - the active name reads in the header, never a duplicated body row.
- **Reproject UV is deterministic planar projection** (dominant-plane detect + bounding-box map, keeping the Front-Ortho U-flip the fixtures author), never `bpy.ops.uv.smart_project` - face-normal projection came back rotated and mirrored, destructive to hand-authored UVs.
- **`see_also` references are https URLs, never repo-local paths** - a local path cannot resolve inside an installed zipped extension, so the help dispatcher only buttons `http(s)` refs; the topic test enforces the URL shape.

### Photoshop to Blender importer

- **Blender reads the manifest, never the PSD.** Direct `.psd` parsing is fragile across versions and duplicates the exporter; the manifest is the stable contract.
- **sprite_frame detection: a PSD group with numeric children (primary) or flat `<name>_<index>` (fallback)**, both on the PS side.

### Testing fixtures

- **Five canonical fixtures = a showcase rig + single-feature isolation** (sprite_frame, sliced atlas, PSD roundtrip, slots); one source feeds writer goldens + importer regens.

### Code modularity

- **Refactored into focused subpackages, no schema / behavior change.**
- **Import discipline: `core/` is bpy-free at module top, `core/bpy_helpers/` is the bpy boundary; panels reach operators only via `bl_idname` strings.**

### Blender system organization

- **Layer-first hybrid** (`core/`, `operators/`, `panels/`, `properties/`, `exporters/`, `importers/`); systems are feature subpackages within each layer, never a top-level per-system tree. Driven by type-ordered registration + the pure-vs-bpy test boundary. Revisit: registration stops being type-ordered, or the addon splits into sub-addons.
- **`_shared/` tier for cross-cutting infra** (cp_keys, report, math, compat shims) in `core/_shared/` (pure) + `core/bpy_helpers/_shared/` (bpy-bound).
- **Every Custom Property key literal lives in `core/_shared/cp_keys.py`** - call sites import the constant.

### Photoshop web-app layout

- **Layer-based layout:** `panels/` + `components/` render, `hooks/` own state, `lib/` is pure, `api/` is the single PS boundary, `utils/` are leaf helpers. Direction `panels -> hooks -> api + lib`. Chosen over vertical slices (small panel count; the pure-vs-boundary seam is the axis that needs enforcing). Revisit: enough independent features that per-feature cross-layer churn outweighs the boundary clarity.
- **`lib/` is UXP-free; `api/` is the only boundary** - what makes `lib/` unit-testable without a Photoshop host.
- **One `@ts-nocheck`: `src/entry.ts`** (the vendored Adobe `PanelController` shape `entrypoints.setup` parses reliably), excluded from the typed gate + ESLint.

### Photoshop UXP migration

- **UXP is the only Photoshop entry point;** legacy JSX retired once the doll oracle confirmed pixel-byte parity.
- **Stack: pnpm + webpack + Babel + ajv + vitest** (Vite rejected - UXP needs CommonJS output).
- **Migration shipped at `format_version: 1` byte-for-byte;** the PSD-manifest v2 bump landed under the tag system.
- **Minimum Photoshop CC 2024 / 25+** (`constants.*` enums, persistent tokens, Spectrum) and **`localFileSystem: "fullAccess"`** (the persistent token + sub-folder writes need more than `"request"`).

### Photoshop tag system

- **Bracket-tags `[tag]` / `[tag:value]` are primary; XMP per-layer is secondary; bracket wins on conflict.**
- **PSD manifest bumped to `format_version: 2`** (root `anchor`, per-layer `origin` / `blend_mode` / `subfolder`, new `kind:"mesh"`); the `.proscenio` schema stays v1 - PSD-side only.
- **`kind:"mesh"` is a hint, not a branch** - stamped as `proscenio_psd_kind`, no downstream branch yet; reserved for deformable-mesh / UV-anim work.
- **Unknown tags pass through to the display name** as warnings, never silently dropped.

### Quick Armature UX

- **GPU preview line + the real bone on click, tail tracking MOUSEMOVE** - instant feedback and Edit-Mode parity.
- **Naming prefix = addon preference + F3 override; Front-Ortho auto-snap restores the prior view on exit** (F3 opt-out).
- **Sweep the auto-created QuickRig on cancel only** (tracks whether the operator made it this session); **the mirror flag lives on the picker armature**, not per-operator.

### Weight paint + automesh

- **Automesh = alpha-trace one-shot, pure Python** (no OpenCV, zero third-party); free-draw deferred.
- **Topology = annulus + alpha-hole support** (outer + inner contour + Constrained Delaunay; holes traced as constraint loops, cut by centroid prune) - lifts the Spine / COA2 no-holes limit.
- **`proscenio_base_sprite` vertex group is the regen anchor** - re-runs remove only verts outside it; the original quad corners survive.
- **`BONE_HEAT` is the bind default for 2D pickers** (pre-flight diagnosis still runs; planar proximity is fallback).
- **Sidecar JSON + UV-anchor reprojection preserves weights across regens** inside the `proscenio_base_sprite` envelope; the provenance overlay shows seed / paint / reprojected.
- **Pre-flight diagnosis on auto-weight failure** (unapplied scale, flipped normals, overlaps, isolated islands, bones outside the bbox) - actionable message, never a raw stack.
- **Density-under-bones ON by default when a picker armature exists**, reusing its bone positions.
- **Interior fill = SIMPLE / DENSE enum** (PG default SIMPLE; `StageParams.interior_mode` default DENSE for test back-compat).
- **Toggle pen for Stage 2 / 4** (Shift / Ctrl tap enters; LMB = vert, drag = free-draw, RMB / Enter = finish, Esc = cancel); subdivisions baked at finish, no schema field. Stage-2 outer silhouette uses the same pen + a green spliced-outer preview.

### Typed-models codegen

- **Pydantic v2 in `packages/models/` is the source of truth**, bundled into the addon via wheels; emit path is `model_validate(...).model_dump_json(...)`.
- **Generated artifacts checked in:** `packages/models/schemas/` (JSON Schema), per-app `schema_bindings/` (TS + GDScript Resources), `docs/content/api/schemas/` (Markdown); each carries an `AUTO-GENERATED` header. `tests/codegen/` fails on drift for JSON / TS / GDScript; docs Markdown is regenerable but ungated (needs an npx tool).
- **ajv stays on the PS side; TS interfaces come from `json-schema-to-typescript`** (smaller bundle, mature unions). Revisit `z.fromJSONSchema()` post-experimental.
- **Discriminated unions use a callable `Discriminator`** defaulting an absent `type` to `"polygon"` (v1 compat); returning `None` for unknown tags gives a clearer error than the field-string variant.
- **GDScript Resources carry `_set_fields: PackedStringArray`** so the animation builder tells "set to JSON default" from "absent in source."
- **Every emitted Godot class is `Proscenio`-prefixed** to avoid engine built-in collisions.
- **Strict typing rolled out per language** (mypy strict family, tsc strict-strict family, Godot `unsafe_*`); the bpy stub snapshot + the Docusaurus site stay deferred.

### Monorepo packages

- **uv workspace members:** `apps/blender`, `packages/{codegen,models,validator}`; `packages/fixtures/` is data-only (no `pyproject.toml`). Anything with a subpackage layout, tests, or a CLI belongs in `packages/`.
- **`schema_bindings/` is the universal per-app codegen folder name** (over `generated/` / `bindings/`).
- **Distribution names carry the `proscenio-` prefix** though in-repo folders are unscoped.

### Documentation architecture

- **Docs site = three audience navbar sections** (Guides / Project / Tools); the IA rule + section map are in [`.ai/conventions/docs.md`](../.ai/conventions/docs.md), the wiring in `apps/docs/sidebars.ts`.
- **Code carries what + how; rationale lives in its home, not in comments** - the comment-routing policy is canonical in [`.ai/conventions/code.md`](../.ai/conventions/code.md); the XZ picture-plane + golden field-order conventions live on the docs Architecture page.
- **Module docstrings only when non-obvious;** a pydantic model class docstring IS the schema `description` (trimming one regenerates the schema + TS binding).
- **Pre-commit drift hooks reject spec-path references + `# Step N` / `# Phase N` markers;** prose-density stays an on-demand advisory.

### Export correctness

- **One picker-first armature resolver `resolve_export_armature(scene)`** shared by the writer, the validator, and the Skeleton readout - they cannot diverge in a multi-armature scene.
- **`MeshElement.polygons` is additive-optional at v1, multi-face only** - old importers ignore it, single-face goldens stay byte-stable, so it ships without the gated migration path.
- **`action_fcurves` is the one duck-typed reader** for legacy + Blender 4.4+ layered-action fcurves, shared by writer + validator (the validator's missing guard was the silent-miss bug).

### Sprite appearance and orientation

- **Appearance is derived from native Blender state, never new authoring props** (`modulate` from object color, `z_index` from PSD Y depth, flips from negative local-scale, `Sprite2D.offset` from quad-bounds-vs-origin) - keeps the GUI / mirror surface from growing.
- **Color channels are `ge=0` (HDR over-bright allowed); `z_index` is bounded to +/-4096** to match Godot's clamp.
- **The bone-driven `sprite_frame` bake reproduces from the posed bone, clamps to the grid, constant interp** - exports with or without the PG (the headless harness has none).
- **Orientation checks are warn-only; the writer keeps its XZ assumption** (full-XY is gated). The mesh-flatness test compares smallest-vs-largest axis spread, so a cutout authored in any plane is not false-warned.
- **`region_filter_clip_enabled` is set wherever `region_enabled` is** - stops atlas frames bleeding at the seam.

### Mesh authoring

- **The extend splice anchors at stroke / contour crossings and picks the kept arc by area** (not nearest-vertex + index) - independent of click sparsity, winding, and seam position, the traps that made the old splice amputate the silhouette.
- **Mesh tools gate on `element_type=="mesh"` (warn-not-hide); the rigid sprite bind delegates to native Ctrl+P > Bone** - meshing a sprite destroys its Sprite2D mapping, and native parenting already provides the rigid bind.
- **"Trace resolution" (the alpha-downscale knob) is named apart from mesh density** - it sets silhouette fineness; vertex count comes from Contour vertices + Interior spacing.

### Rigging, drivers, IK

- **IK export protection = bake-at-export, not live constraints.** The validator hard-errors an active IK chain with an animated target but unkeyed members; "Bake IK to Keyframes" is the one-click fix. No runtime IK consumer, and Godot's 2D `SkeletonModification2D` is experimental + flipped-rig-buggy. Revisit: that stack graduates (the gated round-trip).
- **Proscenio IK scaffolding = a `.IK`-suffixed non-deforming control bone; toggle-off deletes only suffix-matched controls** - never touches hand-authored constraints.
- **Drive-from-Bone = a clamped two-range linear map (`build_driver_expression`, bpy-free) with a negative-spanning default input; the raw expression is an Advanced fallback** - the old raw default clamped negative rotation to 0 and looked broken on first contact.

### Slot placement

- **Create Slot places the Empty at the selection's world-space AABB center via `matrix_world`** - lands on visible geometry regardless of a parented seed or an unapplied origin.

### Atlas packing and PPU

- **PPU round-trips via the persisted exporter value (a localStorage seed), not document metadata;** Blender import also syncs the scene prop.
- **PPU is one document-level value end to end; per-asset PPU is rejected** (uniform PPU is the engine-side best practice). Gated on a recurring real case.
- **The atlas padding ring is edge-extended (alpha bleed), default-on, no knob; atlas rotation is permanently rejected** (Godot's `AtlasTexture` / `region_rect` cannot express a rotated region).
- **The packer keeps single-heuristic MaxRects-BSSF** (~94% occupancy; trying all multiplies pack time for nothing at this scale).
- **Unpack material recovery is marker-Custom-Property based; the PG-snapshot version is deferred to the storage split** - a marker survives a rename.

### Project health gates

- **The models / codegen mypy profile drops `disallow_any_explicit` under the pydantic plugin** (the rest of strict holds; `python_version=3.11`) - the flag fires on framework-synthesized `Any`, not author looseness.
- **`release.yml` routes every `workflow_dispatch` free-text input through env vars, never `${{ inputs.* }}` in a shell body, and is exercisable tagless via a dry-run that skips the gh-release upload** - free-text in a `run:` block is a template-injection vector (zizmor / CodeRabbit).

### Photoshop plugin overhaul

- **Targeted boundary rewrite, not from-scratch** - rewrote only the IPC adapter + export writer behind their `AdaptedDocument` / `Manifest` shapes; the tested logic core (planner, parser, manifest builder, validator) was untouched, since the rot was at the host boundary.
- **Every PS-API collection read is null / non-iterable guarded** (returns `[]`) - the `object null is not iterable` crash came from a host getter returning null where the type said non-null. Baseline rule.
- **Tag-write targets resolve by stable layerID, name-path as fallback** - the cached name-path goes stale on a parent rename and the id disambiguates duplicate siblings. (Legacy-migration adopted the same id-first resolve in spec 053; the click-to-select path resolves its path by name but then selects by the resolved layer's id, leaving only a duplicate-same-name-sibling click as a minor accepted gap.)
- **Export is partial, not all-or-nothing** - a per-layer try/catch writes the manifest for the PNGs that landed and names the failures; the manifest never references a missing PNG.
- **The multiGet IPC fast-path shipped as try-multiGet -> DOM-walk fallback** (spec 048, validated on a real 44-layer PSD: ~3 ms vs ~41 ms). The DOM walk stays as the always-correct net (the reader returns `null` on any failure shape). Live-descriptor quirks vs the type stub (`layerSection` / `bounds` envelopes, the `layerID` key, bottom-up enumeration with group start / end markers) are isolated in the field mapper.
- **The async tree read uses a cancellation-guarded effect, not Suspense** - Suspense would unmount the user's open dropdowns / expanded rows on every poll tick. Revisit: collapsing both read paths to a single shared `adaptDocument` snapshot per tick (deferred).
- **The tag-list re-render bug was a shared per-row `busy` prop, fixed by dropping the per-row disable** - renames serialize through `executeAsModal`, so the disable was defensive UI, not a correctness gate.
- **The doll tag oracle is split from the authoring figure** - `doll_tagged.psd` is the clean end-to-end flow; `debug/doll_tagged_debug.psd` is the kitchen-sink parity oracle.

### Slot bone-follow

- **Two follow shapes, both first-class:** a `slot_bone`-bound slot (object-parent + a Child Of constraint whose inverse cancels the bone rest) and a hand-authored real bone parent. Both export the same bone name and Godot rebuilds them identically. The constraint is the facilitated default (stays flat for any bone orientation, lives in a removable layer, unbinds clean); real bone-parenting is permanently supported, never stripped.
- **The Child Of inverse is `(armature.matrix_world @ pose_bone.matrix).inverted()`** (full loc + rot + scale) - the headless Set-Inverse twin of the importer's `get_skeleton_rest().affine_inverse()`. No Godot change.
- **A real bone parent renders correctly only for into-screen (+/-Y) bones; an in-plane bone collapses the quads edge-on** (verified). The constraint never collapses; the panel flags an in-plane bone-parented slot (`bone_parent_collapses`, `abs(world_dir.y) < 0.7`) and points to Unbind + Bind.
- **The shared `slot_parent_bone` resolver reads `slot_bone` first, then a real BONE parent** - the writer's order, so panel / validator / export never disagree about the followed bone.
- **`create_slot`'s pose-bone path defaults to the constraint shape;** a hand bone-parented Empty is still recognized + exportable.
- **Bind refuses when the slot already follows (two-click Unbind -> Bind), never silently converts or strips.** Bind resolves its armature object-parent-first, then the Skeleton picker, then the export armature; the bone via `prop_search`. Revisit: a slot parented to a non-armature surprises the user by targeting the picker / export rig - then enforce the convention at bind time.

### Outliner selection

- **The stale-row crash is guarded at the operator boundary, not in shared `select_only`** - a blanket suppress there would make the slot / camera / bone callers silently no-op.
- **`template_list.active_index` is a source-collection index (the by-name write was already correct); the highlight bug was fixed by hiding out-of-view-layer rows.** The identity-to-index resolver lives in `core/outliner_view.py` (`source_index_for_name`), shared with the slot list.
- **Favorites are filter-only; the second search bar was dropped for native `filter_name`** - the `scene.objects` source migration was rejected for the lighter `row_visible` filter.

### Weight paint mode sync

- **A native weight-paint mode exit is detected by a modal `event_timer_add` poll of `active_object.mode`** (not a depsgraph / msgbus handler) - the modal is the only context where `_finish`'s `mode_set` / `undo_push` are legal.
- **The provenance overlay refreshes at stroke end, not live** - the modal brackets a native brush operator with no per-sample hook; it tags all `VIEW_3D` areas.
- **"Empty vertex group" = no vert weighted above zero;** the clear-empty operator confirms names before deleting.

### Skeleton chrome and animation target

- **Quick Armature Esc shipped labels-only; destructive cancel stays gated** - `_sweep_empty_armature` already deletes only an auto-created rig, so Esc and Enter are identical on the data; the fix was a dynamic header label. A truly destructive Esc is gated on a live GUI repro.
- **Animation assign-action targets the Skeleton picker (warns + cancels when empty)** via `resolve_skeleton_target` - the "first armature in scene" heuristic was the bug.
- **Cross-panel convention: a panel acting on another's selection draws `draw_target_readout` ("Target: Skeleton \<name\>")** - Mesh Generation, Weight Paint, Animation show it; the owner panel (Skeleton) does not repeat it.

### Slots list UX

- **Multi-select shipped as an operator capability** (the Outliner select operator reads `event.shift` / `event.ctrl`), index sync in `core/outliner_view.py`. The reusable list wrapper was deferred to a genuine third consumer - then built once they materialized (see Blender UI polish below).
- **The attachment list is a custom-draw column over the derived `empty.children` with a `scale_y` cap, not a synced `CollectionProperty`** (`template_list` needs a real collection + a single `active_index`); the native-scroll upgrade is gated on an observed desync. The slot list itself (a real collection) did move to `template_list`.
- **The empty-slot signal is owned solely by the validator error** - the panel dropped the duplicate inline INFO line.

### Godot import verification

- **A Sprite2D region is enabled only when a texture resolves** - an enabled zero-area region draws nothing.
- **Colliding node names use Godot's numeric `add_child` suffix (`_001`), never a kind prefix** - animation tracks resolve targets by leaf name via `find_child`, so a prefix would churn the lookups.
- **Bone-attached slots cancel the bone's full cumulative rest, not the parent-local rest** - `get_skeleton_rest()` returns parent-local in this Godot version; cancelling the cumulative rest anchors absolute-baked attachments at the skeleton origin where authored.

### Blender UI polish

- **The deferred reusable list wrapper was built** once four-plus consumers cleared the trigger: a bpy-free `compute_list_filter` (search + visibility + sort to the flag/order pair) in `core/list_view.py`, plus a `ProscenioListMixin` and a `draw_select_marker` in `panels/_list.py`. The Outliner, Slots, Bones, Actions, the Weight-Paint per-bone overrides, and the element-driver list route through it. Default is source order (the bone list relies on hierarchy order); sorting lists pass a `sort_key`.
- **Bone multi-select reuses the Outliner's per-row-marker pattern** (a radio dot reading the live bone selection, not the single `template_list` active index), wired through the bone-select trio in `core/bpy_helpers/_shared/bone_select.py`. It is live only where bone selection is real (Pose / Edit); Object mode stays single-active.
- **The active-row highlight follows the viewport selection across every object/bone list** - the depsgraph sync drives the Slots index (the active slot) and the Skeleton bone index (the picked armature's active bone), not only the Outliner. The Animation actions list stays independent (its row is the picked armature's active action, not an object).
- **Help bodies are one paragraph string reflowed at draw time** (`reflow_paragraph` against a fixed character budget tuned to the popup width); explicit newlines mark list items, which keep a hanging indent. This retired the hand-wrapping. The budget is a constant because `layout.label` cannot wrap and a popup exposes no draw-time text metrics.
- **The provenance overlay is modal-only** - the standalone Snapshot-panel toggle registered no draw handler outside the Edit Weights modal (which forces the overlay on for its session and restores the prior value on exit), so it was removed rather than given a persistent handler.
- **The shared automesh trace params live on the parent Mesh Generation panel** (Interior Mode, contour vertices, interior spacing, the dense fields), because both Automesh from Alpha and the Interactive modal read them; the alpha-only knobs stay in the subpanel.
- **Named weight snapshots are an additive sidecar field** (`snapshots`, no version bump): unbounded manual save points plus a rolling last-3 auto history captured per Edit Weights session, each a labelled copy of the per-vert entries. Restore-by-name is topology-guarded like Reset to Last Saved Weights.

### Blender authoring design

- **A driven bone's rotation mode is validated on export, not enforced at authoring** - the export validator warns (warn-only, never blocks) when a bone driving a sprite is not in XYZ Euler, since Drive-from-Bone reads the rotation as XYZ and a Quaternion bone drives wrong silently. A **Convert rotation to Euler** operator (active bone or whole armature, in the Skeleton panel) is the one-click fix; Blender converts the stored rotation natively.
- **Manual depth is an authoring-only `depth_offset`, no schema field** - it is added (in PSD-layer units) to the PSD-order object Y before the writer negates it into `z_index`, so an artist reorders a plane without moving the object or re-importing. The writer still emits only `z_index`; the field mirrors + hydrates like the other per-object props.
- **Incorporate-as-Element adopts a hand-authored mesh, Auto-detecting the kind** - a button (Element panel, shown only for a mesh with no `proscenio_type` marker) plus an operator that picks Sprite for a single quad and Mesh otherwise. The choice is resolved in `execute` (an Auto enum default, Mesh / Sprite overrides in the redo panel), not `invoke`, so the heuristic runs on every entry point and is headless-testable. Mirrors the Create Slot button-plus-dialog shape; no schema impact.
- **The PSD `[origin]` is sprite-only** - a Polygon2D has no pivot, so a mesh origin only shifts the Blender object and cancels at export; the importer ignores (and warns about) an `[origin]` on a mesh layer, keeping mesh placement at the bbox centre. A sprite keeps it: the origin becomes the `Sprite2D.offset`, pinned now by a round-trip test that was code-read before.
- **The manual `centered` toggle is retired to a fixed internal constant** - the writer's offset math assumes `centered=true`, so a user flip only broke placement. The field stays (the raw-CP escape hatch + mirror) but leaves the Active Sprite UI.

### Re-import contract

- **Photoshop manifest re-import PRESERVES painted weights via the sidecar reproject** (two tiers: a same-bounds re-import keeps weights and density intact; a changed-bounds re-import reprojects the surviving object-level sidecar onto the rebuilt quad), the same mechanism automesh regen uses - distinct from re-rig, which still LOSES. The guide's loses-weights warning was stale and was rewritten with the weight-operation matrix. Revisit: a workflow that wants PSD re-import to discard weights on purpose.
- **The PSD importer reuses the existing root armature when present** (looked up by the manifest armature name), building a fresh one only when absent, so re-import no longer orphans the prior armature or strands a rig grown on it. Trivial today (single root bone); revisit when multi-bone import needs bone reconciliation.
- **The Godot non-destructive reimporter stub was deleted, not built** - dead, unreferenced code promising a diff/merge that fights Godot's `EditorImportPlugin` model; the wrapper-scene overwrite path (the locked call under Core architecture) is the documented contract. Revisit: same as the wrapper-scene call.

### IK authoring ergonomics

- **Non-deform bones never export** - a general `use_deform=False` filter in the skeleton and animation writers keeps `.IK` / `.pole` controls (and any hand-authored control) out of the Godot export, suffix-agnostic, matching the skinning filter already in the addon.
- **Toggle IK is a conditional Add / Remove IK Chain label** resolved in draw from the active bone's `Proscenio IK` constraint presence - influence lives on the keyframable slider, not a binary button.
- **IK chains surface as both a per-row marker and an IK chains section** (tip / chain length / control), driven by one live per-draw scan of `pose.bones` constraints - no stored chain state, so the panel cannot drift from the rig.
- **The exposed constraint set is the curated trio** (chain length, keyframable influence as the IK/FK-blend seed, pole target) plus an opt-in in-plane lock, never a full redraw of Blender's native constraint UI. The in-plane-lock prebend skips a non-Euler bone rather than forcing its `rotation_mode`.
- **Control bones join a "Proscenio Controls" collection with a theme color** on creation; the custom shape is deferred.

### Materials and pixel art

- **Pixel-art crispness is a per-element "Pixel art" toggle, default OFF; the importer is unchanged (stays `Linear`)** - the toggle sets the object's image-texture nodes to `Closest` when on and back to `Linear` when off. Pixel art is not assumed to be the majority case, so there is no global import default. The full materials inspection / config / repair panel stays dropped (it duplicates native Blender tools). The toggle is authoring-only UI state, never written to the schema.

### Quick Armature interaction redesign

- **A mode layer replaced the saturated chord scheme** - Tab cycles Draw (the prior click-drag authoring, byte-for-byte) and Reparent; the status bar swaps to the active mode's chords (the automesh-authoring precedent). Draw stays additive, so every prior Quick Armature promise holds.
- **Reparent is viewport pick-parent: the nearest bone tip within a screen-constant pixel radius** (Y=0 XZ projection + the shared nearest-index); a miss is a no-op with feedback, a hit sets the chain parent. The overlay highlight projects to the same Y=0 plane as the picker, and the Esc session-state label reads the session-authored records, not the chaining field the pick now also writes.
