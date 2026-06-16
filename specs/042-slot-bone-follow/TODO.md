# Slot bone-follow authoring parity - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Proscenio slot visibly follow its bone inside Blender the way the Godot importer already makes it follow at runtime, with a clickable operator that authors the follow.

**Architecture:** The follow is object-parent + a `Child Of` constraint whose inverse cancels the bone rest (the Blender twin of `slot_builder.gd`'s `get_skeleton_rest().affine_inverse()`), plus the `slot_bone` field the writer already prefers. A shared bpy helper authors it; the bind/unbind operators and the migrated `create_slot` both call it; the shared `slot_parent_bone` resolver learns to read `slot_bone` so the panel and validators stop misreporting a bound slot; the two slot fixtures author the constraint so they open already following their bone.

**Tech Stack:** Python 3.11 + bpy (Blender 5.x addon), pytest (pure + headless-operator), GDScript (read-only reference - no change).

---

## Background the engineer needs

- **The data path already exists.** The writer prefers `slot_bone`, falling back to `parent_bone` only for the old bone-parented shape ([slots.py:28-34](../../apps/blender/exporters/godot/writer/slots.py#L28-L34)). The `slot_bone` PropertyGroup field exists ([object_props.py:279-290](../../apps/blender/properties/object_props.py#L279-L290)) and the CP key `proscenio_slot_bone` is registered ([cp_keys.py](../../apps/blender/core/_shared/cp_keys.py)). Nothing authors the field or a Blender-side transform that moves the slot with the bone.
- **The constraint math is golden-safe.** The writer drops the rig to rest (zeroes every `pose_bone.matrix_basis`) before reading element `matrix_world` ([writer/__init__.py:106-130](../../apps/blender/exporters/godot/writer/__init__.py#L106-L130)). A `Child Of` constraint whose inverse is baked at rest is a no-op at rest, so adding it to the fixtures does **not** move attachments during the geometry read and leaves the golden `.expected.proscenio` unchanged. The inverse MUST be baked while the bone is at rest (fixtures: before any animation is applied).
- **Godot needs no change.** `slot_builder.gd` already parents the slot Node2D under the `Bone2D` and cancels the rest ([slot_builder.gd:64-69](../../apps/godot/addons/proscenio/builders/slot_builder.gd#L64-L69)). This plan mirrors that in Blender; it does not touch GDScript.
- **`.blend` + golden are git-tracked binaries.** `examples/generated/<fixture>/<fixture>.blend` and `<fixture>.expected.proscenio` are committed. Rebuilding a fixture regenerates the `.blend` (needs Blender + the `pillow_layers/*.png`, which exist) and the golden must still match.
- **Relative imports.** From `core/bpy_helpers/slot/`, `core/_shared` is `..._shared` (verified against `core/bpy_helpers/skinning/automesh_hook.py:15`).

## Locked decisions (from STUDY.md, plus implementation-pass calls)

- Follow convention: object-parent + `Child Of` constraint + `slot_bone` field. Not real bone-parenting.
- Set-inverse covers location, rotation, and scale (Child Of defaults - leave all `use_*` True).
- The shared resolver reads `slot_bone` first, then `parent_bone` - same order as the writer.
- Unbind removes the constraint and clears `slot_bone`, leaving the Empty object-parented and inert.
- Re-binding is cheap: running bind again on an already-bound slot recomputes the inverse (Set-Inverse caveat - rebind after moving the slot).
- **(impl call) Constraint name:** `"Proscenio Slot Follow"` - a single named constraint the helpers find/remove by name, so re-bind never stacks duplicates and unbind removes only ours.
- **(impl call) Bone picker UX:** the bind operator carries a `bone_name: StringProperty`; `invoke` opens a props dialog whose `draw` uses `layout.prop_search(self, "bone_name", armature.data, "bones")` (a real bone dropdown), pre-filled from the active pose bone or the slot's current bone. `execute` binds from `self.bone_name`, so headless tests drive it via `bpy.ops.proscenio.bind_slot_to_bone(bone_name=...)`.
- **(impl call) Armature resolution** (`resolve_slot_armature`): the Empty's object-parent when it is an ARMATURE, then the Skeleton picker (`active_armature`), then the scene export armature (`resolve_export_armature`).
- **(impl call) `slot_bone` is written dual** (PG when registered + the `proscenio_slot_bone` CP), mirroring the fixtures, so a headless `--background` re-open still exports the follow.
- **(impl call) Migrated `create_slot` bone path** anchors the new Empty at the bone tail (matching the old BONE-parent anchor) via an object-parent + `matrix_world` write, then binds.

## File structure

| File | Responsibility | Action |
| --- | --- | --- |
| `apps/blender/core/bpy_helpers/slot/__init__.py` | Re-export the slot bpy-helper surface | Create |
| `apps/blender/core/bpy_helpers/slot/bone_follow.py` | `SLOT_FOLLOW_CONSTRAINT`, `resolve_slot_armature`, `bind_slot_to_bone`, `unbind_slot_from_bone` | Create |
| `apps/blender/core/validation/active_slot.py` | `slot_parent_bone` reads `slot_bone` first | Modify |
| `apps/blender/operators/slot/bind.py` | `PROSCENIO_OT_bind_slot_to_bone`, `PROSCENIO_OT_unbind_slot_from_bone` | Create |
| `apps/blender/operators/slot/__init__.py` | Register the new operators | Modify |
| `apps/blender/operators/slot/create.py` | Migrate the pose-bone path off real bone-parenting | Modify |
| `apps/blender/panels/slots.py` | Bind/Unbind buttons in the Active Slot subpanel | Modify |
| `packages/fixtures/slot_swap/build_blend.py` | Author the follow constraint at rest | Modify |
| `packages/fixtures/mixed_feature/build_blend.py` | Author the follow constraint at rest | Modify |
| `apps/blender/core/help_topics.py` | `active_slot` topic mentions Bind to Bone / Unbind | Modify |
| `docs/02-blender-addon/03-slots.md` | Document the Bind to Bone affordance | Modify |
| `docs/content/proscenio/slots.mdx` | Same, web docs mirror | Modify |
| `tests/test_slot_validation.py` | `slot_bone` resolver cases | Modify |
| `tests/test_slot_bone_follow.py` | `resolve_slot_armature` priority (pure pytest) | Create |
| `apps/blender/tests/operators/test_bind_slot_to_bone.py` | bind/unbind + create_slot migrate (headless) | Create |

---

## Task 1: Resolver reads `slot_bone` (validation)

Cheapest item, no dependency on the helper. A correctly-bound slot currently reads as unparented and trips a false error; align the shared resolver with the writer's field order.

**Files:**
- Modify: `apps/blender/core/validation/active_slot.py:63-73` (and the import on line 8)
- Test: `tests/test_slot_validation.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_slot_validation.py`. Extend `_slot_props` to carry an optional `slot_bone`, then add four cases:

```python
def _slot_props(
    *, is_slot: bool = True, slot_default: str = "", slot_bone: str = ""
) -> SimpleNamespace:
    return SimpleNamespace(is_slot=is_slot, slot_default=slot_default, slot_bone=slot_bone)


def test_slot_parent_bone_reads_slot_bone_field_when_object_parented() -> None:
    # The new convention: object-parented Empty + slot_bone field set. The
    # resolver must report the field's bone, not "(unparented)".
    empty = _empty("face.slot", parent_type="OBJECT", props=_slot_props(slot_bone="head"))
    assert slot_parent_bone(empty) == "head"


def test_slot_parent_bone_prefers_slot_bone_over_parent_bone() -> None:
    # slot_bone wins over a leftover bone parent, matching the writer's order.
    empty = _empty(
        "face.slot",
        parent_bone="jaw",
        parent_type="BONE",
        props=_slot_props(slot_bone="head"),
    )
    assert slot_parent_bone(empty) == "head"


def test_slot_parent_bone_falls_back_to_bone_parent_when_no_field() -> None:
    empty = _empty("forearm.swap", parent_bone="forearm.L", parent_type="BONE")
    assert slot_parent_bone(empty) == "forearm.L"


def test_bound_slot_with_field_emits_no_unparented_error() -> None:
    # The whole point: a slot_bone-bound slot with a child is fully valid.
    empty = _empty(
        "face.slot",
        parent_type="OBJECT",
        children=[_mesh("face_neutral")],
        props=_slot_props(slot_bone="head"),
    )
    assert validate_active_slot(empty) == []
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `uv run pytest tests/test_slot_validation.py -k "slot_bone or bound_slot" -v`
Expected: `test_slot_parent_bone_reads_slot_bone_field_when_object_parented` and `test_slot_parent_bone_prefers_slot_bone_over_parent_bone` FAIL (resolver returns `""`); the fallback + no-error cases may already pass.

- [ ] **Step 3: Implement the resolver change**

In `apps/blender/core/validation/active_slot.py`, extend the cp_keys import (line 8):

```python
from .._shared.cp_keys import PROSCENIO_SLOT_BONE, PROSCENIO_SLOT_DEFAULT
```

Replace `slot_parent_bone` (lines 63-73) with:

```python
def slot_parent_bone(obj: object) -> str:
    """The bone ``obj`` follows, or "" when it follows none.

    Reads the ``slot_bone`` field first (the object-parent + Child Of
    convention), then a real ``parent_type == "BONE"`` parent - the same
    order the writer emits (``writer/slots.py``), so the Active Slot panel,
    the slot validators, and the export never disagree about the followed
    bone. A leftover ``parent_bone`` on an OBJECT-parented slot with no
    field is not a live follow.

    Shared by the validators and the panel so the "no parent bone" notion
    has a single definition.
    """
    slot_bone = str(
        read_field(obj, pg_field="slot_bone", cp_key=PROSCENIO_SLOT_BONE, default="")
    )
    if slot_bone:
        return slot_bone
    if getattr(obj, "parent_type", "") != "BONE":
        return ""
    return str(getattr(obj, "parent_bone", ""))
```

Note: `read_field` is already imported (line 9). For a child MESH whose `proscenio.slot_bone` is the PG default `""`, `read_field` returns `""` (falsy) and the parent-bone fallback still runs, so `_check_slot_child_bones` is unaffected.

- [ ] **Step 4: Run the slot validation suite to verify it passes**

Run: `uv run pytest tests/test_slot_validation.py -v`
Expected: PASS (all existing + the four new cases).

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/validation/active_slot.py tests/test_slot_validation.py
git commit -m "fix(blender): slot_parent_bone reads slot_bone field first"
```

---

## Task 2: Shared bone-follow helper

The core authoring logic, called by the operators (Task 3) and the migrated `create_slot` (Task 4).

**Files:**
- Create: `apps/blender/core/bpy_helpers/slot/__init__.py`
- Create: `apps/blender/core/bpy_helpers/slot/bone_follow.py`
- Test: `tests/test_slot_bone_follow.py` (pure pytest for `resolve_slot_armature`); the bind/unbind math is covered headless in Task 3.

- [ ] **Step 1: Write the failing pure-pytest test for `resolve_slot_armature`**

Create `tests/test_slot_bone_follow.py`:

```python
"""Unit tests for slot armature resolution.

Pure pytest - the repo-root conftest's bpy substitute lets bone_follow
import; resolve_slot_armature does attribute access only, so SimpleNamespace
mocks exercise the priority order without Blender.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bpy_helpers.slot.bone_follow import resolve_slot_armature  # noqa: E402


def _armature(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="ARMATURE")


def _context(*, scene_objects=(), picker=None) -> SimpleNamespace:
    proscenio = SimpleNamespace(active_armature=picker)
    scene = SimpleNamespace(objects=list(scene_objects), proscenio=proscenio)
    return SimpleNamespace(scene=scene)


def test_prefers_empty_object_parent_armature() -> None:
    arm = _armature("rig_parent")
    empty = SimpleNamespace(parent=arm)
    ctx = _context(scene_objects=[arm, _armature("other")], picker=_armature("picked"))
    assert resolve_slot_armature(ctx, empty) is arm


def test_falls_back_to_picker_when_parent_not_armature() -> None:
    picked = _armature("picked")
    empty = SimpleNamespace(parent=SimpleNamespace(type="MESH"))
    ctx = _context(scene_objects=[picked], picker=picked)
    assert resolve_slot_armature(ctx, empty) is picked


def test_falls_back_to_scene_export_armature() -> None:
    only = _armature("only_rig")
    empty = SimpleNamespace(parent=None)
    ctx = _context(scene_objects=[only], picker=None)
    assert resolve_slot_armature(ctx, empty) is only


def test_returns_none_when_no_armature() -> None:
    empty = SimpleNamespace(parent=None)
    ctx = _context(scene_objects=[SimpleNamespace(name="m", type="MESH")], picker=None)
    assert resolve_slot_armature(ctx, empty) is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_slot_bone_follow.py -v`
Expected: FAIL at import (`ModuleNotFoundError: core.bpy_helpers.slot.bone_follow`).

- [ ] **Step 3: Create the helper module**

Create `apps/blender/core/bpy_helpers/slot/bone_follow.py`:

```python
"""Slot bone-follow: the Blender twin of the Godot importer's slot anchor.

bpy-bound (manipulates ``Object.constraints`` + reads pose matrices), so this
module imports bpy at top per the bpy_helpers contract. The convention it
authors - object-parent + a Child Of constraint whose inverse cancels the
bone rest - keeps slot attachment quads flat in the picture plane while the
slot rides only the bone's pose delta, mirroring slot_builder.gd's
``get_skeleton_rest().affine_inverse()`` cancel in Godot.
"""

from __future__ import annotations

import bpy

from ..._shared.cp_keys import PROSCENIO_SLOT_BONE
from ..._shared.props_access import active_armature, resolve_export_armature

SLOT_FOLLOW_CONSTRAINT = "Proscenio Slot Follow"


def resolve_slot_armature(
    context: bpy.types.Context, empty: bpy.types.Object
) -> bpy.types.Object | None:
    """The armature a slot Empty should follow a bone of, or None.

    Priority: the Empty's own object-parent when it is an ARMATURE (the slot
    convention parents the Empty to the rig), then the Skeleton picker, then
    the scene's export armature.
    """
    parent = getattr(empty, "parent", None)
    if parent is not None and getattr(parent, "type", None) == "ARMATURE":
        return parent
    picker = active_armature(context)
    if picker is not None:
        return picker
    scene = getattr(context, "scene", None)
    return resolve_export_armature(scene) if scene is not None else None


def _follow_constraint(empty: bpy.types.Object) -> bpy.types.Constraint | None:
    """The single named follow constraint we own on ``empty``, or None."""
    con = empty.constraints.get(SLOT_FOLLOW_CONSTRAINT)
    return con if con is not None and con.type == "CHILD_OF" else None


def bind_slot_to_bone(
    empty: bpy.types.Object, armature: bpy.types.Object, bone_name: str
) -> None:
    """Wire ``empty`` to follow ``bone_name`` of ``armature`` in Blender.

    Re-runnable: an existing follow constraint is removed first so the inverse
    recomputes at the current pose (the Set-Inverse caveat - rebind after
    moving the slot). Writes ``slot_bone`` dual (PG + Custom Property) so the
    writer's preferred field carries the follow even on a headless re-open.

    Raises ``RuntimeError`` when the armature lacks ``bone_name``.
    """
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone is None:
        raise RuntimeError(f"armature '{armature.name}' has no bone '{bone_name}'")

    existing = _follow_constraint(empty)
    if existing is not None:
        empty.constraints.remove(existing)

    con = empty.constraints.new(type="CHILD_OF")
    con.name = SLOT_FOLLOW_CONSTRAINT
    con.target = armature
    con.subtarget = bone_name
    # Headless Set-Inverse: cancel the full bone rest (location + rotation +
    # scale) so only the pose delta moves the slot - the affine_inverse() cancel
    # slot_builder.gd applies in Godot.
    con.inverse_matrix = (armature.matrix_world @ pose_bone.matrix).inverted()

    _write_slot_bone(empty, bone_name)


def unbind_slot_from_bone(empty: bpy.types.Object) -> None:
    """Reverse :func:`bind_slot_to_bone`: drop the constraint + clear slot_bone.

    Leaves the Empty object-parented and inert (the pre-bind state).
    """
    existing = _follow_constraint(empty)
    if existing is not None:
        empty.constraints.remove(existing)
    _write_slot_bone(empty, "")


def _write_slot_bone(empty: bpy.types.Object, bone_name: str) -> None:
    """Write slot_bone PG-first + Custom Property; clear both on empty string."""
    props = getattr(empty, "proscenio", None)
    if props is not None:
        props.slot_bone = bone_name
    if bone_name:
        empty[PROSCENIO_SLOT_BONE] = bone_name
    elif PROSCENIO_SLOT_BONE in empty:
        del empty[PROSCENIO_SLOT_BONE]
```

Create `apps/blender/core/bpy_helpers/slot/__init__.py`:

```python
"""Slot bpy-helpers - bone-follow authoring (object-parent + Child Of)."""

from __future__ import annotations

from .bone_follow import (
    SLOT_FOLLOW_CONSTRAINT,
    bind_slot_to_bone,
    resolve_slot_armature,
    unbind_slot_from_bone,
)

__all__ = [
    "SLOT_FOLLOW_CONSTRAINT",
    "bind_slot_to_bone",
    "resolve_slot_armature",
    "unbind_slot_from_bone",
]
```

- [ ] **Step 4: Run the pure-pytest test to verify it passes**

Run: `uv run pytest tests/test_slot_bone_follow.py -v`
Expected: PASS (4 cases).

- [ ] **Step 5: Commit**

```bash
git add apps/blender/core/bpy_helpers/slot/ tests/test_slot_bone_follow.py
git commit -m "feat(blender): slot bone-follow helper (object-parent + Child Of)"
```

---

## Task 3: Bind / Unbind operators

The clickable affordance. Headless-operator tests drive the real constraint + matrix math.

**Files:**
- Create: `apps/blender/operators/slot/bind.py`
- Modify: `apps/blender/operators/slot/__init__.py`
- Test: `apps/blender/tests/operators/test_bind_slot_to_bone.py`

- [ ] **Step 1: Write the failing headless test**

Create `apps/blender/tests/operators/test_bind_slot_to_bone.py`:

```python
"""Headless tests for the slot bone-follow operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds a one-bone armature
+ an object-parented slot Empty, then drives bind/unbind through bpy.ops and
asserts the constraint, the slot_bone field, and the rest/posed follow.
"""

from __future__ import annotations

import bpy
import pytest
from mathutils import Matrix


def _make_rig(bone: str = "arm") -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new(bone)
    eb.head = (0.0, 0.0, 0.0)
    eb.tail = (0.0, 1.0, 0.0)  # +Y, into the screen (in-plane convention)
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _make_slot(arm: bpy.types.Object, name: str = "weapon") -> bpy.types.Object:
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.parent = arm
    empty.parent_type = "OBJECT"
    empty.location = (0.0, 1.0, 0.0)  # at the bone tail
    empty.proscenio.is_slot = True
    child = bpy.data.objects.new(name + "_att", bpy.data.meshes.new("att"))
    bpy.context.scene.collection.objects.link(child)
    child.parent = empty
    child.parent_type = "OBJECT"
    bpy.context.view_layer.objects.active = empty
    bpy.context.view_layer.update()
    return empty


def _activate(obj: bpy.types.Object) -> None:
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def test_bind_adds_named_constraint_and_writes_field(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)

    result = bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    assert "FINISHED" in result

    con = empty.constraints.get("Proscenio Slot Follow")
    assert con is not None and con.type == "CHILD_OF"
    assert con.target is arm and con.subtarget == "arm"
    assert empty.proscenio.slot_bone == "arm"
    assert empty["proscenio_slot_bone"] == "arm"
    assert empty.parent_type == "OBJECT"  # never bone-parented


def test_bind_keeps_slot_at_rest_then_follows_pose(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    before = empty.matrix_world.translation.copy()

    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    bpy.context.view_layer.update()
    at_rest = empty.matrix_world.translation
    assert (at_rest - before).length == pytest.approx(0.0, abs=1e-4), "moved at rest"

    # Pose the bone; the slot must ride the delta.
    arm.pose.bones["arm"].rotation_mode = "XYZ"
    arm.pose.bones["arm"].rotation_euler = (0.5, 0.0, 0.0)
    bpy.context.view_layer.update()
    posed = empty.matrix_world.translation
    assert (posed - at_rest).length > 1e-3, "slot did not follow the posed bone"


def test_rebind_does_not_stack_constraints(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")
    follow = [c for c in empty.constraints if c.name == "Proscenio Slot Follow"]
    assert len(follow) == 1


def test_unbind_removes_constraint_and_clears_field(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    bpy.ops.proscenio.bind_slot_to_bone(bone_name="arm")

    result = bpy.ops.proscenio.unbind_slot_from_bone()
    assert "FINISHED" in result
    assert empty.constraints.get("Proscenio Slot Follow") is None
    assert empty.proscenio.slot_bone == ""
    assert "proscenio_slot_bone" not in empty


def test_bind_unknown_bone_cancels(automesh_fixture):
    arm = _make_rig()
    empty = _make_slot(arm)
    _activate(empty)
    with pytest.raises(RuntimeError, match="no bone"):
        bpy.ops.proscenio.bind_slot_to_bone(bone_name="ghost")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `blender --background --python apps/blender/tests/run_operator_tests.py -- -k bind_slot`
Expected: FAIL - `bpy.ops.proscenio.bind_slot_to_bone` does not exist yet (`AttributeError`/poll). (On Windows use `godot_std`-style console build is irrelevant here; use the installed `blender`.)

- [ ] **Step 3: Create the operators**

Create `apps/blender/operators/slot/bind.py`:

```python
"""Slot bone-follow operators: bind the active slot to a bone, and unbind.

Authors the object-parent + Child Of follow via the shared bpy helper so the
Blender view matches the Godot runtime. The bind picker is a prop_search bone
dropdown in a props dialog; execute binds from ``bone_name`` so headless tests
pass it directly.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ...core.bpy_helpers.slot import (  # type: ignore[import-not-found]
    bind_slot_to_bone,
    resolve_slot_armature,
    unbind_slot_from_bone,
)
from ...core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]
from ...core.validation import slot_parent_bone  # type: ignore[import-not-found]


class PROSCENIO_OT_bind_slot_to_bone(bpy.types.Operator):
    """Make the active slot follow a bone (object-parent + Child Of)."""

    bl_idname = "proscenio.bind_slot_to_bone"
    bl_label = "Proscenio: Bind Slot to Bone"
    bl_description = (
        "Make the active slot follow a bone in Blender the way it already does "
        "in Godot: keeps the Empty object-parented, adds a Child Of constraint "
        "whose inverse cancels the bone rest, and writes the slot_bone field. "
        "Re-run to rebind after moving the slot"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Bone the slot follows",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        if not is_slot_empty(empty):
            return False
        return resolve_slot_armature(context, empty) is not None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        empty = context.active_object
        active_bone = getattr(context, "active_pose_bone", None)
        if active_bone is not None:
            self.bone_name = active_bone.name
        elif not self.bone_name:
            self.bone_name = slot_parent_bone(empty)
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context) -> None:
        empty = context.active_object
        armature = resolve_slot_armature(context, empty)
        if armature is None:
            self.layout.label(text="no armature to follow", icon="ERROR")
            return
        self.layout.prop_search(self, "bone_name", armature.data, "bones", text="Bone")

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        armature = resolve_slot_armature(context, empty)
        if armature is None:
            report_warn(self, "no armature found for this slot")
            return {"CANCELLED"}
        if not self.bone_name:
            report_warn(self, "pick a bone for the slot to follow")
            return {"CANCELLED"}
        context.view_layer.update()
        bind_slot_to_bone(empty, armature, str(self.bone_name))
        report_info(self, f"slot '{empty.name}' follows bone '{self.bone_name}'")
        return {"FINISHED"}


class PROSCENIO_OT_unbind_slot_from_bone(bpy.types.Operator):
    """Remove the active slot's bone-follow and clear slot_bone."""

    bl_idname = "proscenio.unbind_slot_from_bone"
    bl_label = "Proscenio: Unbind Slot from Bone"
    bl_description = (
        "Remove the slot's bone-follow constraint and clear slot_bone; the "
        "Empty stays object-parented and inert"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        empty = context.active_object
        return is_slot_empty(empty) and slot_parent_bone(empty) != ""

    def execute(self, context: bpy.types.Context) -> set[str]:
        empty = context.active_object
        unbind_slot_from_bone(empty)
        report_info(self, f"slot '{empty.name}' no longer follows a bone")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_bind_slot_to_bone,
    PROSCENIO_OT_unbind_slot_from_bone,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
```

Note: `bind_slot_to_bone` raising `RuntimeError` on an unknown bone surfaces as a `{"ERROR"}` only if reported; here execute pre-validates `bone_name` presence but passes through to the helper. The unknown-bone test expects `RuntimeError` from the helper - `bpy.ops` re-raises it, satisfying `pytest.raises(RuntimeError, match="no bone")`. (The helper message is `"... has no bone '<name>'"`.)

- [ ] **Step 4: Register the operators**

In `apps/blender/operators/slot/__init__.py`, add `bind` to the imports and to both `register()`/`unregister()` (register after `create`, unregister before `create`):

```python
from . import attachment, bind, create, preview_shader, select


def register() -> None:
    create.register()
    bind.register()
    attachment.register()
    select.register()
    preview_shader.register()


def unregister() -> None:
    preview_shader.unregister()
    select.unregister()
    attachment.unregister()
    bind.unregister()
    create.unregister()
```

Also update the package docstring's submodule list to add `- bind.py - PROSCENIO_OT_bind_slot_to_bone, PROSCENIO_OT_unbind_slot_from_bone`.

- [ ] **Step 5: Run the headless test to verify it passes**

Run: `blender --background --python apps/blender/tests/run_operator_tests.py -- -k bind_slot`
Expected: PASS (6 cases).

- [ ] **Step 6: Commit**

```bash
git add apps/blender/operators/slot/bind.py apps/blender/operators/slot/__init__.py apps/blender/tests/operators/test_bind_slot_to_bone.py
git commit -m "feat(blender): Bind/Unbind Slot to Bone operators"
```

---

## Task 4: Migrate `create_slot` bone path

The existing pose-bone path real-bone-parents the Empty, tilting the flat quads out of the picture plane and riding the `parent_bone` fallback. Move it to the convention.

**Files:**
- Modify: `apps/blender/operators/slot/create.py:79-82`
- Test: `apps/blender/tests/operators/test_bind_slot_to_bone.py` (add a create_slot pose-bone case here - it shares the rig builder)

- [ ] **Step 1: Write the failing test**

Append to `apps/blender/tests/operators/test_bind_slot_to_bone.py`:

```python
def test_create_slot_pose_bone_uses_follow_not_bone_parent(automesh_fixture):
    arm = _make_rig()
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    arm.data.bones.active = arm.data.bones["arm"]

    result = bpy.ops.proscenio.create_slot()
    assert "FINISHED" in result
    bpy.ops.object.mode_set(mode="OBJECT")

    empty = bpy.context.view_layer.objects.active
    assert empty.proscenio.is_slot is True
    # The migrated path object-parents + follows; it never bone-parents.
    assert empty.parent is arm
    assert empty.parent_type == "OBJECT"
    assert empty.constraints.get("Proscenio Slot Follow") is not None
    assert empty.proscenio.slot_bone == "arm"
    # Anchored at the bone tail (world (0,1,0)).
    bpy.context.view_layer.update()
    tail = empty.matrix_world.translation
    assert tail.y == pytest.approx(1.0, abs=1e-4)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `blender --background --python apps/blender/tests/run_operator_tests.py -- -k create_slot_pose_bone`
Expected: FAIL - `empty.parent_type == "BONE"` and no follow constraint.

- [ ] **Step 3: Migrate the bone path**

In `apps/blender/operators/slot/create.py`, add the helper import near the other core imports:

```python
from ...core.bpy_helpers.slot import bind_slot_to_bone  # type: ignore[import-not-found]
```

Replace the bone branch (lines 79-82):

```python
        if armature is not None and bone_name:
            # Object-parent + a Child Of follow (not a real bone parent, which
            # would tilt the flat attachment quads out of the picture plane).
            # Anchor at the bone tail, matching the old bone-parent placement,
            # then bind so the slot rides the bone's pose delta.
            empty.parent = armature
            empty.parent_type = "OBJECT"
            context.view_layer.update()
            pose_bone = armature.pose.bones[bone_name]
            empty.matrix_world = Matrix.Translation(armature.matrix_world @ pose_bone.tail)
            context.view_layer.update()
            bind_slot_to_bone(empty, armature, bone_name)
        elif selected_meshes:
```

`Matrix` is already imported (line 9). Leave the `is_slot` write (lines 95-96) where it is - `bind_slot_to_bone` does not touch it.

- [ ] **Step 4: Run create_slot tests to verify they pass**

Run: `blender --background --python apps/blender/tests/run_operator_tests.py -- -k "create_slot or bind_slot"`
Expected: PASS (existing `test_create_slot` geometry cases + the new pose-bone case + Task 3 cases).

- [ ] **Step 5: Commit**

```bash
git add apps/blender/operators/slot/create.py apps/blender/tests/operators/test_bind_slot_to_bone.py
git commit -m "feat(blender): create_slot bone path object-parents + follows"
```

---

## Task 5: Active Slot panel UI

Surface the operators and let the corrected resolver fix the bone line + warning.

**Files:**
- Modify: `apps/blender/panels/slots.py:115-128`

- [ ] **Step 1: Add the Bind/Unbind row**

In `PROSCENIO_PT_active_slot.draw`, after the `if not parent_bone:` warning block (line 128), insert a bind row. The `bone:` line and the warning already read `validation.slot_parent_bone(empty)`, which now reflects `slot_bone`, so a bound slot shows the bone and drops the false warning automatically. Add:

```python
        bind_row = col.row(align=True)
        bind_row.operator(
            "proscenio.bind_slot_to_bone",
            text="Rebind to Bone" if parent_bone else "Bind to Bone",
            icon="BONE_DATA",
        )
        if parent_bone:
            bind_row.operator(
                "proscenio.unbind_slot_from_bone",
                text="",
                icon="X",
            )
```

- [ ] **Step 2: Verify panel imports operators only by bl_idname**

No new import needed - panels reference operators by `bl_idname` string (convention: `panels -> operators` only via strings). Confirm `slots.py` adds no operator class import.

- [ ] **Step 3: Smoke-test registration (panel has no unit test; draw is exercised via manual + the import sweep)**

Run: `blender --background --python apps/blender/tests/run_operator_tests.py -- -k slot`
Expected: PASS (registration succeeds; no panel regression). Manual viewport check happens in Task 8's manual gate.

- [ ] **Step 4: Commit**

```bash
git add apps/blender/panels/slots.py
git commit -m "feat(blender): Active Slot panel Bind/Unbind to Bone buttons"
```

---

## Task 6: Fixtures author the follow constraint

`mixed_feature` (face follows `head`) and `slot_swap` (weapon follows `arm`) already set `slot_bone` + object-parent but sit inert in Blender. Add the constraint, baked at rest, so they open already following - without changing the golden.

**Files:**
- Modify: `packages/fixtures/slot_swap/build_blend.py` (`_build_slot_empty`)
- Modify: `packages/fixtures/mixed_feature/build_blend.py` (`_build_slot`)

- [ ] **Step 1: slot_swap - add the constraint at rest**

In `_build_slot_empty` (after the `slot_bone` writes, before `return empty`), with the bone still at rest (this runs before the swing animation is applied):

```python
    # Author the Blender-side follow so the weapon swings with the arm in the
    # viewport, mirroring the Godot importer. Baked at rest (no action yet), so
    # the writer's rest read leaves the golden unchanged. Name matches
    # core.bpy_helpers.slot.bone_follow.SLOT_FOLLOW_CONSTRAINT.
    con = empty.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Slot Follow"
    con.target = armature_obj
    con.subtarget = ARM_BONE
    bpy.context.view_layer.update()
    pose_bone = armature_obj.pose.bones[ARM_BONE]
    con.inverse_matrix = (armature_obj.matrix_world @ pose_bone.matrix).inverted()
```

- [ ] **Step 2: mixed_feature - add the constraint at rest**

In `_build_slot` (after `_dual(empty, "slot_bone", "proscenio_slot_bone", "head")`), targeting the `head` bone of `armature_obj`:

```python
    # Author the Blender-side follow so the face tracks the head bone in the
    # viewport (mirrors the Godot importer). Baked at rest, golden-neutral.
    con = empty.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Slot Follow"
    con.target = armature_obj
    con.subtarget = "head"
    bpy.context.view_layer.update()
    head_bone = armature_obj.pose.bones["head"]
    con.inverse_matrix = (armature_obj.matrix_world @ head_bone.matrix).inverted()
```

Confirm the bone name is `"head"` in this fixture before running (grep `head` in the file); if the rig names it differently, use that name.

- [ ] **Step 3: Rebuild both .blend fixtures**

Run:
```bash
blender --background --python packages/fixtures/slot_swap/build_blend.py
blender --background --python packages/fixtures/mixed_feature/build_blend.py
```
Expected: each writes its `.blend` under `examples/generated/<fixture>/` without error.

- [ ] **Step 4: Verify the golden is unchanged**

Run: `blender --background --python apps/blender/tests/run_tests.py`
Expected: PASS - the re-exported `.proscenio` matches each committed `.expected.proscenio`. If `slot_swap` or `mixed_feature` golden diffs, STOP: the inverse was not baked at rest (the bone was posed when the constraint was added) - move the constraint authoring before the animation step and re-run.

- [ ] **Step 5: Commit**

```bash
git add packages/fixtures/slot_swap/build_blend.py packages/fixtures/mixed_feature/build_blend.py examples/generated/slot_swap/slot_swap.blend examples/generated/mixed_feature/mixed_feature.blend
git commit -m "feat(fixtures): slot fixtures open already following their bone"
```

(Stage the `.blend1` backups too if the build emits them and they are tracked; do not stage a changed `.expected.proscenio` - it must not change.)

---

## Task 7: Docs + help topic

**Files:**
- Modify: `apps/blender/core/help_topics.py` (`active_slot` topic, around line 797-810)
- Modify: `docs/02-blender-addon/03-slots.md`
- Modify: `docs/content/proscenio/slots.mdx`

- [ ] **Step 1: Extend the `active_slot` help topic**

Add a line to the `active_slot` HelpTopic body describing the affordance, e.g. after the attachment-detail description:

```python
                "Bind to Bone makes the slot follow a bone in the viewport the "
                "same way it follows at runtime in Godot (object-parent + a "
                "Child Of constraint that cancels the bone rest); Unbind removes "
                "it. Rebind after moving the slot - the inverse is baked at bind "
                "time.",
```

- [ ] **Step 2: Document in `docs/02-blender-addon/03-slots.md`**

Extend the Active Slot section:

```markdown
## Active Slot

Shown when a slot Empty is the active object. Lists the slot's child attachments, lets you mark which one is visible at scene load (the SOLO star), and adds the selected mesh as a new attachment.

**Bind to Bone** makes the slot follow a bone inside Blender the way the Godot importer already makes it follow at runtime: it keeps the Empty object-parented (so the flat attachment quads stay in the picture plane) and adds a `Child Of` constraint whose inverse cancels the bone rest, so the slot rides only the bone's pose delta. The bone line and the unparented warning reflect the bound bone once set. **Unbind** removes the follow. Because the inverse is baked when you bind, rebind after moving the slot.
```

- [ ] **Step 3: Mirror in `docs/content/proscenio/slots.mdx`**

Add the equivalent prose to the web docs slots page (match its existing component/heading style; read the file first to follow the MDX conventions).

- [ ] **Step 4: Commit**

```bash
git add apps/blender/core/help_topics.py docs/02-blender-addon/03-slots.md docs/content/proscenio/slots.mdx
git commit -m "docs(blender): document Bind to Bone slot follow"
```

---

## Task 8: Full gate set + import sweep

Run the complete Blender gate set (the repo-root pytest suite is the easy one to miss) before declaring done.

- [ ] **Step 1: Lint + format (apps/blender only)**

Run:
```bash
ruff check apps/blender
ruff format --check apps/blender
```
Expected: clean. Scope `ruff format` writes to the files this change touched only - never `tests/` at large.

- [ ] **Step 2: Type check**

Run: `uv run --project apps/blender mypy --config-file apps/blender/pyproject.toml`
Expected: clean. (Note `# type: ignore[import-not-found]` masks missing modules - rely on the import sweep, not mypy, to catch broken imports.)

- [ ] **Step 3: Repo-root pytest (the easy-to-miss gate)**

Run: `uv run pytest tests/`
Expected: PASS, including `tests/test_slot_validation.py` and `tests/test_slot_bone_follow.py`.

- [ ] **Step 4: Blender goldens + headless operators**

Run:
```bash
blender --background --python apps/blender/tests/run_tests.py
blender --background --python apps/blender/tests/run_operator_tests.py
```
Expected: PASS - goldens match, all operator tests green.

- [ ] **Step 5: Whole-addon import sweep**

Mount the addon as `proscenio` (replicate `run_tests._load_addon_as_package`) and `importlib.import_module` every non-test module to catch relative-import shifts from the new package. Expected: every module imports.

- [ ] **Step 6: Spell check the touched files**

Run cspell over the changed files (pre-commit does this). Add any legitimate new terms to `.cspell/developer-terms.txt`. Expected: clean.

- [ ] **Step 7: Manual viewport check (parity acceptance)**

Open `examples/generated/slot_swap/slot_swap.blend`, scrub the `swing` action: the weapon Empty + visible attachment swing with the arm. Open `examples/generated/mixed_feature/mixed_feature.blend`: the face slot sits on and tracks the head. In the N-panel Active Slot subpanel, a bound slot shows `bone: arm`/`head` with no unparented warning, and Bind/Unbind buttons appear.

- [ ] **Step 8: Final commit if the sweep added anything**

```bash
git add -A
git commit -m "chore(blender): spell dict + sweep fixups for slot bone-follow"
```

---

## Self-review against the spec

- **bind-slot-to-bone operator** -> Task 3 (operator) + Task 2 (helper).
- **Unbind path** -> Task 3 (`PROSCENIO_OT_unbind_slot_from_bone`) + Task 2 (`unbind_slot_from_bone`).
- **create_slot migrated off bone-parenting** -> Task 4.
- **resolver reads slot_bone** -> Task 1.
- **fixtures author the constraint** -> Task 6.
- **STUDY open question (rebind after move)** -> Task 2 re-runnable bind + Task 3 `test_rebind_does_not_stack_constraints` + panel "Rebind to Bone" label (Task 5).
- **Godot surface (slot_builder.gd)** -> reference only; no change (importer already cancels the rest).

## Notes for the executor

- Per repo memory: `uv run pytest tests/` is a separate CI step that breaks on `core/` moves - run it explicitly (Step 3 of Task 8). The new `core/bpy_helpers/slot/` package is a fresh path; the import sweep (Step 5) is what catches a mis-rooted relative import that mypy's `# type: ignore` masks.
- Do not stage a changed `.expected.proscenio` - if one changes, the rest-bake invariant broke (Task 6 Step 4).
- Commit gradually (one per task) - the branch history is the audit trail.
