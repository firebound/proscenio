# SPEC 004 — Slot system (sprite swap)

Status: **placeholder**, not yet designed. Tracked here so it does not get lost.

## Problem (sketch)

A "slot" is a named attachment point that can present one of N sprites at a time, switched at runtime — head expressions (normal/angry/dead), equipment swaps (sword/staff/empty), weapon variants. The schema already defines the shape:

- `slots: [{name, bone, default, attachments[]}]`
- Track type `slot_attachment` with key data `attachment` (sprite name)
- Importer ignores the field today.

## Why this is a placeholder

SPEC 005 (Blender authoring panel) lands first. Slots without a UI to manage them are painful to author through Custom Properties alone, and any attempt at a CLI/text authoring contract for slots would be retrofitted as soon as the panel exists.

## Sketch of expected design (will be re-evaluated when work begins)

- **Godot side**: a slot is a parent node holding sibling sprites; the `slot_attachment` track flips `visible` on each child. No new node type — leverages built-in `visible` property and the existing animation builder.
- **Blender side**: a Collection per slot, with the collection's children being the candidate attachments. The default attachment is identified by a Custom Property or by being the only visible one at export time.
- **Authoring**: SPEC 005's panel gains a "Slots" subpanel — list editing, default picker, attachment ordering.
- **Animation**: `slot_attachment` track in the schema already has `attachment: string` per key. Builder reads, finds the named child of the slot, switches `visible`.

## Out of scope (current sketch)

- Skin systems beyond a flat slot list (Spine has skins, themes — not v1 territory).
- Procedural / runtime attachment generation.
- Slot-aware skinning (a swappable head with its own weights vs the default head's weights). Tracked: see SPEC 003 successor considerations.

## Open questions to resolve when work begins

The list below is opening notes, not locked. Each will be revisited and answered as part of the real STUDY pass.

- Q? — How does the importer represent a slot in the generated scene? Pure node hierarchy (parent + sibling sprites) or a metadata-only tag?
- Q? — How are slot defaults expressed at import time? Default-visible-on-init vs a slot resource with a "current" property?
- Q? — Does a slot's `bone` have to match all of its attachments' `bone`? Probably yes for sanity; document.
- Q? — How does the wrapper-scene pattern (SPEC 001) interact with slot edits? Can the user drive slots from `Effect.gd`-style scripts cleanly?
- Q? — Does SPEC 003 skinning compose with slots? Each attachment can carry its own `weights`; verify the importer handles per-attachment skeleton wiring.

## Successor considerations

- A future "armor / skin" system that swaps multiple slots in lockstep is conceivable. Stay aware but do not couple SPEC 004 to it.
- Animation events / method tracks (backlog) and slot transitions are independent but commonly co-author cues.
