"""Help-topic data model + prose reflow for the in-panel ``?`` popups.

Pure Python - no bpy imports - so the dispatch can be unit-tested and the panel
module can read content without a draw-time import cycle. The topic table itself
lives in :mod:`help_topics_content`; the doc-path mirror + dispatch in
:mod:`help_doc_paths`. Import everything through the :mod:`help_topics` facade.

Each ``HelpSection.body`` is one paragraph string. Prose flows free and is
reflowed to the popup width at draw time (:func:`reflow_paragraph`); a bullet or
numbered list keeps an explicit ``\\n`` between items so the structure survives
the reflow. No Markdown - the popup renders one ``layout.label`` per wrapped line.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Greedy word-wrap budget: ``layout.label`` cannot wrap and Blender exposes no
#: draw-time text metrics in a popup, so prose is reflowed against a fixed
#: character count. This is the readability lever; the popup width is derived
#: from it below so the two can never drift (the old pair - a 480 px popup
#: against a 72-char wrap - left the right band of the popup empty).
POPUP_WRAP_CHARS = 72

#: Default-scale glyph advance for ``layout.label`` (approximate - Blender gives
#: no draw-time metric) plus the popup's inner chrome. Keep ``_POPUP_PX_PER_CHAR``
#: a hair above the real advance so a full-width line never clips; lower it if a
#: band reappears, raise it if text clips. ``POPUP_WRAP_CHARS`` is the readability
#: knob.
_POPUP_PX_PER_CHAR = 5
_POPUP_MARGIN_PX = 30

#: The help popup width passed to ``invoke_popup``, in pixels - DERIVED from the
#: wrap budget so it is always the wrapped-text extent and the empty-band defect
#: cannot return.
POPUP_WIDTH = POPUP_WRAP_CHARS * _POPUP_PX_PER_CHAR + _POPUP_MARGIN_PX


@dataclass(frozen=True)
class HelpSection:
    heading: str
    body: str  # one paragraph; "\n" separates explicit list items / steps


@dataclass(frozen=True)
class HelpTopic:
    """One help entry surfaced via the ``?`` button.

    Sections render in order. ``see_also`` is rendered as a tail list of docs /
    example URLs for users who want to dive deeper.
    """

    title: str
    summary: str  # one-liner shown at the top of the popup
    sections: tuple[HelpSection, ...]
    see_also: tuple[str, ...] = field(default_factory=tuple)
    doc_url: str = ""  # full URL to the online docs page; empty hides the button


_SECTION_WHAT = "What it does"
_SECTION_HOW = "How to use it"
_SECTION_WHERE = "Where it fits"


def _section(heading: str, *parts: str) -> HelpSection:
    """A prose section: ``parts`` join with spaces into one reflowed paragraph."""
    return HelpSection(heading=heading, body=" ".join(parts))


def _list_section(heading: str, *items: str) -> HelpSection:
    """A list/step section: ``items`` join with newlines so each keeps its own line."""
    return HelpSection(heading=heading, body="\n".join(items))


def _is_list_item(text: str) -> bool:
    """True when a paragraph is a bullet (``- ``) or numbered (``1. ``) item."""
    stripped = text.lstrip()
    if stripped.startswith("- "):
        return True
    head = stripped.split(" ", 1)[0]
    return len(head) > 1 and head.endswith(".") and head[:-1].isdigit()


def reflow_paragraph(text: str, width: int) -> list[str]:
    """Greedy word-wrap one logical line to ``width`` characters.

    ``layout.label`` does not wrap, so the popup reflows each paragraph here. A
    bullet / numbered item keeps a two-space hanging indent on its wrapped
    continuation lines so the marker stays visually distinct. Blank input yields
    no lines.
    """
    words = text.split()
    if not words:
        return []
    cont = "  " if _is_list_item(text) else ""
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        indent = cont if lines else ""
        if len(indent) + len(current) + 1 + len(word) > width:
            lines.append((cont if lines else "") + current)
            current = word
        else:
            current = f"{current} {word}"
    lines.append((cont if lines else "") + current)
    return lines
