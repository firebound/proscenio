# Spec 034: Photoshop plugin

Round out the Photoshop tag system and tighten the export roundtrip.

## Scope

- **Retest the waist 1px drift** through the UXP path.
- **Fix the form clearing a set tag** - the advanced-fields form drops the clear signal.
- **Warn on a silent nested [merge]** collapse.
- **Rewrite [name:pre*suf] patterns** the planner already parses.
- **Distinguish kind:"mesh" from "polygon"** downstream (or document the equivalence).
- **A [slice] 9-slice tag** (Cocos-style).
- **Head-turner view groups**.
- **Pseudo-keyword auto-tagging** (Head, Mouth, Eye).
- **An [isolated] warp-independent flag**.
- **Stable layer identity** for duplicate layer names in the write path.
- **Measure the Spectrum shadow-DOM init cost**.

## Study

### Surface notes

- The tag vocabulary ships eleven keywords in `lib/tag-parser.ts`: `[ignore]`, `[merge]`, `[folder:name]`, the kind aliases (`[mesh]`/`[poly]`/`[polygon]` -> mesh, `[sprite]`/`[spritesheet]` -> sprite), the `[origin]` marker, `[origin:x,y]`, `[scale:n]`, `[blend:mode]`, `[path:name]`, and `[name:pre*suf]`; unknown brackets pass through, translation to manifest fields happens at parse time, and the convention deliberately mirrors PhotoshopToSpine's bracket tags.
- The form-clear bug is a relay that drops the baton at the first hop: the `diff*` helpers in `lib/tag-form.ts` correctly signal a cleared field as `undefined`, but `applyDiff` runs `delete changes[key]` on the still-empty changes object (`tag-form.ts:97-99`, an `exactOptionalPropertyTypes` workaround per the backlog entry), so the key never reaches `applyTagChanges` (`lib/tag-writer.ts:90-97`), which clears only keys *present* with value `undefined`.
- The UI symptom is a dead control in the core tag-editing flow: clearing a field marks the form dirty (`Details.tsx:39`), `Apply` enables, and the click does nothing because `Details.tsx:48` gates the rename on `Object.keys(changes).length > 0`. `tag-form.test.ts` has zero clear cases - deliberately, per the backlog, to avoid locking the broken behavior in.
- The waist -1px drift was measured against the JSX exporter's `layer.bounds`; the UXP writer duplicates the layer into a temp document and trims with `Document.trim(TRANSPARENT, ...)` (`api/png-writer.ts:71`) - a different bbox engine, so the logged number predates the code that would have to reproduce it. Pure retest, already queued in the verification session.
- `emitTagConflicts` (`lib/planner.ts:189-213`) checks merge-vs-sprite, double-origin, and mesh-on-plain-group only; no merge-nested entry exists (by design), and the silent collapse is confirmed end-to-end on the doll oracle (`1 [merge]` swallowing `1.1 [merge]`).
- The parser validates and stores `namePattern` (`tag-parser.ts:131-134`) and the Details form offers the field on groups (`Details.tsx:163-174`), but `planner.ts` has zero references to it - the UI currently invites a tag the export silently ignores, which sharpens the gate's trigger (the first confused report).
- `[mesh]`/`[poly]`/`[polygon]` all collapse to `kind: "mesh"` at parse (`tag-parser.ts:112-116`), the Blender importer stamps `PROSCENIO_PSD_KIND` (`importers/photoshop/planes.py:401-403`), and nothing anywhere branches on it; the advanced-guide tag table documents the split but not the present-day equivalence.
- `PngWrite.layerPath` is a name chain (`planner.ts:60`) and `findLayerByPath` takes the first name match per depth (`api/_layer-find.ts:23`), so duplicate siblings resolve to the first; the dangerous same-group case already trips the `duplicate-path` warning (`planner.ts:215-249`) because both entries sanitize to one output path - the residual silent hole needs a `[path:]` override de-colliding the outputs of two same-named siblings.
- The exporter PPU input and the planner stamp exist (`hooks/usePixelsPerUnit.ts`, `planner.ts:137`) but `api/import-flow.ts` never reads `manifest.pixels_per_unit`; the seed fix is owned by the atlas-packing spec's PPU cluster and edits this app without touching this spec's files.
- Spectrum web components sit in 8 section files (33 `sp-*` usages; `ExportSection.tsx` alone has 14); the largest real document is the 22-layer doll, far under the >100-layer lag trigger, and the plain-HTML swap recipe is already proven (`5c6bef2`).

### Research notes

