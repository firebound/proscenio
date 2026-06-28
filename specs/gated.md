# Gated work

Items with real value held behind a written trigger. Each proceeds only when its trigger fires; none is built on imagined demand. Carved out during the 2026-06-11 reconciliation (the durable number-to-topic map is [_index.md](_index.md)). Companion homes: [deferred.md](deferred.md) (sequenced second-stage), [dropped.md](dropped.md) (value below cost), [decisions.md](decisions.md) (locked calls); product backlog indexed from [backlog](backlog/index.md). One line each: item - rationale. **Trigger:** what fires it.

## Schema expressiveness

The Spine-parity expressiveness wave (the day-one appearance slice - modulate / z_index / flip - already shipped). Several share one design pass.

- **sprite-appearance (mask half)** - No single Godot property expresses masking; needs a CanvasGroup-vs-`clip_children` study. **Trigger:** a character actually needs clipping.
- **bezier-curve-preservation** - Godot's cubic auto-spline approximates well (Spine itself flattens to ~10 segments); denser baked sampling is the cheaper first answer. **Trigger:** an animator reports the import misses the Blender curve beyond visual tolerance (answer first with denser sampling).
- **per-key-interp-mixing** - Same fidelity question as Bezier handles; one design pass decides both. **Trigger:** same as Bezier handles.
- **animation-event-tracks** - Table stakes, but the Godot method-call contract (which node, which method, missing-method behavior) needs design. **Trigger:** a game needs a synced cue (footstep, impact, particle) from an imported animation.
- **texture-region-track** - Godot users reach for shaders for continuous UV; discrete cases are covered by slot-swap + sprite-frame tracks. **Trigger:** a user asks for animated water, conveyor, or region-resize effects.
- **multi-atlas-pages** - Per-element `texture` override already splits images, and a bounded character fits one page. **Trigger:** a real character pack overflows the 4096 page (packer returns `None`); interim is per-element `texture` + the exclude flag.
- **nla-strips-to-actions** - Native Bake Action is the documented game-export norm (COA Tools precedent). **Trigger:** an animator layers strips on the NLA and exports.
- **transform-constraint-export** - `RemoteTransform2D` fits only full-channel mix=1 copies; bake-at-export covers the motion. **Trigger:** a Copy Rotation / Copy Transforms rig exports and the target bone does not follow (bake first; `RemoteTransform2D` only for full-channel copies).
- **path-constraint-export** - Path geometry + `PathFollow2D` wiring for a rig style no fixture uses; bake-at-export covers it. **Trigger:** an animator authors a path constraint and asks why nothing happens in Godot.
- **bone-physics-export** - Spine ships a deterministic spring solver and never delegates to engine physics; Godot `Joint2D` chains would be non-deterministic + frame-rate-coupled. **Trigger:** a design has dangly parts baked secondary motion cannot serve (study a deterministic Godot-side solver before `Joint2D`).
- **rig-orientation full-XY support** - Generalizing the transform math for a convention no user asked for; the warn-only detection guard shipped in #105. **Trigger:** a real user authors a rig in the XY plane.
- **format-migration-path** - A migrator for a v2 that does not exist yet is speculative; gating preserves the storage-split ordering. **Trigger:** the first breaking schema bump is scheduled (the storage split is the candidate); build version detection + the v1-to-v2 migrator in that PR series. The storage-split spec (037) stays blocked behind this.

## Mesh authoring

