# Spec 049: Blender UI polish - TODO

Sequenced from [STUDY.md](STUDY.md): the shared list component lands first, its consumers follow, then the help refactor, then the small panel fixes. Four PRs; all "now".

## PR 1 - shared list component + standardization + multi-select + cross-deselect

- [ ] Build a `ProscenioUIList` base/mixin in [`panels/_helpers.py`](../../apps/blender/panels/_helpers.py) (or a new `panels/_list.py`) carrying: native `filter_name` search, the Shift/Ctrl multi-select routing lifted from the Outliner select operator ([`operators/selection.py`](../../apps/blender/operators/selection.py)), and a row cap. Reuse `core/outliner_view.py:source_index_for_name` for identity->index.
- [ ] Migrate the Skeleton bone list ([`panels/skeleton.py`](../../apps/blender/panels/skeleton.py)) and the Animation actions list ([`panels/animation.py`](../../apps/blender/panels/animation.py)) onto the component - they gain native search (native-list-standardization).
- [ ] Migrate the Outliner ([`panels/outliner.py`](../../apps/blender/panels/outliner.py)) and Slots ([`panels/slots.py`](../../apps/blender/panels/slots.py)) lists onto the shared chrome (they already have search) so multi-select + cross-deselect behave uniformly.
- [ ] Wire `invoke` + the `event.shift`/`event.ctrl` read into the Bone select path ([`operators/selection.py`](../../apps/blender/operators/selection.py), single-select today) so bones get multi-select; keep "pick one" lists single (list-multiselect).
- [ ] proscenio-list-cross-deselect: make the active-row highlight track the real Blender active object/bone across all lists (extend the 043 identity-sync), so a row reads active only when its object/bone is the actual active one.
- [ ] Headless tests: the component's `filter_items` paths, the Shift/Ctrl routing, and the identity->index resolver against multiple lists.

## PR 2 - list consumers (Weight Paint overrides + Element drivers)

- [ ] wpaint-override-list-scroll: replace the custom per-bone row loop ([`panels/weight_paint.py`](../../apps/blender/panels/weight_paint.py) ~190-241) with the component (or a height-capped `box()` + `column()`), so a many-bone armature stops pushing the Bind UI down.
- [ ] element-driver-management: in the Drive-from-Bone subpanel ([`panels/_draw_driver_shortcut.py`](../../apps/blender/panels/_draw_driver_shortcut.py)), list the element's `proscenio.*` drivers (target property + source bone) as component rows with an X to remove; add a `remove_driver(data_path)` operator in [`operators/driver.py`](../../apps/blender/operators/driver.py) mirroring `driver_remove()`. The create/replace path and the two-range builder stay as-is.
- [ ] Headless tests: multi-driver list + remove; the override list with many bones.

## PR 3 - help popup width + copy revision (one structural edit)

- [ ] Refactor `HelpSection.body` from `tuple[str, ...]` (pre-wrapped lines) to a paragraph `str` in [`core/help_topics.py`](../../apps/blender/core/help_topics.py); add a greedy reflow against the popup width in the popup `draw()` ([`operators/help_dispatch.py`](../../apps/blender/operators/help_dispatch.py)). This fixes help-popup-text-width and retires the hand-wrapping.
- [ ] tooltip-copy-revision: as the bodies are re-touched by the refactor, run the editorial pass over all 31 topics - panel `?` explains the panel, subpanel `?` explains its specifics without leaking; cut verbosity, verify accuracy. (The status-badge legend + the three lying strings already shipped.)
- [ ] Update [`tests/test_help_topics.py`](../../tests/test_help_topics.py) for the new `body` shape (presence/coverage assertions stay; the type assertion changes).

## PR 4 - small panel fixes (one GUI smoke)

- [ ] show-provenance-overlay-toggle: remove the inert standalone toggle from [`panels/weight_paint.py`](../../apps/blender/panels/weight_paint.py) and surface the control only inside the Edit Weights modal where its draw handler lives ([`operators/skinning/edit_weights.py`](../../apps/blender/operators/skinning/edit_weights.py)). No persistent overlay handler.
- [ ] automesh-shared-params-surfacing: lift the six shared params (`interior_mode`, `contour_vertices`, `interior_spacing`, `density_under_bones`, `bone_radius`, `bone_factor`) from the Automesh-from-Alpha subpanel to the parent Mesh Generation panel ([`panels/mesh_generation.py`](../../apps/blender/panels/mesh_generation.py)) so both Alpha and Interactive show them.
- [ ] wpaint-named-snapshots: add an additive `snapshots` list to the weight sidecar ([`core/skinning/sidecar_schema.py`](../../apps/blender/core/skinning/sidecar_schema.py), pre-launch so no version bump), a `restore_named_snapshot(name)` operator, and a snapshot list (a component consumer) in the Weight Paint panel; headless test for save -> paint -> restore-by-name.
