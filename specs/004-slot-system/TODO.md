# SPEC 004 — TODO (placeholder)

Real TODO lands once the SPEC's STUDY is fully designed (after SPEC 005 ships and informs the panel-level UX). Sketch below is a parking lot, not a commitment.

## Sketch

- [ ] Promote STUDY from placeholder to a full design pass — answer the Q? items in [STUDY.md](STUDY.md), lock decisions.
- [ ] Define authoring contract on the Blender side: how a Collection-per-slot maps to the schema, default picker, attachment ordering.
- [ ] Implement the importer's slot resolver: parent node + sibling visibility-toggled sprites.
- [ ] Implement `slot_attachment` track wiring in `animation_builder.gd`.
- [ ] Add the "Slots" subpanel to SPEC 005's authoring panel — list edit, default selector.
- [ ] Worked example fixture under `examples/<name>/` with a swappable head (default + 1–2 alternates).
- [ ] Tests: importer asserts slot structure, animation track flips visible on the right sibling.
- [ ] Docs: format-spec slot section moves from "schema-only" to live behavior; godot-plugin-dev gains a "Slots" subsection.
