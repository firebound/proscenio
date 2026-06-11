# Spec 036: UI, help and surfaces

Polish the editor UI that is not tied to one tool, finish the help/docs system, and add the new panels.

## Scope

- **Re-wire the orphaned sprite_frame_preview help button**.
- **Fix Reproject UV** - replace `smart_project` to stop the rotated/flipped result (and retest the perf symptom).
- **Show the selected mesh name** in the Active Sprite header.
- **Clamp the Initial frame** to the valid range.
- **Rename "Initial frame" to "Frame"**.
- **Clarify the centered-vs-origin distinction** in help.
- **Left-align mesh names** in the Outliner.
- **Frame and unhide the offending object** on a Validation issue click.
- **Indented tree in the Outliner** (armature > slots > attachments).
- **Rename the validator's internal sprites-vs-elements** vocabulary.
- **Make local-path see-also references clickable**.
- **Replace the Help panel** with a single popup button.
- **Merge Diagnostics into the Help panel**.
- **Populate the per-locale i18n tables**.
- **Migrate inline see-also references to online URLs**.
- **Expand the addon reference pages with screenshots**.
- **Make the docs URL a preference**.
- **Sweep the guide docs** for the new Element/panel vocabulary.
- **Consolidate the cross-module panel helpers**.
- **Native header-drag reorder** for sibling panels.
- **A Materials panel** (interpolation, blend-mode, bulk path fix).
- **An onion-skin overlay** for animators.
- **A joystick / slider multi-pose blend widget**.

## Study

### Surface notes

