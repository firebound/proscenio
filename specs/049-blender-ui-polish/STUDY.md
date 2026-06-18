# Spec 049: Blender UI polish

Batch the now-able editor UI/UX fixes mapped from the post-spec-036 QA walks: a shared list component and its consumers, the help-text rendering, and a set of small panel fixes. Every item's approach is settled here - the open design questions that surfaced alongside these live in [spec 050](../050-blender-authoring-design/STUDY.md), kept apart so this batch can ship without waiting on a decision.

## Scope

Lists (a shared list component, reversing the deferral):

- **native-list-standardization** - standardize every Proscenio panel list on one native-style component (Blender `filter_name` search, consistent row chrome, per-panel custom marks).
- **list-multiselect** - Shift/Ctrl multi-select on the lists whose click maps to a real Blender selection (Skeleton bones), single-select where the click means "pick one".
- **proscenio-list-cross-deselect** - selecting in one list leaves the active-row highlight lit in the others; the highlight should track the real active object/bone across lists.
- **wpaint-override-list-scroll** - the per-bone override list grows unbounded and pushes the rest of the Bind UI down; it needs the component (or at least a scroll cap).
- **element-driver-management** - the Drive-from-Bone subpanel can only replace a driver; add a list of the element's drivers with remove (a real consumer of the component).

Help (copy + popup width share one refactor):

- **tooltip-copy-revision** - revise the `?`/tooltip copy so each panel's button explains the panel and each subpanel explains its own specifics without leaking; cut verbosity, check accuracy.
- **help-popup-text-width** - the `?` popup renders hand-wrapped lines in a narrow column; reflow to the popup width.

Panel fixes:

- **show-provenance-overlay-toggle** - the standalone toggle is inert outside the Edit Weights modal; remove it from the panel and surface it only inside the modal.
- **automesh-shared-params-surfacing** - the params that also drive Automesh Interactive live only in the Automesh-from-Alpha subpanel; lift the shared ones to the parent Mesh Generation panel.
- **wpaint-named-snapshots** - the weight snapshot UX gives no sense of which save point a restore targets; add manual named save points plus a rolling last-3 auto-snapshot history.

## Study

### Lists: the shared component is now justified

[`decisions.md`](../decisions.md) "Slots list UX" deferred a reusable list component "to a genuine third consumer", and gated the attachment native-scroll "on an observed desync". The post-merge QA walk plus this scoping pass surface the third-and-beyond consumer: Skeleton bones and Animation actions both lack native search, the Weight Paint per-bone overrides have no scroll, and the new Element driver list wants the same shape. Four real consumers clears the trigger, so this spec builds the shared component rather than patching each list in isolation.

Inventory of the current lists (file:line, backing):

| List | File | Backing | Search | Scroll/cap |
| --- | --- | --- | --- | --- |
| Skeleton bones | `panels/skeleton.py:30-85`, `template_list` at `:189-197` | real `target.data.bones` + `active_bone_index` | no | dynamic `rows` cap |
| Outliner | `panels/outliner.py:13-127`, `:154-162` | filtered `bpy.data.objects` + `active_outliner_index` | native `filter_name` | none |
| Slots | `panels/slots.py:32-90`, `:178-186` | filtered objects + `active_slot_index` | native `filter_name` | none |
| Animation actions | `panels/animation.py:12-36`, `:63-71` | `bpy.data.actions` + `active_action_index` | no | dynamic `rows` cap |
| Attachments | `panels/slots.py:249-270` | custom-draw over `empty.children` (not a `CollectionProperty`) | no | `scale_y=0.9` |
| Weight Paint overrides | `panels/weight_paint.py:190-241` | custom per-bone row loop (no `UIList`) | no | none |

The shared component is a `ProscenioUIList` base (or mixin) carrying the native `filter_name` search, the Shift/Ctrl multi-select routing already proven in the Outliner select operator (`operators/selection.py:62-123`, reads `event.shift`/`event.ctrl`), and a row cap. The identity-to-index resolver `core/outliner_view.py:source_index_for_name` already shared by Outliner + Slots is the seam to extend.

- **native-list-standardization** is the component itself plus the migration of Bones + Actions onto it (they gain search); the Outliner + Slots lists already have search and migrate for the shared chrome + multi-select. The attachment list stays custom-draw (it has no real `CollectionProperty`, per the locked call) but adopts the same scroll cap. Size **M**.
- **list-multiselect** reuses the Outliner's existing pattern, no new mechanism: the Outliner already shows multi-select via a per-row selection marker (the radio dot reading `obj.select_get()`), not via the `template_list` single `active_index`. Apply that per-row-marker pattern to the lists where multi makes sense - the Skeleton bones (wire `invoke` + the `event.shift`/`event.ctrl` read into the bone select path, single-select only today at `selection.py:126-157`). "Pick one" lists stay single; nothing is replicated for lists that do not need multi. Size **M**.
- **proscenio-list-cross-deselect** resolves per list kind: the object/bone lists (Outliner, Skeleton, Slots) make their active-row highlight follow the real Blender active object/bone (the 043 outliner identity-sync), so a row reads active only when its object/bone is the actual active one. The Animation actions list stays independent - its `active_index` picks the active action of the Skeleton-picked armature, not an object, so it has no shared active-object semantics to sync. Size **S-M**, lands with the component.
- **wpaint-override-list-scroll** migrates the custom per-bone loop (`weight_paint.py:190-241`) onto the component (or a `column()` in a height-capped `box()`), so a many-bone armature stops pushing the Bind UI off-screen. Size **S**.
- **element-driver-management** reads `sprite.animation_data.drivers` filtered to `proscenio.*`, draws each as a row (target property + source bone) with an X, and a new `remove_driver(data_path)` operator mirroring `driver_remove()`. The create path already replaces (`operators/driver.py:_ensure_single_driver`); this adds the missing list + remove. It consumes the component. Size **M**. Respects the locked "Drive-from-Bone = clamped two-range linear map" call - the builder logic is untouched, only management UI is added.

