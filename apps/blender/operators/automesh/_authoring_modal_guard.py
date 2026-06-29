"""Mutual exclusivity for the authoring modals (spec 070).

The mesh-generation modes are one-per-element and must not run at the same time:
Automesh Interactive and Manual Draw each grab the viewport, share GPU overlay
state, and (for the automesh modal) class-level stage state - so launching one
while the other is live corrupts both. Each modal marks itself running on invoke
and stopped on finish; the other's ``poll`` refuses while a different modal is
live. A module-level registry keeps it free of cross-imports between the two
operator modules.
"""

from __future__ import annotations

_active: set[str] = set()


def mark_running(name: str) -> None:
    _active.add(name)


def mark_stopped(name: str) -> None:
    _active.discard(name)


def other_running(name: str) -> bool:
    """True when a DIFFERENT authoring modal than ``name`` is currently live."""
    return bool(_active - {name})


def is_running(name: str) -> bool:
    """True when the modal ``name`` is itself live (drives the toggle button +
    the re-invoke-is-exit handshake)."""
    return name in _active
