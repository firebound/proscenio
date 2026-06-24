# Code-quality and information-architecture audit - June 2026

A read-only audit of the Proscenio monorepo against Single Responsibility, DRY, and a pragmatic reading of SOLID, plus an information-architecture pass on whether the code/package layout is comprehensible to a contributor arriving cold. The audit deliberately stops short of imposing full Clean Architecture; the findings target real, high-value smells where they hurt, not dogma.

Scope sampled: the full `apps/blender/` addon (35k LOC, the largest surface), `apps/photoshop/` (TypeScript UXP plugin), `apps/godot/` (GDScript importer), `packages/models` / `codegen` / `validator` / `fixtures`, and the repo top level. Every finding is grounded in a real path and line; uncertain or low-value observations were dropped in favor of a prioritized shortlist.

## Executive summary

The codebase is in good shape for a pre-1.0 solo project. The schema-as-source-of-truth spine (`packages/models` -> `proscenio_codegen` -> generated TypeScript and GDScript bindings) is genuinely well-built and is the single best structural decision in the repo. The pydantic models, the property layer, and the Godot builders are close to reference quality. The concentration of risk is narrow and predictable: a handful of Blender modal operators have grown into god files, and the "single source of truth" claim leaks at the edges where consumers hand-re-express enum literals and version constants that the codegen already owns.

Severity counts across the shortlist below:

- Must fix: 4 findings (3 cross-language source-of-truth leaks, 1 god-file cluster)
- Nice to have: 9 findings (panel duplication, planner SRP, IA gaps)
- Good patterns called out: 6

The five highest-leverage fixes:

1. Stop hand-re-expressing the `BlendMode` literal union and the `format_version` constant in the consumers; route them through the codegen so the source of truth actually holds (cross-language DRY).
2. Generate the Godot animation track-type dispatch from the schema, or at least share the literal list, so a new `Track.type` cannot be silently dropped by the importer.
3. Break up the two worst Blender god files (`automesh_authoring.py`, `quick_armature.py`) by extracting their modal state machines (pen state, view snapshot, selection snapshot) into small typed helpers, restoring testability.
4. Extract the shared panel empty-state and truncating-header boilerplate into the existing `panels/_helpers.py`, the one place the project already factors panel chrome correctly.
5. Add three short package READMEs (`packages/models`, `packages/codegen`, `packages/validator`) so a newcomer can discover package responsibility from the package itself, not by reading source.

The full report follows.

## Part A - Code quality

### Must fix

#### A1. The `BlendMode` enum is re-declared by hand in the Photoshop consumer

The PSD manifest model defines `BlendMode = Literal["normal", "multiply", "screen", "additive"]` at `packages/models/src/proscenio_models/psd_manifest.py:31`, and the codegen already emits a matching `BlendMode` type into the generated binding at `apps/photoshop/src/schema_bindings/psd_manifest.ts:26`. Despite that, `apps/photoshop/src/lib/manifest.ts:20` re-declares the same four-literal union by hand, and `apps/photoshop/src/lib/tag-parser.ts:170` re-types the identical list a third time as inline string comparisons (`lc !== "normal" && lc !== "multiply" && lc !== "screen" && lc !== "additive"`). The generated binding that would prevent this exists and is simply bypassed. Adding a fifth blend mode to the model regenerates the binding but leaves both hand copies stale; the parser would then reject a value the manifest accepts.

Why it hurts: this is the exact drift the source-of-truth architecture exists to prevent, and it is invisible until an artist hits a rejected blend mode. Suggested direction: have `manifest.ts` re-export `BlendMode` from `../schema_bindings/psd_manifest` (the same re-export pattern the file already uses correctly for `MeshLayer` / `SpriteLayer` / `FrameEntry` at lines 10-23) and route the `tag-parser.ts` guard through a generated membership check rather than inline literals.

#### A2. `format_version` is hardcoded independently in three places

The two schema roots pin their versions in the models (`packages/models/src/proscenio_models/proscenio.py:352` `format_version: Literal[1]` and `packages/models/src/proscenio_models/psd_manifest.py:158` `format_version: Literal[1]`). Each consumer then restates the constant by hand: `apps/godot/addons/proscenio/importer.gd:10` `const SUPPORTED_FORMAT_VERSION := 1` and `apps/photoshop/src/lib/manifest.ts:17` `MANIFEST_FORMAT_VERSION = 1`. There is no shared reference; a schema bump is three coordinated manual edits with nothing to fail when one is missed.

Nuance worth keeping in the fix: these are two distinct per-schema integers (the `.proscenio` document and the PSD manifest each carry their own), so the right shape is two generated constants, not one. The codegen already walks the models and knows both literal values. Suggested direction: emit `format_version` constants as a small generated artifact per consumer (a `proscenio_versions.ts` and a `.gd` const), the same way the type bindings are emitted, so the importer guard and the planner read a generated number.

