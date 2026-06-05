# App cleanups - TODO

See [STUDY.md](STUDY.md) for the findings tables and decisions D1-D5 (localized cleanups for Godot and docs - the two apps that passed the structural audit). Blender's reorg is spec 016; Photoshop's re-layout is spec 018.

Each phase is one PR, behavior-preserving, proven by that app's gate. Phases are independent - any order. Godot gate = `gdformat --check` + `gdlint` + `apps/godot/tests/test_importer.gd`. Docs gate = `pnpm build`.

## Decision lock-in

- [x] D1 - cleanup-only scope, no structural reorg.
- [x] D2 - group by app, one PR each.
- [x] D3 - extract shared Godot builder helpers; collapse the `sanitize` shim.
- [x] D4 - delete unused docs assets; rename `withDefs.ts`.
- [x] D5 - leave Godot `reimporter.gd` as-is (explicit non-action).
- [ ] Q1 - Godot `reimporter.gd`: lean keep in place. Confirm in review.

## Phase 1 - Godot builder dedup

- [ ] Extract the shared `_resolve_sprite_texture` into a helper both builders call (a static `resolve_sprite_texture(...)` in a `builders/` helper or a `node_name_util.gd` sibling); call from `polygon_builder.gd:8-29` and `sprite_frame_builder.gd:12-29`.
- [ ] Extract the shared slot parent-resolution into `resolve_sprite_parent(skeleton, sanitized_name, bone_name, slot_map)`; call from `polygon_builder.gd:118-131` and `sprite_frame_builder.gd:92-105` (polygon's `is_skinned` branch stays in the caller).
- [ ] Point `animation_builder.gd:43,158` at `NodeNameUtil.sanitize`; drop the `SlotBuilder.sanitize` shim (`slot_builder.gd:32-33`).
- [ ] Reword the cubic-interpolation comment at `animation_builder.gd:120-123` to match the LINEAR-default + CUBIC-for-transforms code; remove the stray `#.` at `animation_builder.gd:142-144`.
- [ ] Q1: leave `reimporter.gd` in place (or add a one-line backlog pointer if review prefers).
- [ ] Gate green.

## Phase 2 - Docs tidy

- [ ] Delete `apps/docs/static/img/undraw_docusaurus_mountain.svg`, `undraw_docusaurus_react.svg`, `undraw_docusaurus_tree.svg`, `docusaurus.png` (keep `favicon.ico`, `logo.svg`, `docusaurus-social-card.jpg`).
- [ ] Rename `apps/docs/src/schema/withDefs.ts` -> `with-defs.ts`; update the 6 `@site/src/schema/withDefs` imports under `docs/content/**` (the exported `withDefs` function name is unchanged).
- [ ] Gate green (`pnpm build`).

## Out of scope

No structural reorganization (these apps passed); no Photoshop (spec 018) or Blender (spec 016); no behavior change; no schema or `format_version` bump.
