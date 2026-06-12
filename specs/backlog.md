# Backlog

Items that are not in any active spec. Each entry promotes into a numbered spec under `specs/` when work begins. Order within a section is rough priority.

Forward-compatibility items gated on a future Blender release live in a dedicated [`backlog-blender-6.md`](backlog-blender-6.md). Cross-cutting type-safety and lint-enforcement gaps (strict gates configured but not run, trees exempted from type checking) live in [`backlog-code-quality.md`](backlog-code-quality.md).

The 2026-06-11 reconciliation of specs 027-035 emptied most of this file: resolved work was removed (locked calls recorded in [`decisions.md`](decisions.md)), and the not-now work moved to [`DEFERRED.md`](DEFERRED.md) (sequenced second-stage), [`GATED.md`](GATED.md) (held behind a written trigger), and [`DROPPED.md`](DROPPED.md) (value below cost, with rationale). What remains here is work owned by the not-yet-started specs (ui-help-surfaces, storage-split, reach) plus standing architecture notes.

## Blender addon

### Panel helper consolidation (cross-module dupes)

**What:** the spec 022 restructure split the sidebar into 13 panel modules, and small private context accessors recur across them. `_scene_skinning` + `_active_armature` were duplicated in `mesh_generation.py` and `weight_paint.py` (consolidated into `panels/_helpers.py` during the PR #96 review); similar one-liners still live module-local elsewhere (`_active_mesh_props`, `_explicit_target`, `_scene_props`, the per-module `_is_*` predicates). Sweep `panels/` for accessors that are genuinely identical across modules and lift them into `_helpers.py`; leave module-specific ones where they are.

**Why:** CodeRabbit flagged the `_scene_skinning` / `_active_armature` pair on PR #96. Duplicated accessors drift when one copy changes and the other does not, and `panels/_helpers.py` already exists as the home for cross-cutting panel helpers (header drawer, mode predicates, scene accessors).

**Trigger:** low priority - fold in when next touching the panel modules, or when a third copy of any accessor appears.

### Validator internal naming (sprites vs elements)

The element-vocabulary rename (the former spec 019) renamed the wire end-to-end and swept the Blender / Photoshop / Godot / fixtures internals, but `packages/validator` was outside its Phase 1-4 scope and never touched. It still uses the pre-rename internal names `report.sprites` + `SpritePayload` (`measurement.py:177`, `report.py:63`). Internal accumulator names, not the wire field, so nothing breaks. Rename to `report.elements` / `ElementPayload` (and the `test_validator_report.py` import) the next time the validator is touched. Low priority, cosmetic.

### Spec 021 follow-up: unfinished discovery

The spec 021 UI/UX audit is pruned. Its IA design fed specs 022 (restructure), 023 (help / docs / i18n), and 024 (preferences), and the sprite-rigid-bind + atlas findings were filed elsewhere in this backlog - that purpose is served. One thread outlived it:

- **Phase A / B discovery (never finished).** The reconciliation against `backlog-ui-feedback.md` was only partly run (~15 areas pending, much now overtaken by spec 022 shipping); the hands-on per-tool audit (GOOD / BAD / MISSING, needs the maintainer in a GUI Blender) never ran. Resume only if a fresh holistic UX pass is wanted.

(The per-asset-PPU bucket from this audit is now in [`GATED.md`](GATED.md); the bone-collections + hierarchy-editing bucket is in [`DROPPED.md`](DROPPED.md).)

### Spec 022 follow-up: in-editor smoke + guide-doc rename sweep

Spec 022 shipped and verified the 13-panel restructure (2026-06-09: panels renamed, `feature_status` bands updated, the stale `skinning` fallback gone, operator suite green at 50, addon registers headless). It also renamed the operator `proscenio.automesh_from_sprite` -> `automesh_from_alpha` and the Skinning panel -> Mesh Generation. Two deferrals outlive the spec:

- **In-editor visual smoke (workstation).** Headless cannot render panels. At a GUI Blender, confirm the sibling-panel tree (nothing nested under the version line), the accordion subpanels collapsing independently, the warn-not-hide hints, the per-header badge + `?`, and the `debug_mode` preference showing / hiding Diagnostics + the Debug Pipeline subpanel. A layout regression found here is a new bug.
- **Guide-doc rename sweep.** `docs/00-guides/00-basic/02-blender.md` and `docs/00-guides/01-advanced/02-blender.md` still say "Automesh from Sprite" / "Skinning panel"; `backlog-manual-testing.md` references the old names too (a historical log, lower priority). The same two guide pages also carry pre-Element-rename vocabulary - fold this into the spec 019 guide-doc residual for one holistic pass. Verified IA map (while shipping #100): the old "Skinning" panel split into "Mesh Generation" (Automesh from Alpha / Automesh Interactive / Debug Pipeline) and "Weight Paint" (Bind / Edit Weights / Snapshot / Sidecar IO / Weight Transfer); "Active Sprite" persists as a sibling of "Active Mesh" under an "Element" parent (NOT "Active Element"). The workflow prose needs rewriting against this, not find-replace.

**Trigger:** the visual smoke at the next workstation session; the docs sweep follows the review (or sooner - the renames are known).

### Spec 024 follow-up: docs-URL preference (D3) + overrides (D4 - none)

Spec 024 shipped the full preferences surface (2026-06-09: the `errors / info / debug` `log_level` enum gated once in `core/_shared/report`, the `debug` tier now backed by real per-item traces - importer planes, automesh counters, validation issues - so it is not inert; the `debug_mode` bool; all under a Developer box in `addon_prefs.py`). Two locked decisions defer the rest by design:

- **Docs-URL as a preference (D3).** The docs base is the constant `_DOCS_BASE` in `core/help_topics.py`. Promote it to a preference only if a real need surfaces (a self-hosted docs mirror, a version switch).
- **Per-project overrides (D4) - decided NONE.** The scene PropertyGroup already covers per-`.blend` state; preferences stay user-global. Recorded so it is not re-litigated.

**Trigger:** the docs-URL pref lands when a second docs target appears.

### Spec 023 follow-up: i18n tables, see-also URLs, docs depth

Spec 023 shipped and verified the help / docs / i18n layer (2026-06-09: per-subpanel help topics, the `doc_url` + "Open online docs" button, the Godot badge icon via `bpy.utils.previews`, the `bpy.app.translations` isolation mechanism in `core/i18n.py`, and the `docs/02-blender-addon/` reference section). Three deferrals outlive the spec, all by-design:

- **Per-locale translation tables (STUDY non-goal).** The mechanism is wired - English msgids are the source and `bpy.app.translations` auto-translates registered strings - but `TRANSLATIONS` is empty ("translate as we go"). Populate by appending `(locale, {(msgctxt, msgid): msgstr})` rows; no call-site changes.
- **Migrate inline see-also refs to online URLs.** The `specs/` / `examples/` see-also entries render as plain labels because they do not resolve in an installed (zipped) extension; the working clickable link is the per-topic `doc_url` / "Open online docs" button. Convert the local refs to online URLs once the matching pages exist.
- **Expand the addon reference pages.** `docs/02-blender-addon/` is a first cut (one brief page per panel mirroring the `?` help); add screenshots and deeper per-tool detail as the panels settle.

### Joystick / slider authoring

Multi-pose blend widget. The artist authors N corner poses (e.g. mouth shapes); a 2D widget interpolates between them as the artist drags a slider in the viewport. Pairs with Godot's `AnimationTree.BlendSpace2D` so the imported character can blend the same way at runtime. Requires a Blender PG carrying the pose set + corner coordinates, plus an exporter path that emits the blend space.

**Trigger:** the first character with parametric facial expressions (mouth phonemes, eye direction) lands.

### Onion-skin overlay

Viewport draw handler that renders the rest pose plus N keyframes around the current playhead in low-opacity outlines. Authoring shortcut for animators tweaking timing without scrubbing back and forth. Pure GPU overlay; no schema or export impact.

**Trigger:** an animator reports that scrubbing the timeline to compare poses is the slowest part of polishing an action.

### Split PropertyGroup vs Custom Property storage by intent (target: 1.0.0)

**What:** the current authoring-panel design mirrors every PropertyGroup field on `Object.proscenio` to a sibling raw Custom Property (`obj["proscenio_type"]`, `obj["proscenio_frame"]`, ...) via `update` callbacks, and `core/hydrate.py` rehydrates the PG from CPs on `load_post`. The 11 fields in `OBJECT_PROPS` are mirrored uniformly, which is over-broad: some fields are editor-time only and could live as PG-canonical with no CP at all, while others are animatable / driver targets where the CP is the durable storage and the PG is just a typed widget projection.

**Why:** PropertyGroup data is backed by IDProperty but its visibility depends on the addon's RNA descriptor being registered. Disable → save → reenable cycles can purge orphaned IDProperty data depending on Blender version, so PG is a brittle home for anything that must survive addon-absent file states or be a stable driver target. Raw CPs have none of those constraints, which is why Rigify and similar mature addons keep the *animator-facing* surface (IK/FK switches, layer toggles) on CPs and reserve PGs for *generator-internal* metadata. Mirroring everything pays the cost (doubled write paths, sync risk, undo desync, `deferred_hydrate` timer, dual-key reader fallback in `read_field`) for fields that do not need the resilience. Mirroring nothing loses real resilience for fields that do (`frame` is keyframable into Godot's `AnimationPlayer`; Drive-from-Bone wires drivers onto sprite properties). Blender also cannot keyframe a field nested inside a PropertyGroup ([T48975](https://developer.blender.org/T48975)), so an animatable / driver-target field has to live as a top-level Custom Property regardless.

**Decision (locked):** option **A** - split by intent. Editor-time-only fields become PG-canonical with no CP mirror; animatable / driver-target fields become CP-canonical with PG as a typed widget wrapper. Documented as a deliberate contract, not legacy debt - rewrite the `properties/__init__.py` docstring to call this out instead of describing CPs as "legacy".

**Scope sketch:**

- PG-canonical (drop the CP mirror): `sprite_type`, `region_mode`, `region_x`, `region_y`, `region_w`, `region_h`, `material_isolated`.
- CP-canonical (PG is the typed widget; writer reads CP directly): `frame`, `hframes`, `vframes`, `centered`, `proscenio_slot_index`.
- Drop the mirror entirely (PG-only, pure UI / editor state never exported and never a driver target): `is_outliner_favorite`. It carries a CP mirror today via the blanket `on_any_update` path yet is not even in the `hydrate` map - asymmetric dead weight.
- Reader (`writer/sprites.py`, slot index reads, etc.) drops the `read_field(pg_field=..., cp_key=..., default=...)` dual fallback and reads each field from its canonical home.
- `_update_*` mirror callbacks deleted for the PG-canonical group; retained only as PG → CP one-way for the CP-canonical group (since the PG is the widget the user touches).
- `core/hydrate.py` becomes a one-shot migrator: on `load_post`, hydrate any `.blend` that still has legacy CPs in the PG-canonical group into the PG, then *delete* those CPs so the field has a single source of truth post-migration. Gate behind a `format_version` check on the scene PG so it runs at most once per file.
- `_handlers.py`: keep `load_post` for the one-shot migrator; `save_pre` and `deferred_hydrate` timer can likely be deleted once the mirror is gone (revalidate during the rewrite).
- Drive-from-Bone operator: target the CP path for animatable fields so the driver `data_path` is `pose.bones["X"]["proscenio_frame"]`-style rather than the nested PG path. Reduces driver fragility on linking / append.
- Collapses the duplicate field-mapping tables (code-duplication spec finding N14): today `core/hydrate.py` `OBJECT_PROPS` (11 rows) is a hand-maintained subset of `core/mirror.py` `OBJECT_MIRROR_MAP` (14 rows), so adding a field means editing both in lockstep. After the split each field has a single canonical home and the two tables fold into the per-intent mapping, removing the lockstep hazard. The dedup pass deferred N14 here rather than force-merge the tables, since this redesign reshapes them anyway (merging now would just be re-undone).

**Trigger to revisit:** before 1.0.0 release. Block on this landing so the public surface ships with the final storage contract; post-1.0 schema or storage migrations cost real users.

**Out of scope for this entry:**

- Library-override / linking semantics for the surviving PG fields (separate concern; address only if a user reports issues).
- Schema `format_version` bump - the contract on disk does not change; only the in-`.blend` storage shape does. May still want a `format_version` bump on the *scene PG* to gate the migrator.

## Photoshop and Krita

### Krita exporter

`coa_tools2/Krita/coa_export.py` works in Krita 4.x. Phase 2 port-forward target.

### GIMP exporter

`coa_tools2` has a GIMP path. Lower priority - fewer 2D animation users on GIMP.

## Architecture revisits

These items intentionally violate or expand on a current hard rule. They are **not slated** - listed only so that if the trigger condition appears in a future spec discussion, we have prior art on the alternatives we already considered.

### GDExtension / C# escape hatch

**Current rule:** [`AGENTS.md`](../AGENTS.md) hard rule #3 - no GDExtension, no native runtime; the Godot plugin is GDScript-only and runs only at editor import time. See [`.ai/skills/architecture.md`](../.ai/skills/architecture.md) for the rationale.

**Why this entry exists:** the maintainer prefers strong typing, nullables, and a real compiler over GDScript's dynamic feel ("magia e reza braba"). Firebound itself is C# (mono build). Continuing in GDScript is a deliberate trade for plugin reach in the broader 2D community, not an endorsement of GDScript's ergonomics.

**Triggers that would justify reopening the rule:**

- **Deep Firebound integration** - Firebound exposes a runtime API (signals, services, custom nodes) that the imported character must talk to natively, and surfacing that contract through GDScript adapters becomes the bottleneck.
- **Performance ceiling hit** - `Polygon2D` skinning with high bone counts measured against a real game scene exceeds frame budget; compute-shader skinning via GDExtension becomes the cheapest path.
- **Live link Blender ↔ Godot** - pose/animation/sprite delta streaming over a socket needs sustained throughput that GDScript's dictionary parsing cannot hit.
- **Binary `.proscenio` format** - JSON parse time becomes import-loop pain on large projects; binary format reader benefits from native code.
- **Editor authoring tools that need round-trip serialization back to `.proscenio`** - writing the format from inside Godot at interactive speed.

**What that future spec would look like:**

- Likely targets a *separate optional component* (`apps/godot-csharp/`) that ships alongside the GDScript plugin, gated behind a feature flag, so non-mono users still have the GDScript path.
- Mono-only audience cut would be **documented openly** as the price of the feature; this is acceptable for Firebound users (already on mono) but acknowledged as a regression for general OSS reach.
- Anything moved to native must remain **import-time only** unless the spec explicitly relaxes the runtime side. Generated `.scn` keeps using built-in nodes.

**See also:** [`.ai/skills/architecture.md`](../.ai/skills/architecture.md), [`.ai/README.md`](../.ai/README.md), the language-decision discussion in this backlog's revision history.