#### A3. The Godot animation track-type dispatch re-expresses the schema enum

`Track.type` is `Literal["bone_transform", "sprite_frame", "slot_attachment"]` at `packages/models/src/proscenio_models/proscenio.py:322`. The importer hand-writes a `match track_type:` over the same three literals at `apps/godot/addons/proscenio/builders/animation_builder.gd:51-60`, with a `_:` arm that only `push_warning`s. The per-key channel names (`position`, `rotation`, `scale`, `frame`, `attachment`) from `Key` (`proscenio.py:311-318`) are similarly restated as inline strings inside the track builders. Adding a track type to the model produces no GDScript error - the new type silently routes to the warning arm and the channel is dropped at import.

Why it hurts: unlike A1/A2 this can corrupt output rather than reject input, and the failure mode (a missing animation channel) is hard to trace back to a stale match. Suggested direction: extend the codegen to emit the track-type and key-channel literal lists as generated GDScript constants, and dispatch off those; even without generated stubs, a single generated `const TRACK_TYPES` shared with a test asserting exhaustiveness closes the silent-drop hole.

#### A4. Two Blender modal operators have become god files

`apps/blender/operators/automesh/automesh_authoring.py` (1335 lines) is a single operator class (`PROSCENIO_OT_automesh_authoring`, roughly lines 170-1282) carrying 20-plus mutable class variables and 50-plus methods that mix the modal lifecycle, a five-stage pipeline, a toggle-pen gesture state machine, stroke persistence per stage, overlay refresh, tooltip rendering, and session snapshot/restore. The parallel stroke lists (`_user_strokes` vs `_user_outer_strokes`) drive duplicated snap/delete/undo handling per stage, and `_advance` (around lines 987-1047) branches across all five stages while also doing error handling and user reporting.

`apps/blender/operators/armature/quick_armature.py` (1100 lines) has the same shape: one operator class (about lines 96-973) owning a view-snapshot state machine spread across seven class variables (`_restore_view_*`, `_post_snap_view_*`, snapshot at ~795, restore at ~832), a separate selection snapshot, six single-call event-predicate functions (~993-1033), and handler registration that is duplicated between `_unregister_handlers` (~912) and `_sweep_orphan_handlers` (~1065) to catch script-reload leaks.

Why it hurts: the business logic (bone creation, mesh authoring, coordinate transforms) is reachable only through the modal harness, so almost none of it is unit-testable without a live Blender event loop, and a single misnamed class var silently breaks a modal across invokes. Suggested direction: extract the state machines into small frozen dataclasses that the operator owns - a `_ViewSnapshot`, a `_SelectionSnapshot`, a `_PenState` - and a `_HandlerRegistry` context manager for the draw-handler lifecycle. Replace the per-stage `if`-ladders in `_advance` and in `bridge.build_automesh` (`apps/blender/core/bpy_helpers/automesh/bridge.py:744-902`, a 160-line stage-branching orchestrator) with a stage-keyed dispatch table. This is a refactor for testability, not a rewrite; the dataclasses are extractable incrementally.

### Nice to have

#### A5. Coordinate-transform helpers are fragmented in the authoring pipeline

`apps/blender/core/bpy_helpers/automesh/authoring_pipeline.py:500-549` defines five overlapping transform functions (`_world_to_local_xz`, `_world_steiners_to_local`, `_to_world_xz`, `_to_local_xz`) differing only by scalar-vs-list and forward-vs-inverse, with inconsistent error handling (some return `None`, some raise). A caller must know which to pick. Suggested direction: one `_CoordinateMapper` built from `matrix_world` exposing `to_world` / `to_local` / list variants.

#### A6. `_strokes_to_cdt_inputs` packs three stroke kinds into one function

`authoring_pipeline.py:732-824` is a 93-line function branching across point, cut, and fold strokes with nested index allocation and edge building; no single path is testable in isolation. The sibling `read_user_strokes` path also silently drops malformed items with no count surfaced to the user. Suggested direction: extract `_emit_point_stroke` / `_emit_cut_stroke` / `_emit_fold_stroke` and return a `(strokes, dropped_count)` result from the reader so corruption is reported, not swallowed.

#### A7. Panel empty-state and header boilerplate is copy-pasted across panel files

