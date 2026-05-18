# Wave 13.2 - Planar Proximity Bind: Design

Status: design locked via `/brainstorming` session 2026-05-17. Ready for implementation plan.

Scope: bind a mesh to a picker armature via a custom planar-distance algorithm that never hits Blender's bone-heat solver, surface structured diagnoses when something goes wrong, write a sidecar stub that Wave 13.2-sidecar consumes for reproject.

Locked SPEC decisions: D4 (no bone heat default), D5 (PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY enum), D11 (pre-flight structured diagnoses).

## Decisions (brainstorming output)

| # | Decision | Locked value | Rationale |
| --- | --- | --- | --- |
| Q1 | `falloff_power` default | **2.0** (inverse square) | Animate / Spine / DragonBones convention. Sharp enough for cutout 2D, smooth enough to avoid binary feel. |
| Q2 | `max_distance` default | **adaptive: 1.5 * armature world bbox max extent** | Scales with rig. User overridable via F3 redo (-1 = adaptive sentinel). |
| Q3 | Sidecar capture timing | **bind writes minimal stub now** (version + vertex_group_names + topology_hash + entries=[]) | Schema locked early. Wave 13.2-sidecar populates entries; bind never touched again. |
| Q4 | Pre-flight diagnose scope | **all 5** (scale, normals, overlap, islands, bone_bbox) | Diagnose surface = #1 community pain (D11 STUDY). Each helper ~20 LOC, ~150 LOC total. |
| Q5 | Orphan vert behaviour | **WARN + count + suggested fix** | Vert with 0 bones in range = static under deformation = visible tear. User must know. |
| Q6 | Existing vertex groups | **preserve `proscenio_base_sprite`, wipe rest, recreate** | D3 UV anchor sobrevive. Bone groups from prior bind get refreshed. |
| Q7 | Test layering | **pure pytest + headless operator pytest + minimal MANUAL_TESTING** | Headless operator pytest is the new layer; bind ships the pattern + MANUAL_TESTING shrinks to UI/modal-only residue. |

## Architecture

