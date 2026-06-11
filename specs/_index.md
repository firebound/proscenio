# Spec index

Durable map of every spec: number to topic. Spec folders are pruned once the work ships - the content stays in git history; this index keeps the human-readable record so a pruned number never loses its identity. The `_` prefix sorts it above the numbered folders.

Recover a pruned spec's full text from history:

```sh
git log --all --diff-filter=A -- 'specs/NNN-*/STUDY.md'   # find the slug + add commit
git show <commit>:specs/NNN-slug/STUDY.md
```

`002` was reused for two unrelated specs (a numbering quirk that history preserves); there is no `001`.

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
| 027 | export-correctness | Output integrity: writer respects the armature picker, whole-mesh export, validator slot-noise + CP-read fixes | planned |
| 028 | schema-expressiveness | Format v2: appearance / track / constraint passthrough end to end, plus the migration path | planned |
| 029 | mesh-authoring | Automesh interactive fix + mesh-generation panel gating, defaults, and manual hull | planned |
| 030 | skinning-weight-paint | Weight-paint bind fixes, panel cleanup, and the advanced skinning toolset | planned |
| 031 | rigging-and-posing | Quick Armature, skeleton, drivers, IK, and pose-library authoring | planned |
| 032 | slot-attachments | Slot placement fixes + slots panel, warnings, and skin coordination | planned |
| 033 | atlas-packing | Atlas authoring + packing heuristics + pixels-per-unit through the pipeline | planned |
| 034 | photoshop-plugin | PS tag-system features + export-roundtrip stability | planned |
| 035 | project-health | CI matrix, lint / type / coverage gates, fixtures, and release packaging | planned |
| 036 | ui-help-surfaces | Editor UI polish, help/docs system, and new panels (materials, onion-skin) | planned |
| 037 | storage-split | Collapse dual PG-vs-CP storage to one canonical home per field (1.0.0) | planned |
| 038 | reach | Additional DCC exporters (Krita, GIMP) and the GDExtension escape hatch | planned |
