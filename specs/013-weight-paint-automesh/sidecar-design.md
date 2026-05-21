# Wave 13.2 - Weight Sidecar + Reproject: Design

Status: design locked 2026-05-20. Decisions taken autonomously per user delegation; UX-touching items confirmed via questions.

Scope: populate the `WeightSidecar` entries that bind currently leaves empty, snapshot weights pre-automesh-regen + reproject onto the new topology via UV-anchor barycentric interpolation, surface provenance counts in the panel. Materializes D6 - the differentiator vs Spine / COA Tools 2 (both lose weights on mesh regen).

Locked decision: D6 (sidecar JSON keyed by UV anchors + auto-reproject on regen + visible provenance overlay).

## Decisions

### Technical (autonomous)

| # | Decision | Locked value | Rationale |
| --- | --- | --- | --- |
| T1 | Entry shape | `SidecarEntry(uv_anchor, weights, provenance)` dataclass; entries=list of these | Canonical per-vert record; serializes cleanly via dataclasses.asdict; provenance literal narrows downstream branching |
| T2 | UV anchor per vert | Single anchor = active UV layer's value at the vert's first loop | Standard 2D-sprite Blender convention; border verts pick first loop deterministically |
| T3 | Reproject algorithm | Barycentric over 3 nearest UV anchors via mathutils.kdtree | Same lift as Animate / DragonBones; degrades to nearest-anchor + auto_seed when degenerate |
| T4 | Topology hash trigger | Reproject ONLY when topology_hash diverges; identical-hash regen leaves entries untouched | Saves compute on no-op regens (debug stage = "final" re-runs); preserves entries verbatim |
| T5 | Sidecar version | Stay on v1; entries=[] = stub state, populated = post-paint state | Same shape works for both; no migration cost |
| T6 | Counts overlay data | Recompute from entries list on draw; not persisted separately | Single source of truth; no drift |
| T7 | Migration | Sprites bound before this wave have entries=[]; populates organically on next bind | Forward-only; no migration script needed |
| T8 | Failure modes | UV layer missing during snapshot = silently fall back to empty entries (T7 forward-only spirit); restore + post-regen reproject ERROR + abort since those require real UVs; all entries fail reproject = fall back to fresh bind + WARN with count; corrupt sidecar = catch ValueError + treat as fresh bind | D11 spirit: actionable hints, never raw stack trace |
| T9 | Provenance diff (bind path) | `_apply_bone_heat` + algorithm path stamp all new entries with `provenance="auto_seed"` after weights computed | Bind = "all auto" baseline; paint modal (future wave) flips to `user_paint` via diff |
| T10 | `restore_weight_snapshot` operator scope | Reapplies existing sidecar to current mesh ONLY; does NOT trigger regen | Single responsibility - "revert my recent paint to last saved state"; regen flow handled by automesh hook |
| T11 | Automesh integration | Automesh operator gains pre/post hook: pre-regen snapshot (if PG flag + sidecar populated), post-regen reproject + apply | One operator surface; flag controls the auto-flow |

### UX-touching (user confirmed)

| # | Decision | Locked value |
| --- | --- | --- |
| U1 | `preserve_on_regen` default | **ON** - automesh regen auto snapshot + reproject by default. PG flag exposed in panel for explicit opt-out |
| U2 | Provenance overlay visibility | **Toggle in panel, default OFF** - "Show provenance" checkbox in Snapshot sub-box. GPU draw handler ships in Wave 13.2-paint (this wave provides data + toggle only) |

## Scope split

**This wave (sidecar) ships:**

- Populated `entries` data structure with provenance
- Pure reproject algorithm
- Snapshot + apply bpy helpers
- Automesh pre/post hook integration
- `restore_weight_snapshot` operator
- Panel sub-box with counts text + toggles
- Tests (pure + headless)

**Deferred to Wave 13.2-paint:**

- Provenance overlay GPU draw handler (cyan/white/gray colored discs)
- Live `user_paint` tagging via diff during paint modal

**Deferred to Wave 13.3:**

- `proscenio.copy_weights_to_selected` (cross-mesh transfer)
- Sidecar import/export to external file

## Architecture

