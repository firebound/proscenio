"""Skeleton panel + bone UIList + accordion subpanels.

The Skeleton panel hosts the isolated project-wide Active Armature
selector and the armature-presence messaging. The body splits into
subpanels: Armature (the bone hierarchy), Pose Mode (pose-only
authoring ops), and Quick Armature (the modal rig draw + its defaults).
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.bone_export import bone_is_exported  # type: ignore[import-not-found]
from ..core.bone_view import bone_depth, bone_sort_key  # type: ignore[import-not-found]
from ..core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    resolve_collection,
)
from ..core.bpy_helpers._shared.bone_select import (  # type: ignore[import-not-found]
    BONE_SELECT_MODES,
    bone_is_selected,
)
from ..core.bpy_helpers.armature import (  # type: ignore[import-not-found]
    IkChainScan,
    scan_ik_chains,
)
from ..core.bpy_helpers.i18n import iface
from ..core.list_view import compute_list_filter  # type: ignore[import-not-found]
from ..core.rig_ui_view import RigUIRow, rig_ui_rows  # type: ignore[import-not-found]
from ._draw_ik import (
    _active_ik_constraint,
    _draw_ik_constraint_props,
    _draw_ik_toggle,
)
from ._draw_rig_ui import draw_eye, draw_swatch
from ._helpers import _POSE_FRIENDLY_MODES, draw_help_button, draw_subpanel_header
from ._list import ProscenioListMixin, draw_select_marker

__all__ = ["_active_ik_constraint"]


def _explicit_target(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene's picked Active Armature object, or None."""
    scene_props = getattr(context.scene, "proscenio", None)
    return scene_props.active_armature if scene_props is not None else None


def _bone_connectivity_icon(bone: bpy.types.Bone) -> str:
    """The bone-list left indicator icon: connectivity, or the bone glyph.

    Every list row is a bone, so the type icon is redundant - the left icon shows
    parenting connectivity instead: ``LINKED`` when joined to its parent,
    ``UNLINKED`` for a disconnected child, and the plain ``BONE_DATA`` glyph for a
    root (no parent, so no connectivity to show).
    """
    if getattr(bone, "use_connect", False):
        return "LINKED"
    if getattr(bone, "parent", None) is not None:
        return "UNLINKED"
    return "BONE_DATA"


# Rig UI eye pinned width; the swatch/theme columns live in ``_draw_rig_ui``.
_RIG_UI_EYE_UNITS = 1.4


# Below this N-panel width the Skeleton header drops the picked-armature name
# and keeps just "Skeleton" (a custom draw_header label cannot truncate, so the
# name is dropped wholesale rather than left to vanish mid-word). GUI-tunable.
_SKELETON_HEADER_NAME_MIN_WIDTH = 220


