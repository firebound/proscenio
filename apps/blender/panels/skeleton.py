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
    collection_theme_label,
)
from ..core.bpy_helpers._shared.bone_select import (  # type: ignore[import-not-found]
    BONE_SELECT_MODES,
    bone_is_selected,
)
from ..core.bpy_helpers.armature import (  # type: ignore[import-not-found]
    IkChainScan,
    scan_ik_chains,
)
from ..core.list_view import compute_list_filter  # type: ignore[import-not-found]
from ._helpers import _POSE_FRIENDLY_MODES, draw_help_button, draw_subpanel_header
from ._list import ProscenioListMixin, draw_select_marker

# Constraint that marks a Proscenio-owned IK chain; the name is the single
# source the panel reads (a renamed .IK control suffix must not change the cue).
_IK_CONSTRAINT_NAME = "Proscenio IK"


def _explicit_target(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the scene's picked Active Armature object, or None."""
    scene_props = getattr(context.scene, "proscenio", None)
    return scene_props.active_armature if scene_props is not None else None


def _theme_bone_color_set(theme_label: str) -> bpy.types.ThemeBoneColorSet | None:
    """The theme's bone color set for a ``"1"``..``"15"`` theme label, or None.

    ``THEME0N`` maps to ``bone_color_sets[N - 1]`` on the active theme; the set's
    ``normal`` color is what the Rig UI swatch draws as a fixed colored dot. Any
    gap - empty label, no themes, out-of-range - is a clean None.
    """
    if not theme_label:
        return None
    try:
        idx = int(theme_label) - 1
    except ValueError:
        return None
    themes = getattr(bpy.context.preferences, "themes", None)
    sets = themes[0].bone_color_sets if themes else None
    if sets is None or not (0 <= idx < len(sets)):
        return None
    return sets[idx]


# Rig UI rows are three parts: a fixed eye, a flexible middle that the select
# button(s) split equally, and a fixed theme selector. The eye and the theme
# selector are built only from non-stretching widgets (an icon-only toggle /
# button and a label) each pinned to a UI-unit width, so they stay the same size
# on every row and the middle's text buttons absorb all the extra width.
# Deliberately NO color field in the selector: a color field (and a text button)
# stretches and grabs the row's spare width on a wide panel - ui_units_x only
# sets a minimum - so the theme number is a label and the picker an icon-only
# button. All GUI-tunable.
_RIG_UI_EYE_UNITS = 1.4
_RIG_UI_DOT_UNITS = 0.9
_RIG_UI_NUM_UNITS = 1.2


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
        op = name_row.operator(
            "proscenio.select_bone_by_name",
            text=("  " * depth) + item.name,
            icon="BONE_DATA",
            emboss=False,
        )
        op.armature_name = arm_name
        op.bone_name = item.name
        right = split.row(align=True)
        right.alignment = "RIGHT"
        self._draw_bone_flags(right, item, arm_name)

    @staticmethod
    def _draw_bone_flags(row: bpy.types.UILayout, item: bpy.types.Bone, arm_name: str) -> None:
        """Draw the right-side connectivity icon, relative toggle, and favorite star.

        Connectivity is a hover-tooltip info icon (a no-op operator - a
        ``layout.label`` carries no tooltip): ``LINKED`` when connected,
        ``UNLINKED`` for a disconnected child, nothing for a root. Relative
        parenting is a live ``CON_CHILDOF`` toggle (only meaningful with a
        parent). The export toggle pins a rig helper off the Godot export. The
        favorite star pins the bone in the list.
        """
        if getattr(item, "use_connect", False):
            info = row.operator("proscenio.bone_flag_info", text="", icon="LINKED", emboss=False)
            info.flag = "connected"
        elif item.parent is not None:
            info = row.operator("proscenio.bone_flag_info", text="", icon="UNLINKED", emboss=False)
            info.flag = "disconnected"
        if item.parent is not None:
            rel = row.operator(
                "proscenio.toggle_bone_relative_parent",
                text="",
                icon="CON_CHILDOF",
                emboss=False,
                depress=bool(getattr(item, "use_relative_parent", False)),
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
            self.layout.label(text="Skeleton")

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
            row.label(text="no Armature in scene - use Quick Armature below", icon="INFO")
        elif explicit_target is None:
            box = layout.box()
            box.label(
                text="no rig picked - skeleton ops will create a new Proscenio.QuickRig",
                icon="INFO",
            )
            box.label(text="Use existing instead:")
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
    nesting: a top-level collection with children renders as a labelled row of
    per-child select buttons (the Rigify-style "Arm.L: IK | FK | Tweak"
    grouping); a childless collection renders as a single-button row. Each row
    carries an eye bound to the collection's visibility and a swatch that
    colors the whole collection. Selection + visibility only - assignment stays
    in Blender's native Bone Collections panel.
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
        target = _explicit_target(context)
        collections = getattr(getattr(target, "data", None), "collections", None)
        return bool(collections)

    def draw_header_preset(self, context: bpy.types.Context) -> None:
        draw_subpanel_header(self.layout, context, "rig_ui", "rig_ui")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        target = _explicit_target(context)
        if target is None:
            return
        for collection in getattr(target.data, "collections", []):
            self._draw_collection_row(layout, target.name, collection)

    def _draw_collection_row(
        self,
        layout: bpy.types.UILayout,
        arm_name: str,
        collection: bpy.types.BoneCollection,
    ) -> None:
        """Draw one collection row: eye + select button(s) | color swatch.

        A parent collection prints its name as a header line, then a row whose
        buttons are its child collections side by side; a childless collection is
        a single full-width button. Either way the row is a single ``split`` at a
        fixed factor - eye + buttons in the left cell, swatch in the right - so
        the swatch column lines up on every row regardless of the button count,
        and the split caps the swatch cell so a color field cannot expand it.
        """
        children = list(getattr(collection, "children", []))
        if children:
            layout.label(text=collection.name)
        row = layout.row(align=True)
        # Three parts: fixed eye | flexible middle | fixed theme selector.
        # 1. Eye - pinned width, independent of the rest.
        eye = row.row(align=True)
        eye.ui_units_x = _RIG_UI_EYE_UNITS
        self._draw_eye(eye, collection)
        # 2. Middle - takes the remaining width; the collection / subcollection
        #    select buttons split it equally (three children -> three thirds).
        middle = row.row(align=True)
        for member in children or [collection]:
            btn = middle.operator("proscenio.select_bone_collection", text=member.name)
            btn.armature_name = arm_name
            btn.collection_name = member.name
        # 3. Theme selector - pinned width (a parent colors its whole subtree).
        self._draw_swatch(row, arm_name, collection)

    @staticmethod
    def _draw_eye(row: bpy.types.UILayout, collection: bpy.types.BoneCollection) -> None:
        row.prop(
            collection,
            "is_visible",
            text="",
            icon="HIDE_OFF" if collection.is_visible else "HIDE_ON",
            toggle=True,
        )

    @staticmethod
    def _draw_swatch(
        layout: bpy.types.UILayout,
        arm_name: str,
        collection: bpy.types.BoneCollection,
    ) -> None:
        """Draw the fixed-width theme selector (the row's third part).

        Three non-stretching, UI-unit-pinned slots so the selector is the same
        size on every row and never grabs the middle's spare width:

        - a dot slot: the theme color as a fixed-size ``template_node_socket``
          circle (NOT a ``prop`` color field - that one widget stretches and
          expands the whole selector, the bug that kept the red bar growing);
          blank when the collection's bones do not share one ``THEME##`` slot;
        - a number slot: a label with the theme number (blank when no theme) -
          a label, not button text, which would stretch;
        - the picker: an icon-only operator (the only clickable part) - a color
          icon when themed, a dim empty circle when not. Clicking opens the
          palette dialog (a parent colors its whole subtree).
        """
        armature = bpy.data.objects.get(arm_name)
        label = collection_theme_label(armature, collection.name) if armature else ""
        color_set = _theme_bone_color_set(label)
        theme = layout.row(align=True)
        # Dot slot: the theme color as a fixed-size template_node_socket circle
        # when themed; otherwise just an invisible spacer (a non-breaking-space
        # label) that reserves the same width WITHOUT drawing a second circle -
        # an empty "" label would collapse and misalign the row, and a
        # transparent socket still draws its outline (the redundant extra icon).
        dot = theme.row(align=True)
        dot.ui_units_x = _RIG_UI_DOT_UNITS
        if color_set is not None and hasattr(dot, "template_node_socket"):
            dot.template_node_socket(color=(*tuple(color_set.normal), 1.0))
        else:
            dot.label(text="\u00a0")
        # Number slot: a non-breaking space when there is no number, NOT "" -
        # an empty label collapses (ui_units_x is only a minimum and is ignored
        # for empty content), which is what made the no-theme rows narrower.
        num = theme.row(align=True)
        num.ui_units_x = _RIG_UI_NUM_UNITS
        num.alignment = "RIGHT"
        num.label(text=label or "\u00a0")
        # One picker icon for every row (the "color" affordance), themed or not.
        op = theme.operator("proscenio.color_bone_collection", text="", icon="COLOR")
        op.armature_name = arm_name
        op.collection_name = collection.name


def _active_ik_constraint(context: bpy.types.Context) -> bpy.types.Constraint | None:
    """The active pose bone's ``Proscenio IK`` constraint, or None."""
    bone = getattr(context, "active_pose_bone", None)
    if bone is None:
        return None
    return bone.constraints.get(_IK_CONSTRAINT_NAME)


def _draw_ik_toggle(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Draw the create / remove IK button with an honest, state-resolved label.

    One operator (``proscenio.toggle_ik_chain``) does both create and destroy;
    the label reads "Add IK Chain" when the active bone has no Proscenio IK and
    "Remove IK Chain" when it does, so the button names the action it performs.
    """
    has_chain = _active_ik_constraint(context) is not None
    text = "Remove IK Chain" if has_chain else "Add IK Chain"
    icon = "X" if has_chain else "CON_KINEMATIC"
    layout.operator("proscenio.toggle_ik_chain", text=text, icon=icon)


def _draw_ik_constraint_props(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    constraint: bpy.types.Constraint,
) -> None:
    """Draw the curated IK constraint controls for the active chain.

    The trio the IK flow needs - chain length, keyframable influence (the
    IK/FK-blend seed, with an explicit insert-key button), pole target - plus an
    opt-in "lock chain in-plane" toggle that gives the otherwise-hidden
    ``lock_ik_*`` flags a visible owner. Deliberately not the full native
    KinematicConstraint UI (no stretch / iterations / weight): the export bakes
    the chain, so those are native-UI territory.
    """
    box = layout.box()
    box.label(text="Proscenio IK", icon="CON_KINEMATIC")
    box.prop(constraint, "chain_count", text="Chain length")

    influence_row = box.row(align=True)
    influence_row.prop(constraint, "influence", text="Influence", slider=True)
    # Explicit insert-key affordance for the IK/FK-blend seed (the prop already
    # honors keying; this is the one-click button on the chain's tip bone).
    influence_row.operator("proscenio.key_ik_influence", text="", icon="KEYFRAME_HLT")

    box.prop(constraint, "pole_target", text="Pole target")
    if constraint.pole_target is not None and constraint.pole_target.type == "ARMATURE":
        box.prop_search(
            constraint,
            "pole_subtarget",
            constraint.pole_target.data,
            "bones",
            text="Pole bone",
        )

    _draw_ik_inplane_lock(box, context, constraint)


def _draw_ik_inplane_lock(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    constraint: bpy.types.Constraint,
) -> None:
    """Opt-in "lock chain in-plane" toggle for the active chain's tip bone.

    Locks the chain's out-of-plane rotation DOFs on the constrained bone so the
    solve stays in the 2D picture plane. Off by default and clearly labelled,
    because loose ``lock_ik_*`` flags are hidden bone state that otherwise read
    as "the bone will not rotate" with no explanation.
    """
    bone = getattr(context, "active_pose_bone", None)
    if bone is None or constraint.name != _IK_CONSTRAINT_NAME:
        return
    locked = bool(bone.lock_ik_x and bone.lock_ik_z)
    op = layout.operator(
        "proscenio.toggle_ik_inplane_lock",
        text="Unlock chain in-plane" if locked else "Lock chain in-plane",
        icon="LOCKED" if locked else "UNLOCKED",
    )
    op.bone_name = bone.name


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
            layout.label(text="enter Pose mode to bake / save poses", icon="INFO")
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
            layout.label(text="no IK chains - add one in Pose Mode", icon="INFO")
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
        layout.operator("proscenio.quick_armature", text="Quick Armature", icon="GREASEPENCIL")
        scene_props = getattr(context.scene, "proscenio", None)
        qa_props = getattr(scene_props, "quick_armature", None) if scene_props is not None else None
        if qa_props is None:
            return
        layout.prop(qa_props, "lock_to_front_ortho")
        layout.prop(qa_props, "default_chain")
        layout.prop(qa_props, "name_prefix")
        layout.prop(qa_props, "snap_increment")


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
