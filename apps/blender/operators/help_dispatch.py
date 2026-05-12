"""Help-dispatch operators: status badge, help popup, smoke test (5.1.d.5)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ..core.feature_status import (  # type: ignore[import-not-found]
    STATUS_BADGES,
    FeatureStatus,
)
from ..core.help_topics import topic_for  # type: ignore[import-not-found]


class PROSCENIO_OT_status_info(bpy.types.Operator):
    """Status-icon proxy: hover -> band tooltip; click -> open status legend."""

    bl_idname = "proscenio.status_info"
    bl_label = "Proscenio: Feature Status"
    bl_options: ClassVar[set[str]] = {"REGISTER", "INTERNAL"}

    band: StringProperty(  # type: ignore[valid-type]
        name="Band",
        description="FeatureStatus enum value - 'godot-ready', 'blender-only', etc.",
        default="godot-ready",
    )

    @classmethod
    def description(
        cls,
        _context: bpy.types.Context,
        properties: bpy.types.AnyType,
    ) -> str:
        try:
            band = FeatureStatus(properties.band)
        except ValueError:
            return str(cls.bl_label)
        return str(STATUS_BADGES[band].tooltip)

    def invoke(self, _context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        bpy.ops.proscenio.help("INVOKE_DEFAULT", topic="status_legend")
        return {"FINISHED"}

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return {"FINISHED"}


class PROSCENIO_OT_help(bpy.types.Operator):
    """Pop up an in-panel help dialog for a given topic id (5.1.d.5)."""

    bl_idname = "proscenio.help"
    bl_label = "Proscenio: Help"
    bl_description = "Open an explanation of this panel section"
    bl_options: ClassVar[set[str]] = {"REGISTER", "INTERNAL"}

    topic: StringProperty(  # type: ignore[valid-type]
        name="Topic",
        description="Help-topic id resolved against core.help_topics.HELP_TOPICS",
        default="pipeline_overview",
    )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        result: set[str] = context.window_manager.invoke_popup(self, width=480)
        return result

    def execute(self, _context: bpy.types.Context) -> set[str]:
        return {"FINISHED"}

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        topic = topic_for(self.topic)
        if topic is None:
            layout.label(text=f"unknown help topic: {self.topic!r}", icon="ERROR")
            return
        header = layout.row()
        header.label(text=topic.title, icon="QUESTION")
        layout.label(text=topic.summary)
        for section in topic.sections:
            layout.separator()
            layout.label(text=section.heading + ":", icon="DOT")
            for line in section.body:
                layout.label(text=line)
        if topic.see_also:
            layout.separator()
            layout.label(text="See also:", icon="URL")
            for ref in topic.see_also:
                layout.label(text="  " + ref)


class PROSCENIO_OT_smoke_test(bpy.types.Operator):
    """Smoke test operator - confirms the addon registers and dispatches."""

    bl_idname = "proscenio.smoke_test"
    bl_label = "Proscenio: Smoke Test"
    bl_description = "Print a sanity check to the system console"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        message = "Proscenio smoke test OK"
        self.report({"INFO"}, message)
        print(f"[Proscenio] {message}")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_help,
    PROSCENIO_OT_status_info,
    PROSCENIO_OT_smoke_test,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