class PROSCENIO_UL_bones(ProscenioListMixin, bpy.types.UIList):
    """List view for ``Armature.bones`` - the Armature subpanel uses this.

    Multi-select: a click maps to a real bone selection (Shift extends, Ctrl
    toggles), so in POSE / EDIT modes each row shows the per-row selection
    marker. The shared mixin gives it native ``filter_name`` search; source
    (hierarchy) order is kept so the depth indent stays meaningful.
    """

    bl_idname = "PROSCENIO_UL_bones"

    def filter_items(
        self,
        context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        """Run the shared name/visibility filter, then refresh the IK scan once.

        ``filter_items`` is Blender's single per-draw-pass hook (it runs once
        before the per-row ``draw_item`` calls), so it is where the IK scan is
        rebuilt: keying a cross-redraw cache on the bone count missed chains
        added / removed on existing bones (those leave the count unchanged), so
        the tip / control icons went stale. A fresh scan per pass keeps the cue
        live; ``draw_item`` then reads the cached scan as an O(1) set lookup.

        It also applies the hierarchy/flat-alpha sort (:func:`bone_sort_key`) and
        the favorites-only filter, mirroring the Outliner: A-Z off keeps the
        parenting tree, on flattens to plain alphabetical; the favorites toggle
        on the Active Armature header hides every non-pinned bone.
        """
        self._ik_scan = self._scan_ik_for(data)  # type: ignore[attr-defined]
        bones = list(getattr(data, propname))
        scene_props = getattr(context.scene, "proscenio", None)
        favorites_only = bool(
            scene_props is not None and getattr(scene_props, "skeleton_show_favorites", False)
        )
        sort_alpha = bool(getattr(self, "use_filter_sort_alpha", False))

        def _visible(bone: bpy.types.Bone) -> bool:
            if not favorites_only:
                return True
            bone_props = getattr(bone, "proscenio", None)
            return bool(bone_props is not None and getattr(bone_props, "is_favorite", False))

        return compute_list_filter(
            bones,
            bitflag=self.bitflag_filter_item,
            name_filter=self.filter_name or "",
            name_of=lambda bone: bone.name,
            visible=_visible,
            sort_key=lambda bone: bone_sort_key(bone, sort_alpha=sort_alpha),
        )

    def _scan_ik_for(self, data: bpy.types.AnyType) -> IkChainScan:
        """Scan the armature owning the list's ``data`` block for IK chains."""
        armature_obj = next(
            (o for o in bpy.data.objects if o.type == "ARMATURE" and o.data is data),
            None,
        )
        if armature_obj is None:
            return IkChainScan(chains=[])
        return scan_ik_chains(armature_obj)

    def draw_item(
        self,
        context: bpy.types.Context,
        layout: bpy.types.UILayout,
        data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        row = layout.row(align=True)
        # `data` is the armature data block. Walk back to its owning Object
        # so the operator can address it by name + sync bone selection.
        armature_obj = next(
            (o for o in bpy.data.objects if o.type == "ARMATURE" and o.data is data),
            None,
        )
        # Multi-select marker, only where bone selection is real (POSE / EDIT):
        # the single template_list highlight cannot show a multi-bone selection.
        if armature_obj is not None and context.mode in BONE_SELECT_MODES:
            draw_select_marker(
                row, selected=bone_is_selected(armature_obj, item.name, context.mode)
            )
        # IK cue: a chain tip carries the constraint icon, a control bone (some
        # chain's subtarget) carries the goal-object glyph. Driven by the live
        # constraint scan (refreshed once per pass in ``filter_items``), never
        # the .IK name suffix. Fall back to a fresh scan if a draw somehow runs
        # before ``filter_items`` populated it.
        scan = getattr(self, "_ik_scan", None)
        if scan is None:
            scan = self._scan_ik_for(data)
        if scan.is_tip(item.name):
            row.label(text="", icon="CON_KINEMATIC")
        elif scan.is_control(item.name):
            row.label(text="", icon="EMPTY_ARROWS")
        # The native A-Z toggle flattens the list to plain alphabetical; the
        # parenting-tree indent is meaningful only in the default (hierarchy)
        # order, so it is dropped when sorting alphabetically (mirrors the
        # Outliner).
        sort_alpha = bool(getattr(self, "use_filter_sort_alpha", False))
        depth = 0 if sort_alpha else bone_depth(item)
        arm_name = armature_obj.name if armature_obj is not None else ""
        # A bare operator button stretches and centers its text, which hid the
        # depth indent. Split the row and draw the name in a LEFT-aligned
        # sub-row so it hugs the left edge (same fix as the Outliner); the
        # connectivity icons + favorite star take the right side.
        split = row.split(factor=0.62, align=True)
        name_row = split.row()
        name_row.alignment = "LEFT"
        # Every row is a bone, so the type icon (BONE_DATA) is redundant: show the
        # connectivity instead, as the row's left indicator (LINKED connected /
        # UNLINKED disconnected child / BONE_DATA root). It rides the select
        # button's icon - the name still selects; the icon is just the cue (the
        # right side holds the interactive toggles). Mirrors the Outliner.
        op = name_row.operator(
            "proscenio.select_bone_by_name",
            text=("  " * depth) + item.name,
            icon=_bone_connectivity_icon(item),
            emboss=False,
        )
        op.armature_name = arm_name
        op.bone_name = item.name
        right = split.row(align=True)
        right.alignment = "RIGHT"
        self._draw_bone_flags(right, item, arm_name)

    @staticmethod
    def _draw_bone_flags(row: bpy.types.UILayout, item: bpy.types.Bone, arm_name: str) -> None:
        """Draw the right-side interactive toggles: relative, export, favorite.

        The right side is interactive only - the connectivity cue moved to the
        row's left icon (:func:`_bone_connectivity_icon`), so the no-op info icon
        is gone from here. Relative parenting is a live toggle (only meaningful
        with a parent); like the export and favorite toggles it stays flat
        (``emboss=False``) and shows its state by swapping the icon, not by a
        near-invisible depress: a filled ``PINNED`` pushpin when on (the child is
        pinned to follow the parent's transform), a hollow ``UNPINNED`` when off -
        the same filled/hollow read as the favorite star. The export toggle pins a
        rig helper off the Godot export. The favorite star pins the bone in the
        list.
        """
        if item.parent is not None:
            relative = bool(getattr(item, "use_relative_parent", False))
            rel = row.operator(
                "proscenio.toggle_bone_relative_parent",
                text="",
                icon="PINNED" if relative else "UNPINNED",
                emboss=False,
            )
            rel.armature_name = arm_name
            rel.bone_name = item.name
        # Export toggle: an exported bone shows the EXPORT tray; a non-exported
        # one (control scaffolding or a helper the rigger pinned off) shows a
        # CANCEL glyph, depressed so the excluded few stand out in the list. The
        # icon reads the combined gate so an IK control reads "won't export" too,
        # but clicking only flips the rigger's own exclude_from_export flag.
        # (Render/visibility icons are deliberately avoided - this is about the
        # Godot export, not the viewport or render.)
        exported = bone_is_exported(item)
        exp = row.operator(
            "proscenio.toggle_bone_export",
            text="",
            icon="EXPORT" if exported else "CANCEL",
            emboss=False,
            depress=not exported,
        )
        exp.armature_name = arm_name
        exp.bone_name = item.name
        bone_props = getattr(item, "proscenio", None)
        is_fav = bool(bone_props is not None and getattr(bone_props, "is_favorite", False))
        fav = row.operator(
            "proscenio.toggle_bone_favorite",
            text="",
            icon="SOLO_ON" if is_fav else "SOLO_OFF",
            emboss=False,
        )
        fav.armature_name = arm_name
        fav.bone_name = item.name


class PROSCENIO_PT_skeleton(bpy.types.Panel):
    """Skeleton - the project-wide armature selector + presence checks."""

    # The full "Skeleton: <name>" title is drawn in draw_header (bl_label
    # blank) because Blender renders draw_header LEFT of bl_label here, so the
    # whole title must live in one place to read in order. A custom draw_header
    # label has no native truncation, so instead of letting "Skeleton: <name>"
    # vanish when narrow, draw_header drops the <name> below a width threshold
    # and keeps the short "Skeleton" - which survives narrow widths fine.
    bl_label = ""
    bl_idname = "PROSCENIO_PT_skeleton"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 4
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode in _POSE_FRIENDLY_MODES

    def draw_header(self, context: bpy.types.Context) -> None:
        target = _explicit_target(context)
        try:
            name = target.name if target is not None else None
        except ReferenceError:
            name = None
        region = getattr(context, "region", None)
        width = getattr(region, "width", 9999)
        # Keep "Skeleton: <name>" while there is room; drop the name (the base
        # "Skeleton" stays) once the panel is too narrow to fit it.
        if name and width >= _SKELETON_HEADER_NAME_MIN_WIDTH:
            self.layout.label(text=f"Skeleton: {name}")
        else:
            self.layout.label(text=iface("Skeleton"))

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "skeleton", "skeleton")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        # Writes during ``draw`` are forbidden by Blender, so the initial
        # fill happens in the load_post handler; here the picker is surfaced
        # read-only (clearing it falls back to QuickRig).
        if scene_props is not None:
            row = layout.row(align=True)
            row.label(text="", icon="ARMATURE_DATA")
            row.prop(scene_props, "active_armature", text="")
        # The "Exports: <name>" read-out moved to Pipeline > Export (the panel
        # that actually exports); Skeleton just picks the rig.
        explicit_target = _explicit_target(context)
        if not armatures:
            row = layout.row()
            row.label(text=iface("no Armature in scene - use Quick Armature below"), icon="INFO")
        elif explicit_target is None:
            box = layout.box()
            box.label(
                text=iface("no rig picked - skeleton ops will create a new Proscenio.QuickRig"),
                icon="INFO",
            )
            box.label(text=iface("Use existing instead:"))
            buttons = box.column(align=True)
            for arm in armatures:
                op = buttons.operator(
                    "proscenio.set_active_armature",
                    text=arm.name,
                    icon="ARMATURE_DATA",
                )
                op.armature_name = arm.name


class PROSCENIO_PT_armature(bpy.types.Panel):
    """Active Armature subpanel - the bone hierarchy of the picked armature."""

    bl_label = "Active Armature"
    bl_idname = "PROSCENIO_PT_armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 0
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        target = _explicit_target(context)
        return target is not None and bool(getattr(target.data, "bones", None))

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "armature", "armature")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        target = _explicit_target(context)
        scene_props = getattr(context.scene, "proscenio", None)
        if target is None or scene_props is None:
            return
        bones = getattr(target.data, "bones", [])
        # Whole-rig viewport draw style (Octahedral / Stick / B-Bone / Envelope
        # / Wire) - the native armature display_type, surfaced here so it is one
        # click from the panel while authoring.
        layout.prop(target.data, "display_type", text="Display As")
        # The armature name rides the Skeleton header; the body carries the bone
        # count plus the favorites-only filter toggle (mirrors the Outliner).
        header = layout.row(align=True)
        header.label(text=f"{len(bones)} bone(s)")
        fav_toggle = header.row()
        fav_toggle.alignment = "RIGHT"
        fav_toggle.prop(scene_props, "skeleton_show_favorites", text="Favorites", icon="SOLO_ON")
        layout.template_list(
            "PROSCENIO_UL_bones",
            "",
            target.data,
            "bones",
            scene_props,
            "active_bone_index",
            rows=min(max(len(bones), 3), 8),
        )
        # Convert-to-Euler is the one-click fix for the export validator's
        # driven-bone-not-XYZ warning: Drive-from-Bone reads rotation as XYZ.
        convert = layout.row(align=True)
        convert.operator(
            "proscenio.convert_rotation_to_euler", text="Active to Euler", icon="DRIVER"
        ).scope = "ACTIVE"
        convert.operator(
            "proscenio.convert_rotation_to_euler", text="All to Euler", icon="DRIVER"
        ).scope = "ALL"