### Help: copy and popup width share one refactor

The help popup is invoked at `operators/help_dispatch.py` with `invoke_popup(width=480)` and renders the body via `layout.label(text=line)` per line. `layout.label` does not wrap, and the bodies in `core/help_topics.py` are hand-wrapped into ~50-80 char lines, so the text sits in a narrow column with an empty right margin. There are 31 topics / ~88 sections / ~3300 words.

- **help-popup-text-width**: refactor `HelpSection.body` from `tuple[str, ...]` (pre-wrapped lines) to a paragraph `str`, and reflow it in `draw()` with a greedy line-break against the popup width. This makes the hand-wrapping obsolete. Size **M**.
- **tooltip-copy-revision**: the body refactor forces re-touching every topic's text, so the editorial concision/accuracy pass rides the same edit - one pass over the 31 topics (panel `?` = panel overview, subpanel `?` = its own specifics). The prior spec already fixed the status-badge legend and the three lying strings, so only the editorial pass remains. Size **S**. `tests/test_help_topics.py` asserts presence/shape, not content, but the `body` type change needs its assertion updated. This is also the proof-of-concept for the `docs-no-hard-wrap-rule` code-quality item.

### Panel fixes

- **show-provenance-overlay-toggle**: the panel toggle (`weight_paint.py:338`) registers no draw handler; the provenance overlay handler is registered only inside the Edit Weights modal (`edit_weights.py:97-99`) and torn down on finish, so the panel-body copy is dead UI. The fix (user call) is to remove the standalone toggle and keep the control only inside the modal where it works. A persistent read-only overlay (drawing the seed / paint / reprojected colors outside the modal) was considered - it would not break the locked modal-mutation rule since drawing is read-only - but declined as scope not worth it now. Size **S**.
- **automesh-shared-params-surfacing**: the six shared params (`interior_mode`, `contour_vertices`, `interior_spacing`, `density_under_bones`, `bone_radius`, `bone_factor`) live only in the Automesh-from-Alpha subpanel (`panels/mesh_generation.py:132-169`) but the Interactive modal reads them at invoke; lift them to the parent Mesh Generation panel (already modal-agnostic, already holds `interior_mode`) so both entry points show them. Findings F-47/F-48. Size **S**.
- **wpaint-named-snapshots**: the panel offers one "reset to last saved" with no sense of which point it restores. Build both kinds, not either/or: **manual named save points** (unlimited, user-named, for autonomy) and **auto-snapshots** (captured per paint session, a rolling history capped at the last 3, for convenience). Add an additive `snapshots` list to the sidecar (`core/skinning/sidecar_schema.py`, pre-launch so no version bump) carrying both kinds with a kind flag, a `restore_named_snapshot(name)` operator, and a snapshot list (a component consumer) that shows the named saves plus the last-3 auto entries. Size **M**.

### Assessment

Scales: flow-value 5 = core flow; test-burden 5 = GUI-session-only; bug-surface 5 = new stateful surface; underuse-risk 5 = speculative demand.

| Item | Flow value | Test burden | Bug surface | Underuse risk | Verdict | Why |
| --- | --- | --- | --- | --- | --- | --- |
| shared-list-component | 3 | 2 | 2 | 1 | now | The infra; four real consumers clear the deferral trigger. Filter/route logic is headless-testable. |
| native-list-standardization | 2 | 2 | 1 | 1 | now | Bones + Actions gain search; the rest adopt shared chrome. |
| list-multiselect | 3 | 2 | 2 | 2 | now | Wires invoke+event into the bone path; multi-highlight is an approximation owned in one place. |
| proscenio-list-cross-deselect | 3 | 2 | 2 | 1 | now | Highlight-follows-active-object; extends the 043 identity-sync. |
| wpaint-override-list-scroll | 3 | 1 | 1 | 1 | now | A many-bone armature pushes the Bind UI off-screen today. |
| element-driver-management | 3 | 2 | 2 | 1 | now | The list + remove the create path never added; builder logic untouched. |
| help-popup-text-width | 2 | 2 | 1 | 1 | now | Body refactor + greedy reflow; retires the hand-wrapping. |
| tooltip-copy-revision | 2 | 1 | 1 | 2 | now | One editorial pass; rides the body refactor. |
| show-provenance-overlay-toggle | 2 | 1 | 1 | 1 | now | Remove inert UI; the cheap correct fix, not a persistent overlay. |
| automesh-shared-params-surfacing | 2 | 1 | 1 | 1 | now | Lift six params to the parent panel; ~15 LOC. |
| wpaint-named-snapshots | 3 | 3 | 2 | 2 | now | Additive sidecar field + restore-by-name + a list; the snapshot UX is opaque today. |

### Verdict summary

**11 now (the component + 10 scoped items), 0 defer, 0 gate, 0 drop.** The recommendation is four PRs, sequenced so the component lands first and its consumers follow - see [TODO.md](TODO.md).