The same "select a mesh element" info-box guard appears at `apps/blender/panels/weight_paint.py:55`, `apps/blender/panels/mesh_generation.py:50`, and `apps/blender/panels/element.py:73`; the header-truncation logic is duplicated near-verbatim between `apps/blender/panels/skeleton.py:173-186` and `apps/blender/panels/element.py:56-64` (both with a 220px threshold). The project already has the right home for this: `panels/_helpers.py` correctly factors status badges, help buttons, and `draw_subpanel_header`. Suggested direction: add `draw_mesh_element_guard(layout)` and `draw_truncating_header(layout, full, short, min_width)` to `_helpers.py` and call them from the panels. Low risk, high consistency payoff.

#### A8. `help_topics.py` keeps two parallel dictionaries that must stay in sync

`apps/blender/core/help_topics.py` holds the `HELP_TOPICS` registry (roughly lines 124-589) and a separate `_DOC_PATHS` mirror (roughly 606-654). Adding a topic is two edits; missing the second silently breaks a doc link (a test catches drift, but only after the fact). Suggested direction: embed the doc path on the `HelpTopic` dataclass itself and let `_DOC_PATHS` become a derived view used only by the test. The text-reflow utility and the hardcoded popup pixel metrics (lines 38-51) also belong in a small tested layout helper rather than a config module.

#### A9. `planner.ts` is a controlled god file

`apps/photoshop/src/lib/planner.ts` (833 lines) builds the manifest, walks the PSD layer tree, computes bounds, collects warnings, and plans PNG writes in a single pass. It is well-factored internally, so this is a clarity issue rather than a correctness one. Two concrete sub-issues: `buildPolygonEntry` (~656) and `buildSpriteFromLayer` (~704) duplicate the same folder/blend/safeName/folderPrefix derivation, and `walkLayer` (~347-399) dispatches six concerns (ignore, hidden, kind, origin marker, merge, sprite) in one body. Suggested direction: extract a `buildEntryMetadata(source, inherited, settings)` helper for the shared derivation, and split manifest construction from write planning so the manifest is a reusable intermediate value.

#### A10. Validation thresholds are scattered module constants

`apps/blender/core/validation/export.py` defines tuning constants locally (`_PLANE_TOLERANCE = 0.1` at line 30, `_UV_SHEET_TOLERANCE = 0.02` at line 35, `_IK_TRANSFORM_PROPS` at 37-40). The validator orchestration itself is clean and delegates correctly; the only smell is that a global tolerance tweak means editing source. Minor: move to an addon-preferences block if these become user-tunable, otherwise leave with a docstring note.

#### A11. Region and UV normalization is an unenforced cross-component contract

The `[0,1]`-normalized convention for `texture_region` and `uv` is documented in the model (`packages/models/src/proscenio_models/proscenio.py:44-50`) but not enforced by a pydantic validator, while the Godot side multiplies by texture size at `apps/godot/addons/proscenio/builders/sprite_builder.gd:66-72` and `builders/mesh_builder.gd:103-105`. A writer that emitted pixel-space by mistake would double-scale silently. The model docstring already flags that the schema range constraint is deferred pending the goldens retirement, so this is a known gap, not an oversight; recording it here keeps it visible. Suggested direction: add the `0 <= v <= 1` validator once the pixel-space test fixtures are retired.

### Good patterns worth preserving

- The pydantic models (`packages/models/src/proscenio_models/proscenio.py`) are exemplary: a `_Strict` base mirroring `additionalProperties: false`, cross-field invariants that JSON Schema cannot express carried as `model_validator`s (polygon/uv length match at line 148, frame-within-grid at 253), and a callable discriminator (line 271) that handles the optional-`type`-defaults-to-mesh case cleanly. The docstrings explain the encoding choices rather than the obvious.
- The codegen (`packages/codegen/src/proscenio_codegen/godot_emit.py`) is a clean single-purpose AST-style emitter: a `_ResolvedType` dataclass carries the type mapping plus parse snippet, `_resource_class_name` prefixes every class to avoid shadowing Godot built-ins, and it defers blank-line formatting to `gdformat` rather than reproducing it by hand.
- The `core/` vs `core/bpy_helpers/` split is a deliberate, documented testability boundary (bpy-free direct children, bpy-bound under `bpy_helpers/`, stated in both `__init__` docstrings) - the reason pytest can exercise the domain logic at all.
- The property layer (`apps/blender/properties/scene_props.py`, `object_props.py`) is reference-quality: enum item tuples co-located with their consumers, atomic update callbacks, descriptions doubling as help text.
- The Godot builders (`animation_builder.gd`, `mesh_builder.gd`, `sprite_builder.gd`, `slot_builder.gd`) each hold one concern with a clean filter-then-dispatch shape; aside from the A3 enum-dispatch leak they are tight.
- The Godot writer modules (`exporters/godot/writer/`) avoid the duplication trap: `_wrap_frame` / `_grid_max_frame` in `sprite_frame_animations.py:148-168` are defined once and reused across baked and keyframed paths, and the driver evaluator strips `__builtins__` (good security posture).

