# Spec 036: UI, help and surfaces - TODO

Sequenced from the assessment in [STUDY.md](STUDY.md): 14 rows land now across five PR-sized chunks, one defers, five gate on written triggers, three are proposed for pruning.

## Now

### PR 1 - re-wire the orphaned help topics (blocking)

- [ ] Wire the `sprite_frame_preview` topic into [`_draw_sprite.py`](../../apps/blender/panels/_draw_sprite.py) via the zero-caller [`draw_subbox_header`](../../apps/blender/panels/_helpers.py) above the `Setup Preview` / `Remove Preview` row (feature id + topic `sprite_frame_preview`).
- [ ] Wire the `pose_library` topic onto the `Save Pose to Library` row in [`skeleton.py`](../../apps/blender/panels/skeleton.py) (same subbox-header pattern, or a `?` button on the row).
- [ ] Add a reverse-coverage test to [`test_help_topics.py`](../../tests/test_help_topics.py): every id in `HELP_TOPICS` appears in `panels/` + `operators/` source, so the next restructure cannot orphan a topic silently.

### PR 2 - Reproject UV deterministic projection

- [ ] Replace `bpy.ops.uv.smart_project` in [`uv_authoring.py`](../../apps/blender/operators/uv_authoring.py) with planar projection: detect the dominant mesh plane, map UVs from the bounding box, keep the Front-Ortho U-flip the fixtures author.
- [ ] Drop the Edit-Mode toggle + `select_all` dance the operator no longer needs, and the now-stale limitation prose in the docstring + tooltip.
- [ ] Headless tests: orientation preserved on an XZ quad, idempotent second run; the perf symptom re-check stays in the verification session.

### PR 3 - batched polish pass (one GUI smoke verifies all)

- [ ] Show the selected mesh name in the **Active Sprite** subpanel ([`element.py`](../../apps/blender/panels/element.py)) as a readout row or `draw_header` override.
- [ ] Clamp `frame` to `[0, hframes*vframes-1]` via an update callback in [`object_props.py`](../../apps/blender/properties/object_props.py) (write `self["frame"]` to avoid recursion; reclamp when `hframes` / `vframes` shrink) + headless test.
- [ ] Rename `Initial frame` to `Frame` ([`object_props.py`](../../apps/blender/properties/object_props.py), line 96).
- [ ] Add the centered-vs-PS-origin contrast line to the `active_sprite` topic in [`help_topics.py`](../../apps/blender/core/help_topics.py).
- [ ] Left-align Outliner row labels ([`outliner.py`](../../apps/blender/panels/outliner.py)) with a `alignment="LEFT"` sub-row.
- [ ] Unhide + frame the object on a validation issue click: extend `select_issue_object` in [`selection.py`](../../apps/blender/operators/selection.py) with `hide_set(False)`, `hide_viewport = False`, and `view3d.view_selected` under a WINDOW-region override.
- [ ] Migrate the three local see-also refs ([`help_topics.py`](../../apps/blender/core/help_topics.py) lines 182, 334, 512) to GitHub URLs - this also closes the clickable-refs row, since [`help_dispatch.py`](../../apps/blender/operators/help_dispatch.py) already buttons every `http(s)` ref; flip `test_see_also_references_exist_on_disk` to a URL-shape check.
- [ ] Final mechanical commit: sweep `panels/` for accessors duplicated across modules (`_active_mesh_props` and siblings) and lift the genuinely identical ones into [`_helpers.py`](../../apps/blender/panels/_helpers.py).

### PR 4 - one Help panel

- [ ] Replace the cheat-sheet body of [`help.py`](../../apps/blender/panels/help.py) with a single `Open help` button invoking the existing `proscenio.help` popup; move the operator reference into a help topic.
- [ ] Fold the smoke-test button from [`diagnostics.py`](../../apps/blender/panels/diagnostics.py) into the same panel behind the `debug_mode` poll and delete the Diagnostics module.

### PR 5 - guide-doc rename sweep (docs only, after PRs 3-4 land)

- [ ] Rewrite [`00-basic/02-blender.md`](../../docs/00-guides/00-basic/02-blender.md) and [`01-advanced/02-blender.md`](../../docs/00-guides/01-advanced/02-blender.md) against the shipped IA: `Automesh from Alpha`, the **Mesh Generation** / **Weight Paint** split, the **Element** parent, and this spec's `Frame` rename + Help merge - prose rewrite, not find-replace.

## Deferred

- **Indented Outliner tree** - full bone-parent nesting restructures `filter_items` for modest gain over the shipped category sort + attachment indent; revisit with the w4 outliner wave.
- **Validator sprites-vs-elements rename** - gate: the next change that touches `packages/validator` carries the mechanical `SpritePayload` -> `ElementPayload` rename.
- **Per-locale i18n tables** - gate: first non-English user request or a contributed translation PR; never populate before this spec's copy churn lands.
- **Addon reference screenshots** - gate: panel-layout freeze at the 1.0 tag; any set captured before that goes stale within a release.
- **Docs URL as a preference** - gate: a second docs target appears (spec 024 D3 locked decision).
- **Joystick / slider multi-pose blend** - gate: the first character with parametric facial expressions enters production AND 1D Drive from Bone proves insufficient; design schema-first (`BlendSpace2D` export), widget last.

## Dropped

- **Native header-drag reorder** - sibling top-level panels already drag natively; `bl_parent_id` subpanels are an upstream Blender limit; nothing buildable on our side.
- **Materials panel** - bulk path repair duplicates Blender's `Find Missing Files`; the inspection/bulk-config surface is speculative; if pixel-art blur lands in production the answer is a one-line import-time `Closest` interpolation option, not a panel.
- **Onion-skin overlay** - free extensions (B Onion Skin) already ghost rigged characters and Blender has an open upstream design task; building our own is the spec's largest GUI-test surface for zero pipeline impact.