```text
apps/blender/core/skinning/
├── sidecar_schema.py          [AMEND] WeightSidecar.entries: list[SidecarEntry]; add SidecarEntry dataclass
└── weight_reproject.py        [NEW] pure: kdtree + barycentric interp

apps/blender/core/bpy_helpers/skinning/
├── bind_apply.py              [AMEND] both bind paths call snapshot_sidecar to populate entries
├── sidecar_io.py              [NEW] snapshot_sidecar / apply_sidecar (vertex_groups <-> entries via UVs)
└── automesh_hook.py           [NEW] pre/post regen hook for automesh operator

apps/blender/operators/
├── automesh.py                [AMEND] invokes automesh_hook pre + post regen when PG flag set
└── restore_weight_snapshot.py [NEW] PROSCENIO_OT_restore_weight_snapshot

apps/blender/properties/scene_props.py
                               [AMEND] add preserve_on_regen + show_provenance_overlay to ProscenioSkinningProps

apps/blender/panels/skinning.py
                               [AMEND] add _draw_snapshot_box helper (toggles + counts pill + Restore button)

tests/skinning/
├── test_sidecar_schema.py     [AMEND] SidecarEntry round-trip tests
└── test_weight_reproject.py   [NEW] reproject algorithm tests (4-6 tests)

apps/blender/tests/operators/
├── test_bind_mesh.py          [AMEND] bind now populates entries with provenance=auto_seed
├── test_automesh_regen.py     [NEW] bind -> automesh regen -> verify entries reprojected
└── test_restore_snapshot.py   [NEW] restore reverts current weights to last sidecar state
```

## Components

### Pure - `sidecar_schema.py` (amend)

```python
ProvenanceKind = Literal["auto_seed", "user_paint", "reprojected"]


@dataclass(frozen=True)
class SidecarEntry:
    """One per-vert record: UV anchor + bone weights + how the weights got there."""
    uv_anchor: tuple[float, float]
    weights: dict[str, float]
    provenance: ProvenanceKind


@dataclass(frozen=True)
class WeightSidecar:
    version: int
    vertex_group_names: list[str]
    mesh_topology_hash: str
    entries: list[SidecarEntry] = field(default_factory=list)  # was list[dict]
```

`to_json` / `from_json` adapt to nested SidecarEntry serialization via `dataclasses.asdict` + reconstructor.

### Pure - `weight_reproject.py` (NEW, ~120 LOC)

```python
def reproject_entries(
    old_entries: list[SidecarEntry],
    new_uv_anchors: list[Point2D],
    *,
    max_distance: float = 0.1,
) -> list[SidecarEntry | None]:
    """One output entry per new vert. None means 'no anchor in range, caller should auto_seed'.

    Algorithm:
    1. Build KDTree over old_entries' uv_anchors
    2. For each new_anchor:
       a. find 3 nearest old anchors within max_distance
       b. if fewer than 3 found, return None (out-of-range)
       c. compute barycentric coords of new_anchor in the triangle
       d. if barycentric degenerate (point outside triangle by > eps) -> return None
       e. else interpolate weights per bone, return SidecarEntry(provenance='reprojected')
    """
```

Uses `mathutils.kdtree` -> pure since stdlib `mathutils` is bpy-bundled but importable standalone in tests when faked. Actually `mathutils` requires Blender. So this module IS bpy-adjacent. Move to `bpy_helpers/` then? No - mathutils is available in Blender's bundled Python AND in fake-bpy-module for tests. Tests use a tiny KDTree replacement OR we hand-roll a simple O(n^2) KNN since n is small (typical sprite mesh < 1000 verts). Hand-roll keeps pure module truly pure.

```python
def _knn_3(
    anchors: list[Point2D], target: Point2D, max_distance: float
) -> list[tuple[int, float]]:
    """O(n) walk - returns up to 3 (index, distance) pairs sorted by distance, filtered by max_distance."""
```

### bpy - `sidecar_io.py` (NEW)

```python
def snapshot_sidecar(
    obj: bpy.types.Object, armature: bpy.types.Object, provenance: ProvenanceKind = "auto_seed"
) -> WeightSidecar:
    """Build a populated sidecar from obj's current vertex groups + UVs.

    For each vert:
    - read UV from active uv_layer's first loop containing the vert
    - read weights for each deform bone group
    - tag with provenance
    Returns WeightSidecar ready to JSON-serialize.
    """


def apply_sidecar(obj: bpy.types.Object, sidecar: WeightSidecar) -> dict[str, int]:
    """Write sidecar entries into obj's vertex groups.

    Counters: {verts_applied, groups_created, missing_uv_count}.
    Assumes obj's UV layer is the same one used at snapshot time.
    """
```

