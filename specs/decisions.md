# Decisions

Locked architectural and per-feature calls. ADR-light: the call, the rationale, and the revisit trigger. Open work lives in the per-domain backlogs indexed from [`backlog`](backlog/index.md); this is the consolidated home for settled calls - the hand-written planning docs were retired once each feature shipped, so the rationale worth keeping was mirrored back here. One clause per rationale; impl detail stays in the code it cites.

## Core architecture

| Decision | Rationale | Revisit trigger |
| --- | --- | --- |
| **No GDExtension / native runtime** | GDScript-only plugin; generated `.scn` is native nodes, runs on plain Godot 4 with the plugin uninstalled. | Deep Firebound integration, `Polygon2D` skinning perf ceiling, Blender <-> Godot live-link, binary `.proscenio`, in-Godot round-trip. |
| **Conversion one-time, at editor import** | Heavy work at import; runtime is Godot core (C++), no GDScript perf ceiling. | Same as GDExtension. |
| **Strong typing everywhere** | GDScript `untyped_declaration=2`, Python `mypy --strict`, TS `strict`. | Baseline rule. |
| **Schemas are the contract (pre-launch: no bump)** | Pre-launch shape changes happen in place at the current `format_version`, no migration code, proven by regenerating fixtures + goldens; the number freezes at first public release. CI validates fixtures every stage. | First public release flips to bump-plus-migration for every later cross-component shape change. |
| **Storage split: one home per field, by read boundary** | Each per-Object field has one storage home (spec 037, shipped). Export/headless-read and animatable / driver-target fields are Custom-Property-canonical: they store in the `proscenio_*` idprop the writer reads, and the panel edits them through a `get`/`set` PropertyGroup proxy over that idprop (Blender cannot keyframe / reliably drive a PG-nested field, and the idprop resolves with no addon registered). Pure-GUI fields (pixel art, atlas flags, the driver picker, outliner favorite) are PropertyGroup-canonical - no idprop. The uniform mirror, the hydrate, and the save-pre flush are gone; no migrator ships (pre-release, no `.blend` in the wild - fixtures regenerate). Drive-from-Bone drivers target `["proscenio_<key>"]`. | Refines the earlier "editor-only is PG-canonical" wording: export-read wins because it keeps the headless writer registration-free. |
| **Addon preferences user-global, no per-project** | The scene PropertyGroup already carries per-`.blend` state. | A real need for per-project preference values. |
| **Wrapper-scene reimport, full overwrite** | Importer overwrites `.scn`; the user wrapper `.tscn` survives with scripts / extras. Marker-based merge would lose scripts on a bone rename (no stable IDs) and double the code paths. | Concrete pain the wrapper pattern cannot serve. |
| **One component per PR** | PS / Blender / Godot ship independent PRs; schema bumps cross all by definition. | None. |
| **Lockstep product versioning** | Three apps are one coupled pipeline (the addon emits a `format_version` the importer reads), so one SemVer `vX.Y.Z` bumped by the highest severity; unchanged apps re-stamp and ride along. Per-app detail in the CHANGELOG; `format_version` stays independent. Detail in [`.ai/conventions/layout.md`](../.ai/conventions/layout.md). | A component gains an independent consumer or release cadence. |
| **C# / GDExtension = documented escape hatch** | Maintainer prefers typing but stays in GDScript for 2D-community reach; Firebound itself stays C#. | Same as GDExtension. |
| **`apps/` + `packages/` + `scripts/` + `tools/` split** | apps ship; packages are shared building blocks; scripts are dependency-free one-offs; tools are standalone packages (own deps / build / tests), not shipped. Own manifest / build means tools or packages, never scripts. Detail in [`.ai/conventions/layout.md`](../.ai/conventions/layout.md). | A third standalone pnpm package warrants a root pnpm workspace alongside uv. |
| **Manual-test surface owned by QA Companion** | The walkable `checklist/` is living data round-tripped by the tool in `tools/qa-companion/`; the seeding `findings.md` audit was triaged + retired 2026-06-15 (code issues to bug backlogs, doc gaps to `backlog-docs.md`, rest dropped). | The checklist block format changes shape, or the tool is replaced. |
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

