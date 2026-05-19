# Wave 13.2 - Skinning Panel + Bind Pivot B: Design

Status: design locked via `/brainstorming` session 2026-05-19. Ready for implementation plan.

Scope: add Bind sub-box to the existing `PROSCENIO_PT_skinning` panel, persist bind settings via `ProscenioSkinningProps`, and pivot D4 - BONE_HEAT becomes the default bind mode (real-world feedback post PR #54: bone heat works better than our planar proximity for the common case of bones co-planar with sprites).

Locked decisions: D13 (subpanel placement), D4 AMENDMENT (bone heat allowed as default), D5 (5-value BindMode enum: BONE_HEAT / PROXIMITY / ENVELOPE / SINGLE_NEAREST / EMPTY).

## Decisions (brainstorming output)

| # | Decision | Locked value | Rationale |
| --- | --- | --- | --- |
| Q1 | Wave scope | **Bind sub-box only** | Edit Weights + Snapshot ship in their own waves (paint/sidecar). Keeps PR tight + reviewable. |
| Q2 | BONE_HEAT representation | **Value of `bind_init_mode` enum** | Replaces the separate `use_bone_heat: BoolProperty` (redundant). Single dropdown UX. Default = `BONE_HEAT`. |
| Q3 | Panel surface | **Mode dropdown + button only** | Falloff + max_distance accessible via F3 redo. Casual user UI clean; power-user controls one hotkey away. |
| Q4 | Disable rule | **Disabled when picker armature missing** | Most common pain (no picker) caught visually; other diagnoses (scale/normals/etc) surface as ERROR reports on click. |

## D4 amendment

Original D4: "bone heat solver usage = explicit user opt-in only, NEVER default. No default-bind code path may call `parent_with_automatic_weights` blind."

Amended D4: "bone heat solver = ALLOWED as default for the 2D picker workflow (bones co-planar with sprite). The COA Tools 2 pain D4 was guarding against (3D character bone heat failures) does not apply when bones are tangent to the sprite plane. Our planar proximity algorithm becomes an opt-in fallback for cases where bone heat fails or finer control is needed. The 5 D11 pre-flight diagnoses still run before ANY bind path."

Trigger: manual smoke on PR #54 showed (a) bone heat produces visibly better falloff in the common case and (b) our 1/dist^p normalization spreads weight to all bones in range, including ones far from the vert, producing washed-out gradients vs bone heat's tight local influence.

## Architecture

Reuses existing structure - no new packages, no relocations:

- `apps/blender/core/skinning/skinning_modes.py` - amend `BindMode` literal + dispatcher
- `apps/blender/core/bpy_helpers/skinning/bind_apply.py` - amend `apply_bind` to delegate when mode is BONE_HEAT
- `apps/blender/operators/bind_mesh.py` - amend enum default, remove `use_bone_heat` BoolProperty, add invoke() that reads PG
- `apps/blender/properties/scene_props.py` - amend `ProscenioSkinningProps` with 3 bind fields
- `apps/blender/panels/skinning.py` - amend with `_draw_bind_box` helper between Automesh and Debug sub-boxes

## Components

### Pure - `skinning_modes.py`

```python
BindMode = Literal["BONE_HEAT", "PROXIMITY", "ENVELOPE", "SINGLE_NEAREST", "EMPTY"]


def bind_weights_for_mode(
    mode: BindMode,
    vert_positions_xz: list[Point2D],
    bone_segments: list[BoneSegmentNamed2D],
    *,
    falloff_power: float = 2.0,
    max_distance: float | None = None,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, list[float]] | None:
    """Returns None for BONE_HEAT (signal: caller delegates to Blender).
    Otherwise per-bone list of per-vert weights as before.
    """
    if mode == "BONE_HEAT":
        return None
    # ... existing branches unchanged
```

The `None` sentinel keeps the pure module zero-bpy. The bpy caller in `bind_apply.py` checks for `None` and dispatches to `_delegate_to_bone_heat`.

### bpy - `bind_apply.py`

```python
def apply_bind(
    obj: bpy.types.Object,
    armature: bpy.types.Object,
    mode: BindMode,
    *,
    falloff_power: float = 2.0,
    max_distance: float = -1.0,
    envelope_radii: dict[str, float] | None = None,
) -> dict[str, int]:
    """Existing signature + return shape preserved. Adds BONE_HEAT branch."""
    if mode == "BONE_HEAT":
        return _apply_bone_heat(obj, armature)
    # ... existing flow for our algorithms

def _apply_bone_heat(obj, armature) -> dict[str, int]:
    """Wipes prior groups, runs ARMATURE_AUTO, stamps sidecar.

    Atomicity matches the algorithm path: sidecar cleared BEFORE the
    bpy.ops call, stamped AFTER on success. Failure raises RuntimeError
    upward; caller (operator) surfaces hint about trying PROXIMITY.
    """
    # 1. Clear prior sidecar
    if _SIDECAR_KEY in obj:
        del obj[_SIDECAR_KEY]
    # 2. Wipe non-base groups
    groups_wiped = _wipe_non_base_groups(obj)
    # 3. Run Blender bone heat
    prior_active = bpy.context.view_layer.objects.active
    try:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    finally:
        bpy.context.view_layer.objects.active = prior_active
    # 4. Stamp sidecar with topology hash + names of generated groups
    deform_bone_names = [b.name for b in armature.data.bones if b.use_deform]
    topology_hash = compute_topology_hash(
        len(obj.data.vertices),
        [list(p.vertices) for p in obj.data.polygons],
    )
    obj[_SIDECAR_KEY] = to_json(build_minimal_stub(deform_bone_names, topology_hash))
    # 5. Count orphans (vert with sum-of-weights < eps)
    orphan_verts = _count_orphans(obj, deform_bone_names)
    return {
        "verts_bound": len(obj.data.vertices),
        "orphan_verts": orphan_verts,
        "groups_created": len(deform_bone_names),
        "bones_used": len(deform_bone_names),
        "groups_wiped": groups_wiped,
    }
```

### Operator - `bind_mesh.py`

```python
class PROSCENIO_OT_bind_mesh_to_armature(bpy.types.Operator):
    bl_idname = "proscenio.bind_mesh_to_armature"
    bl_label = "Proscenio: Bind Mesh to Picker Armature"
    bl_options = {"REGISTER", "UNDO"}

    bind_init_mode: EnumProperty(
        items=[
            ("BONE_HEAT", "Bone Heat (Blender native)",
             "Delegate to Blender's Parent w/ Auto Weights (recommended for sprites with bones on the picture plane)"),
            ("PROXIMITY", "Proximity (1/d^p)", "..."),
            ("ENVELOPE", "Envelope", "..."),
            ("SINGLE_NEAREST", "Single nearest", "..."),
            ("EMPTY", "Empty", "..."),
        ],
        default="BONE_HEAT",
    )
    falloff_power: FloatProperty(default=2.0, min=0.5, max=8.0)
    max_distance: FloatProperty(default=-1.0)
    # use_bone_heat REMOVED

    def invoke(self, context, _event):
        # Read PG defaults so panel + F3 redo both reflect persisted settings
        scene_props = getattr(context.scene, "proscenio", None)
        skinning = getattr(scene_props, "skinning", None) if scene_props else None
        if skinning is not None:
            self.bind_init_mode = str(skinning.bind_init_mode)
            self.falloff_power = float(skinning.bind_falloff_power)
            self.max_distance = float(skinning.bind_max_distance)
        return self.execute(context)

    def execute(self, context):
        # ... validations + diagnoses (unchanged from PR #54)
        try:
            counters = apply_bind(obj, armature, self.bind_init_mode,
                                  falloff_power=self.falloff_power,
                                  max_distance=self.max_distance)
        except RuntimeError as exc:
            if self.bind_init_mode == "BONE_HEAT":
                report_error(self,
                    f"bone-heat failed: {exc}. Try mode=PROXIMITY as fallback "
                    "(Skinning panel > Bind mode dropdown)")
            else:
                report_error(self, f"bind failed: {exc}")
            return {"CANCELLED"}
        # ... orphan/wiped/info reports (unchanged)
        return {"FINISHED"}
```

### PropertyGroup - `scene_props.py`

Adds to `ProscenioSkinningProps`:

```python
bind_init_mode: EnumProperty(
    name="Bind mode",
    description="Algorithm used by Bind to Picker Armature",
    items=[
        ("BONE_HEAT", "Bone Heat (Blender native)", "..."),
        ("PROXIMITY", "Proximity (1/d^p)", "..."),
        ("ENVELOPE", "Envelope", "..."),
        ("SINGLE_NEAREST", "Single nearest", "..."),
        ("EMPTY", "Empty", "..."),
    ],
    default="BONE_HEAT",
)
bind_falloff_power: FloatProperty(
    name="Bind falloff power",
    description="Exponent for 1/dist^power (PROXIMITY only)",
    default=2.0, min=0.5, max=8.0,
)
bind_max_distance: FloatProperty(
    name="Bind max distance",
    description="Bones beyond this distance contribute zero. -1 = adaptive (1.5x armature bbox). PROXIMITY only",
    default=-1.0,
)
```

Field naming: `bind_` prefix avoids collision with `automesh_*` fields already in the PG.

### Panel - `skinning.py`

New helper:

```python
def _draw_bind_box(
    layout: bpy.types.UILayout,
    skinning_props: bpy.types.PropertyGroup | None,
    picker: bpy.types.Object | None,
) -> None:
    """Sub-box for the Bind to Picker Armature operator."""
    box = layout.box()
    box.label(text="Bind to picker", icon="LINK_BLEND")
    if skinning_props is not None:
        box.prop(skinning_props, "bind_init_mode", text="Mode")
    row = box.row()
    row.enabled = picker is not None
    row.operator(
        "proscenio.bind_mesh_to_armature",
        text="Bind to Picker Armature",
        icon="MOD_ARMATURE",
    )
```

Wire into `PROSCENIO_PT_skinning.draw`:

```python
_draw_automesh_box(layout, skinning_props)
_draw_bind_box(layout, skinning_props, picker)   # NEW between automesh + debug
_draw_debug_box(layout, skinning_props)
```

## Data flow

```text
User clicks "Bind to Picker Armature" in Skinning panel
  -> invoke() reads scene.proscenio.skinning defaults
  -> execute()
       validations (mesh / verts / picker / deform bones)
       collect_diagnoses_for_object - ALWAYS runs
         errors? report each + CANCELLED
         warns? report INFO + continue
       apply_bind(mode=BONE_HEAT or PROXIMITY/...)
         BONE_HEAT: delegate to bpy.ops.object.parent_set ARMATURE_AUTO
                    sidecar cleared pre-call, stamped post-call (atomic)
         others:    existing weight computation path (PR #54)
       report counters + FINISHED
```

## Error matrix (additions)

| Condition | Action | Message template |
| --- | --- | --- |
| `bone-heat raises RuntimeError` | ERROR + abort | `bone-heat failed: {exc}. Try mode=PROXIMITY as fallback (Skinning panel > Bind mode dropdown)` |
| `picker armature missing (panel state)` | Button disabled + tooltip | (no message; visual gray-out) |

Original error matrix from `bind-design.md` is preserved unchanged for the non-BONE_HEAT paths.

## Migration from PR #54

Breaking changes (acceptable - addon pre-1.0, no programmatic users):

- `use_bone_heat: BoolProperty` removed from operator (replaced by `bind_init_mode="BONE_HEAT"`)
- Default `bind_init_mode` changes from `PROXIMITY` to `BONE_HEAT`
- Headless operator tests update assertions to expect BONE_HEAT default behavior

Documented in commit body + amended D4 entry in STUDY.md / TODO.md.

## Testing

### Pure pytest (`tests/skinning/`)

Add to `test_skinning_modes.py`:

```python
def test_bone_heat_mode_returns_none():
    # BONE_HEAT is a sentinel; bpy caller delegates to Blender
    out = bind_weights_for_mode(
        "BONE_HEAT", [(0.0, 0.0)], [((0.0, 0.0), (0.0, 0.0), "A")]
    )
    assert out is None
```

### Headless operator pytest (`apps/blender/tests/operators/test_bind_mesh.py`)

Update existing `test_bind_happy_path` assertion to expect BONE_HEAT path (still produces vertex groups, sidecar still written).

Add:

```python
def test_bind_explicit_proximity_still_works(automesh_fixture):
    """Power-user fallback path still functions when explicitly chosen."""
    _activate("hand")
    _set_picker("automesh.hand_rig")
    result = bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="PROXIMITY")
    assert "FINISHED" in result


def test_bind_writes_sidecar_for_bone_heat(automesh_fixture):
    """Sidecar invariant: stub stamped regardless of algorithm."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature(bind_init_mode="BONE_HEAT")
    payload = obj.get("proscenio_weight_sidecar")
    assert payload is not None
    sidecar = json.loads(payload)
    assert sidecar["version"] == 1
    assert sidecar["entries"] == []
```

### MANUAL_TESTING.md (`1.20` update)

Replace existing forward-looking note with concrete steps using the new panel button:

```text
T1 - Panel button + BONE_HEAT default:
  Open examples/generated/automesh/automesh.blend. Set picker armature in Skeleton subpanel.
  Select hand sprite. Sidebar (N) > Proscenio > Skinning > Bind to picker box.
  1. Confirm Mode dropdown defaults to "Bone Heat (Blender native)".
  2. Click "Bind to Picker Armature" button.
  3. Confirm info bar: "Proscenio: bind: N verts to 3 bones (M orphans). Mode=BONE_HEAT".
  4. Switch to Weight Paint mode, confirm wrist/palm/fingertip vertex groups exist with gradient.
  5. Switch Mode dropdown to "Proximity (1/d^p)", click button again.
  6. Confirm second bind succeeded + sidecar got re-stamped (Object Properties > Custom Properties > proscenio_weight_sidecar).
T2 - Panel button disabled when picker missing:
  Skeleton subpanel > clear picker armature (X button).
  Skinning > Bind sub-box: button greyed out, tooltip "set picker first".
```

## Out of scope (deferred to other waves)

- Edit Weights sub-box (Wave 13.2-paint - depends on edit_weights modal operator)
- Snapshot sub-box (Wave 13.2-sidecar - depends on restore_weight_snapshot operator + populated sidecar entries)
- F3 menu binding for operators (cross-cutting addon change, separate concern)
- Fixing the projection bug + tightening falloff in PROXIMITY mode (low priority - PROXIMITY is now a rarely-used fallback)
- New BindMode values (e.g. BONE_HEAT_WITH_SMOOTHING) - YAGNI
