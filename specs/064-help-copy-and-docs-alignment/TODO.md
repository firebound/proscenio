# Spec 064: Help copy and docs alignment - TODO

Candidate work, pending the STUDY calls. The geometry fix and the coverage test are objective and land first; the copy rewrite and the docs deepening ride the locked contract. Code lands in a branch + PR; the docs-site pages commit direct to main per the docs convention.

## PR 1 - reconcile popup geometry (objective, code)

- [ ] In `core/help_topics.py:33-40`, introduce `_PX_PER_CHAR` and derive `POPUP_WIDTH = POPUP_WRAP_CHARS * _PX_PER_CHAR + padding` so the drawn width is always the wrapped extent (Decision 1, option C). Pick the wrap budget so the popup hugs the text at default UI scale; re-tune after the copy rewrite settles body length.
- [ ] Core unit test (bpy-free): assert `POPUP_WIDTH` tracks `POPUP_WRAP_CHARS` through the constant, and that no reflowed line of any registered topic exceeds the wrap budget.

## PR 2 - exact-mirror coverage test and the mapping fixes (objective, code)

- [ ] Add the two-way coverage test enforcing the exact mirror (Decision 3, option A): every panel `?` maps to the bare panel page; every subpanel `?` maps to `<parent-page>#<subpanel-anchor>`; every panel-page H2 has a subpanel topic and vice versa; every doc path resolves to a real page or anchor in `docs/02-blender-addon/`; the page set equals the panel set exactly (no extra pages, no missing ones). Extend the existing spec-036 reverse-coverage test rather than adding a parallel one.
- [ ] Map `pipeline_overview -> pipeline` (it is the Pipeline panel's own topic) and `sprite_bone_parent -> element#attach-to-bone` (section already exists) in `_DOC_PATHS`; point `status_legend -> index#status-badges`.
- [ ] Re-point `validation -> pipeline#validate` after the page fold (see DOCS).
- [ ] Resolve `pose_library` and `sprite_frame_preview` per Decision 5: anchor `pose_library` inside `skeleton#pose-mode` (in-section anchor, not a sibling H2), and decide `sprite_frame_preview` (in-section anchor versus `bl_description`) once its body weight is visible in PR 3.

## PR 3 - rewrite the help copy to the two-tier contract (pending Decision 2; code)

- [ ] Add the shape test first: panel topics carry `sections = ()` and stay under the body-length budget; no subpanel body repeats its parent's summary (Decision 2, option A).
- [ ] Rewrite the ten panel topics to one overview paragraph each (intent + pipeline stage), dropping their `sections` and relying on the `Open online docs` link for depth.
- [ ] Rewrite the subpanel topics to one focused summary plus at most one tight section, scoped to that subpanel's own controls, referencing the parent by name only.
- [ ] Apply the terminology guard: `Element` vocabulary (not legacy `Sprite`), the three weight operations kept distinct, the lone `import_photoshop` GitHub URL folded into the doc page and out of `see_also`.

## PR 4 - i18n-stable string structure (pending Decision 4; code)

- [ ] Author each rewritten body as one whole-string msgid with a stable translation context (the topic id); no sentence built by f-string concatenation.
- [ ] Route the popup draw and panel labels through the existing `core/i18n.py` translation lookup so a populated table would take effect; leave `TRANSLATIONS` empty.
- [ ] Update the [`gated.md`](../gated.md) `i18n-locale-tables` trigger to record that the copy-churn prerequisite (spec 064) is met and a locale can be populated on first non-English request.

## DOCS (direct to main, not a PR) - mirror the panel tree exactly

- [ ] Fold `09-validation.md` into `pipeline.md` as the `## Validate` section between `## Import` and `## Export`; its two H2s (`Errors block the export`, `Warnings inform but still export`) demote to H3 under it. Remove the standalone page and its `sidebars.ts` entry; add a redirect from the old `blender-addon/validation` slug.
- [ ] Confirm the page set equals the ten panels plus index exactly: `pipeline`, `outliner`, `element`, `slots`, `skeleton`, `mesh-generation`, `weight-paint`, `animation`, `atlas`, `helpers`, `index` (About). No other pages.
- [ ] Confirm every subpanel owns one H2 section under its parent page (Element / Skeleton / Weight Paint / Mesh Generation / Slots already match; Pipeline gains `#validate`); anchor `pose_library` inside `skeleton#pose-mode`.
- [ ] Deepen the thin panel-only pages (`outliner.md`, `animation.md`, `atlas.md`, `helpers.md`) with the worked detail the popups now omit.
- [ ] Make the index `#status-badges` the single canonical badge legend and point the status icons at it.
- [ ] Verify every anchor the rewritten `_DOC_PATHS` targets resolves (the coverage test from PR 2 gates this).

## Close-out

- [ ] Post-impl cleanup: prune this spec into [`_index.md`](../_index.md), move the locked calls to [`decisions.md`](../decisions.md), confirm the gated trigger rewrite, and update the QA Companion checklist for the new help-copy and doc-link surface.