class PROSCENIO_PT_rig_ui(bpy.types.Panel):
    """Rig UI subpanel - per-collection select buttons + visibility toggles.

    Reads the picked armature's native bone collections and honors their 4.1+
    nesting recursively (:func:`core.rig_ui_view.rig_ui_rows`): a collection with
    children prints its name as a header line, then a row whose buttons are its
    direct children side by side, and each child that itself has children recurses
    into its own header row below (depth-first, no indent - the header groups it).
    A top-level childless collection is a single-button row. Every row carries an
    eye bound to the collection's visibility and the theme selector's three
    columns (so they line up across rows), but only a top-level row's picker is
    live and colors that whole subtree - one color control per tree; nested rows
    reserve the columns with an empty dot and an inert picker. Selection +
    visibility only - assignment stays in Blender's native Bone Collections panel,
    which is also where the empty-state notice points when the armature has no
    collections yet.
    """

    bl_label = "Rig UI"
    bl_idname = "PROSCENIO_PT_rig_ui"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 1
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        # Show whenever a rig is picked; the no-collections case is an in-panel
        # notice (the project's empty-state convention), not a hidden panel.
        return _explicit_target(context) is not None

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "rig_ui", "rig_ui")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        target = _explicit_target(context)
        if target is None:
            return
        collections = getattr(getattr(target, "data", None), "collections", None)
        if not collections:
            layout.label(
                text=iface("no bone collections - add them in Blender's Bone Collections panel"),
                icon="INFO",
            )
            return
        for row in rig_ui_rows(collections):
            self._draw_row(layout, target, row)

    def _draw_row(
        self,
        layout: bpy.types.UILayout,
        armature: bpy.types.Object,
        view_row: RigUIRow,
    ) -> None:
        """Draw one :class:`RigUIRow`: optional header + eye | buttons | theme.

        ``view_row`` encodes the nesting (header label for a grouping collection,
        the select buttons, and the collection the eye / theme selector act on).
        The theme selector is drawn ONLY on a top-level row: a top-level color
        applies to the whole subtree below it, so there is exactly one color
        control per tree and the sub-collection rows stay eye + buttons. The eye
        and theme selector are pinned to a fixed width so the middle button(s)
        split the remaining width equally.
        """
        if view_row.header is not None:
            layout.label(text=view_row.header)
        row = layout.row(align=True)
        # 1. Eye - pinned width, bound to the row's collection visibility.
        eye = row.row(align=True)
        eye.ui_units_x = _RIG_UI_EYE_UNITS
        draw_eye(eye, resolve_collection(armature, view_row.collection_name))
        # 2. Middle - the remaining width; the select buttons split it equally.
        middle = row.row(align=True)
        for member_name in view_row.member_names:
            btn = middle.operator("proscenio.select_bone_collection", text=member_name)
            btn.armature_name = armature.name
            btn.collection_name = member_name
        # 3. Theme selector - drawn on EVERY row so the columns line up; the
        #    picker only acts on a top-level row (it colors the whole subtree),
        #    nested rows reserve the same space with an inert blank picker.
        draw_swatch(row, armature.name, view_row.collection_name, view_row.is_top_level)