> **SUPERSEDED by spec 069 (Skeleton Rig UI and bone display, 2026-06-27).** The Tab Draw/Reparent mode layer and the viewport tail-tip pick-parent were both removed. Quick Armature now runs as an Edit-mode session where reparent is native bone selection (right-click selects a bone, the next connected draw chains from it). The spec 068 seed-from-active-bone survives. See the "Skeleton Rig UI and bone display" section below.

- **A mode layer replaced the saturated chord scheme** - Tab cycles Draw (the prior click-drag authoring, byte-for-byte) and Reparent; the status bar swaps to the active mode's chords (the automesh-authoring precedent). Draw stays additive, so every prior Quick Armature promise holds.
- **Reparent is viewport pick-parent: the nearest bone tip within a screen-constant pixel radius** (Y=0 XZ projection + the shared nearest-index); a miss is a no-op with feedback, a hit sets the chain parent. The overlay highlight projects to the same Y=0 plane as the picker, and the Esc session-state label reads the session-authored records, not the chaining field the pick now also writes.

### Help copy and docs alignment

- **The help popup width is derived from the wrap budget** (`POPUP_WIDTH = POPUP_WRAP_CHARS * _POPUP_PX_PER_CHAR + margin`), so the drawn width is the wrapped-text extent by construction and the empty-band defect cannot return; the wrap budget is the lone readability knob.
- **Two-tier help copy, tested**: a panel `?` is one shallow what-and-why paragraph (`sections=()`); a subpanel `?` is one focused summary plus at most one section scoped to its own controls, never re-explaining the parent; worked depth lives on the doc page. A shape test enforces the tiers.
- **The docs mirror the Blender panel tree exactly** (user-locked): every top-level panel is one page, every subpanel one H2 section under it, the About footer is the index; a topic that is neither anchors inside its host section. 09-validation.md folded into `pipeline#validate` (client redirect from the old slug), and a two-way coverage test holds `_DOC_PATHS` to the mirror in both directions.
- **Help strings are translation-stable, not translated**: each body is one whole-string msgid routed through `core/i18n.py` `iface()` under a per-topic context (shared labels under the default context); `TRANSLATIONS` stays empty (zero visible change), unblocking the gated `i18n-locale-tables` item without a second copy pass.
- **Row-button / helper topics anchor inside their host section** (`pose_library` -> `skeleton#save-pose-to-library`, `sprite_frame_preview` -> `element#material-preview`), never a sibling H2 - the mirror reserves H2s for subpanels.

### Multilanguage i18n (spec 072)

- **English is the canonical msgid on both surfaces; a locale is append-only** - the Blender addon and the Docusaurus docs register pt-BR as the first non-English locale with English preserved as the source. Adding a language is a new `core/i18n_locales/<locale>.py` module (Blender) plus an `i18n/<locale>/` tree (docs) plus a content pass, not a mechanism change. Locale codes differ by tool: Blender `pt_BR`, Docusaurus `pt-BR`.
- **The Blender per-locale tables are a bpy-free package folded by a thin assembler** - `core/i18n_locales/` holds one `LOCALE` + `ROWS` module per language; `core/bpy_helpers/i18n.py` folds them into the `{locale: {(ctxt, msgid): msgstr}}` mapping and hands it to `bpy.app.translations.register`. Operators translate under the `"Operator"` msgctxt, everything else under `"*"` (confirmed against `bl_rna.translation_context`).
- **The catalog is extracted + reverse-coverage-guarded, never hand-maintained** - `scripts/blender/extract_i18n.py` (AST, bpy-free) collects the translatable msgids; a test re-extracts on every run and fails on a new untranslated string or a stale row, so the table cannot drift from the source.
- **Layout `text=` overrides are cataloged, not wrapped in `iface()`** - Blender auto-translates `label`/`prop`/`operator`/`menu` `text=` from the registered table (the `translate=True` default), so a string literal there is a catalog entry - the idiomatic model, no call-site change. `iface()` is reserved for report messages (via a `set_translator`-injected translator that keeps `core/_shared/report.py` bpy-free, prefix outside the translated text) and f-string templates; interpolated f-string messages stay English and are deferred.
- **Docs exclude the auto-generated schema reference; copy is a native-reviewed first pass** - the 31 hand-authored pages are translated, `docs/content/**` (codegen schema reference) stays English behind Docusaurus's per-page fallback (a locale-aware codegen pass is gated on real demand). The translation copy is machine-assisted, reviewed by the team.

