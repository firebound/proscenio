# Spec index

Durable map of every spec: number to topic. Spec folders are pruned once the work ships - the content stays in git history; this index keeps the human-readable record so a pruned number never loses its identity. The `_` prefix sorts it above the numbered folders.

Recover a pruned spec's full text from history:

```sh
git log --all --diff-filter=A -- 'specs/NNN-*/STUDY.md'   # find the slug + add commit
git show <commit>:specs/NNN-slug/STUDY.md
```

`002` was reused for two unrelated specs (a numbering quirk that history preserves); there is no `001`.

The 027-035 wave was pruned together on 2026-06-11 (PRs #104-#113): the resolved work left the backlogs, the not-now work moved to [deferred.md](deferred.md) / [gated.md](gated.md) / [dropped.md](dropped.md), and the locked calls landed in [decisions.md](decisions.md). Per-spec PR mapping: 027 #104, 028 #105, 029 #106, 030 #107, 031 #108, 032 #109, 033 #110, 034 #111, 035 #112 / #113.

Spec 039 was pruned 2026-06-15 (PR #116): the examples open, texture, render and animate faithfully - wrapper script paths, texture import-order, the in-plane bone convention, skinned-sibling render, rest-pose geometry bake and the rest-matrix animation builder all shipped. The remaining test-infra item (point test-godot at the real baked goldens, retire the drifting hand-authored mixed_feature copy) moved to [deferred.md](deferred.md).

Spec 041 was pruned 2026-06-13 (PR #115): the plugin fixes shipped, the multiGet reader + shared-adaptation dedup moved to [deferred.md](deferred.md), the large-doc windowing to [gated.md](gated.md), and the locked calls to [decisions.md](decisions.md).

Spec 040 was retired 2026-06-13: it was a one-time automatic pass that mapped the whole product's manual-test surface, so its two outputs are living data rather than a prunable plan. The walkable surface lives in the QA Companion tool ([tools/qa-companion/checklist/](../tools/qa-companion/checklist/)); the code-read audit (`findings.md`) was triaged and retired on 2026-06-15 - real code issues to the bug backlogs, doc/help-text gaps to [backlog-docs.md](backlog-docs.md), the rest dropped. See [decisions.md](decisions.md).

Specs 043-048 (the 2026-06-16 polish sprint) were pruned together 2026-06-18 after a per-spec audit confirmed each shipped with implementing code, behavior-locking tests, and a CI step (the deferred remainders moved to [deferred.md](deferred.md) / [gated.md](gated.md), the locked calls to [decisions.md](decisions.md), and the resolved backlog issues left [backlog.md](backlog.md)). 043 outliner-selection: viewport-follow + stale-row crash guard + single native search + the shared identity-to-index resolver (PRs #119-#123, #125). 044 weight-paint-mode-sync: modal-timer mode exit, stroke-end overlay refresh, Proximity bind params, clear-empty-vgroups; override-list scroll + named snapshots stayed in the backlog. 045 skeleton-quick-armature: labels-only Quick Armature chords, picker-driven assign-action, skeleton chrome; destructive Esc cancel gated. 046 slots-list-ux: native slot `template_list` + custom-draw attachment column + attach-via-picker; the synced-CollectionProperty backing gated. 047 godot-import-verify (PRs #127-#132): texture-gated sprite region + the four baked-golden regression guards + two model-quirk doc notes; the generic eight-golden walk stays a partial in [deferred.md](deferred.md). 048 photoshop-read-perf (PR #133): async multiGet document reader behind a DOM-walk fallback + busy-flag re-render scope; the single shared snapshot per tick stayed deferred.

Spec 042 was pruned 2026-06-16 (PR #117): the slot bone-follow slice shipped complete - the Bind / Unbind operators (object-parent + a Child Of constraint that cancels the bone rest + the `slot_bone` field), `create_slot` migrated off real bone-parenting, the shared resolver reading `slot_bone`, legacy bone-parent normalization on bind and unbind, and the `mixed_feature` + `slot_swap` fixtures authoring the constraint. Nothing was deferred or gated - the STUDY's four items were all "now" and all shipped; the locked calls landed in [decisions.md](decisions.md).

| # | Spec | Summary | Status |
| --- | --- | --- | --- |
| 000 | initial-plan | Initial plan: what Proscenio is, settled vs open decisions; drove the Phase 0 to Phase 1 work | pruned |
| 002 | reimport-merge | Godot reimport without clobbering user work (scripts, child nodes, in-editor animations) | pruned |
| 002 | spritesheet-sprite2d | Sprite2D / spritesheet render path for frame-by-frame pixel art and effect sprites | pruned |
| 003 | skinning-weights | Per-vertex skinning weights + `Polygon2D.skeleton` wiring (deformable cutout) | pruned |
| 004 | slot-system | Named attachment slots that swap one of N sprites at runtime | pruned |
| 005 | blender-authoring-panel | Blender sidebar authoring panel replacing raw Custom Properties | pruned |
| 006 | photoshop-importer | Photoshop to Blender importer (auto mesh + armature from the manifest) | pruned |
| 007 | testing-fixtures | Test fixtures: the 1-sprite-1-PNG path + real `sprite_frame` animation coverage | pruned |
| 008 | uv-animation | UV animation tracks (scrolling textures, water, gradient sweeps); stub, never greenlit | pruned |
| 009 | code-modularity | Structural-quality audit: god-modules, mixed responsibility, DRY/SRP, behavior-preserving reorg | pruned |
| 010 | photoshop-uxp-migration | Migrate the Photoshop plugin from ExtendScript JSX to UXP (React) | pruned |
| 011 | photoshop-tag-system | Explicit per-layer tag system + tagging UI (replaces name inference) | pruned |
| 012 | quick-armature-ux | Quick Armature operator UX overhaul (preview, lifecycle, Front-Ortho snap) | pruned |
| 013 | weight-paint-automesh | Weight-paint ergonomics + automesh (alpha trace); survey of 9 cutout tools | pruned |
| 014 | typed-models-codegen | Typed domain models as the source of truth + codegen + living docs | pruned |
| 015 | monorepo-packages | Repo restructure into an apps/ + packages/ split | pruned |
| 016 | blender-app-system-organization | Layer-first reorg: `_shared/` infra tier, per-system subpackages, god-module splits | pruned |
| 017 | app-cleanups | Localized Godot + docs cleanups (builder dedup, dead assets); the two apps that passed the audit | pruned |
| 018 | photoshop-web-app-layout | Re-layout the Photoshop src into api/lib/hooks/components/panels/utils (web-app shape) | pruned |
| 019 | naming-consistency | The `Element` vocabulary: mesh to Polygon2D, sprite to Sprite2D, full wire rename | pruned |
| 020 | test-coverage | Coverage lift 36% to 88.8%, Sonar gate green; host mocks + in-Blender instrumentation | pruned |
| 021 | blender-ui-audit | Reconcile UX feedback against code, per-tool audit, bucket findings into specs (discovery) | pruned |
| 022 | blender-ui-restructure | 13-panel sibling tree: flatten the root, accordion subpanels, warn-not-hide, debug_mode | pruned |
| 023 | blender-help-docs-i18n | Per-subpanel help, online doc links, Godot badge icon, i18n mechanism | pruned |
| 024 | blender-addon-preferences | Addon preferences: log level (errors/info/debug), debug_mode, Developer group | pruned |
| 025 | code-duplication | Type-2/3/4 clone audit (AST + k-gram, beyond Sonar's line scan); ~30 single-source helpers extracted across two PRs, justified divergences (N9/N12/N14/D6) kept | pruned |
| 026 | documentation-architecture | Knowledge-home map: audience-driven Docusaurus re-IA, comment/docstring routing policy (~2,900 audited), codified in `.ai/` with enforcement | pruned |
| 027 | export-correctness | Output integrity: writer respects the armature picker, whole-mesh export, validator slot-noise + CP-read fixes | pruned |
| 028 | schema-expressiveness | Format v2: appearance / track / constraint passthrough end to end, plus the migration path | pruned |
| 029 | mesh-authoring | Automesh interactive fix + mesh-generation panel gating, defaults, and manual hull | pruned |
| 030 | skinning-weight-paint | Weight-paint bind fixes, panel cleanup, and the advanced skinning toolset | pruned |
| 031 | rigging-and-posing | Quick Armature, skeleton, drivers, IK, and pose-library authoring | pruned |
| 032 | slot-attachments | Slot placement fixes + slots panel, warnings, and skin coordination | pruned |
| 033 | atlas-packing | Atlas authoring + packing heuristics + pixels-per-unit through the pipeline | pruned |
| 034 | photoshop-plugin | PS tag-system features + export-roundtrip stability | pruned |
| 035 | project-health | CI matrix, lint / type / coverage gates, fixtures, and release packaging | pruned |
| 036 | ui-help-surfaces | Editor UI polish, help/docs system, and new panels (materials, onion-skin) | planned |
| 037 | storage-split | Collapse dual PG-vs-CP storage to one canonical home per field (1.0.0) | planned |
| 038 | reach | Additional DCC exporters (Krita, GIMP) and the GDExtension escape hatch | planned |
| 039 | example-fidelity | Example pipeline fidelity: wrapper script paths, texture import-order, in-plane bones, skinned-sibling render | pruned |
| 040 | end-to-end-verification | Automatic pass mapping the whole manual-test surface (452 items) + a code-read audit (176 findings); both now owned by the QA Companion tool (`tools/qa-companion`) | retired |
| 041 | photoshop-overhaul | Make the UXP plugin usable: null-crash fix + export-writer resilience (the 040 trigger), layerID targeting, adaptive poll, debug toggle; multiGet + dedup deferred | pruned |
| 042 | slot-bone-follow | Slot bone-follow authoring parity: a Bind Slot to Bone operator (Child Of + slot_bone), create_slot migrated off bone-parenting, resolver reads slot_bone, fixtures author the constraint | pruned |
| 043 | outliner-selection | Outliner follows the viewport selection, no crash on stale rows, single native search | pruned |
| 044 | weight-paint-mode-sync | Edit Weights tracks the weight-paint mode; expose the Proximity bind params in the panel | pruned |
| 045 | skeleton-quick-armature | Quick Armature Esc cancels properly, Animation uses the picked armature, Skeleton chrome polish | pruned |
| 046 | slots-list-ux | Native searchable slot/attachment lists (reusable list component) + attach-to-existing-slot picker | pruned |
| 047 | godot-import-verify | Verify the sprite manual-region scaling with a test + two model-quirk doc notes | pruned |
| 048 | photoshop-read-perf | Tag-list busy-flag scoping + a batchPlay multiGet document reader | pruned |