class PROSCENIO_PT_pose_mode(bpy.types.Panel):
    """Pose Mode subpanel - pose-only authoring shortcuts."""

    bl_label = "Pose Mode"
    bl_idname = "PROSCENIO_PT_pose_mode"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 3
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "pose_mode", "pose_mode")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        if context.mode != "POSE":
            layout.label(text=iface("enter Pose mode to bake / save poses"), icon="INFO")
            return
        layout.operator("proscenio.bake_current_pose", text="Bake Current Pose", icon="KEY_HLT")
        _draw_ik_toggle(layout, context)
        layout.operator("proscenio.bake_ik_chain", text="Bake IK to Keyframes", icon="KEYFRAME_HLT")
        # When the active bone carries a Proscenio IK chain, surface the curated
        # constraint controls inline so the IK flow lives in Proscenio.
        constraint = _active_ik_constraint(context)
        if constraint is not None:
            _draw_ik_constraint_props(layout, context, constraint)
        # The subpanel header explains Pose Mode; the pose-library asset flow
        # (writable-library precheck, where the asset lands) has its own topic,
        # so the row carries its own ? - the orphan the #96 restructure left.
        pose_row = layout.row(align=True)
        pose_row.operator(
            "proscenio.save_pose_asset",
            text="Save Pose to Library",
            icon="ASSET_MANAGER",
        )
        draw_help_button(pose_row, "pose_library")