### bpy - `automesh_hook.py` (NEW)

```python
def maybe_pre_regen_snapshot(
    obj: bpy.types.Object, armature: bpy.types.Object
) -> WeightSidecar | None:
    """Snapshot weights into a sidecar BEFORE automesh wipes the mesh.

    Returns None when (a) no picker armature, (b) PG preserve_on_regen=False,
    (c) obj has no existing populated sidecar (= fresh-bind state).
    """


def maybe_post_regen_reproject(
    obj: bpy.types.Object, armature: bpy.types.Object, prior_sidecar: WeightSidecar
) -> dict[str, int]:
    """Reproject prior_sidecar entries onto obj's new topology + apply weights.

    Returns counters: {reprojected, auto_seed, total}.
    """
```

Automesh operator's `execute()` gains:

```python
# at start of execute, after validation
prior_sidecar = maybe_pre_regen_snapshot(obj, armature)

# ... existing automesh logic ...

# after automesh.build runs successfully + before report:
if prior_sidecar is not None:
    counts = maybe_post_regen_reproject(obj, armature, prior_sidecar)
    report_info(self, f"sidecar: {counts['reprojected']} reprojected + {counts['auto_seed']} auto-seed of {counts['total']} verts")
```

### Operator - `restore_weight_snapshot.py` (NEW)

```python
class PROSCENIO_OT_restore_weight_snapshot(bpy.types.Operator):
    bl_idname = "proscenio.restore_weight_snapshot"
    bl_label = "Proscenio: Restore Weight Snapshot"
    bl_description = (
        "Reapply the last saved weight sidecar to the active mesh. Reverts manual "
        "paint changes made after the most recent bind / automesh regen. Does NOT "
        "trigger automesh regen"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return obj.get("proscenio_weight_sidecar") is not None

    def execute(self, context):
        # 1. Read sidecar from obj["proscenio_weight_sidecar"]
        # 2. Validate topology_hash matches (else error)
        # 3. apply_sidecar(obj, sidecar) -> counters
        # 4. Report
```

### PropertyGroup amend

```python
preserve_on_regen: BoolProperty(
    name="Preserve weights on regen",
    description="When ON (default), automesh regen snapshots current weights + reprojects them onto the new topology via UV anchors",
    default=True,
)
show_provenance_overlay: BoolProperty(
    name="Show provenance overlay",
    description="Color verts by source: cyan=reprojected, white=user paint, gray=auto seed. Requires Wave 13.2-paint",
    default=False,
)
```

### Panel - new sub-box

Add `_draw_snapshot_box(layout, skinning_props, sidecar_json)` after Bind box, before Debug:

```text
+- Snapshot ---------------------------+
| [x] Preserve weights on regen        |
| [ ] Show provenance overlay          |
| 187 paint / 42 seed / 12 reprojected |
| [    Restore Weight Snapshot    ]    |
+--------------------------------------+
```

Counts read live from `obj["proscenio_weight_sidecar"]` JSON (parse + count by provenance). Restore button disabled when no sidecar exists.

## Data flow

```text
User clicks Automesh from Sprite (with preserve_on_regen=True, sidecar populated):
  -> automesh.execute()
       maybe_pre_regen_snapshot(obj, armature) -> WeightSidecar (current state)
       build_automesh() -> mesh regenerated (topology changes)
       maybe_post_regen_reproject(obj, armature, prior_sidecar)
         -> reproject_entries(prior_entries, new_uv_anchors)
         -> apply_sidecar(obj, new_sidecar)
         -> counters {reprojected: N, auto_seed: M}
       report INFO with counts
       FINISHED

User clicks Restore Weight Snapshot:
  -> restore_weight_snapshot.execute()
       sidecar = from_json(obj["proscenio_weight_sidecar"])
       if sidecar.mesh_topology_hash != current_hash:
         ERROR "topology changed since snapshot - run automesh regen with preserve_on_regen ON"
         CANCELLED
       apply_sidecar(obj, sidecar) -> counters
       report INFO "restored N verts"
       FINISHED

User clicks Bind to Picker Armature (any mode):
  -> bind_mesh.execute()
       ... existing diagnose + apply_bind ...
       (apply_bind now internally calls snapshot_sidecar after writing weights)
       result sidecar has entries populated with provenance=auto_seed
       FINISHED
```

