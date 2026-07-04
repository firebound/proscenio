"""Shared type alias for the per-locale tables (no intra-package deps).

Kept in its own module so both the package ``__init__`` and every locale
module can import it without a circular import (``__init__`` imports the
locale modules, which would otherwise import back from ``__init__``).
"""

from __future__ import annotations

#: One catalog entry: ``((msgctxt, msgid), msgstr)``. The ``msgid`` is the
#: canonical English source string; ``msgctxt`` is usually ``"*"`` (Blender's
#: default interface context) or ``"Operator"``.
LocaleRow = tuple[tuple[str, str], str]