Domain package layout matching the cleanup convention adopted in Wave 13.2 (PR #52):

```text
apps/blender/core/skinning/
├── __init__.py                  # re-exports public surface
├── planar_proximity.py          # pure: 1/dist^2 falloff + normalize
├── bind_diagnosis.py            # pure: 5 BindDiagnosis checks
├── skinning_modes.py            # pure: BindMode enum + dispatcher
└── sidecar_schema.py            # pure: WeightSidecar dataclass + topology_hash

apps/blender/core/bpy_helpers/skinning/
├── __init__.py
├── diagnose_collect.py          # bpy: walks obj/armature, calls pure checks
└── bind_apply.py                # bpy: vertex groups + sidecar stub write

apps/blender/operators/bind_mesh.py
                                 # PROSCENIO_OT_bind_mesh_to_armature

apps/blender/tests/operators/
├── conftest.py                  # fixture loader + addon register
└── test_bind_mesh.py            # 6 headless operator tests

apps/blender/tests/run_operator_tests.py
                                 # pytest entry point invoked by CI

tests/skinning/
├── test_planar_proximity.py     # pure pytest
├── test_bind_diagnosis.py       # pure pytest
├── test_skinning_modes.py       # pure pytest
└── test_sidecar_schema.py       # pure pytest
```

Pure / bpy split:

- Algorithm, diagnoses, schema = pure (zero bpy import; pytest-able without Blender).
- Vertex group write + bone segment extraction = bpy-bound.
- Operator = orchestrator + F3 properties + reports.

Reuses `distance_to_segment` from `core.automesh.density` (already pure-Python, already tested). No new generic-geometry module.

## Components

### Pure modules

`planar_proximity.py` (~80 LOC):

```python
def compute_proximity_weights(
    vert_xz: Point2D,
    bone_segments: list[BoneSegment2D],   # (head_xz, tail_xz, bone_name)
    falloff_power: float = 2.0,
    max_distance: float | None = None,
) -> dict[str, float]:
    """1/dist^falloff per bone, filter by max_distance, normalize sum=1."""
```

Empty dict when no bones survive the max_distance filter (orphan vert signal for the bpy caller).

`bind_diagnosis.py` (~150 LOC):

```python
DiagnosisKind = Literal["scale", "normals", "overlap", "islands", "bone_bbox"]
Severity = Literal["error", "warn"]

@dataclass(frozen=True)
class BindDiagnosis:
    kind: DiagnosisKind
    severity: Severity
    message: str
    hint: str

def diagnose_scale(scale_xyz) -> BindDiagnosis | None        # error if any axis != 1.0 (eps 1e-4)
def diagnose_flipped_normals(face_normals) -> BindDiagnosis | None  # error if any normal Y < 0
def diagnose_overlapping_verts(vert_positions, eps=1e-5) -> BindDiagnosis | None  # warn if any pair within eps
def diagnose_isolated_islands(face_indices, vert_count) -> BindDiagnosis | None   # warn if >1 island via union-find
def diagnose_bones_outside_bbox(mesh_bbox, bone_segments_world) -> BindDiagnosis | None  # warn if any bone outside
```

`skinning_modes.py` (~100 LOC):

```python
BindMode = Literal["PROXIMITY", "ENVELOPE", "SINGLE_NEAREST", "EMPTY"]

def bind_weights_for_mode(
    mode: BindMode,
    vert_positions_xz: list[Point2D],
    bone_segments: list[BoneSegment2D],
    *,
    falloff_power: float = 2.0,
    max_distance: float | None = None,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, list[float]]:
    """Per-bone list of per-vert weights. Dispatches by mode."""
```

- PROXIMITY -> calls `compute_proximity_weights` per vert, transposes.
- ENVELOPE -> per-vert weight = 1 if vert within `envelope_radii[bone]`, else 0; normalized.
- SINGLE_NEAREST -> per-vert pick nearest bone, weight 1.0; tie-break = first in `armature.data.bones` order.
- EMPTY -> all-zero weights for every (bone, vert).

`sidecar_schema.py` (~60 LOC):

```python
SIDECAR_VERSION = 1

@dataclass(frozen=True)
class WeightSidecar:
    version: int
    vertex_group_names: list[str]
    mesh_topology_hash: str
    entries: list[dict]   # Wave 13.2-sidecar populates; bind leaves []

def compute_topology_hash(vert_count: int, face_indices: list[list[int]]) -> str:
    """sha1(f'{vert_count}|{sorted_face_tuples}') hex."""

def build_minimal_stub(vertex_group_names, topology_hash) -> WeightSidecar
def to_json(sidecar: WeightSidecar) -> str
def from_json(s: str) -> WeightSidecar
```

### bpy-bound modules

`diagnose_collect.py` (~120 LOC):

```python
def collect_diagnoses_for_object(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
) -> list[BindDiagnosis]:
    """Extract primitive data from bpy + call 5 pure checks. Returns merged list."""
```

Mappings:

- Scale: `obj.scale[:]`.
- Normals: bmesh `face.normal` per polygon.
- Overlap: bmesh vert positions + KD-tree (`mathutils.kdtree`) when verts > 1000, else O(n^2).
- Islands: bmesh `select_linked` walk; count connected components.
- Bone bbox: `armature.matrix_world @ bone.head/tail` per deform bone; mesh world bbox from `obj.bound_box` transformed by `obj.matrix_world`.

`bind_apply.py` (~180 LOC):

```python
def apply_bind(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    mode: BindMode,
    *,
    falloff_power: float = 2.0,
    max_distance: float = -1.0,   # < 0 = adaptive (1.5 * armature world bbox extent)
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, int]:
    """Returns counters: {verts_bound, orphan_verts, groups_created, bones_used}."""
```

Side effects:

1. Wipes every vertex group EXCEPT `proscenio_base_sprite`.
2. Creates one vertex group per deform bone in the picker armature.
3. Populates per-vertex weights via `vertex_groups[name].add([vert_idx], weight, "REPLACE")`.
4. Writes `obj["proscenio_weight_sidecar"]` = JSON of `WeightSidecar` stub.

ENVELOPE mode radii sourcing: when `mode="ENVELOPE"`, `apply_bind` reads each deform bone's `bone["proscenio_envelope_radius"]` Custom Property; missing keys default to `1.0` world units. The dict is built once + passed into `bind_weights_for_mode` as `envelope_radii`. Edit Weights modal (Wave 13.2-paint) becomes the UI surface for tuning these radii; bind feature alone exposes them via the manual Custom Property editor only.

Vert + bone coord conversion: both projected to XZ world space.

- Bone segments world: `armature.matrix_world @ bone.head/tail`, drop Y.
- Mesh verts world: `obj.matrix_world @ vert.co`, drop Y.

Adaptive max_distance when input < 0: `1.5 * max(armature_world_bbox.extent.x, .y, .z)`.

Orphan: vert where sum(weights across bones) < 1e-6.

### Operator

`bind_mesh.py` (~150 LOC):

```python
class PROSCENIO_OT_bind_mesh_to_armature(bpy.types.Operator):
    bl_idname = "proscenio.bind_mesh_to_armature"
    bl_label = "Bind Mesh to Picker Armature"
    bl_options = {"REGISTER", "UNDO"}

    bind_init_mode: EnumProperty(
        items=[("PROXIMITY",...), ("ENVELOPE",...), ("SINGLE_NEAREST",...), ("EMPTY",...)],
        default="PROXIMITY",
    )
    falloff_power: FloatProperty(default=2.0, min=0.5, max=8.0)
    max_distance: FloatProperty(default=-1.0,
        description="< 0 = adaptive (1.5x armature bbox)")
    use_bone_heat: BoolProperty(default=False,
        description="OPT-IN ONLY (D4) - legacy bone-heat path. Default OFF.")

    def execute(self, context):
        ...
```

Execute flow:

1. Resolve picker armature (`scene.proscenio.active_armature`). Error if missing or not ARMATURE.
2. Validate active obj is MESH with > 0 verts.
3. `collect_diagnoses_for_object` -> if any severity=error, report each + abort.
4. Report any severity=warn diagnoses as INFO + continue.
5. If `use_bone_heat=True`: delegate to `bpy.ops.object.parent_set(type="ARMATURE_AUTO")` raw (per D4 opt-in; surface raw Blender error if it raises) + skip the rest.
6. `apply_bind(...)` -> counters.
7. If `counters["orphan_verts"] > 0`, WARN report ("N verts have no bone in range - increase max_distance or move armature closer").
8. INFO report: "bind: {verts_bound} verts to {bones_used} bones ({orphan_verts} orphans). Mode={mode}."
9. Return `{"FINISHED"}`.

### Tests

#### Pure pytest (`tests/skinning/`)

Mirror automesh layout. Each pure helper gets a test file. Total ~20 tests across 4 files. Examples:

```python
# test_planar_proximity.py
def test_two_equidistant_bones_get_equal_weight():
    out = compute_proximity_weights((0.5, 0), [((0,0),(0,0),"A"), ((1,0),(1,0),"B")])
    assert out == {"A": 0.5, "B": 0.5}

def test_bone_beyond_max_distance_filtered():
    out = compute_proximity_weights((0,0), [((100,0),(100,0),"far")], max_distance=1.0)
    assert out == {}

# test_bind_diagnosis.py
def test_unapplied_scale_returns_error():
    d = diagnose_scale((2.0, 2.0, 2.0))
    assert d.kind == "scale" and d.severity == "error"

# test_skinning_modes.py
def test_EMPTY_mode_returns_zero_weights():
    out = bind_weights_for_mode("EMPTY", [(0,0),(1,0)], [((0,0),(0,0),"A")])
    assert out == {"A": [0.0, 0.0]}

# test_sidecar_schema.py
def test_topology_hash_sensitive_to_vert_count():
    assert compute_topology_hash(4, [[0,1,2]]) != compute_topology_hash(5, [[0,1,2]])
```

#### Headless operator pytest (`apps/blender/tests/operators/test_bind_mesh.py`)

NEW LAYER. Runs INSIDE Blender via `apps/blender/tests/run_operator_tests.py` (~50 LOC entry that invokes `pytest.main` on the operators dir after mounting + registering the addon + opening the fixture .blend).

6 tests cover the bind happy path + diagnoses + sidecar foundation:

```python
def test_bind_happy_path(automesh_fixture):
    obj = bpy.data.objects["hand"]
    bpy.context.view_layer.objects.active = obj
    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "FINISHED" in result
    assert len(obj.vertex_groups) == 4  # base_sprite + 3 bones
    assert {"wrist", "palm", "fingertip"} <= {g.name for g in obj.vertex_groups}

def test_bind_diagnose_unapplied_scale(automesh_fixture):
    obj = bpy.data.objects["hand"]
    obj.scale = (2.0, 2.0, 2.0)  # NOT applied
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "CANCELLED" in result

def test_bind_diagnose_bones_outside_bbox_warns_but_proceeds(automesh_fixture):
    bpy.data.objects["automesh.hand_rig"].location.x = 100.0
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "FINISHED" in result   # warn does not abort

def test_bind_preserves_base_sprite_group_on_rerun(automesh_fixture):
    # automesh first to create base_sprite group
    bpy.ops.proscenio.automesh_from_sprite()
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "proscenio_base_sprite" in {g.name for g in bpy.context.active_object.vertex_groups}
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="SINGLE_NEAREST")  # re-bind different mode
    assert "proscenio_base_sprite" in {g.name for g in bpy.context.active_object.vertex_groups}

def test_bind_writes_sidecar_stub(automesh_fixture):
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    payload = bpy.context.active_object.get("proscenio_weight_sidecar")
    sidecar = json.loads(payload)
    assert sidecar["version"] == 1
    assert sidecar["entries"] == []
    assert "wrist" in sidecar["vertex_group_names"]

def test_bind_SINGLE_NEAREST_one_bone_per_vert(automesh_fixture):
    obj = bpy.data.objects["hand"]
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="SINGLE_NEAREST")
    # Each vert should have weight 1.0 in exactly one bone group
    for vert in obj.data.vertices:
        weights = [g.weight for g in vert.groups
                   if obj.vertex_groups[g.group].name in {"wrist", "palm", "fingertip"}]
        assert len([w for w in weights if w > 0.5]) == 1
```

CI wired: new step in `test-blender` job invokes `~/blender/blender --background --python apps/blender/tests/run_operator_tests.py`.

#### MANUAL_TESTING residue

`tests/MANUAL_TESTING.md` 1.20 gains ONE entry only (UI-only, can't be headless tested):

```text
T1 - Panel button vs F3 redo:
  Skinning panel > Bind to Picker Armature button.
  Then F3 → bind operator visible with all properties exposed.
  Mode dropdown shows 4 options. use_bone_heat checkbox visible in F3 but NOT in panel.
```

Everything else in T2-T6 = covered by headless operator pytest above.

## Data flow

```text
operator.execute()
  ↓
resolve picker armature (active_armature from scene)
  ↓ if None → ERROR + abort
collect_diagnoses_for_object(obj, armature) → list[BindDiagnosis]
  ↓ filter severity=error → if any: report each + abort
  ↓ filter severity=warn → report each as INFO + continue
apply_bind(obj, armature, mode, **opts) → counters dict
  ↓ extract bone_segments_world + adaptive max_distance
  ↓ dispatch skinning_modes.bind_weights_for_mode
  ↓ wipe non-base vertex groups + recreate per-bone + populate weights
  ↓ write obj["proscenio_weight_sidecar"] = JSON stub
  ↓
if counters.orphan_verts > 0 → WARN report
INFO report: "bind: N verts to K bones (M orphans). Mode=X."
return {"FINISHED"}
```

Sidecar atomicity: written AFTER vertex groups succeed. If `apply_bind` raises mid-write, sidecar absent on next run = fresh seed (no false reproject). Acceptable.

## Error matrix

| Condition | Action | Message template |
| --- | --- | --- |
| No picker armature | ERROR + abort | `no picker armature set - pick one in Skeleton panel first` |
| Picker has no deform bones | ERROR + abort | `picker '{name}' has no deform bones - enable deform on bones first` |
| Active obj not mesh | ERROR + abort | `active object must be a mesh` |
| Mesh has 0 verts | ERROR + abort | `mesh has 0 verts` |
| diagnose `scale` (severity=error) | ERROR + abort | `mesh has unapplied scale {x,y,z} - press Ctrl+A → Scale` |
| diagnose `normals` (error) | ERROR + abort | `mesh has flipped face normals - select all + Mesh → Normals → Recalculate Outside` |
| diagnose `overlap` (warn) | WARN + continue | `{N} overlapping vert pairs detected - consider Mesh → Clean Up → Merge by Distance` |
| diagnose `islands` (warn) | WARN + continue | `{N} isolated islands - each will be bound independently` |
| diagnose `bone_bbox` (warn) | WARN + continue | `{N}/{total} bones outside mesh bbox - those weights will be 0` |
| `apply_bind` raises | ERROR + abort | `bind failed: {exc}` |
| `orphan_verts > 0` | WARN + continue | `{N} verts have no bone in range - increase max_distance or move armature closer` |
| `use_bone_heat=True` raises | ERROR + surface raw | `(raw Blender bone-heat error verbatim)` |

## Out of scope (deferred)

- Coverage report pipeline (pytest-cov + sonar-scanner push) → chore wave separada pós-bind.
- Hypothesis property-based testing for pure math → backlog.
- ENVELOPE radii editor UI → Wave 13.2-paint (Edit Weights modal owns it).
- Scene PropertyGroup persistence for bind_init_mode / falloff_power / max_distance → Wave 13.2-panel (operator F3 properties stand alone for this wave).
- Sidecar `entries` population + reproject logic → Wave 13.2-sidecar (foundation only here).
- `proscenio.copy_weights_to_selected` (multi-mesh batch) → Wave 13.3.
- BONE_HEAT BindMode enum value → not added; bone-heat stays behind the F3-only opt-in BoolProperty per D4.

## Open follow-ups (post-merge)

- Convention update: `.ai/conventions.md` gains a "headless operator pytest pattern" subsection documenting the runner script + fixture loader + addon register sequence. New pattern - future operators (paint, sidecar, modal) reuse it.
- SPEC 013 TODO Wave 13.2 bind entry refined with this design's checklist + links.
- CI workflow YAML: add `Headless operator tests` step to `test-blender` job, after the existing fixture diff step.
