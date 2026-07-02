"""In-panel help-topic dispatch facade for Proscenio.

Powers the ``?`` button surfaced next to every Proscenio subpanel. Split into
three internal modules, re-exported here so callers and tests keep one import:

- :mod:`help_topics_model`   the data model (``HelpTopic`` / ``HelpSection``),
  the popup-width constants, and prose reflow.
- :mod:`help_topics_content` the ``HELP_TOPICS`` table.
- :mod:`help_doc_paths`      the ``_DOC_PATHS`` mirror + ``topic_for`` dispatch.

Pure Python - no bpy imports - so the dispatch can be unit-tested and the panel
module can read content without a draw-time import cycle.
"""

from __future__ import annotations

from .help_doc_paths import _DOC_PATHS, _DOCS_BASE, known_topic_ids, topic_for
from .help_topics_content import HELP_TOPICS
from .help_topics_model import (
    _POPUP_MARGIN_PX,
    _POPUP_PX_PER_CHAR,
    POPUP_WIDTH,
    POPUP_WRAP_CHARS,
    HelpSection,
    HelpTopic,
    reflow_paragraph,
)

__all__ = [
    "HELP_TOPICS",
    "POPUP_WIDTH",
    "POPUP_WRAP_CHARS",
    "_DOCS_BASE",
    "_DOC_PATHS",
    "_POPUP_MARGIN_PX",
    "_POPUP_PX_PER_CHAR",
    "HelpSection",
    "HelpTopic",
    "known_topic_ids",
    "reflow_paragraph",
    "topic_for",
]
