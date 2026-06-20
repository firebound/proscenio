# Spec 055: Re-import contract

What survives a re-import is a core promise the pipeline makes at two stages (Photoshop manifest into Blender, Blender export into Godot), and the promise currently disagrees with the code at both. The documentation says a manifest re-import loses painted weights, while the code reprojects them from a surviving sidecar. The Photoshop importer rebuilds the armature on every run, against a doc claim that rotation, parenting, and weights survive. The Godot reimporter is an empty stub whose header promises a diff/merge that never happens. This spec settles the contract, then aligns code and docs to it.

This spec is STUDY-first: scaffolded ahead of the decisions, because each item is a "which side is the truth" call before any code moves. Measure both sides before assuming either is right. The TODO lists the candidate work per outcome; the actual rows are written once the contract is locked.

## Scope

- Decide and document what survives a Photoshop manifest re-import (painted weights, armature, parenting), then make the code match.
- Decide whether the Photoshop importer should keep rebuilding the armature every run, or reuse the existing one.
- Decide whether to build the non-destructive Godot reimporter (diff/merge preserving user edits) or to drop the claim and document the wrapper-scene pattern as the supported path.

## Open questions (resolve before coding)

- Photoshop re-import weights: does the current sidecar reprojection mean weights now survive a placement-changing re-import, making the "loses weights" doc stale, or is the reprojection an unintended regression of the three deliberately distinct weight operations? Measure the round-trip first.
- Photoshop re-import armature: does `build_root_armature` running every import actually destroy rotation / parenting / weights, or do they survive by reconstruction? Verify before correcting the doc or the code.
- Godot reimporter: is the non-destructive diff/merge worth building, or is the wrapper-scene instancing pattern the honest supported path? This is the heavy product call.

## Sources

Drains the "Re-import de PSD: doc diz perde weights, codigo reprojeta" and "Re-import always rebuilds the armature" items from [`backlog-bugs-found.md`](../backlog-bugs-found.md), and the "Non-destructive reimporter is an empty stub" decision from [`backlog-godot-importer.md`](../backlog-godot-importer.md). The `FLOW-REIMPORT-WEIGHTS-01` walk in the QA Companion checklist cannot be an oracle until this lands.
