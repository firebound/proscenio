# Naming consistency: the Element vocabulary (mesh / sprite anchored on Godot)

Status: **decisions locked, ready for TODO**. A cross-component rename that fixes the overloaded "sprite" vocabulary. The umbrella term becomes `Element`; the two kinds are renamed and re-anchored on the Godot node they produce (`mesh` -> `Polygon2D`, `sprite` -> `Sprite2D`). This is the first spec in the larger `apps/blender` UI/UX review, deliberately sequenced **before** the panel/information-architecture work because every later panel spec renders these terms - renaming first stops the UI specs from baking in the wrong words.

## Problem

The word "sprite" carries three incompatible jobs at once, and the meaning flips depending on which app you are reading.

1. **"sprite" is the umbrella AND a kind.** The `.proscenio` wire array is `sprites[]`, the Blender panel is "Active Sprite", and the glossary defines "Sprite" as "a textured 2D shape, single quad or arbitrary mesh" - i.e. the umbrella for *everything*. But "sprite" is also what an artist means by a single rigid quad (a `Sprite2D`). One word is both the genus and one of its species.
2. **The `[sprite]` tag is inverted.** In `apps/photoshop/src/lib/tag-parser.ts` the tag `[sprite]` maps to `kind: "polygon"`, i.e. it produces a Godot `Polygon2D`, not a `Sprite2D`. An artist who tags a layer `[sprite]` expecting a 4-vert sprite gets a deformable polygon instead. The only way to author a `Sprite2D` today is `[spritesheet]` on a group, which forces 2+ frames - there is no single-frame sprite path from Photoshop at all.
3. **The kind names do not match the Godot result the user reasons about.** The maintainer's mental model is anchored on the final node: `Sprite2D` = a 4-vert plane, `Polygon2D` = more verts (a "mesh" / "poly"). The wire calls these `polygon` and `sprite_frame`; Blender's `sprite_type` enum calls them `Polygon` and `Sprite Frame`; Photoshop tags call them `[polygon]`/`[mesh]` and `[spritesheet]`. Three vocabularies for two nodes, none of which reads as "mesh" or "sprite".
4. **A redundant PSD-only kind.** The PSD manifest carries three kinds - `polygon`, `mesh`, `sprite_frame` - where `polygon` and `mesh` both collapse to `Polygon2D` downstream (`mesh` only stamps a `proscenio_psd_kind` hint that nothing branches on yet). The split predates the decision to treat every `Polygon2D` as mesh-capable.

The pipeline taxonomy itself is *sound*: there really are exactly two render paths, and they really do map to `Polygon2D` and `Sprite2D`. The audit verdict from the UI/UX review was that the distinction is correct but the **words** are wrong. This spec fixes the words, repo-wide, before any panel is redrawn.

## What we want

One umbrella term and two kind names, every kind name chosen so it reads the same in Photoshop, in Blender, and as the Godot node it becomes. Authors pick a term that tells them the final result; maintainers read one word per concept across all three apps and the wire.

- **Umbrella: `Element`.** Replaces "sprite" wherever it meant "any pipeline object" - the `sprites[]` array, the "Active Sprite" panel, the `sprite_type` field, the glossary genus term.
- **Kind `mesh` -> `Polygon2D`.** Deformable cutout: arbitrary vertex count, UV, vertex weights. Tags `[mesh]` / `[poly]`. Was `polygon` (+ the absorbed `mesh` hint).
- **Kind `sprite` -> `Sprite2D`.** Rigid textured quad with an optional spritesheet grid. Frame count is an *attribute*, not a kind: 1 frame = static sprite, N frames = animated spritesheet. Tags `[sprite]` (single) / `[spritesheet]` (group of frames). Was `sprite_frame`.

The "spritesheet" concept stops being a kind and becomes "a `sprite` whose frame count is greater than one". `mesh` is elevated to a first-class kind name (it is now THE name for the `Polygon2D` path) rather than a deformable-intent hint riding on `polygon`.

## Design space

