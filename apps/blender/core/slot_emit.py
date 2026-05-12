"""Pure-Python slot emission helpers (SPEC 004 Wave 4.1).

Bpy-free. The writer's bpy walker (``_build_slots`` in
``exporters/godot/writer.py``) shapes its inputs into the structures
this module accepts, then dispatches here for the actual ``slots[]``
list construction. Keeps the slot logic unit-testable without booting
Blender.

Conventions
-----------
- Slot ``name`` defaults to the Empty object's name.
- ``bone`` is the Empty's ``parent_bone`` when ``parent_type == "BONE"``,
  empty string otherwise (per D3).
- ``attachments`` ordered by the Empty's child list as the bpy walker
  feeds it in - the writer can sort or preserve outliner order. The
  writer side currently feeds in ``children`` order; D12 z-order
  follows that.
- ``default`` resolves to the explicit ``slot_default`` field when
  non-empty AND it names an existing attachment; otherwise falls back
  to the first attachment by sorted name (per D2).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlotInput:
    """One Empty's slot data, post-bpy extraction."""

    name: str
    bone: str
    slot_default: str
    attachments: tuple[str, ...]


def build_slot_dict(slot: SlotInput) -> dict[str, object]:
    """Project a :class:`SlotInput` into a schema-shaped dict.

    Returns the shape required by ``schemas/proscenio.schema.json``
    ``Slot`` def: ``{name, bone, default, attachments[]}``. ``bone``
    and ``default`` are emitted only when non-empty so the writer's
    output stays minimal-surface.
    """
    out: dict[str, object] = {
        "name": slot.name,
        "attachments": list(slot.attachments),
    }
    if slot.bone:
        out["bone"] = slot.bone
    default = _resolve_default(slot.slot_default, slot.attachments)
    if default:
        out["default"] = default
    return out


def _resolve_default(slot_default: str, attachments: tuple[str, ...]) -> str:
    """D2: explicit slot_default wins when valid; else first sorted attachment.

    Empty attachments list yields ``""`` (no default emitted). An invalid
    ``slot_default`` (names a child that does not exist) silently falls
    through to the sorted-first fallback - the panel's validation pass
    surfaces it as an error so the user sees the broken reference, but
    the writer keeps emitting a usable default in the meantime.
    """
    if not attachments:
        return ""
    if slot_default and slot_default in attachments:
        return slot_default
    return min(attachments)


def build_slots(slots: list[SlotInput]) -> list[dict[str, object]]:
    """Project a list of ``SlotInput`` into the writer's ``slots[]`` array.

    Output is sorted by slot name so the .proscenio diff stays stable
    across re-exports (mirrors how ``sprites[]`` is emitted in writer
    name order).
    """
    return [build_slot_dict(slot) for slot in sorted(slots, key=lambda s: s.name)]
