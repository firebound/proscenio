"""Panel/subpanel -> docs-path mirror + the topic dispatch."""

from __future__ import annotations

from dataclasses import replace

from .help_topics_content import HELP_TOPICS
from .help_topics_model import HelpTopic

# Base URL of the per-panel Blender addon reference (docs/02-tools/blender-addon).
# topic_for injects the matching page (and section anchor) as the topic's
# doc_url so the help popup's "Open online docs" button lands on it - the URL
# scheme lives here once instead of on every HelpTopic literal.
_DOCS_BASE = "https://firebound.github.io/proscenio/tools/blender-addon/"

#: The canonical panel/subpanel -> doc-path mirror (spec 064, Decision 3). The
#: docs site mirrors the Blender panel tree exactly: every top-level panel topic
#: points at its bare page; every subpanel topic points at
#: ``<parent-page>#<subpanel-anchor>``; the three topics that are neither a panel
#: nor a subpanel (``status_legend``, ``pose_library``, ``sprite_frame_preview``)
#: deep-link to an anchor inside their host section rather than owning a page or a
#: top-level section. ``tests/test_help_topics.py`` holds this map to the panel
#: tree and the doc headings in both directions, so a drift fails CI.
_DOC_PATHS: dict[str, str] = {
    # Pipeline panel + its three subpanels (Validate folded in from the old
    # standalone 09-validation.md page, spec 064).
    "pipeline_overview": "pipeline",
    "import_photoshop": "pipeline#import",
    "validation": "pipeline#validate",
    "export": "pipeline#export",
    # Outliner panel.
    "outliner": "outliner",
    # Element panel + its five subpanels.
    "active_element": "element",
    "active_mesh": "element#active-mesh",
    "active_sprite": "element#active-sprite",
    "sprite_bone_parent": "element#attach-to-bone",
    "texture_region": "element#texture-region",
    "drive_from_bone": "element#drive-from-bone",
    # Slots panel + its one subpanel.
    "slot_system": "slots",
    "active_slot": "slots#active-slot",
    # Skeleton panel + its subpanels. pose_library is the Save Pose to Library
    # row button inside Pose Mode, so it deep-links to its own in-section anchor
    # under that section rather than owning a top-level section (Decision 5).
    "skeleton": "skeleton",
    "armature": "skeleton#active-armature",
    "rig_ui": "skeleton#rig-ui",
    "pose_mode": "skeleton#pose-mode",
    "pose_library": "skeleton#save-pose-to-library",
    "quick_armature": "skeleton#quick-armature",
    # Mesh Generation panel + its subpanels.
    "mesh_generation": "mesh-generation",
    "automesh_alpha": "mesh-generation#automesh-from-alpha",
    "automesh_interactive": "mesh-generation#automesh-interactive",
    "debug_pipeline": "mesh-generation#debug-pipeline",
    # Manual Mesh - its own top-level panel + page (spec 070).
    "manual_mesh": "manual-mesh",
    # Weight Paint panel + its subpanels.
    "weight_paint": "weight-paint",
    "bind": "weight-paint#bind",
    "edit_weights": "weight-paint#edit-weights",
    "snapshot": "weight-paint#snapshot",
    "weight_transfer": "weight-paint#weight-transfer",
    # Animation, Atlas, Helpers panels.
    "animation": "animation",
    "atlas": "atlas",
    "helpers": "helpers",
    # sprite_frame_preview is the Material Preview sub-box on the Active Sprite
    # subpanel, so it deep-links to its own in-section anchor under that section
    # (Decision 5), not the bare subpanel H2.
    "sprite_frame_preview": "element#material-preview",
    # status_legend is the About/index page's badge legend, not a panel.
    "status_legend": "index#status-badges",
}


def topic_for(topic_id: str) -> HelpTopic | None:
    """Return the help topic for an id, or ``None`` for unknown ids.

    Topics listed in ``_DOC_PATHS`` get their ``doc_url`` filled from the
    addon reference base so the popup's "Open online docs" button works
    without repeating the URL on every literal.
    """
    topic = HELP_TOPICS.get(topic_id)
    if topic is None:
        return None
    rel = _DOC_PATHS.get(topic_id)
    if rel and not topic.doc_url:
        return replace(topic, doc_url=_DOCS_BASE + rel)
    return topic


def known_topic_ids() -> tuple[str, ...]:
    """Return every topic id in registration order. Useful for tests."""
    return tuple(HELP_TOPICS.keys())