## Part B - Folder organization and information architecture

### Top-level layout

The top-level split (`apps/`, `packages/`, `docs/`, `specs/`, `.ai/`, `tools/`, `scripts/`) is self-explanatory and well-documented. `AGENTS.md` and `.ai/conventions/layout.md` give precise, defensible rules for each bucket - notably the `scripts/` (true one-off, no own deps) versus `tools/` (own deps/build/tests, e.g. `tools/qa-companion/`) versus `packages/` (shared, consumed by apps) distinction, which is the kind of boundary that usually rots and here is written down. The four-way `apps/` layout (three pipeline plugins plus the docs site) is clear from the README component table and AGENTS.md. A newcomer reading the README, then AGENTS.md, then `.ai/conventions/layout.md` lands oriented. This is above the bar for a project this size.

### Where a newcomer still gets lost

#### B1. Missing package READMEs (nice to have, high payoff)

Only `packages/fixtures/` carries a README. `packages/models`, `packages/codegen`, and `packages/validator` have none, so the responsibility of the three most architecturally central packages is discoverable only by reading source or the architecture doc. The README component table names `packages/models` but not `codegen` or `validator` at all. Suggested direction: a three-paragraph README in each (`models` = source of truth and how to bump a schema; `codegen` = what it emits and the regen command; `validator` = what it checks and how it relates to the per-app validation). This is the single highest-leverage onboarding fix.

#### B2. The mirrored `core/` and `core/bpy_helpers/` subtrees cost a lookup

`apps/blender/core/` and `apps/blender/core/bpy_helpers/` both contain subpackages of the same names (`armature`, `atlas`, `automesh`, `psd`, `skinning`, `slot`, `spritesheet`, `_shared`). The split is principled and documented (bpy-free vs bpy-bound), so this is not disorder - but a newcomer hunting "the automesh code" finds two `automesh/` directories and must read an `__init__` docstring to learn which holds what. The docstrings do explain it well. Suggested direction: leave the structure (it earns its keep for testability) but consider a one-line `# bpy-free` / `# bpy-bound` marker convention or a short note in the addon README so the duplication reads as intentional at a glance rather than as an accident.

#### B3. `examples/authored/` vs `examples/generated/` and the fixtures relationship

`examples/` carries `authored/` (hand-built source like `doll`, `firebound_guy`) and `generated/` (pipeline output like `simple_psd`, `slot_cycle`), and `packages/fixtures/` builds yet another set of `.blend` fixtures consumed by tests; `scripts/godot/sync_fixtures.py` syncs `examples/generated/*/godot/` into `apps/godot/examples/`. The relationship among these three example/fixture homes is real and correct but is the most likely place for a newcomer to get confused about which directory is canonical and which is derived. The `packages/fixtures/README.md` helps; an `examples/README.md` stating the authored-vs-generated split and pointing at the sync script would close the gap.

### Naming and nesting

Naming is consistent and the conventions file (`.ai/conventions/layout.md`) codifies it per language (`snake_case.py`, `CATEGORY_OT_*` / `CATEGORY_PT_*` for Blender classes, `kebab-case.ts`, `PascalCase.tsx`). Nesting depth in the Blender addon is the deepest in the repo (`apps/blender/core/bpy_helpers/automesh/...` is five levels), which is a consequence of the feature-package plus bpy-split organization rather than gratuitous; it stays navigable because the names are predictable. No orphaned or accidentally duplicated locations were found beyond the intentional `core/` mirroring in B2 and the multiple example homes in B3.

### On the planned docs restructure

The concurrent docs effort (area index pages, the three tool docs moving under `docs/02-tools/`, a getting-started area) is already partly visible in the tree (`docs/00-guides/00-getting-started/`, `docs/01-project/index.md`). It clearly helps newcomers: an audience-sliced navbar (Guides / Project / Tools) with a getting-started landing is exactly the altitude a cold contributor needs, and `.ai/conventions/docs.md` already specifies where each kind of knowledge belongs. That effort addresses the user-facing documentation IA. It does not touch the two code-side gaps above (B1 package READMEs, B3 examples README), which remain worth doing independently because a contributor reading the repo on GitHub - not the docs site - is the audience for in-repo READMEs.

## Closing note

Nothing here threatens the architecture; the spine is sound and the worst offenders are localized to two modal operators and a thin band of enum/constant leakage. Fixing A1-A3 hardens the property the whole design rests on (the schema as the only shared contract), and fixing A4 restores testability to the largest untested surface. The IA is already good for the size of the project; the package READMEs in B1 are the cheapest meaningful improvement.