- **manual-hull-pen-tool** - SHIPPED 2026-06-27 (spec 066, PR #162): the gate was reopened and built. The OUTER stage of the automesh interactive modal gained a Manual contour tool on the existing click-pen machine (click points, close the loop, it replaces `output.outer`), selected via the new bare-Tab per-stage tool cycle. Kept here as the record. Note: the contour pen still edits an existing mesh element's contour and ends at APPLY; a from-blank pen-creation tool and persistent re-editing are the open follow-on (`mesh-pen-authoring` in [backlog/ui-feedback.md](backlog/ui-feedback.md)). Original gate framing: demand class confirmed (Spine / Live2D / Moho), Edit Mode + Reproject UV was the fallback that made it gesture-convenience only.

## Skinning and weight paint

- **auto-patch-joint-cover** - Overlap caps at joints + seam weighting already cover the need. **Trigger:** a humanoid fixture ships end to end AND the artist reports articulation gaps overlapping art + seam weighting cannot hide.
- **bone-heat-override-post-pass** - New capability on the default bind path; the merge machinery exists but should not be built without demand. **Trigger:** a Bone-Heat user asks for per-bone Soft/Hard instead of switching to Proximity.
- **custom-weight-overlay** - Native overlay opacity already shipped as the cheap answer. **Trigger:** a real skinning session judges the native overlay insufficient on flat meshes.

## Rigging and posing

Quick-Armature / skeleton / pose extensions whose value is convenience the native tools or shipped work already cover.

- **qa-chain-naming-suffixes** - The flat counter works; after-the-fact batch rename covers the gap. **Trigger:** batch rename stops covering on a real multi-chain rig.
- **qa-mirror-suffix** - No symmetric rig fixture exists, cutouts are commonly asymmetric, and mirrored create entangles the in-modal undo stack. **Trigger:** a bilaterally symmetric rig fixture ships end to end.
- **sticky-panel** - The fix is a poll-architecture change, and the two-ranges rework may have reduced the pain. **Trigger:** re-measure the mesh-to-pose-bone swap pain after the two-ranges rework; proceed only if it still hurts.
- **drive-slot-from-bone** - A new driver target type + roundtrip burden; no rig has asked for bone-driven attachment swaps. **Trigger:** a real rig asks for bone-driven attachment swaps.
- **ik-chain-helper** - The shipped IK target wiring absorbs most of the need; pole scaffolding is build-on-demand. **Trigger:** a rigging session still asks for one-click target-plus-pole scaffolding.
- **ik-round-trip** - Godot's 2D `SkeletonModification2D` is Experimental and breaks under negative X scale (#79960, #75224); the bake gate covers the export. **Trigger:** Godot's 2D SkeletonModification graduates from experimental and the flipped-rig bugs close.
- **pose-auto-categorise** - Blender's native catalogs cover a single rig; auto-assign pays off across multiple characters. **Trigger:** a second character's poses enter the library.

## UI, help and surfaces

Editor chrome and help extensions whose value is real but waits on a demand signal or a stable surface. Carved out when spec 036 was pruned (2026-06-18).

- **validator-element-rename** - The cosmetic `SpritePayload` -> `ElementPayload` rename in `packages/validator`; the `Element` vocabulary is wired everywhere else, this is the last internal hold-out. **Trigger:** the next change that touches `packages/validator` carries it.
- **i18n-locale-tables** - `core/i18n.py` registers an empty `TRANSLATIONS`; populating means translating every label and multi-line help body, then re-maintaining the table on every copy change, and the docs site is English-only. **Trigger:** the first non-English user request or a contributed translation PR. The copy-churn prerequisite is now met - spec 064 landed the translation-stable help copy (each topic body is one whole-string msgid routed through `core/i18n.py` `iface()` under a per-topic context), so a locale can be populated without a second copy pass.
- **addon-docs-screenshots** - The `docs/02-tools/blender-addon/*` pages carry no captures; any set goes stale within a release while the panels still churn. **Trigger:** a panel-layout freeze at the 1.0 tag.
- **docs-url-preference** - `_DOCS_BASE` stays a constant (the spec 024 D3 locked deferral); a preference is speculative against one docs target. **Trigger:** a second docs target (a mirror or a version switch) appears.
- **joystick-slider-blend** - A 2D pose-blend gizmo + a pose-set PropertyGroup + a `BlendSpace2D` export path; a real animator staple (AE Joysticks 'n Sliders, Cubism parameters) but maximum cost on every axis. **Trigger:** the first character with parametric facial expressions enters production AND 1D Drive-from-Bone proves insufficient; design schema-first, the widget last.

## Atlas packing

- **per-asset-ppu** - A schema bump + three tools for a workflow the engine-side practice avoids (uniform PPU is the Unity guidance). **Trigger:** the mixed-PPU case recurs on a real project after uniform-PPU normalization is rejected.
- **per-object-pack-state** - A new stateful UI surface against today's single-shared-atlas reality, no multi-atlas pages to justify per-object badges. **Trigger:** multi-atlas pages ship, or a manual session logs hybrid pack-state confusion.
- **atlas-region-helper** - An authoring operator for a workflow with no logged friction (only reproject + region-from-UV ops exist). **Trigger:** a manual-testing session logs UV-snap friction during atlas region authoring.

## Photoshop plugin

New tag types + roundtrip hardening with no consuming runtime yet; each reserved name costs nothing until its concept exists.

- **nested-merge-warning** - By-design recursive semantics that surprised nobody on the doll run; an info entry would be false-positive fatigue. **Trigger:** an artist reports a sub-layer inside `[merge]` vanishing without realizing the collapse was deliberate.
- **name-pattern-rewrite** - Zero consumers (parser stores `namePattern`, planner never reads it); the rewrite order needs a real workflow to design against. **Trigger:** a fixture or workflow needs prefix/suffix templating on a group.
- **kind-mesh-vs-polygon** - Nothing downstream branches on the stamped kind yet (all mesh aliases build the same Polygon2D); equivalence is documented. **Trigger:** mesh-deformation work ships and the Blender importer branches on the stamped kind.
- **isolated-flag** - Tags a per-layer pose-channel concept no tool consumes. **Trigger:** a per-layer pose channel concept lands (authoring panel or continuous-UV-animation work).
- **stable-layer-identity** - First-match resolution is real, but the `duplicate-path` warning catches the common case and no wrong-PNG report has surfaced. **Trigger:** a wrong-PNG export report from duplicate sibling names, or a feature addressing layers by stable handle.
- **spectrum-shadow-dom** - A profiling session for a lag threshold (>100 layers) no document has hit (largest real doc is 22 layers). **Trigger:** a lag report opening Tags on a >100-layer PSD; first response swaps hot widgets to plain HTML (precedent `5c6bef2`).

## Project health

CI / coverage / fixture / repo gates whose cost is not yet justified by a real exposure.

- **blender-multi-version-matrix** - DONE 2026-06-22: the full headless suite ran green on Blender 4.2 LTS for `v0.9.1-beta` (fixtures rebuilt under 4.2 so they open on both; a 4.2-only brush-preset registration bug fixed). No permanent second CI leg was added - re-run the 4.2 suite per release instead. Kept here as the record.
- **blender-43-legacy-actions** - DONE 2026-06-22: covered by the 4.2 matrix run above - the `action_fcurves` paths exercise green on 4.2 through the animation goldens.
- **godot-editor-reimport-test** - Headless editor-import harnesses are flaky; the highest-value half (the saved-scene assert) shipped separately. **Trigger:** the first import-flow regression the builders-direct suite + saved-scene assert fail to catch.
- **mypy-ignore-errors-subtrees** - The full sweep is weeks of stub-fighting across ~6900 bpy-bound lines. **Trigger:** sweep each exempted module on its next functional touch; the validator trio (`addon_loader`, `coverage`, `measurement`) is the pilot.
- **run-coverage-ci** - Instrumented in-Blender reruns lengthen the longest job to produce a report no CI consumer reads. **Trigger:** Sonar analysis moves into CI; until then the local pre-scan recipe in `sonar-project.properties` is the workflow.
- **flat-fixture-buckets** - Pure reorganization whose move ripples through spec TODOs, the fixtures index, wrapper paths, and the sync script. **Trigger:** piggyback the move onto the next edit of a flat fixture (locked backlog decision).
- **origin-pivot-fixture** - Origin paths are triple-covered today (doll oracle, tag_smoke, pytest). **Trigger:** ship with the sprite-pivot-offset writer work, or the first regression where origin handling diverges between PSD authoring styles.
- **issue-pr-templates** - Zero protection for a solo repo. **Trigger:** the repo opens to outside contributors.
- **doll-roundtrip-remeasure** - The retired JSX reader logged a -1px waist drift (Blender manifest `255x173` versus the JSX-era `255x172`); the UXP png-writer now trims via `Document.trim(TRANSPARENT)`, a different bounding-box engine, so the drift needs re-measuring through the UXP path - align rounding on a persisting drift, or close it on a match. A pixels-per-unit of 100 is the doll fixture's baseline assumption, re-measured alongside. **Trigger:** before the first public `v*` tag, folded into the same release-readiness pass as `blender-multi-version-matrix`. (Moved from `backlog/bugs-found.md` in the 2026-06-20 backlog-drain wave.)

## Photoshop overhaul

- **large-doc collapse-by-default + windowed rendering** - Proscenio characters are flat (the doll is 22 layers), so this is the speculative large-doc tail; UXP has no `react-window` guarantee. **Trigger:** a real Proscenio-scale-or-larger PSD makes the Tags panel painful after the IPC fixes land; re-measure first, since the multiGet reader may make it unnecessary.