class PROSCENIO_PT_ik_chains(bpy.types.Panel):
    """IK chains subpanel - inventory of the picked armature's Proscenio IK chains.

    The marker on each bone row answers "is this bone part of a chain"; this
    section answers "what chains exist and what do they target", each row a
    click that selects the chain tip. Both read the same live constraint scan.
    """

    bl_label = "IK chains"
    bl_idname = "PROSCENIO_PT_ik_chains"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 4
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        target = _explicit_target(context)
        if target is None:
            return False
        return bool(scan_ik_chains(target).chains)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "pose_mode", "pose_mode")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        target = _explicit_target(context)
        if target is None:
            return
        chains = scan_ik_chains(target).chains
        if not chains:
            layout.label(text=iface("no IK chains - add one in Pose Mode"), icon="INFO")
            return
        for chain in chains:
            box = layout.box()
            tip_row = box.row(align=True)
            select = tip_row.operator(
                "proscenio.select_bone_by_name",
                text=chain.tip,
                icon="CON_KINEMATIC",
                emboss=False,
            )
            select.armature_name = target.name
            select.bone_name = chain.tip
            detail = tip_row.row()
            detail.alignment = "RIGHT"
            detail.label(text=f"chain {chain.chain_count}")
            control_text = chain.control if chain.control else "(no control)"
            box.label(text=f"control: {control_text}", icon="EMPTY_ARROWS")


