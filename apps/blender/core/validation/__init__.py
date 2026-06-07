"""Proscenio validation surface (the authoring panel).

Two entry points map to the panel's two validation paths:

- :func:`validate_active_element` - cheap structural checks for inline
  feedback; called on every panel redraw, must stay O(1) on the active
  object.
- :func:`validate_active_slot` - cheap slot-Empty checks for inline
  feedback in the Active Slot subpanel.
- :func:`validate_export` - full lazy pass triggered by the Validate
  button or the Export operator; allowed to walk every scene object,
  check vertex groups against bones, hit the disk for atlas files.

All three return :class:`list[Issue]`. The panel layer renders icons
+ text from each issue; export blocks when any issue carries severity
``error``.

Validation here is structural and semantic - JSON Schema validation
runs in CI and the test runner, not in the live Blender session.

Submodules per concern:

- ``issue.py``         the ``Issue`` dataclass
- ``active_element.py`` cheap MESH validators
- ``active_slot.py``   cheap Empty/slot validators
- ``export.py``        full pre-export pass + atlas file checks
- ``_shared.py``       PG/CP read helpers shared between validators
"""

from __future__ import annotations

from .active_element import validate_active_element
from .active_slot import validate_active_slot
from .export import validate_export
from .issue import Issue, Severity

__all__ = [
    "Issue",
    "Severity",
    "validate_active_element",
    "validate_active_slot",
    "validate_export",
]
