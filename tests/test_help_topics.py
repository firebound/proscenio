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


def test_see_also_references_exist_on_disk() -> None:
    """Cross-references must point at real directories or files.

    Catches drift - if a referenced path is renamed or removed, the help
    topic surfaces a broken pointer.
    """
    for topic_id, topic in HELP_TOPICS.items():
        for ref in topic.see_also:
            target = REPO_ROOT / ref
            assert target.exists(), (
                f"topic {topic_id!r} references missing path {ref!r} "
                f"(resolved to {target})"
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
