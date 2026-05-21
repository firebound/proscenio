"""Pure weight diff (SPEC 013.2 paint, T6).

Detects vertex indices whose weight changed by more than ``eps``.
StrokeDiffTracker uses this to know which sidecar entries flip to
``user_paint`` provenance after a brush stroke ends.

Pure Python: stdlib only.
"""

from __future__ import annotations


def diff_weights(
    before: dict[int, float],
    after: dict[int, float],
    *,
    eps: float = 1e-4,
) -> set[int]:
    """Return vert indices whose weight changed by more than eps.

    Missing vert in ``after`` (group removed by paint) counts as changed.
    Missing vert in ``before`` (group gained by paint) counts as changed.
    """
    touched: set[int] = set()
    for vert_idx, prior in before.items():
        current = after.get(vert_idx)
        if current is None or abs(current - prior) > eps:
            touched.add(vert_idx)
    for vert_idx in after:
        if vert_idx not in before:
            touched.add(vert_idx)
    return touched
