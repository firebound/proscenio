# IA redesign - plan + evaluation (working notes)

Maintainer's restructure plan (captured verbatim-intent) plus a critical pass. This is brainstorming scratch, not the final spec. Forks marked **[FORK]** need a decision before the design locks.

## Plan (maintainer intent)

Global:

- **G1 - accordion subpanels.** Every area/group is a collapsible subpanel (`bl_parent_id` child), like native `View > View Lock`. The sections inside a tool (Mesh/Sprite, Texture Region, Drive from Bone) become real subpanels, not boxes.
- **G2 - drop contextual hiding.** Panels no longer vanish on the wrong selection. Default: show the panel with a clear "why this is inactive" warning. Hiding becomes an opt-in in the addon preferences (off by default).
- **G3 - addon preferences.** Expose info-log level (debug / errors / info) and the contextual-hiding toggle in Blender's addon prefs.
- **G4 - help everywhere.** Every panel + subpanel carries a brief, direct tooltip and a godot/blender indicator, each linking to the official Proscenio docs. A single project file feeds the doc links as `site + path` (no per-tool docs exist yet).

Per tool: Active Element (warn instead of hide; Type isolated selector + per-type body; drop the weight-paint box for an inline warning; show manual region options). Slots (rename from Active Slot; always visible; list all slots clickable; Create Slot moves here; Active Slot becomes a contextual subpanel). Skeleton (armature selector reads as project-wide; Armature subpanel shows hierarchy + connected/relative-parent flags, drop length, add bone-collections mgmt; Pose Mode subpanel always visible with a warning; Quick Armature grouped; fix the no-armature-blocks-create bug). Mesh Generation (rename from Skinning; warn instead of hide; Interior Mode isolated; "Automesh from Sprite" -> "from Alpha"; elevate any skinning-global options; rename the modal entry for parity; Debug off unless debug mode). Weight Paint (NEW; all weight features here). Outliner (promote to top level). Animation (ok). Atlas (ok; mapped features pending). Helpers (Preview Camera moves here). Validation+Export (split: Validation subpanel = issues + Validate button; Export subpanel = import + export + re-export). Help (keep; add per-operator tooltips; isolate descriptions for reuse + i18n). Diagnostics (only in debug mode).

## Strengths (keep)

- **Warnings over hiding (G2).** Directly fixes a real bug: today you cannot select a mesh to add to a slot because the Active Slot panel vanishes on mesh selection. Discoverability win.
- **Slots always-visible + list + Create Slot here.** Closes that bug end to end and gives a project overview the inventory showed was missing.
- **Project-wide armature selector made obvious.** It already drives Skeleton + Skinning; surfacing that scope is honest.
- **"Automesh from Alpha" rename.** Accurate - it traces the alpha contour, not "the sprite". Removes a real misnomer.
- **Weight Paint as its own panel + the sprite question.** Correct domain reasoning (see Answers).
- **Debug-gated UI (Debug Pipeline, Diagnostics).** Hides power-user noise behind the same debug pref as the log level. Coherent.
- **Validate button in the Validation panel.** Fixes a standing backlog item (button currently lives in Export).
- **i18n: isolate strings first, translate later.** Right sequence; Blender supports it (see Answers).

## Tensions and recommendations

1. **[FORK] Doc links to docs that do not exist yet (G4).** Linking every tooltip to per-tool docs that are unwritten ships dead links. But inline help already exists (`core/help_topics.py` has explanations + see-also). Recommendation: the registry maps `feature_id -> {site, path}`; the `?` popup shows the inline explanation NOW and reveals an "Open online docs" button only when the path is set. Inline help works day one; online links light up as pages land. Reuse/extend `help_topics.py` rather than starting fresh.
2. **Tooltip cannot carry a clickable link.** Blender tooltips are plain strings. "Every tooltip links to docs" has to split: tooltip = brief one-line hover (the field/panel description); the LINK lives in the `?` popup (which can hold buttons). So the contract is "every panel/subpanel has (a) a brief tooltip AND (b) a `?` that opens the doc", not "the tooltip is a link".
3. **[FORK] Where does Bind live after Weight Paint splits off?** With weight features moving out, "Mesh Generation" = automesh only, and Bind (which creates the initial weights) is orphaned. Recommendation: Bind belongs in **Weight Paint** (bind is the precursor to painting). Then Mesh Generation = pure automesh (one-shot + interactive + debug), Weight Paint = Bind + Edit + Snapshot + Sidecar IO + Transfer. Cleaner two-panel story than leaving Bind in Mesh Generation.
4. **[FORK] Active Element nesting depth.** "Type subpanel with Mesh/Sprite nested as children" is three levels deep (Panel > Type subpanel > per-type body). Native tops out at two (View > View Lock). Recommendation: Type selector isolated at the panel top + ONE "Body" subpanel that swaps Mesh/Sprite content by type = two levels. Less indentation, same outcome.
5. **[FORK] Contextual-hiding as an addon pref may be YAGNI.** The warning-instead-of-hide default is the win. The user-pref to re-enable hiding adds a toggle every panel must honor. Recommendation: ship always-show-with-warning; add the hide pref only if a power user asks. Keeps the prefs to just log level + debug for v1.
6. **Reorder vs collapse caveat.** Top-level panels in a tab are user-drag-reorderable; subpanels (`bl_parent_id`) are collapsible but NOT drag-reorderable (their order is registration / `bl_order`). So accordion = yes; "drag to reorder inside a panel" = no. Set a sensible default order; do not promise in-panel reorder.
7. **Elevating "skinning-global" automesh options - verify first.** The automesh props all live on `scene.proscenio.skinning`, but they are automesh parameters (resolution, alpha threshold, contour, interior fill). `interior_mode` is the genuine master toggle and is a fine isolated selector. `density_under_bones` / `bone_radius` / `bone_factor` are interior-fill params tied to the picker armature - they read as automesh-internal, not skinning-global. Recommendation: elevate `interior_mode` only; keep the rest inside the Automesh subpanel unless a second consumer appears.
8. **"Mesh Generation" name.** Accurate once Bind leaves (rec 3). If Bind stays, the name undersells it. Tie this name to the rec-3 decision.
9. **Import under an "Export" subpanel.** Import (input) under a panel named Export (output) is mildly contradictory. Minor: either name the panel "Pipeline I/O" or keep two subpanels (Import / Export) under a neutral parent. Low priority.