### Y Location draw-order authoring

- **One field replaces the two depth mechanisms**: `Y Location (Draw Order)` (`y_draw_order`) supersedes the old `depth_offset` float and the importer's separate `z_order` Y-stamp, retiring both hardcoded `0.001` constants. The label names what it is in both worlds - the Blender Y location, authored as the integer draw order that becomes the Godot `z_index`.
- **The stored integer is the source of truth, not a computed view of Y** (user-weighed): `y_draw_order` is a stored `IntProperty`; its update callback writes `Y = order * spacing` and the writer negates the integer into `z_index` (never dividing Y). So the export is independent of the spacing preference - changing the spacing only re-spreads planes in the viewport and can never shift the exported order, and a stray viewport drag cannot silently reorder. Chosen over a Y-mirroring proxy for exactly that robustness.
- **Spacing is one addon preference, defaulted to the Blender clip_start** (`y_location_spacing`, default `0.01`): it matches Blender's default 3D-view `clip_start` so the layer gap clears the perspective depth buffer at the usual camera distance (0.001 is marginal there); the gap is invisible in the front-ortho deliverable view. The canonical default lives once as `DEFAULT_Y_LOCATION_SPACING` in the bpy-free core so the preference and the validation default never drift.
- **Re-import resyncs the order where it already repositions**: import seeds `y_draw_order` from the PSD layer order; a re-import re-applies it to non-slot meshes (whose placement it re-applies anyway) and leaves slot-attached meshes alone (the slot owns them).
- **Viewport-legibility tools live in the Helpers panel**: the 3D-view `clip_start` / `clip_end` (native space properties) and a `Re-space Planes` operator (rewrites every element's `Y = order * spacing`, applying a changed preference and snapping a dragged plane back).
- **The Outliner exposes the order inline** on plane rows (mesh / attachment), editing each row's own object via `id_data`; the field is dropped below a narrow-panel width where its (possibly negative) number would clip, staying editable full-width in the Element panel.
- **A manual Y drag is flagged, not honored**: validation warns when `round(Y / spacing) != y_draw_order` (warning severity - the export reads the integer regardless); the spacing is injected so the validation core stays bpy-free.

### Element individual reimport

- **A per-Element reimport scopes the spec 055 contract to one manifest entry** - a `Re-import from PSD` button in the Element panel (`reimport_element`) re-stamps only the active element, reusing the import's existing root armature and inheriting `planes._ensure_mesh` (same-bounds keeps the mesh + painted weights + automesh density, changed-bounds reprojects from the surviving sidecar). Every sibling element is untouched, and the whole-figure feet-anchor (`_anchor_meshes_at_feet`) is deliberately skipped so the one element does not shift relative to its siblings.
- **The element resolves to its manifest layer by the stamped origin, name-keyed** - `reimport_element` reads `proscenio_import_origin` (`psd:<layer>`, prefix stripped) and looks it up in the manifest, falling back to the object name. Robust to a Blender-side object rename (the stamp survives); a PSD-side layer rename misses and degrades to a warn-and-no-op that leaves the element intact (the spec 053 posture). Stable-id resolution stays the later hardening behind the gated `stable-layer-identity`.
- **The source manifest path is remembered per object** - a new `PROSCENIO_IMPORT_MANIFEST` Custom Property stamped on every imported object lets the reimport run with one click; the operator falls back to the file picker only when the idprop is absent or the file is gone. Per-object rather than scene-level so two manifests imported into one scene each resolve their own source.

### Quick Armature root bone

- **The Quick Armature chain seeds from the active bone, with zero new chords** - `invoke` seeds the chain parent (`_last_bone_name`) from the resolved target armature's active bone when present, so selecting the importer root, launching, and drawing a connected bone chains the first bone onto it. Additive: with no active bone the first bone is unparented exactly as before, and `_create_bone` already guards a seed absent from the target's edit bones, so a stale active bone degrades to unparented. Chosen over a new press-mode chord (spec 066 is concurrently fighting chord saturation in the sibling automesh modal) and over reinterpreting an existing modifier; it composes with spec 058's Reparent for mid-session retargeting. Revisit: if a per-launch override (seed off) is ever wanted.
- **The importer root bone defaults to 1 unit, configurable per import** - `ROOT_BONE_LENGTH` bumped 0.05 -> 1.0 (the old length was an awkward Reparent pick target); a `root_bone_length` `FloatProperty` on the import operator threads through `import_manifest` into `build_root_armature(length=...)` exactly like `root_bone_name`, min-clamped to a small positive epsilon. Because `build_root_armature` reuses an existing root in place (spec 055), the length only sizes a freshly built root and never retro-resizes an imported rig - correct, not a bug. The root bone is non-deform, so the size change never reaches the Godot export (goldens unchanged). Preferences-level config rejected as heavier than the need.

### Skeleton Rig UI and bone display

- **The bone-list row is split by interactivity** - the left is a non-interactive connectivity icon (linked / unlinked / root), replacing the redundant bone-type icon every row carried; the right is an interactive cluster of flat (borderless) toggles: a relative-parent pin that swaps filled / hollow by state (an embossed variant and an orientation-icon pair were tried and rejected), the Godot export toggle, and the favorite star. Per-flag hover tooltips were dropped with the no-op info operator (connectivity reads from the left icon).
- **The bone list sorts hierarchy or flat-alpha** off a bpy-free `bone_view` (`bone_sort_key`, mirroring `outliner_view`); the depth indent is visible in hierarchy order and zeroes under A-Z. A per-bone favorite + a favorites-only header toggle reuse the shared list filter.
- **Rig UI is a recursive collection tree, with one color control per top-level subtree** - the panel flattens the bone-collection tree depth-first (a header row plus a grouped child-button row at every depth, not just two levels) via the bpy-free `rig_ui_view.rig_ui_rows`. The color picker is live only on top-level rows and re-tints the whole subtree (`iter_collection_bones` / `color_bone_collection` resolve bones recursively via `bones_recursive`); a brief direct-only-color attempt still read as "propagating" because a bone shared across nested collections re-coloured, so a single deliberate color point at the top is the model. The per-row eye / select buttons / theme selector are built from identical widgets on every row so the columns align (`ui_units_x` is a minimum, not a cap - a themed socket dot was wider than a no-theme spacer, which was the real "huge gap"). An empty rig shows an INFO notice rather than the panel vanishing (the IK-chains / Pose empty-state convention).
- **Custom bone-shape widgets were DROPPED for the native display_type dropdown** - a flat 2D `custom_shape` is anchored in bone-local space, so it only orients correctly when every bone's roll agrees, which a real 2D rig's do not (it looked right only on the bone pointing right). The `bone_widgets` module, the `assign_bone_shape` operator, and the Bone Display subpanel were removed; the native `display_type` dropdown covers the need.
- **Per-bone export exclusion gates the Godot skeleton** - `bone_is_exported(bone)` = `use_deform AND NOT proscenio.exclude_from_export` (bpy-free, `getattr`-defaulted); the skeleton + animation writers skip an excluded bone and reparent its deform children to the nearest exported ancestor. The panel toggle reads the combined gate (an export / cancel icon, depressed when excluded - render/visibility icons avoided since this is the Godot export, not the viewport). The toggle refuses a non-deform bone (already out of the export, so storing the flag would be hidden state the icon does not reflect and a trap if the bone later becomes deform). A Drive-from-Bone driver does NOT auto-exclude its source bone (CodeRabbit-driven): a source can be a real deform bone (an eye sprite driven by the deforming head bone), and auto-excluding would silently corrupt the skeleton - a non-deform helper is already dropped by the gate, a deform helper is excluded explicitly.
- **Quick Armature runs as an Edit-mode session with reparent by native selection** - `invoke` enters Edit once on the target and authors on `edit_bones` directly (no per-bone Edit/Object round trip), restoring the entry mode on exit. Reparent is Blender's own bone selection: right-click selects a bone and the next connected draw chains from it; nothing selected continues from the last-authored bone. This removed spec 058's Tab Draw/Reparent mode and the entire tail-tip pick subsystem (the spec 068 seed-from-active-bone survives). The launch button swaps to Exit Quick Armature while running (a re-invoke finishes the session rather than starting a second one), and the live gesture cheat-sheet is mirrored in a collapsible panel section.
- **The shared chord cheat-sheet spacing was fixed and the pattern codified** - each label gets a leading space and the row forces `row.alignment = "LEFT"` (the default EXPAND split the row width equally between labels, pushing a combo's meaning to the panel's right edge - the "huge gap"; neither `align=True` nor `align=False` fixes it). The reusable interactive-tool gesture-cheat-sheet pattern (chord spacing + the collapsible panel mirror gated on the modal's `_statusbar_appended`) is documented in `.ai/conventions/code.md`; applying it to the Automesh and Edit Weights panels is the remaining cross-tool follow-up.

### Mesh generation interaction

- **The manual contour reuses the existing click-pen machine, in the existing OUTER stage** - the contour is not a new authoring surface or a new stage: it is a tool on the same click-by-click polyline machine the interior extend/cut/fold strokes already run on (close-on-first-vert, live preview, subdivision baking, X/Z lock, Ctrl+Z vert undo). Its closed loop commits to `self._output.outer` (replacing the alpha-traced contour); every downstream stage triangulates it unchanged, so the SIMPLE/DENSE order and the cut/fold marking are identical. The auto-trace stays the OUTER stage default and recomputes on switch-back, so Auto<->Contour is reversible.
- **Bare Tab cycles the active tool of the current stage; LMB always acts with the active tool** - this deleted the Shift/Ctrl tap-toggle and its `_mod_tap_kind` / `_on_modifier_tap` / tap-vs-Ctrl+Z disambiguation (the root of the saturation) and collapsed the NEUTRAL/DRAW split. Per-stage cycles: OUTER = Auto-trace | Manual contour; edit-outline = Extend | Cut; edit-interior = Point | Fold | Cut. The fixed constraints survive as distinct gestures (Ctrl+Z undo, X/Z lock, 0-9 / wheel subdivisions, RMB/Enter finish, Esc cancel, Alt+click delete). Scoped to bare Tab so Blender's Ctrl+Tab (mode pie) and Shift+Tab (snap) are untouched - the modal intercepts and consumes it, the precedent spec 058's Quick Armature borrowed. Dedicated keys and a pie menu were the rejected alternatives. The pure cycle vocabulary lives bpy-free in `core/skinning/authoring_stages.py` (`stage_tools` / `next_tool` / `default_tool` / `tool_is_pen`).
- **Scope boundary (open follow-on)**: the contour pen edits the OUTER contour of an existing mesh element and ends at APPLY (a one-shot session). A from-blank pen-creation tool (first click drops the first vert, Illustrator-style) and persistent re-editing of an applied mesh are deliberately out of spec 066's scope - logged at the time as `mesh-pen-authoring` and since closed by spec 070: a standalone Manual Mesh modal now authors a contour from blank and re-opens an applied mesh for editing.

### Manual mesh authoring (spec 070)

- **The OUTER stage went auto-only; manual silhouette work became additive islands** - spec 066's "Manual contour" tool on the OUTER stage (and its live-triangulation / RMB-drag / DEL / ENTER coupling) was reverted. The interactive modal's edit-outline stage tools are now `add` / `knife` / `remove` / `delete`: KNIFE is the former Cut corridor renamed only, ADD is a closed-loop island rasterized into the alpha mask and re-traced (an overlapping island UNIONS into one merged contour; a fully-detached island is dropped + warned, self-enforcing "must overlap"), REMOVE is a closed-loop island routed into `holes_world`. The OUTER manual pen left the automesh modal because hand-authoring a whole contour belongs in its own surface (the Manual Mesh modal below), not bolted onto the auto-trace stage where it produced the "follows my drawing" spike.
- **Draw-with-vertices is a standalone Manual Mesh modal, not an automesh stage** - `PROSCENIO_OT_draw_mesh_vertices` runs its own modal loop, overlay registration, and status bar on its own panel ("Manual Mesh"), reusing only the PURE tech (the closed-loop `VertexPen`, `compute_triangulation_preview`, `apply_mesh` with a manual outer, the overlay draw funcs) - no automesh stage machine. The two modals are mutually exclusive: each entry's poll refuses while the other modal runs (one authoring modal at a time). The automesh interactive entry now carries an EXPERIMENTAL badge (`feature_status`), the Manual Mesh entry is BLENDER_ONLY.
- **The pen is two-phase: DRAW (open contour) then EDIT, close does not auto-apply** - placing points builds an open polyline; closing the loop opens an EDIT phase (move a vert with RMB-drag, insert a vert on a placed edge splitting it with both halves inheriting the edge subdiv, scroll over a hovered edge to set THAT edge's subdivisions, DEL/Ctrl+Z the last point); ENTER applies, Esc clears the in-progress line then exits. Per-edge subdivision counts are independent (the wheel changes only the edge being drawn), baked into the ring at apply.
- **Manual Mesh has its own SIMPLE/DENSE interior toggle** - a `manual_interior_mode` scene enum (default SIMPLE) independent of the automesh trace params; DENSE reveals the interior-spacing field and the modal `_params` reads the mode rather than hardcoding SIMPLE. Kept separate from the automesh shared params so the standalone tool is self-contained.
- **An applied manual mesh is re-editable via a stored source ring** - apply writes the contour to a `proscenio_manual_contour` Custom Property (`{points LOCAL, edge_subdivs}`) and interior strokes to `proscenio_user_strokes`; a fresh re-invoke on a manually-meshed element preloads the pen (points + per-edge subdivs) and strokes straight into the EDIT phase. The spec 071 revert clears the CP.
- **Interior detail is a Tab-cycled tool inside the EDIT phase** - Tab cycles OUTER / INTERIOR POINT / INTERIOR FOLD; INTERIOR FOLD has both a drag (free-draw) and a click (free edges / chain) sub-gesture, gated inside the contour by `point_in_polygon` (a gesture aiming outside turns the cursor warning red - the one allowed cursor-tooltip use, warnings only). The active tool shows in the status bar + the panel's collapsible Shortcuts mirror, never in a cursor tooltip.

### Mesh revert to plane (spec 071)

- **Revert rebuilds the quad from the import placement tag, not a stored snapshot** - `PROSCENIO_OT_revert_to_plane` (`proscenio.revert_to_plane`, REGISTER/UNDO) rebuilds the original textured plane from the `PROSCENIO_IMPORT_PLACEMENT` Custom Property (`_build_quad` with the recorded size + offset), so no extra snapshot data is carried. Restricted to PSD-imported mesh elements (the placement tag is the rebuild source); a no-placement / incorporated element degrades to a warn-and-no-op ("no original plane recorded"). The bounding-box rebuild for no-placement elements stays gated behind a real request.
- **Revert wipes the generated geometry + skinning + authoring strokes, keeps import identity** - it clears every deform vertex group, `proscenio_base_sprite`, the weight sidecar / bone-mode / envelope / mirror keys, the automesh authoring strokes (`PROSCENIO_USER_*`), and the manual contour CP (`proscenio_manual_contour`, spec 070), while keeping `PROSCENIO_IMPORT_PLACEMENT` / `_ORIGIN` / `_MANIFEST`, `element_type`, and the image material. It is distinct from a PSD re-import (spec 067, which re-runs automesh): the target here is the flat quad, not a re-generated mesh.
- **The button lives on the Element panel behind a destructive confirm** - shown only for a mesh element with a placement tag; clicking raises a confirmation dialog warning the generated mesh and weight paint will be destroyed (the operator has UNDO, so the dialog notes the image + placement are kept and Ctrl+Z undoes it). The operator REPORTs a cleared summary (N weights / vgroups / strokes) so the destructive scope is visible.