## Error matrix

| Condition | Action | Message |
| --- | --- | --- |
| Snapshot (pre-regen): mesh has no UV layer | WARN + empty entries | `mesh has no UV layer - sidecar entries empty; bind still wrote vertex groups` |
| Post-regen reproject: new mesh has no UV layer | WARN + auto_seed stub | `target mesh has no UVs - skipping reproject, sidecar reset to auto_seed stub` |
| Sidecar topology_hash mismatch on Restore | ERROR + abort | `topology changed since last snapshot - automesh regen with preserve_on_regen ON to re-establish` |
| Reproject: all entries out of range | WARN + continue with auto_seed | `{N} verts reprojected, {M} fell back to auto-seed (sprite changed significantly)` |
| Corrupt sidecar JSON | ERROR + abort | `existing sidecar is corrupt: {ValueError msg}; re-bind to reset` |

## Test plan

### Pure pytest

`tests/skinning/test_sidecar_schema.py` (amend, 2 new):

- `test_entry_round_trip` - SidecarEntry serializes + parses + matches
- `test_v1_with_populated_entries` - to_json / from_json with non-empty entries preserves provenance values

`tests/skinning/test_weight_reproject.py` (NEW, 5 tests):

- `test_identical_topology_passes_through` - same UV anchors -> weights identical, all marked reprojected
- `test_coarser_to_finer_interpolates` - 4 anchors at corners -> 9 new anchors on 3x3 grid -> middle anchor gets averaged weights
- `test_far_anchor_falls_back_to_none` - new anchor outside max_distance from all old -> returns None
- `test_degenerate_triangle_returns_none` - 3 nearest are collinear -> caller falls back to auto_seed
- `test_single_bone_weight_preserved` - all entries have weight 1.0 on one bone -> reprojected also weight 1.0

### Headless operator pytest

`apps/blender/tests/operators/test_bind_mesh.py` (amend):

- update `test_bind_writes_sidecar_stub` -> `test_bind_writes_populated_sidecar` (entries now > 0, all provenance=auto_seed)

`apps/blender/tests/operators/test_automesh_regen.py` (NEW):

- `test_automesh_regen_with_preserve_on_reprojects` - bind hand, automesh regen with preserve=True, verify entries reprojected count > 0
- `test_automesh_regen_with_preserve_off_wipes` - bind hand, set PG preserve_on_regen=False, automesh regen, verify no reproject (entries empty post-regen)

`apps/blender/tests/operators/test_restore_snapshot.py` (NEW):

- `test_restore_after_paint_reverts_to_snapshot` - bind, manually mutate vert group weight, restore -> weight matches snapshot
- `test_restore_with_stale_topology_aborts` - bind, regen with preserve=False, restore -> CANCELLED

### MANUAL_TESTING.md 1.21

```text
T1 - Sidecar populated on bind:
  Bind hand sprite. Object Properties > Custom Properties > proscenio_weight_sidecar JSON has entries list (not []), each entry has uv_anchor + weights + provenance="auto_seed".

T2 - Automesh regen preserves weights:
  Bind hand. Note the wrist vertex group's gradient pattern.
  Skinning panel > Snapshot sub-box > confirm "preserve_on_regen" is ON.
  Click Automesh from Sprite (resolution 0.5 or any different value).
  Info bar: "sidecar: N reprojected + M auto-seed of K verts".
  Switch to Weight Paint mode. Wrist gradient pattern similar to pre-regen.

T3 - Restore Weight Snapshot:
  Bind hand. Switch to Weight Paint, manually paint over part of the wrist group (set some verts to 0).
  Skinning panel > Snapshot > click "Restore Weight Snapshot".
  Info bar: "restored N verts".
  Painted area returns to original gradient.

T4 - Counts pill:
  After bind, Snapshot sub-box shows e.g. "0 paint / 187 seed / 0 reprojected".
  After regen with preserve ON: counts shift (some reprojected appear).
```

## Out of scope (deferred)

- Provenance overlay GPU draw handler -> Wave 13.2-paint
- Live `user_paint` provenance tagging via paint modal diff -> Wave 13.2-paint
- Sidecar import/export to external file -> Wave 13.3
- `proscenio.copy_weights_to_selected` cross-mesh transfer -> Wave 13.3
- Sidecar versioning bump infrastructure (v2/v3) -> only when schema actually breaks
