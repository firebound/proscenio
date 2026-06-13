# Spec 040: End-to-end verification - TODO

Build the exhaustive manual-test surface defined in [STUDY.md](STUDY.md), then keep it
green. The inventory is built once by fan-out; the checklist is then walked by a human each
release and maintained as the surface changes.

## Now

### Build the inventory (fan-out, one pass)

- [x] Inventory every surface unit against its doc page: emit hybrid-format items
      (table / block / flow-script) into the four checklist files. One agent per panel /
      section reads intent (docs) + reality (code) and classifies each control.
      _Done 2026-06-13: 452 items, 176 findings (10 high-sev) via the spec-040-inventory fan-out._
  - [ ] [checklist/blender.md](checklist/blender.md) - Outliner, Element, Slots, Skeleton, Mesh Generation, Weight Paint, Animation, Atlas, Validation, Pipeline, Helpers, Diagnostics, Help, Preferences.
  - [ ] [checklist/photoshop.md](checklist/photoshop.md) - Exporter (Folder / Import / Export / Reexport / RevealOutput), Tags, Validate, Migration, Doc, Debug, tag vocabulary.
  - [ ] [checklist/godot.md](checklist/godot.md) - import / reimport, the five builders, wrapper-scene safety, fixtures.
  - [ ] [checklist/flows.md](checklist/flows.md) - the cross-app roundtrips (doll, slot_swap, slot_cycle, atlas_pack, a PSD fixture), synthesized from the basic guides + the assembled inventory.
- [ ] Fold the surviving [manual-testing.md](../manual-testing.md) items in as `pending`
      rows tagged with the PR that shipped the fix; then retire that file (pointer to here).
- [ ] Roll up the [README dashboard](README.md): per-app totals, % done, and the
      failing / blocked roster.

### Triage the audit findings

- [ ] File the **Photoshop manifest-export failure** (the spec trigger) into
      [backlog-bugs-found.md](../backlog-bugs-found.md) with a repro once the exact failure
      mode is captured.
- [ ] Promote every high-severity finding (drift / suspected-bug / dead control) with a
      repro into [backlog-bugs-found.md](../backlog-bugs-found.md); leave low-sev
      drift / undocumented / unimplemented notes in each checklist file's Findings table.

## Recurring

- [ ] Walk the checklist before each release tag; a `fail` here is a blocking bug.
- [ ] When a panel / operator / section is added or changed, add or update its items in the
      same PR (the checklist is part of the surface's contract, like its doc page).

## Deferred

- Automatable subsets: items whose expected result a headless assert _could_ check
  (structural counts, validator output) are candidates to migrate from manual to CI later.
  Out of scope for the first pass - the goal now is complete human coverage, not automation.
