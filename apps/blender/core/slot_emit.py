"""Pure-Python slot emission helpers (the slot system).

Bpy-free. The writer's bpy walker (``build_slots_for_scene`` in
``exporters/godot/writer/slots.py``) shapes its inputs into the structures
this module accepts, then dispatches here for the actual ``slots[]``
list construction. Keeps the slot logic unit-testable without booting
Blender.

Conventions:

- Slot ``name`` defaults to the Empty object's name.
- ``bone`` is the Empty's ``parent_bone`` when ``parent_type == "BONE"``,
  empty string otherwise (per D3). The pydantic ``Slot`` field is
  ``Optional[str]``; an empty string from the bpy walker maps to
  ``bone=None`` so the document does not emit the field.
- ``attachments`` ordered by the Empty's child list as the bpy walker
  feeds it in.
- ``default`` resolves to the explicit ``slot_default`` field when
  non-empty AND it names an existing attachment; otherwise falls back
  to the first attachment by sorted name (per D2). Empty resolves to
  ``None`` so the document does not emit the field.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired, TypedDict

from proscenio_models import Slot


class _SlotKwargs(TypedDict):
    """Constructor kwargs for ``Slot``.

    ``bone`` / ``default`` are ``NotRequired`` so an empty value omits
    the key under ``model_dump_json(exclude_unset=True)`` rather than
    serialising ``"bone": null`` - matching the legacy dict writer that
    only set them when non-empty.
    """

    name: str
    attachments: list[str]
    bone: NotRequired[str]
    default: NotRequired[str]


@dataclass(frozen=True)
class SlotInput:
    """One Empty's slot data, post-bpy extraction."""

    name: str
    bone: str
    slot_default: str
    attachments: tuple[str, ...]


def build_slot(slot: SlotInput) -> Slot:
    """Project a :class:`SlotInput` into a typed ``Slot`` model.

    Field order on the model mirrors the schema's ``Slot`` def
    (``name``, ``attachments``, ``bone``, ``default``) so
    ``model_dump_json(exclude_unset=True)`` reproduces the goldens
    byte-for-byte. ``bone`` and ``default`` map empty strings to
    ``None`` so the model emits the field as unset.
    """
    kwargs: _SlotKwargs = {
        "name": slot.name,
        "attachments": list(slot.attachments),
    }
    if slot.bone:
        kwargs["bone"] = slot.bone
    default = _resolve_default(slot.slot_default, slot.attachments)
    if default:
        kwargs["default"] = default
    return Slot(**kwargs)


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


def build_slots(slots: list[SlotInput]) -> list[Slot]:
    """Project a list of ``SlotInput`` into the writer's ``slots[]`` array.

    Output is sorted by slot name so the .proscenio diff stays stable
    across re-exports (mirrors how ``sprites[]`` is emitted in writer
    name order).
    """
    return [build_slot(slot) for slot in sorted(slots, key=lambda s: s.name)]