**The help-orphan regression (#96 mechanics).** Fix `6749412` wired a `?` button for the `sprite_frame_preview` topic via `draw_subbox_header`; the sidebar restructure (PR #96, `2d512a7`) rebuilt the Element body into real subpanels (`panels/element.py`), replaced `_draw_sprite_frame.py` with `_draw_sprite.py`, and dropped the call. `draw_subbox_header` survives in `panels/_helpers.py:88-108` with zero callers. `_draw_sprite.draw_body` draws `hframes` / `vframes` / `frame` / `centered`, the atlas readout, and `Setup Preview` / `Remove Preview` with no help affordance; the **Active Sprite** subpanel header `?` opens the `active_sprite` fields topic, not the preview-shader topic with its caveats. It regressed silently because `tests/test_help_topics.py::test_panel_topic_ids_present` checks a hardcoded id list against the table - table-side only; no test asserts every table topic has a panel caller. Inventory (the bug entry asked for one): exactly two orphans today, `sprite_frame_preview` (`help_topics.py:417`) and `pose_library` (`help_topics.py:451` - `Save Pose to Library` sits in the **Pose Mode** subpanel whose `?` opens `pose_mode`). The re-wire is a few lines per orphan plus a reverse-coverage pytest that scans `panels/` + `operators/` source for each topic id, which pins the whole family against the next restructure.

**Reproject UV is structural, not a tweak.** `operators/uv_authoring.py:73` still calls `bpy.ops.uv.smart_project`; the shipped mitigations are docstring + tooltip + an Object-Mode-only poll. Smart Project picks projection from face normals, so an XZ picture-plane quad (normal -Y) comes back rotated 90 degrees and mirrored - destructive to hand-authored UVs. The proper fix in the bug entry is deterministic planar projection: detect the dominant mesh plane, map UVs from the bounding box, respect the Front-Ortho U-flip that `build_blend.py` authors. That is pure math over `mesh_uvs` helpers - headless-testable - and it removes the Edit-Mode toggle + `select_all` + operator-cache dance that is the likely perf symptom (the perf re-check stays a `[retest]` row in the verification session).

**One-line vs structural, across the polish rows.** `rename-initial-frame` is one word (`object_props.py:96`). `centered-vs-origin-help` is one added contrast line in the `active_sprite` topic (`help_topics.py:612-618` explains `centered`; it never contrasts it with the object origin imported from the PS `[origin]` tag). `left-align-names` is a known UIList quirk: `outliner.py:70-77` draws rows as `row.operator(..., emboss=False)` and operator text centers; wrapping in a sub-row with `alignment="LEFT"` fixes it. `header-mesh-name` is a readout row or a `draw_header` override on the **Active Sprite** subpanel (static `bl_label`, `element.py:94`). `clamp-initial-frame` is an update-callback clamp (`object_props.py:95-102` has `min=0` only; the real max is `hframes*vframes-1`, dynamic, so it cannot be a static `max=` - write `self["frame"]` in the callback to avoid update recursion, and reclamp when `hframes` / `vframes` shrink). `frame-unhide-on-click` extends `selection.py:31-37` (`select_named_or_warn` then return) with `hide_set(False)` + `hide_viewport=False` + `view3d.view_selected`; the click already happens inside a VIEW_3D sidebar so only the WINDOW-region override is fiddly, and the change benefits all three panels that share `draw_issue_row`.

**The see-also pair is one fix.** `help_dispatch.py:89-93` already renders `http(s)` refs as `wm.url_open` buttons; exactly three local-path refs remain (`help_topics.py:182,334` -> `specs/decisions.md`, `:512` -> `examples/generated/simple_psd`). Local paths can never resolve inside an installed zipped extension, so the clickability fix IS the URL migration: point the three refs at their GitHub URLs and every ref becomes a button with zero new code. `test_see_also_references_exist_on_disk` then flips from a disk-existence check to a URL-shape check.

**Help + Diagnostics merge shrinks the panel count.** `panels/help.py` is a 17-row operator cheat-sheet panel (the user called it unusable); `panels/diagnostics.py` is one smoke-test button already behind the `debug_mode` preference poll. The merge: one **Help** panel with an `Open help` button invoking the existing `proscenio.help` popup (move the operator reference into a help topic) plus the smoke-test button when `debug_mode` is on. Net minus one panel, minus one module, and the popup mechanic (`PROSCENIO_OT_help.invoke_popup`) already exists.

**Panel-helper consolidation trigger fires with this spec.** The backlog gate was "fold in when next touching the panel modules" - the polish batch touches them. `panels/_helpers.py:36-43` holds only the PR-#96 pair; `_active_mesh_props` and sibling scene-props accessors still live module-local (`element.py:24-29` and four other panels). Mechanical, mypy + pytest gated, zero GUI cost.

**Drag-reorder has nothing left to build.** Sibling top-level panels already get native header-drag reordering from Blender (`bl_order` only sets the initial order); `bl_parent_id` subpanels cannot be reordered - an upstream limitation, tracked as such in the backlog row. Both halves are closed: one ships free, one is not ours to fix.

**Materials panel: the pain is real, the panel is not the fix.** The importer builds materials without ever setting `ShaderNodeTexImage.interpolation` (`importers/photoshop/planes.py:317-325`), so pixel art previews blurry under Blender's Linear default, and `_BLEND_METHOD_BY_MODE` routes every non-opaque mode to `BLEND` (`planes.py:62-67,342`). But the proposed panel's third pillar, bulk image-path repair, duplicates Blender's native `File > External Data > Find Missing Files`; the inspection list and regex bulk-config are a new stateful surface with no demand evidence. If the blur pain materializes in production the answer is a one-line import-time interpolation option, not a panel.

**Onion skin and joystick are the two max-cost rows.** Both are new viewport surfaces: a GPU draw handler evaluating the rig at other frames (onion skin needs per-frame depsgraph re-evaluation - `frame_set` cost - plus handler lifecycle across mode changes and undo) and a custom gizmo + pose-set PropertyGroup + a schema/export path to Godot `BlendSpace2D` (joystick). Test burden is GUI-session-only for both, the scarcest resource. Neither has a line of code in the tree.

**i18n is wired, empty by design.** `core/i18n.py` registers an empty `TRANSLATIONS` tuple under `bpy.app.translations`; populating means translating every registered string including multi-line help bodies, then maintaining the table on every copy change - and this very spec renames labels and merges panels, invalidating rows before they exist.

**Docs surface.** `docs/02-blender-addon/` is 13 pages averaging 14 lines, no screenshots, anchored by `_DOC_PATHS` (`help_topics.py:839-869`) which the `Open online docs` button targets - any heading restructure must keep those anchors. The two guide pages actively lie today: `docs/00-guides/00-basic/02-blender.md:55` still says `Automesh from Sprite` (operator renamed to `automesh_from_alpha`) and `01-advanced/02-blender.md:59` documents a **Skinning** panel that split into **Mesh Generation** + **Weight Paint**; the backlog notes this needs a prose rewrite against the shipped IA, not find-replace. `_DOCS_BASE` (`help_topics.py:837`) stays a constant per the spec 024 D3 locked decision.

### Research notes

- **Onion skin, native:** Blender has onion skinning for Grease Pencil only; mesh/armature onion skin is an open upstream design task ([Blender #102217](https://developer.blender.org/T102217)). Motion paths cover bone-trajectory timing checks natively.
- **Onion skin, ecosystem:** [B Onion Skin](https://extensions.blender.org/add-ons/b-onion-skin/) (free, official extensions platform) ghosts animated meshes including rigged characters; [Mesh Onion Skins](https://github.com/tingjoybits/Mesh_Onion_Skins) (free) and [Onion Skin Tools](https://superhivemarket.com/products/onion-skin-tools) (paid) do the same. A Proscenio overlay would duplicate an installable, pipeline-orthogonal authoring aid.
- **Onion skin, cutout practice:** Live2D Cubism shipped onion skin as an official feature in 4.1 ([Cubism editor manual](https://docs.live2d.com/en/cubism-editor-manual/onion-skin/)) - cutout posers do use it, so the demand is genuine but already served in-ecosystem for Blender users.
- **Joystick/slider:** [Joysticks 'n Sliders](https://aescripts.com/joysticks-n-sliders/) is described as the industry-standard pose-based rigging system for After Effects (five corner poses blended by a 2D controller; sliders for pose rows), widely adopted for face rigs ([Cub Studio](https://www.cubstudio.com/joysticks-n-sliders), [Kashu face-rig template](https://kashu.co/face-rig-with-joysticks-and-sliders-free-template/)); Cubism's whole model is the same idea as first-class `parameters` (Angle X, Mouth open/close) ([Cubism manual, About Parameters](https://docs.live2d.com/en/cubism-editor-manual/parameter/)). An animator staple for parametric faces - but only once a parametric-face character exists; the Godot runtime half maps to `AnimationTree.BlendSpace2D`.
- **Materials pain:** Blender's Linear texture-interpolation default blurring pixel art is a recurring documented complaint with a one-click known fix (set the Image Texture node to Closest) - e.g. [VRM-Addon issue #491](https://github.com/saturday06/VRM-Addon-for-Blender/issues/491) and pixel-art tutorials ([TutsByKai](https://www.youtube.com/watch?v=EKONCNCbpB0)). Bulk path repair already exists natively: `File > External Data > Find Missing Files` walks a folder and relinks exact-filename matches ([Blender tracker #102557](https://developer.blender.org/T102557), [yelzkizi guide](https://yelzkizi.org/missing-textures-or-linked-files-detected-in-blender/)).
- **i18n:** Blender publishes no locale-usage telemetry; it ships 29 UI languages of which only about six are fully covered ([Blender developer docs, internationalization](https://developer.blender.org/docs/features/interface/internationalization/), [translator guide](https://developer.blender.org/docs/handbook/translating/translator_guide/)) - even core cannot keep tables full. No demand signal exists for a non-English Proscenio UI; the docs site is English-only.

### Assessment

Scales: flow-value 5 = core flow; test-burden 5 = GUI-session-only; bug-surface 5 = new stateful overlay; underuse-risk 5 = speculative demand.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| sprite-frame-preview-help-orphan | 3 | 2 | 1 | 2 | now | Blocking regression; few lines + a reverse-coverage test that pins the whole topic family. |
| reproject-uv-orientation | 4 | 3 | 2 | 2 | now | Destructive op today; deterministic planar projection is headless-testable math; perf `[retest]` stays in the verification session. |
| header-mesh-name | 2 | 1 | 1 | 2 | now | Readout row; rides the polish batch. |
| clamp-initial-frame | 2 | 2 | 2 | 1 | now | Update-callback clamp, headless test; idprop write avoids recursion. |
| rename-initial-frame | 2 | 1 | 1 | 1 | now | One word; near-zero cost. |
| centered-vs-origin-help | 2 | 1 | 1 | 2 | now | One contrast line in the existing topic. |
| left-align-names | 2 | 1 | 1 | 1 | now | Two-line UIList alignment fix; universal readability. |
| frame-unhide-on-click | 3 | 2 | 2 | 2 | now | Closes the validation loop; one operator, three panels benefit. |
| indented-tree | 2 | 3 | 3 | 2 | defer | Category sort + attachment indent already shipped; full nesting restructures `filter_items` for modest marginal value. |
| validator-element-rename | 1 | 2 | 1 | 1 | gate | Cosmetic internal rename in `packages/validator`; trigger: the next change that touches `packages/validator`. |
| see-also-clickable | 2 | 1 | 1 | 2 | now | Collapses into the URL migration - zero new code once refs are `http(s)`. |
| help-panel-popup-button | 2 | 2 | 2 | 1 | now | Popup mechanic exists; removes an unusable panel. |
| merge-diagnostics-help | 2 | 2 | 2 | 1 | now | Pairs with the popup button; net minus one panel + module. |
| i18n-locale-tables | 1 | 3 | 2 | 5 | gate | No demand signal; every copy change in this spec would invalidate rows. Trigger: first non-English user request or a contributed translation PR. |
| see-also-online-urls | 2 | 1 | 1 | 2 | now | Three string edits; also the clickability fix. |
| addon-docs-screenshots | 2 | 4 | 1 | 3 | gate | GUI capture + per-release staleness while panels still churn (this spec churns them). Trigger: panel-layout freeze at the 1.0 tag. |
| docs-url-preference | 1 | 1 | 1 | 5 | gate | Spec 024 D3 locked deferral. Trigger: a second docs target (mirror or version switch) appears. |
| guide-doc-rename-sweep | 3 | 1 | 1 | 1 | now | Both guide pages mislead every new learner today; docs-only PR, sequenced after this spec's renames land. |
| panel-helper-consolidation | 1 | 2 | 1 | 1 | now | Its recorded trigger ("next panel-module touch") fires with the polish batch; mechanical, headless-gated. |
| subpanel-drag-reorder | 1 | 5 | 3 | 3 | drop | Top-level half is native Blender already; subpanel half is an upstream limit. Nothing buildable. |
| materials-panel | 2 | 4 | 4 | 4 | drop | Path repair duplicates native Find Missing Files; inspection/bulk surface is speculative. If pixel-art blur lands in production, the fix is a one-line import-time `Closest` option, not a panel. |
| onion-skin-overlay | 2 | 5 | 5 | 4 | drop | Free ecosystem extensions (B Onion Skin) already ghost rigged characters; upstream design task open; max GUI-test surface for zero pipeline impact. |
| joystick-slider-blend | 3 | 5 | 5 | 5 | gate | Real animator staple (AE Joysticks 'n Sliders, Cubism parameters) but max cost on every axis. Trigger: the first character with parametric facial expressions (phonemes, eye direction) enters production AND the 1D Drive from Bone path proves insufficient; design schema-first (`BlendSpace2D` export), widget last. |

### Verdict summary

**14 now, 1 defer, 5 gate, 3 drop.** None of the three new surfaces survives as buildable work: materials-panel and onion-skin-overlay are proposed for pruning (ecosystem and native tooling already cover the real pains), joystick-slider-blend stays gated on the first parametric-face character. The recommendation is five PRs: (1) the blocking help-orphan re-wire (both orphans + the reverse-coverage test), (2) the Reproject UV planar-projection rewrite, (3) **one batched polish PR** - header-mesh-name, clamp-initial-frame, rename-initial-frame, centered-vs-origin help line, left-align outliner names, frame-unhide on issue click, the see-also URL migration (closes two scope rows), and the panel-helper consolidation as its final mechanical commit - all verified by a single GUI smoke pass, (4) the Help popup button + Diagnostics merge, (5) the guide-doc rename sweep after the UI renames land so the prose matches the shipped editor.