## Answers to the embedded questions

- **Weight paint on sprites?** No. A `sprite` is a rigid `Sprite2D` - it attaches to ONE bone (a `parent_bone`, effectively weight = 1), it is not deformed. Weight paint is a mesh-only concept. The Weight Paint panel should poll `element_type == "mesh"`; a sprite gets a simple "Bound to bone: X" rigid control instead of a weight workflow. Your instinct is right - collapse to a single bone.
- **Blender i18n - how, and how to approach.** Blender ships `bpy.app.translations`: you register a dict keyed by locale, mapping `(msgctxt, msgid) -> translated string`, and look strings up with `pgettext_iface` / `pgettext_data`; the UI auto-translates registered `msgid`s when "Translate Interface" is on. Right approach = isolate EVERY user-facing string (labels, descriptions/tooltips, doc paths) in ONE module as the canonical English source with stable keys, shaped so the translation layer wraps it later. Build the isolation now (single source), defer the actual translation tables. `help_topics.py` is the natural home to grow into this.

## Decomposition (this is more than one spec)

The plan spans several concerns. Suggested spec split, IA first:

- **Spec 1 - IA restructure.** Panel/subpanel tree, accordion subpanels, isolated selectors, warning-instead-of-hide, the operator relocations (Create Slot -> Slots, Validate -> Validation, Preview Camera -> Helpers), the renames (Skinning -> Mesh Generation, Automesh from Alpha), Outliner to top level. The Quick-Armature no-rig bugfix rides here.
- **Spec 2 - help + docs + i18n system (cross-cutting).** Brief-tooltip + `?`-popup + doc-link registry (`site + path`), badge everywhere (incl. fixing `skinning` in the taxonomy and filling the badge gaps), string isolation shaped for i18n.
- **Spec 3 - addon preferences.** Log level + debug-mode gate (and the contextual-hide toggle if rec 5 is rejected).

## Parked (Bucket C - feature work, not IA)

- Bone-collections management in Proscenio (new feature).
- Atlas packing features already mapped in the backlog (strip whitespace, edge padding, etc.).
- Bone hierarchy / connected / relative-parent readout is partly IA (display) and partly feature; the display lands with Spec 1, richer editing is Bucket C.

## Resolved (locked) - 2026-06-07

All four forks settled, embedded questions answered, decomposition agreed.

- **Fork 1 - Bind home.** Bind and every weight-related operator (Bind, Edit Weights, Snapshot, Sidecar IO, Weight Transfer) live in the **Weight Paint** panel. Mesh Generation = automesh only.
- **Fork 2 - Active Element nesting.** Isolated Type selector at the panel top + ONE "Body" subpanel that swaps Mesh/Sprite content. Two levels.
- **Fork 3 - contextual-hide pref.** Cut (YAGNI). Panels always show; they warn when inactive. v1 addon prefs = log level + debug only.
- **Fork 4 - doc links.** Registry `feature_id -> {site, path}`. The `?` popup shows inline help now (reuse `help_topics.py`) and reveals an "Open online docs" button only when the path resolves. No dead links.
- **Reframe accepted.** Tooltip = brief one-line hover string; the doc link lives in the `?` popup, never in the tooltip.
- **Export -> Pipeline.** The Export panel is renamed **Pipeline** with two subpanels: Import (Photoshop) and Export (export / re-export / PPU / last path).
- **Sprite rigid bind (embedded Q1).** Sprites are not weight-painted - a `sprite` (Sprite2D) binds rigidly to a single bone (weight = 1 on its `parent_bone`). The Weight Paint panel polls `element_type == "mesh"`; the sprite path is a "Bound to bone: X" control. Recorded in `backlog.md` (Blender addon); to be isolated as a behavior when the Weight Paint panel lands.
- **i18n (embedded Q2).** Deferred to AFTER the IA restructure. Isolate strings first (single canonical source, stable keys), translate later via `bpy.app.translations`.

Decomposition (sequencing): this spec (021) is the audit/discovery; it feeds **022 - IA restructure** (the locked design above), then **023 - help + docs + i18n**, then **024 - addon preferences**. 022 carries the Quick-Armature no-rig bugfix and the Skinning-taxonomy badge fix as ride-alongs.