### Axis A - umbrella term (the genus formerly "sprite")

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A1.** `Element` | Generic, unloaded, reads cleanly as "any pipeline object"; the maintainer picked it over "Object" (which collides with Blender's `bpy.types.Object`) | Touches the wire array name `sprites[]` -> `elements[]` | **Lock** (user choice). |
| **A2.** `Object` | Most generic English term | Collides head-on with Blender's `Object` - the addon is full of `bpy.types.Object`; ambiguous in every Blender file | Reject. |
| **A3.** keep `Sprite` as umbrella | No rename | The exact overload being removed | Reject. |

### Axis B - kind names, anchored on the Godot node

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **B1.** `mesh` (-> `Polygon2D`) + `sprite` (-> `Sprite2D`) | Each name reads as the node it produces; matches the maintainer's "4 verts = sprite / more verts = mesh" model; frees "spritesheet" to be an attribute | The rename | **Lock** (user choice). |
| **B2.** keep `polygon` + `sprite_frame` | No rename | `polygon` reads as geometry not kind; `sprite_frame` implies "always multi-frame"; neither says "Sprite2D" | Reject. |

### Axis C - rename SCOPE

Decides whether the rename reaches the wire or stops at the presentation layer. Locked to C1.

| Option | What changes | Pros | Cons | Verdict |
| --- | --- | --- | --- | --- |
| **C1. Full wire rename** | `.proscenio` `sprites[]`->`elements[]`, `type` values `polygon`/`sprite_frame`->`mesh`/`sprite`; PSD manifest kind renames + collapse; regenerate all `schema_bindings/`; regenerate fixtures + goldens. Done in place at the current version number - see Axis F | Total consistency - the `.proscenio` file itself reads `elements`/`mesh`/`sprite`, matching the UI and the Godot nodes; no lingering translation layer | Largest blast radius: bindings regen, every fixture + golden regenerates, a 3-app coordinated change | **Lock.** |
| **C2. Presentation-only (wire frozen)** | Rename Blender PG fields + UI labels + PS tag vocabulary + docs; keep `sprites[]`/`polygon`/`sprite_frame` on the wire | No schema bump, no fixture churn, byte-stable wire | The `.proscenio` file still says `sprites`/`polygon` - reintroduces the dual vocabulary the user wants gone; "consistency focused on the final result" is not achieved; AND it does not even fully avoid manifest work (the `[sprite]` single-frame fix forces a manifest shape change regardless) | Reject. |

**Locked: C1.** The maintainer's stated goal is consistency focused above all on the final Godot result - a half-rename that leaves the wire reading `sprites`/`polygon` defeats the purpose. The project is pre-launch (no external consumers), so reshaping the wire is free of real-world breakage. The codegen pipeline makes binding regeneration mechanical (change `packages/models/`, re-run codegen), and the fixtures have a single-source regeneration path. Whether this reshape bumps the version number is a separate call - see Axis F.

### Axis F - schema versioning at this stage

The rename reshapes two published-shape schemas (`.proscenio`, the PSD manifest). The schema-contract rule in `decisions.md` says any cross-component shape change bumps `format_version` + ships a migration. But that rule protects *deployed consumers*, and there are none yet - Proscenio has never shipped or been used in production.

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **F1.** Both schemas land at `v1`, in place, no bump | Honest launch history (`v1` = the first public schema); no migration code; less work (`.proscenio`'s `Literal` / Godot's `SUPPORTED_FORMAT_VERSION` are untouched); reflects that pre-launch the schema is still being defined | "Goes backward" on the PSD manifest (`2`->`1`) mid-dev-history; contradicts the literal bump rule (which this spec then revises) | **Lock.** |
| **F2.** `.proscenio` in place at `v1`, PSD manifest left at `v2` | No backward move on the PSD manifest | Launches with out-of-sync numbers (`v1` + `v2`) implying a PSD `v1` nobody used | Reject. |
| **F3.** Bump as the rule literally says (`1`->`2`, `2`->`3`) | Honors the current rule verbatim | Launches at `v2`/`v3` - writes a history that never happened; adds migration code for zero consumers | Reject. |

`format_version` is a *launch* concern, not a dev-churn concern: pre-launch the schema is a moving target and the number is meaningless until there is a consumer to protect. The number freezes at launch. This spec adopts that principle and revises the `decisions.md` "Schemas are the contract" rule to scope the bump-plus-migration requirement to *post-launch* changes (D10). The PSD manifest collapses `2`->`1` here because this spec already rewrites its shape; `.proscenio` simply stays `1`.

### Axis D - PSD `polygon` + `mesh` collapse

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **D1.** Collapse `polygon` + `mesh` into a single `mesh` kind | Matches the 2-kind model exactly; `mesh` = `poly` = `Polygon2D` is the maintainer's mental model (they are synonyms, not two kinds); every `Polygon2D` is mesh-capable, so the capability is universalized not lost | Drops the `proscenio_psd_kind` deformable-intent hint (which nothing branches on today) | **Lock.** Tags `[mesh]`, `[poly]`, `[polygon]` all map to kind `mesh`. |
| **D2.** keep both PSD kinds | Preserves the rigid-vs-deformable authoring hint | Reintroduces a 3rd kind the rest of the pipeline does not have; the hint is redundant with "does this mesh carry weights / an automesh base group", which is already tracked | Reject. |

This honors the maintainer's "I do not understand why `kind: mesh` needs to leave" - **`mesh` stays**; it is `polygon` (as a separate kind name) that is absorbed into it. "Rigid quad cutout" becomes "a `mesh` that happens to be a 4-vert quad with no weights", not a distinct kind.

### Axis E - the `[sprite]` fix and single-frame sprite authoring

Fixing the inversion (`[sprite]` must produce a `Sprite2D`) creates a new capability that does not exist today: a single-frame sprite authored from Photoshop. The PSD manifest's `SpriteFrameLayer` currently requires `frames` with `min_length=2`.

| Option | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **E1.** Relax `frames` to `min_length=1`; `[sprite]` on a single layer emits a 1-frame sprite (hframes=vframes=1) | One uniform sprite shape; static sprite is just the N=1 case; the importer's `hframes x vframes` math already handles 1x1 | A 1-frame "spritesheet" reads slightly odd in the manifest | **Lock.** |
| **E2.** Add a distinct single-PNG sprite shape separate from the frames list | Cleaner single-frame representation | A third manifest shape for what is conceptually the same `Sprite2D`; more code | Reject. |

So `[sprite]` (single layer) and `[spritesheet]` (group of N frames) both produce kind `sprite`; they differ only in frame count.

## Target vocabulary

Anchored left-to-right on the final Godot node. This table is the contract the rename implements and the seed for the glossary update.

| Concept | PS tag (author writes) | PSD manifest `kind` | `.proscenio` `type` | Blender `element_type` | Godot node |
| --- | --- | --- | --- | --- | --- |
| Deformable cutout | `[mesh]` / `[poly]` / `[polygon]` | `mesh` | `mesh` | `mesh` | `Polygon2D` |
| Static sprite | `[sprite]` | `sprite` (1 frame) | `sprite` | `sprite` (frames = 1) | `Sprite2D` |
| Animated sprite | `[spritesheet]` (on a group) | `sprite` (N frames) | `sprite` | `sprite` (frames > 1) | `Sprite2D` |

Umbrella, everywhere: `sprites[]` -> `elements[]`; "Active Sprite" panel -> "Active Element"; `sprite_type` -> `element_type`; glossary genus "Sprite" -> "Element".

### What does NOT rename (deliberate)

- **`Polygon2D` / `Sprite2D`** - Godot engine class names, not ours.
- **The geometry field `polygon: list[Vec2]`** on the mesh element - it maps to Godot's `Polygon2D.polygon` property. Only the `type` *discriminator value* changes (`polygon` -> `mesh`); the vertex-list *field* keeps the name `polygon`.
- **`hframes` / `vframes` / `frame` / `centered` / `texture_region`** - `Sprite2D` attributes; they stay, now living under the `sprite` element.
- **`uv` / `weights`** - mesh-element attributes; unchanged.

## Current to target mapping

### Wire (`.proscenio`, stays `format_version` 1)

| Today | Target |
| --- | --- |
| `sprites: list[Sprite]` | `elements: list[Element]` |
| `PolygonSprite`, `type: "polygon"` | `MeshElement`, `type: "mesh"` |
| `SpriteFrameSprite`, `type: "sprite_frame"` | `SpriteElement`, `type: "sprite"` |
| `_sprite_discriminator` -> `{polygon, sprite_frame}` | `_element_discriminator` -> `{mesh, sprite}` |
| `format_version: Literal[1]` | unchanged (`Literal[1]`) |

### PSD manifest (`format_version` 2 -> 1, collapse)

| Today | Target |
| --- | --- |
| `PolygonLayer`, `kind: Literal["polygon", "mesh"]` | `MeshLayer`, `kind: Literal["mesh"]` |
| `SpriteFrameLayer`, `kind: "sprite_frame"`, `frames` min 2 | `SpriteLayer`, `kind: "sprite"`, `frames` min 1 |
| `_layer_discriminator` -> `{polygon_or_mesh, sprite_frame}` | `_layer_discriminator` -> `{mesh, sprite}` |
| `format_version: Literal[2]` | `format_version: Literal[1]` (collapse, see Axis F) |

### Photoshop (`apps/photoshop/src/`)

| Today | Target |
| --- | --- |
| `tag-parser.ts`: `case "polygon"/"sprite": kind="polygon"` | `case "mesh"/"poly"/"polygon": kind="mesh"` |
| `tag-parser.ts`: `case "mesh": kind="mesh"` | folded into the line above |
| `tag-parser.ts`: `case "spritesheet": kind="sprite_frame"` | `case "spritesheet": kind="sprite"` (group, N frames) |
| (no single-layer sprite path) | `case "sprite": kind="sprite"` (single layer, 1 frame) |
| `PolygonKind = "polygon" \| "mesh"`, `kind?: ... \| "sprite_frame"` | `kind?: "mesh" \| "sprite"` |
| `planner.ts` / `manifest.ts` `"sprite_frame"` | `"sprite"` |

### Blender (`apps/blender/`)

| Today | Target |
| --- | --- |
| `object_props.py`: `sprite_type` enum, items `polygon`/`sprite_frame` | `element_type`, items `mesh`/`sprite` |
| `SPRITE_TYPE_ITEMS` | `ELEMENT_TYPE_ITEMS` |
| `panels/active_sprite.py` ("Active Sprite") | `panels/active_element.py` ("Active Element") |
| `panels/_draw_polygon.py` / `_draw_sprite_frame.py` | `_draw_mesh.py` / `_draw_sprite.py` |
| `core/sprite_frame/`, `core/bpy_helpers/sprite_frame/` | `core/sprite/`, `core/bpy_helpers/sprite/` |
| `core/validation/active_sprite.py` | `core/validation/active_element.py` |
| writer/importer literals `"polygon"`/`"sprite_frame"`, `sprites[]` | `"mesh"`/`"sprite"`, `elements[]` |

### Godot (`apps/godot/addons/proscenio/`)

| Today | Target |
| --- | --- |
| `document.sprites` | `document.elements` |
| `builders/polygon_builder.gd` (`PolygonBuilder`) | `builders/mesh_builder.gd` (`MeshBuilder`) |
| `builders/sprite_frame_builder.gd` (`SpriteFrameBuilder`) | `builders/sprite_builder.gd` (`SpriteBuilder`) |
| `SUPPORTED_FORMAT_VERSION := 1` | unchanged (`:= 1`) |
| `schema_bindings/*` (auto-generated) | regenerated from the renamed models |

### Docs + skills

`.ai/skills/glossary.md` (add `Element`, `mesh`, `sprite` rows; rewrite the `Sprite` row), `format-spec.md`, `architecture.md`, `blender-dev.md`, `godot-dev.md`, `photoshop-uxp-dev.md`, `references.md`, `testing.md`; `.ai/conventions/code.md` + `docs.md`; `README.md`; `examples/**/README.md`. The `tests/*.md` logs (UI_FEEDBACK / BUGS_FOUND / MANUAL_TESTING) are historical and left as-is.

## Decisions (to lock)

- **D1 (Axis A).** Umbrella term is `Element`. `sprites[]` -> `elements[]`, "Active Sprite" -> "Active Element", `sprite_type` -> `element_type`.
- **D2 (Axis B).** Two kinds, named for their Godot node: `mesh` -> `Polygon2D`, `sprite` -> `Sprite2D`.
- **D3 (Axis C).** Full wire rename - the JSON shape itself changes (`elements`, `mesh`, `sprite`), not just the UI labels. Locked.
- **D4 (Axis D).** Collapse PSD `polygon` + `mesh` into a single `mesh` kind; `[mesh]`/`[poly]`/`[polygon]` all map to it. The deformable-intent hint is dropped (universalized: every mesh is `Polygon2D`-deformable-capable).
- **D5 (Axis E).** `[sprite]` on a single layer produces a 1-frame `sprite`; `frames` relaxes to `min_length=1`. Static sprite is the N=1 case of the same shape `[spritesheet]` produces.
- **D6 (no-rename guard).** `Polygon2D`/`Sprite2D` (engine), the geometry field `polygon`, and the `Sprite2D` attributes (`hframes`/`vframes`/`frame`/`centered`/`texture_region`) keep their names. Only the umbrella array, the class names, the `type`/`kind` discriminator values, the Blender `sprite_type` field, and the UI labels rename.
- **D7 (no migration code).** No bump (D10), so no version-guard change and no upgrade reader. Schema shapes change in place; fixtures + goldens regenerate from their single source. A stray old-shape file would fail strict schema validation (unexpected `sprites` key under `additionalProperties: false`) rather than a version check - acceptable pre-launch since every such file lives in-repo and regenerates atomically in the Phase 0 PR.
- **D8 (phasing).** Land producer-first, contract-first: models + codegen + fixtures -> Blender -> Photoshop -> Godot -> docs. The shape change crosses all components at once (the schema-crosses-all exception to one-component-per-PR); the Phase 0 PR is explicitly cross-cutting.
- **D9 (glossary is the authority).** The target-vocabulary table lands in `.ai/skills/glossary.md` as the canonical term home; later UI/UX specs cite it instead of redefining terms.
- **D10 (freeze-at-launch versioning, Axis F).** Both schemas land at `format_version: 1` (`.proscenio` stays 1, PSD manifest collapses 2->1). `format_version` is fixed at launch, not bumped during pre-launch churn; in-dev shape changes happen in place, proven by fixture regeneration. This revises the `decisions.md` "Schemas are the contract" rule to scope its bump-plus-migration requirement to post-launch changes; the revision lands in Phase 0.

## Phasing

Producer-to-consumer so the contract is renamed before anyone reads it. Each phase is independently gate-verifiable; the shared shape change means Phase 0 must merge before the apps can adopt.

- **Phase 0 - models + codegen + fixtures + the versioning decision.** Rename in `packages/models/` (classes, discriminator callables + values, array name); collapse the PSD manifest `format_version` literal `2`->`1`, leave `.proscenio` at `1` (D10). Revise the `decisions.md` "Schemas are the contract" entry to scope the bump rule to post-launch. Regenerate every `schema_bindings/` artifact (TS, GDScript, JSON Schema, docs Markdown). Update the committed-match codegen tests. Regenerate all `.proscenio` + manifest fixtures and writer goldens from source. Gate: `pytest tests/codegen/`, model unit tests, schema validation.
- **Phase 1 - Blender.** `element_type` PG field + `ELEMENT_TYPE_ITEMS`, panel rename (`active_element.py`, `_draw_mesh.py`, `_draw_sprite.py`), `core/sprite/` folder rename, writer + importer literals, validation, help topics, feature-status. Gate: the full Blender gate set (ruff, mypy, repo-root pytest, fixture suite 7/7, operator suite, import sweep). Smoke: the Active Element panel renders both kinds.
- **Phase 2 - Photoshop.** `tag-parser.ts` vocabulary (the `[sprite]` flip, `[spritesheet]` -> sprite, `[mesh]`/`[poly]`/`[polygon]` -> mesh), `PolygonKind`/`TagBag`, planner + manifest writer, emit the manifest at the collapsed v1. Gate: `tsc --noEmit`, ESLint, vitest (the tag-parser + exporter suites carry the proof).
- **Phase 3 - Godot.** `document.elements`, rename builders (`MeshBuilder`, `SpriteBuilder`) + their files, builder discriminator filters on `mesh`/`sprite` (`SUPPORTED_FORMAT_VERSION` stays 1). Gate: gdformat --check, gdlint, `test_importer.gd` against the regenerated fixtures.
- **Phase 4 - docs + skills + glossary.** Glossary rows, format-spec, all `.ai/skills/*`, conventions, READMEs, examples. No code gate; spell-check + link check.

## Open questions

- **Q1 (tag aliases).** Keep `[polygon]` and `[poly]` as accepted aliases for `[mesh]` indefinitely, or warn-and-deprecate `[polygon]` so artists migrate to `[mesh]`? Leaning keep-as-silent-aliases (artists should not have to relearn), decide during Phase 2.
- **Q2 (Blender `core/sprite_frame/` rename).** Folder rename to `core/sprite/` triggers the repo-root `uv run pytest tests/` import-path breakage noted in the Blender test-gate memory; confirm the gate is run after the move, not before.

## Non-goals

- No new render path, no behavior change beyond the `[sprite]` inversion fix and the single-frame sprite it enables. Same two Godot nodes, same deformation, same spritesheet math.
- No panel layout / information-architecture change - that is the next spec in the UI/UX series. This spec only renames; it does not move or regroup panels.
- No `Storage split by field intent` work (a separate backlog item) even though it touches the same PG fields.
- The `tests/*.md` feedback logs are historical records, not renamed.

## Related

- [`../decisions.md`](../decisions.md): the "Spritesheet Sprite2D discriminator", "Slot system" (kind-agnostic), and "Photoshop tag system" (`kind: "mesh"` hint) entries this rename supersedes; the "Schemas are the contract" rule this **revises** (D10) to scope the bump-plus-migration requirement to post-launch.
- [`../../.ai/skills/glossary.md`](../../.ai/skills/glossary.md): the canonical term home this spec rewrites (D9).
- [`../../.ai/skills/format-spec.md`](../../.ai/skills/format-spec.md): the wire-shape reference that documents `sprites[]` and the `type` discriminator.
- [`../backlog.md`](../backlog.md): the `apps/blender` UI/UX review this spec opens; the panel/IA spec follows it.
- [`../../tests/UI_FEEDBACK.md`](../../tests/UI_FEEDBACK.md): the raw audit feedback, including "'sprite' overloaded -> rename" which seeds this spec.
