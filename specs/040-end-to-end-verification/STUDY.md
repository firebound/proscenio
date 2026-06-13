# Spec 040: End-to-end verification

A standing, exhaustive manual-test surface for the whole pipeline: every option, field,
button, and feature across the three apps, plus the cross-app flows that string them
together. The trigger was a real run that hit a wall - the Photoshop plugin could not
export a manifest at all - and the realization that no artifact enumerates *everything a
human should click and confirm* before a release. Spec 039 did this for the Godot example
pipeline; this spec generalizes it to the entire product surface.

The work has two outputs, derived from the same pass:

1. **A durable, re-runnable manual-test checklist** - the artifact a human walks before a
   release tag, checking items off. Supersedes the flat [manual-testing.md](../manual-testing.md);
   its items fold in here.
2. **Audit findings** - every place the documented *intent* and the implemented *reality*
   diverge (doc says X, code does Y / documented-but-unimplemented / undocumented control /
   dead widget / suspected bug). These promote to [backlog-bugs-found.md](../backlog-bugs-found.md)
   (still-broken) the moment a failure carries a repro.

## Scope

Every user-reachable interaction, audited against its documented intent:

- **Blender addon** - 11 sidebar panels + Diagnostics + Help, their subpanels, every
  field / toggle / button, ~40 operators (Quick Armature, automesh one-click + interactive
  modal, the five bind modes, Edit Weights modal, slots, atlas pack/unpack/apply,
  drivers/IK, pose library, import, export), addon preferences, and modal-overlay behavior.
- **Photoshop UXP plugin** - the Exporter / Tags / Validate / Debug panels and their
  sections (Folder, Import, Export, Reexport, RevealOutput, Migration, Tags, Validate, Doc,
  Debug), the tag vocabulary, and the export -> manifest + PNG path.
- **Godot plugin** - import / reimport, the five builders, wrapper-scene safety, and the
  committed example fixtures.
- **Cross-app flows** - the full PS -> Blender -> Godot roundtrips (doll, slot_swap,
  slot_cycle, atlas_pack, a PSD-sourced fixture).

### Intent oracle

`docs/` mirrors the surface almost 1:1, so each item is checked against a documented
intent, not just "does it not crash":

- [docs/02-blender-addon/](../../docs/02-blender-addon/) - one page per panel = the Blender intent oracle.
- [docs/03-photoshop-plugin/](../../docs/03-photoshop-plugin/) + [advanced PS guide](../../docs/00-guides/01-advanced/01-photoshop.md) - PS intent + tag vocabulary.
- [docs/04-godot-plugin/](../../docs/04-godot-plugin/) - Godot intent.
- [docs/00-guides/](../../docs/00-guides/) - the end-to-end flow oracle for the cross-app scripts.

The audit method per surface: read the doc page (**intent**) and the panel / operator code
(**reality**), emit a test item for every control, and flag every divergence as a finding.

## The checklist format (canonical)

The checklist is **hybrid**: dense tables for simple widgets, blocks for rich operators,
numbered scripts for flows. Every fan-out agent and every future contributor follows this
legend so the surface stays uniform.

### IDs

`<APP>-<SURFACE>-<NN>` - stable, so a failure can be cited from
[backlog-bugs-found.md](../backlog-bugs-found.md).

- **APP:** `BL` Blender · `PS` Photoshop · `GD` Godot · `FLOW` cross-app.
- **SURFACE:** short uppercase token per panel / section (e.g. `SKEL`, `ELEM`, `MESH`,
  `WPAINT`, `ATLAS`, `EXPORT`, `TAGS`, `IMPORT`, `BUILD`, `DOLL`). The per-app checklist
  file fixes its own token table at the top.
- **NN:** zero-padded sequence within the surface.

### Status vocabulary

`pending` · `pass` · `fail` · `blocked` · `n/a` · `regressed`

- `fail` / `regressed` MUST carry a one-line repro and cross-link a row in
  [backlog-bugs-found.md](../backlog-bugs-found.md).
- `n/a` is for `planned` / `out-of-scope` controls (the addon's own badge taxonomy):
  documented as not-yet-real, so they are listed but not expected to pass.
- `blocked` = cannot test because an upstream item fails (cite the blocking ID).

### Item shapes

**Simple widget** (toggle, field, read-only label) - one table row:

```
| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-ELEM-01 | Type: Polygon2D / Sprite2D | switching reveals the matching field group | 02-element.md#type | panels/element.py | pending |
```

**Rich operator** (modal, multi-step, side effects) - a block:

```
#### [ ] BL-SKEL-03 · Quick Armature
- **Intent:** draw bones head->tail in the viewport (docs: 04-skeleton.md#quick-armature)
- **Code:** operators/armature/quick_armature.py
- **Pre:** an armature is the active object; Object Mode
- **Steps:** 1. N-panel > Skeleton > Quick Armature  2. drag head->tail  3. ESC to cancel mid-draw
- **Expect:** preview line tracks the cursor; release creates a Front-Ortho-aligned Bone2D; ESC leaves no leaked draw handler
- **Status:** pending
```

**Cross-app flow** - a numbered script with a checkpoint per step:

```
### [ ] FLOW-DOLL-01 · doll  PS -> Blender -> Godot
- **Pre:** doll.psd open in Photoshop; a clean apps/godot project
1. PS: Export panel > Export        -> manifest + per-layer PNGs land in the output folder
2. Blender: Pipeline > Import manifest -> planes + a root bone appear; textures resolve
3. ... 
- **Expect (end state):** the Godot scene renders the textured, rigged character; no missing-dependency dialog
- **Status:** pending
```

### Findings section

Each checklist file ends with a Findings table for divergences surfaced during the audit:

```
| ID | Type | Sev | Control | Detail | Code |
| --- | --- | --- | --- | --- | --- |
```

Types: `drift` (doc != code) · `undocumented` (control with no doc) · `unimplemented`
(doc describes a feature with no code) · `dead` (control wired to nothing) ·
`suspected-bug` (reproduces wrong). High-sev findings with a repro promote to
[backlog-bugs-found.md](../backlog-bugs-found.md).

## Method

The inventory is built by a fan-out: one agent per surface unit reads its doc page + its
panel / operator code, classifies each control (widget vs operator vs flow-step), and
emits items + findings in the format above. Per-app assemblers render the checklist files;
the cross-app flows are synthesized from the basic guides plus the assembled inventory. The
[README dashboard](README.md) rolls up counts and the failing / blocked roster.

## Relationship to other specs

- **039 (example-fidelity)** seeded the idea on the Godot side; its `manual-testing.md`
  Godot items map into [checklist/godot.md](checklist/godot.md) and [checklist/flows.md](checklist/flows.md).
- **036 (ui-help-surfaces)** owns several already-known Blender UI bugs in
  [backlog-bugs-found.md](../backlog-bugs-found.md); this audit references them rather than
  re-filing.
- The surviving [manual-testing.md](../manual-testing.md) "fix shipped, smoke pending"
  items are absorbed as `pending` rows here, tagged with the PR that shipped the fix.
