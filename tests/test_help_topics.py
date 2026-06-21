"""Unit tests for the in-panel help-topic dispatch table.

Pure pytest, no Blender. Confirms every topic surfaced by the panel UI
exists in the table + carries non-empty content + cross-references
real directories on disk.

The exact-mirror coverage test (spec 064) extends the spec-036 reverse-coverage
check below: it parses the Blender-addon doc headings off disk and holds the
``_DOC_PATHS`` map to the panel tree in both directions, so the docs site and
the in-panel ``?`` deep-links cannot drift apart.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.help_topics import (  # noqa: E402
    _DOC_PATHS,
    _DOCS_BASE,
    _POPUP_MARGIN_PX,
    _POPUP_PX_PER_CHAR,
    HELP_TOPICS,
    POPUP_WIDTH,
    POPUP_WRAP_CHARS,
    HelpTopic,
    known_topic_ids,
    reflow_paragraph,
    topic_for,
)


def test_pipeline_overview_is_present() -> None:
    """Required topic id - the main panel button targets it."""
    assert "pipeline_overview" in HELP_TOPICS


def test_topic_for_returns_known_topic() -> None:
    topic = topic_for("active_element")
    assert isinstance(topic, HelpTopic)
    assert topic.title


def test_topic_for_unknown_returns_none() -> None:
    assert topic_for("nonexistent_topic") is None


def test_every_topic_has_required_fields() -> None:
    for topic_id, topic in HELP_TOPICS.items():
        assert topic.title, f"empty title for {topic_id!r}"
        assert topic.summary, f"empty summary for {topic_id!r}"
        assert topic.sections, f"no sections for {topic_id!r}"
        for section in topic.sections:
            assert section.heading, f"empty section heading in {topic_id!r}"
            # body is one paragraph string ("\n" separates explicit list items).
            assert isinstance(section.body, str), f"non-str body in {topic_id!r}"
            assert section.body.strip(), f"empty section body in {topic_id!r}"
            for item in section.body.split("\n"):
                assert item.strip(), (
                    f"blank list item in {topic_id!r}/{section.heading!r}"
                )


def test_reflow_wraps_each_line_to_the_width() -> None:
    lines = reflow_paragraph("alpha bravo charlie delta echo", 11)
    assert all(len(line) <= 11 for line in lines)
    # No words lost or reordered by the wrap.
    assert " ".join(lines).split() == ["alpha", "bravo", "charlie", "delta", "echo"]


def test_reflow_blank_input_yields_no_lines() -> None:
    assert reflow_paragraph("   ", 40) == []


def test_popup_width_is_derived_from_the_wrap_budget() -> None:
    # The popup width must track the wrap budget by construction, so the two
    # cannot drift apart and re-open the empty right-band defect (spec 064).
    assert POPUP_WIDTH == POPUP_WRAP_CHARS * _POPUP_PX_PER_CHAR + _POPUP_MARGIN_PX


def test_no_topic_body_reflows_past_the_wrap_budget() -> None:
    for topic_id, topic in HELP_TOPICS.items():
        bodies = [topic.summary, *(section.body for section in topic.sections)]
        for body in bodies:
            for line in reflow_paragraph(body, POPUP_WRAP_CHARS):
                over = len(line) > POPUP_WRAP_CHARS
                assert not over, f"{topic_id}: line over {POPUP_WRAP_CHARS}: {line!r}"


def test_reflow_bullet_keeps_a_hanging_indent() -> None:
    lines = reflow_paragraph("- alpha bravo charlie delta", 12)
    assert lines[0].startswith("- ")
    assert all(line.startswith("  ") for line in lines[1:]), "continuation lines indent"


def test_panel_topic_ids_present() -> None:
    """Every topic id wired by the panel module must resolve."""
    panel_topic_ids = [
        "status_legend",
        "pipeline_overview",
        "active_element",
        "skeleton",
        "animation",
        "atlas",
        "validation",
        "export",
        "drive_from_bone",
        "pose_library",
    ]
    for tid in panel_topic_ids:
        assert tid in HELP_TOPICS, f"missing topic {tid!r}"


def test_see_also_references_are_urls() -> None:
    """Cross-references must be https URLs, not local paths or plaintext http.

    The help popup renders an http(s) ref as a clickable ``wm.url_open``
    button; a local path cannot resolve inside an installed (zipped) extension,
    so a non-URL ref is a dead button, and a clickable help link should not be
    plaintext http. This replaced the old disk-existence check when the
    local-path refs were migrated to GitHub https URLs.
    """
    for topic_id, topic in HELP_TOPICS.items():
        for ref in topic.see_also:
            assert ref.startswith("https://"), (
                f"topic {topic_id!r} see_also {ref!r} is not an https URL "
                f"(a local path cannot resolve in an installed extension, and "
                f"clickable help links should not be plaintext http)"
            )


def test_known_topic_ids_returns_registration_order() -> None:
    ids = known_topic_ids()
    assert ids[0] == "status_legend"  # first registered, first in dict
    assert "active_element" in ids


def test_no_duplicate_topic_ids() -> None:
    assert len(HELP_TOPICS) == len(set(HELP_TOPICS.keys()))


def test_every_topic_has_a_panel_or_operator_caller() -> None:
    """Reverse coverage: every topic id is referenced under panels/ or operators/.

    The forward test above checks that wired ids resolve; this one checks
    the other direction - that no topic in the table is orphaned with no UI
    entry point. A sidebar restructure that drops a ``?`` wiring then fails
    here instead of silently stranding the topic (the #96 regression that
    orphaned ``sprite_frame_preview`` and ``pose_library``).
    """
    addon = REPO_ROOT / "apps" / "blender"
    blob_parts: list[str] = []
    for sub in ("panels", "operators"):
        for path in sorted((addon / sub).rglob("*.py")):
            blob_parts.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(blob_parts)
    missing = [
        tid for tid in HELP_TOPICS if f'"{tid}"' not in blob and f"'{tid}'" not in blob
    ]
    assert not missing, f"help topics with no panel/operator caller: {missing}"


# ---------------------------------------------------------------------------
# Spec 064: the exact docs <-> panel mirror.
#
# The locked structural rule (STUDY.md, Decision 3): the docs mirror the Blender
# panel tree exactly. Every top-level panel owns one page; every subpanel owns
# one H2 section under its parent page; the About footer panel owns the index
# page; and a topic that is neither a panel nor a subpanel anchors inside its
# host section instead of owning a page or a top-level section.
#
# The tables below ARE that mirror, made visible. The tests hold them to three
# other artifacts in both directions: the ``?`` topics wired in panels/, the
# ``_DOC_PATHS`` map, and the doc-page headings on disk.
# ---------------------------------------------------------------------------

DOCS_DIR = REPO_ROOT / "docs" / "02-blender-addon"

#: The eleven pages the mirror allows: the ten top-level panels plus the index
#: (the About footer panel). Bare page slug -> the panel topic that owns it. The
#: index has no panel topic of its own (status_legend deep-links to an anchor on
#: it but is not a panel), so it maps to None.
PANEL_PAGES: dict[str, str | None] = {
    "pipeline": "pipeline_overview",
    "outliner": "outliner",
    "element": "active_element",
    "slots": "slot_system",
    "skeleton": "skeleton",
    "mesh-generation": "mesh_generation",
    "weight-paint": "weight_paint",
    "animation": "animation",
    "atlas": "atlas",
    "helpers": "helpers",
    "index": None,
}

#: Every subpanel topic -> the ``<page, anchor>`` H2 section it owns under its
#: parent page. Each anchor here MUST exist as an H2 on that page, and every H2
#: on a subpanel-bearing page MUST be claimed here (both directions are tested).
SUBPANEL_SECTIONS: dict[str, tuple[str, str]] = {
    # Pipeline subpanels (Validate folded in from the old standalone page).
    "import_photoshop": ("pipeline", "import"),
    "validation": ("pipeline", "validate"),
    "export": ("pipeline", "export"),
    # Element subpanels.
    "active_mesh": ("element", "active-mesh"),
    "active_sprite": ("element", "active-sprite"),
    "sprite_bone_parent": ("element", "attach-to-bone"),
    "texture_region": ("element", "texture-region"),
    "drive_from_bone": ("element", "drive-from-bone"),
    # Slots subpanel.
    "active_slot": ("slots", "active-slot"),
    # Skeleton subpanels.
    "armature": ("skeleton", "active-armature"),
    "pose_mode": ("skeleton", "pose-mode"),
    "quick_armature": ("skeleton", "quick-armature"),
    # Mesh Generation subpanels.
    "automesh_alpha": ("mesh-generation", "automesh-from-alpha"),
    "automesh_interactive": ("mesh-generation", "automesh-interactive"),
    "debug_pipeline": ("mesh-generation", "debug-pipeline"),
    # Weight Paint subpanels.
    "bind": ("weight-paint", "bind"),
    "edit_weights": ("weight-paint", "edit-weights"),
    "snapshot": ("weight-paint", "snapshot"),
    "weight_transfer": ("weight-paint", "weight-transfer"),
}

#: Topics that are neither a panel nor a subpanel: they hang off a row button or
#: a sub-box and deep-link to an anchor inside a host section (Decision 5). Each
#: maps to the ``<page, anchor>`` it points into. The anchor for status_legend
#: is its own H2 on the index page; pose_library / sprite_frame_preview ride the
#: H2 of their host subpanel section until the copy-rewrite PR gives them a
#: dedicated in-section anchor.
ANCHOR_TOPICS: dict[str, tuple[str, str]] = {
    "status_legend": ("index", "status-badges"),
    "pose_library": ("skeleton", "pose-mode"),
    "sprite_frame_preview": ("element", "active-sprite"),
}


def _slugify_heading(text: str) -> str:
    """Approximate Docusaurus's GitHub-style heading-id slug.

    Lowercase, drop inline-code backticks and other punctuation, collapse runs
    of whitespace to single hyphens. Enough for the plain-word headings the
    Blender-addon pages use; the test asserts the result, so a heading whose
    slug differs fails loudly here.
    """
    slug = text.strip().lower()
    slug = slug.replace("`", "")
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug.strip("-")


def _doc_page_slug(path: Path) -> str:
    """Bare routing slug for a doc file: the ``NN-`` ordering prefix is stripped.

    Docusaurus routes ``10-pipeline.md`` at ``.../pipeline`` and ``index.md`` at
    the section root, so ``_DOC_PATHS`` keys on the bare slug while the files on
    disk carry the numeric prefix.
    """
    stem = path.stem
    return stem.split("-", 1)[1] if re.match(r"^\d+-", stem) else stem


def _doc_page_path(slug: str) -> Path:
    """Resolve a bare routing slug to its prefixed file on disk."""
    for path in DOCS_DIR.glob("*.md"):
        if _doc_page_slug(path) == slug:
            return path
    raise FileNotFoundError(f"no Blender-addon doc page for slug {slug!r}")


def _page_headings(slug: str) -> dict[int, list[str]]:
    """Return ``{level: [anchor, ...]}`` for one Blender-addon page's headings.

    Parses ATX headings (``#``..``###``) off disk, skipping fenced code blocks,
    and returns their slug anchors keyed by heading level.
    """
    text = _doc_page_path(slug).read_text(encoding="utf-8")
    headings: dict[int, list[str]] = {}
    in_fence = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not match:
            continue
        level = len(match.group(1))
        headings.setdefault(level, []).append(_slugify_heading(match.group(2)))
    return headings


def _wired_help_topics() -> set[str]:
    """Every ``help_topic`` id wired by a ``?`` in panels/ (bpy-free, source-parsed).

    Matches the four header/help-button draw helpers' trailing topic argument so
    a new ``?`` wiring that the mirror tables forget to cover fails the
    completeness test below.
    """
    panels_dir = REPO_ROOT / "apps" / "blender" / "panels"
    topics: set[str] = set()
    # draw_subpanel_header(layout, context, feature_id, "topic")
    # draw_subbox_header(box, title, icon, feature_id, "topic")
    header_call = re.compile(
        r"draw_sub(?:panel|box)_header\([^)]*?,\s*['\"][^'\"]+['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*,?\s*\)",
        re.DOTALL,
    )
    # draw_help_button(layout, "topic")
    button_call = re.compile(r"draw_help_button\([^,]+,\s*['\"]([^'\"]+)['\"]\s*\)")
    for path in sorted(panels_dir.rglob("*.py")):
        src = path.read_text(encoding="utf-8")
        topics.update(header_call.findall(src))
        topics.update(button_call.findall(src))
    return topics


def test_doc_pages_on_disk_equal_the_locked_panel_set() -> None:
    """The page set is exactly the ten panels plus index - no extras, no missing.

    After the spec-064 fold there is no standalone 09-validation.md; Validate is
    a section of the Pipeline page. ``_category_.json`` is sidebar metadata, not
    a page.
    """
    on_disk = {_doc_page_slug(p) for p in DOCS_DIR.glob("*.md")}
    assert on_disk == set(PANEL_PAGES), (
        f"doc page set drifted from the locked panel mirror: "
        f"extra={sorted(on_disk - set(PANEL_PAGES))} "
        f"missing={sorted(set(PANEL_PAGES) - on_disk)}"
    )
    assert not (DOCS_DIR / "09-validation.md").exists(), (
        "09-validation.md must be folded into pipeline.md#validate (spec 064)"
    )


def test_mirror_tables_partition_the_doc_paths() -> None:
    """The three mirror tables together cover exactly the ``_DOC_PATHS`` keys.

    Every topic with a doc deep-link is classified as a panel, a subpanel, or an
    anchor topic - and nothing is classified twice or left out.
    """
    panel_topics = {t for t in PANEL_PAGES.values() if t is not None}
    classified = panel_topics | set(SUBPANEL_SECTIONS) | set(ANCHOR_TOPICS)
    overlaps = (
        (panel_topics & set(SUBPANEL_SECTIONS))
        | (panel_topics & set(ANCHOR_TOPICS))
        | (set(SUBPANEL_SECTIONS) & set(ANCHOR_TOPICS))
    )
    assert not overlaps, (
        f"topics classified in more than one mirror table: {sorted(overlaps)}"
    )
    assert classified == set(_DOC_PATHS), (
        f"mirror tables disagree with _DOC_PATHS: "
        f"only_in_tables={sorted(classified - set(_DOC_PATHS))} "
        f"only_in_DOC_PATHS={sorted(set(_DOC_PATHS) - classified)}"
    )


def test_every_doc_path_matches_its_mirror_classification() -> None:
    """``_DOC_PATHS`` values equal what the mirror tables say they must be.

    A panel topic -> the bare page; a subpanel/anchor topic -> ``page#anchor``.
    """
    for page, topic in PANEL_PAGES.items():
        if topic is None:
            continue
        assert _DOC_PATHS[topic] == page, (
            f"{topic}: panel topic must map to bare {page!r}"
        )
    for topic, (page, anchor) in {**SUBPANEL_SECTIONS, **ANCHOR_TOPICS}.items():
        assert _DOC_PATHS[topic] == f"{page}#{anchor}", (
            f"{topic}: must map to {page}#{anchor!r}"
        )


def test_every_doc_path_resolves_to_a_page_and_anchor_on_disk() -> None:
    """Every ``_DOC_PATHS`` value points at a real page file and, when it has a
    ``#anchor``, a real heading on that page."""
    for topic, rel in _DOC_PATHS.items():
        page, _, anchor = rel.partition("#")
        assert page in {_doc_page_slug(p) for p in DOCS_DIR.glob("*.md")}, (
            f"{topic}: doc page {page!r} is missing"
        )
        if anchor:
            anchors = {
                a
                for level_anchors in _page_headings(page).values()
                for a in level_anchors
            }
            assert anchor in anchors, (
                f"{topic}: anchor #{anchor} not found as a heading in {page}.md "
                f"(have: {sorted(anchors)})"
            )


def test_every_subpanel_section_is_an_h2_on_its_parent_page() -> None:
    """Each subpanel topic's anchor is an actual H2 (not H1/H3) on its page.

    The mirror reserves H2s for subpanels, so the anchor must live at H2 depth.
    """
    for topic, (page, anchor) in SUBPANEL_SECTIONS.items():
        h2s = set(_page_headings(page).get(2, []))
        assert anchor in h2s, (
            f"{topic}: #{anchor} must be an H2 on {page}.md (H2s there: {sorted(h2s)})"
        )


def test_every_h2_on_a_subpanel_page_has_a_subpanel_topic() -> None:
    """Reverse direction: no orphan H2. Every H2 on a subpanel-bearing panel page
    is claimed by exactly one subpanel topic.

    The index page is excluded: it is the About panel's prose page, and its H2s
    (What it does / The sidebar / Header affordances / Status badges) are
    documentation structure, not subpanels - status_legend deep-links to one
    anchor but is not a subpanel.
    """
    claimed: dict[str, set[str]] = {}
    for _topic, (page, anchor) in SUBPANEL_SECTIONS.items():
        claimed.setdefault(page, set()).add(anchor)
    for page in PANEL_PAGES:
        if page == "index":
            continue
        h2s = set(_page_headings(page).get(2, []))
        orphans = h2s - claimed.get(page, set())
        assert not orphans, (
            f"{page}.md has H2(s) with no subpanel topic pointing at them: {sorted(orphans)} "
            f"(the mirror requires every subpanel-page H2 to be a subpanel section)"
        )


def test_every_wired_question_button_topic_has_a_doc_path() -> None:
    """Every ``?`` topic wired in panels/ resolves to a ``_DOC_PATHS`` entry.

    This is the forward leg of the mirror: a panel/subpanel/button that surfaces
    a ``?`` must deep-link somewhere, so a new wiring without a doc mapping fails
    here. (status_legend's ``?`` is the status operator, not a panel header
    topic, so it is allowed to be wired elsewhere; it still carries a doc path.)
    """
    wired = _wired_help_topics()
    # Sanity: the parser actually found the wirings, not an empty set.
    assert "pipeline_overview" in wired and "validation" in wired, (
        f"help-topic wiring parser found too little: {sorted(wired)}"
    )
    missing = sorted(t for t in wired if t not in _DOC_PATHS)
    assert not missing, f"wired ? topics with no _DOC_PATHS deep-link: {missing}"


def test_every_wired_topic_is_in_the_mirror_tables() -> None:
    """Every wired ``?`` topic is classified by the mirror tables, so a new
    panel/subpanel cannot be added without the mirror test covering it."""
    wired = _wired_help_topics()
    classified = (
        {t for t in PANEL_PAGES.values() if t is not None}
        | set(SUBPANEL_SECTIONS)
        | set(ANCHOR_TOPICS)
    )
    missing = sorted(t for t in wired if t not in classified)
    assert not missing, f"wired ? topics absent from the mirror tables: {missing}"


def test_topic_for_fills_doc_url_for_every_mapped_topic() -> None:
    """``topic_for`` injects the ``_DOCS_BASE`` doc_url for each mapped topic."""
    for topic_id, rel in _DOC_PATHS.items():
        topic = topic_for(topic_id)
        assert topic is not None, f"{topic_id} not in HELP_TOPICS"
        assert topic.doc_url == _DOCS_BASE + rel, (
            f"{topic_id}: doc_url {topic.doc_url!r} != base + {rel!r}"
        )
