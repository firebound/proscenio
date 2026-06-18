"""Unit tests for the in-panel help-topic dispatch table.

Pure pytest, no Blender. Confirms every topic surfaced by the panel UI
exists in the table + carries non-empty content + cross-references
real directories on disk.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.help_topics import (  # noqa: E402
    HELP_TOPICS,
    HelpTopic,
    known_topic_ids,
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
            assert section.body, f"empty section body in {topic_id!r}"
            for line in section.body:
                assert line, f"empty line in {topic_id!r}/{section.heading!r}"


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