class PROSCENIO_PT_quick_armature(bpy.types.Panel):
    """Quick Armature subpanel - the modal rig draw + its defaults.

    Always reachable, even with no armature in the scene, so the
    operator that creates a rig is never gated behind one already
    existing.
    """

    bl_label = "Quick Armature"
    bl_idname = "PROSCENIO_PT_quick_armature"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_skeleton"
    bl_order = 5
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "quick_armature", "quick_armature")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        _draw_quick_armature_shortcuts(layout)
        # While a session runs the button re-invokes as an exit request (the
        # operator turns a re-invoke into a "finish the running modal" signal).
        active = _quick_armature_is_running()
        layout.operator(
            "proscenio.quick_armature",
            text="Exit Quick Armature" if active else "Quick Armature",
            icon="X" if active else "GREASEPENCIL",
        )
        scene_props = getattr(context.scene, "proscenio", None)
        qa_props = getattr(scene_props, "quick_armature", None) if scene_props is not None else None
        if qa_props is None:
            return
        layout.prop(qa_props, "lock_to_front_ortho")
        layout.prop(qa_props, "default_chain")
        layout.prop(qa_props, "name_prefix")
        layout.prop(qa_props, "snap_increment")


def _quick_armature_is_running() -> bool:
    """True while a Quick Armature modal session is live."""
    from ..operators.armature.quick_armature import (  # type: ignore[import-not-found]
        PROSCENIO_OT_quick_armature as op,
    )

    return op.is_running()


def _draw_quick_armature_shortcuts(layout: bpy.types.UILayout) -> None:
    """Mirror the modal's status-bar cheatsheet on the panel while it runs.

    The Quick Armature modal already paints a gesture cheatsheet on the STATUSBAR
    and the 3D header (:func:`operators.armature._status_bar.emit_chord_layout`).
    The same call renders into any layout, so here it doubles onto the panel while
    the modal is active - the same pattern the automesh interactive subpanel uses
    for its modal indicator.

    Drawn in a native collapsible section (``layout.panel``), closed by default so
    it stays out of the way. Only drawn while the modal is running.
    """
    from ..operators.armature._status_bar import emit_chord_layout  # type: ignore[import-not-found]
    from ..operators.armature.quick_armature import (  # type: ignore[import-not-found]
        PROSCENIO_OT_quick_armature as op,
    )

    if not op.is_running():
        return
    header, body = layout.panel("proscenio_quick_armature_shortcuts", default_closed=True)
    header.label(text=iface("Shortcuts"), icon="GREASEPENCIL")
    if body is not None:
        emit_chord_layout(body, op)


_classes: tuple[type, ...] = (
    PROSCENIO_UL_bones,
    PROSCENIO_PT_skeleton,
    PROSCENIO_PT_armature,
    PROSCENIO_PT_rig_ui,
    PROSCENIO_PT_pose_mode,
    PROSCENIO_PT_ik_chains,
    PROSCENIO_PT_quick_armature,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