- PhotoshopToSpine script README (EsotericSoftware spine-scripts): twelve tags - `[bone]` `[slot]` `[skin]` `[folder]` `[scale]` `[trim]` `[overlay]` `[mesh]` `[ignore]` `[merge]` `[name:pattern]` `[path]`. Proscenio's vocabulary is the same convention minus the Spine-runtime concepts, and Spine does implement the `[name:pattern]` rewrite - precedent that the reserved slot is sane, not that demand exists here.
- Spine script history (esotericsoftware forum): the tag set accreted by demand - `[overlay]` arrived years after the core set - the same demand-gated growth model this spec adopts.
- Live2D Cubism PSD manual (docs.live2d.com): no tag system at all - the conventions are structural (one merged part per layer, the group hierarchy becomes the Parts tree) and the manual recommends unique layer names because duplicates cause problems later; identity-by-name is the industry baseline, which supports gating stable-layer-identity instead of pre-engineering for duplicate names.
- Adobe Character Animator, Prepare artwork + Tags and behaviors (helpx.adobe.com): auto-tagging matches keywords *inside* layer names ("My Ah" matches the "Ah" tag) under a rigid Head/Mouth group contract, and the `+` prefix marks warp-independence; CA affords the implicit magic because its face behaviors consume the tags - Proscenio has no consuming behavior, only the rig the artist builds.
- Character Animator head turner (helpx + community tutorials): the Frontal/Quarter/Profile view groups are a face-puppetry behavior bound to CA's head-turn runtime; in a bones-plus-slots model the same swap is slot attachments, which already ship.
- 9-slice (Unity manual, GameMaker blog, GDevelop Panel Sprite, PixiJS NineSliceSprite): uniformly presented as scalable UI furniture - buttons, panels, HUD, health bars; none of the engine docs proposes it for characters, and Godot consumes nine-patch via `NinePatchRect` / `StyleBoxTexture` configured in the editor on a plain texture.

### Assessment

Flow value 5 = core flow; test burden 1 = pure unit (the TS side runs on vitest, the cheapest suite in the repo), 5 = recurring manual GUI; bug surface 1 = bugfix, 5 = new stateful surface; underuse risk 1 = universal, 5 = speculative. A new tag is never parser-only: it costs planner emission, a manifest field, Blender-side consumption, docs, and tests across at least two apps - `[slice]` would add a Godot builder hop on top.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| tag-form-clear | 4 | 1 | 1 | 1 | now | Real bug in the core tag-editing flow: `Apply` reads enabled, the clear dies in `computeChanges` before the rename; pure-model fix, the backlog already sketches the carrier shape, vitest-only. |
| waist-1px-drift | 3 | 5 | 1 | 1 | now | Retest only: the JSX-era measurement is stale against the UXP trim path; it rides the already-scheduled verification GUI session, so no new manual layer - decide rounding only if the drift survives. |
| nested-merge-warning | 2 | 1 | 2 | 3 | gate | By-design recursive semantics that surprised nobody on the doll authoring run; an info entry without a confusion report on file is false-positive fatigue. |
| name-pattern-rewrite | 2 | 2 | 3 | 4 | gate | Zero consumers; the rewrite order (joinName interaction, `[path:]` precedence) needs a real workflow to design against; Spine precedent keeps the slot reserved, not the implementation. |
| kind-mesh-vs-polygon | 2 | 1 | 1 | 4 | gate | Nothing downstream exists to branch for; document the equivalence now (one guide line riding the bugfix PR) and branch when mesh-deformation ships. |
| slice-9slice-tag | 1 | 4 | 3 | 5 | drop | 9-slice is UI furniture in every engine doc; the pipeline ships rigged characters and Godot already owns nine-patch insets engine-side - the tag would round-trip editor settings through parser, manifest, importer, and builder. |
| head-turner-groups | 1 | 5 | 5 | 5 | drop | CA face puppetry coupled to a face-rig template and a head-turn runtime Proscenio lacks; slots already express view swaps; the heaviest possible test class for an imagined audience. |
| pseudo-keyword-tagging | 1 | 3 | 4 | 5 | drop | Implicit match-inside-name tagging is CA's collision-prone shortcut for behaviors Proscenio does not have; it contradicts the locked explicit-bracket design. |
| isolated-flag | 1 | 4 | 4 | 5 | gate | Tags a concept (per-layer pose channel) no tool in the pipeline has; the reserved name costs nothing until the concept exists. |
| stable-layer-identity | 2 | 2 | 2 | 4 | gate | First-match resolution is real but the duplicate-path warning already catches the common dup-sibling case; no wrong-PNG report ever; the `{name, index}` hint is on record. |
| spectrum-shadow-dom | 1 | 5 | 1 | 5 | gate | A manual profiling session for a lag threshold (>100 layers) no document has hit; the plain-HTML swap is the proven first response, so measure only if a swap is contested. |

### Verdict summary

- **Now (2):** tag-form-clear (the one code change, a vitest-covered pure-model bugfix), waist-1px-drift (retest folded into the verification session).
- **Gate (6):** nested-merge-warning, name-pattern-rewrite, kind-mesh-vs-polygon (downstream branch), isolated-flag, stable-layer-identity, spectrum-shadow-dom - triggers written in [TODO.md](TODO.md).
- **Drop (3):** slice-9slice-tag, head-turner-groups, pseudo-keyword-tagging - propose pruning from the backlog.
- The tag vocabulary is feature-complete for the character flow it serves; every growth candidate waits on a demonstrated workflow, the same demand-accretion the Spine script followed, and the three pruned items are lifts from tools whose consuming runtimes Proscenio does not have.
- Cross-spec: the atlas-packing spec's ppu-roundtrip chunk edits this app (`api/import-flow.ts` - different files, no conflict with the tag-form fix); the waist retest and the PPU 10x waiver re-measure share the one verification GUI session.
