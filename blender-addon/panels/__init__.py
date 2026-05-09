"""Blender UI panels (SPEC 005).

The sidebar is anchored by `PROSCENIO_PT_main`. Every other panel is a
child via `bl_parent_id`, which gives us collapsible subsections users
can fold individually. Subpanels poll on the active selection (or scene
state) so empty subpanels do not clutter the sidebar.
"""

from typing import ClassVar

import bpy

from ..core import validation  # type: ignore[import-not-found]
from ..core.feature_status import badge_for, status_for  # type: ignore[import-not-found]


class PROSCENIO_PT_main(bpy.types.Panel):
    """Sidebar root — version banner; child panels do the work."""

    bl_label = "Proscenio"
    bl_idname = "PROSCENIO_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row()
        row.label(text="Pipeline v0.1.0")
        right = row.row()
        right.alignment = "RIGHT"
        op = right.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
        op.topic = "pipeline_overview"


_OBJECT_FRIENDLY_MODES = {"OBJECT", "EDIT_MESH", "PAINT_WEIGHT", "PAINT_VERTEX"}
_POSE_FRIENDLY_MODES = {"OBJECT", "POSE", "EDIT_ARMATURE"}
_HELP_OP_IDNAME = "proscenio.help"
_STATUS_OP_IDNAME = "proscenio.status_info"


def _draw_subpanel_header(
    layout: bpy.types.UILayout,
    feature_id: str,
    help_topic: str,
) -> None:
    """Append status icon + help button to a Proscenio subpanel foldout.

    Called from ``draw_header_preset`` (NOT ``draw_header``): Blender
    renders ``draw_header_preset`` content RIGHT of the auto-drawn
    ``bl_label``, which is what we want. ``draw_header`` would land
    BEFORE the title, sandwiching the icons between the foldout arrow
    and the title text.

    The status icon is wrapped in ``proscenio.status_info`` so hovering
    surfaces the band-specific tooltip (Blender does not honor custom
    tooltips on plain ``layout.label``). Clicking opens the status
    legend popup.
    """
    badge = badge_for(feature_id)
    status = status_for(feature_id)
    op = layout.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op.band = status.value
    op = layout.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = help_topic


def _draw_sprite_frame_readout(
    box: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Show atlas + region + frame size info for a sprite_frame mesh.

    Reads the active mesh's first image-textured material to surface atlas
    pixel dimensions; combines with the region override (or full atlas) +
    hframes/vframes to compute frame pixel size. Read-only — purely a
    discoverability helper so the user can verify their grid lines up.
    """
    atlas_size = _discover_atlas_size_for(obj)
    if atlas_size is None:
        box.label(text="atlas: not linked in material", icon="INFO")
        return
    aw, ah = atlas_size
    box.label(text=f"atlas: {aw}x{ah} px", icon="IMAGE_DATA")
    if props.region_mode == "manual":
        rw_px = max(1, round(props.region_w * aw))
        rh_px = max(1, round(props.region_h * ah))
        box.label(text=f"region: {rw_px}x{rh_px} px (manual)")
    else:
        rw_px, rh_px = aw, ah
        box.label(text=f"region: {rw_px}x{rh_px} px (full atlas)")
    hf = max(1, int(props.hframes))
    vf = max(1, int(props.vframes))
    fw = rw_px // hf
    fh = rh_px // vf
    box.label(text=f"frame: {fw}x{fh} px ({hf}x{vf} grid)")


def _draw_weight_paint_disabled_hint(layout: bpy.types.UILayout) -> None:
    """Show why weight paint controls are not surfaced for sprite_frame meshes.

    sprite_frame renders as a Sprite2D in Godot — no Polygon2D.skeleton, no
    per-vertex bone weights. Weight painting on this mesh has no effect on
    the exported scene; the panel reflects that to avoid silent confusion.
    """
    box = layout.box()
    box.label(
        text="weight paint not applicable to sprite_frame",
        icon="INFO",
    )
    box.label(text="(Sprite2D is not deformed by bones)")


def _discover_atlas_size_for(obj: bpy.types.Object) -> tuple[int, int] | None:
    """Walk the active mesh's materials and return the first image's pixel size."""
    mesh = obj.data
    materials = getattr(mesh, "materials", None) or []
    for mat in materials:
        size = _first_tex_image_size(mat)
        if size is not None:
            return size
    return None


def _first_tex_image_size(mat: bpy.types.Material | None) -> tuple[int, int] | None:
    if mat is None or not mat.use_nodes or mat.node_tree is None:
        return None
    for node in mat.node_tree.nodes:
        if node.type != "TEX_IMAGE" or node.image is None:
            continue
        w, h = node.image.size
        if w > 0 and h > 0:
            return (int(w), int(h))
    return None


def _draw_region_box(
    layout: bpy.types.UILayout,
    props: bpy.types.AnyType,
    *,
    sprite_type: str,
) -> None:
    """Render the texture_region authoring box (5.1.c.1).

    Auto mode shows a static "computed at export" hint; manual mode unlocks
    the four region floats + the Snap-to-UV-bounds operator. For sprite_frame,
    auto mode means the writer omits texture_region entirely (full atlas).
    """
    box = layout.box()
    box.label(text="Texture region", icon="UV_DATA")
    box.prop(props, "region_mode", text="")
    if props.region_mode == "manual":
        row = box.row(align=True)
        row.prop(props, "region_x")
        row.prop(props, "region_y")
        row = box.row(align=True)
        row.prop(props, "region_w")
        row.prop(props, "region_h")
        if sprite_type == "polygon":
            box.operator("proscenio.snap_region_to_uv", text="Snap to UV bounds", icon="UV")
    else:
        hint = (
            "computed from UV bounds at export"
            if sprite_type == "polygon"
            else "omitted at export — full atlas used"
        )
        box.label(text=hint, icon="INFO")


def _draw_active_sprite_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    """Pick the body subsection by sprite_type + active mode."""
    if props.sprite_type == "sprite_frame":
        _draw_sprite_frame_body(layout, context, obj, props)
    elif context.mode == "PAINT_WEIGHT":
        _draw_weight_paint_brush(layout, context)
    else:
        _draw_polygon_body(layout, obj, props)


def _draw_sprite_frame_body(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    box = layout.box()
    box.label(text="Sprite frame", icon="IMAGE_DATA")
    box.prop(props, "hframes")
    box.prop(props, "vframes")
    box.prop(props, "frame")
    box.prop(props, "centered")
    _draw_sprite_frame_readout(box, obj, props)
    _draw_preview_shader_buttons(box, obj)
    _draw_region_box(layout, props, sprite_type="sprite_frame")
    if context.mode == "PAINT_WEIGHT":
        _draw_weight_paint_disabled_hint(layout)


def _draw_preview_shader_buttons(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    """Render Material Preview slicer setup/remove buttons (SPEC 004 D13).

    Both buttons render side-by-side; only one is enabled at a time
    depending on whether the slicer node is currently linked into the
    active mesh's material.
    """
    has_slicer = _material_has_slicer(obj)
    row = layout.row(align=True)
    setup = row.row()
    setup.enabled = not has_slicer
    setup.operator(
        "proscenio.setup_sprite_frame_preview",
        text="Setup Preview",
        icon="SHADERFX",
    )
    remove = row.row()
    remove.enabled = has_slicer
    remove.operator(
        "proscenio.remove_sprite_frame_preview",
        text="Remove Preview",
        icon="X",
    )


def _material_has_slicer(obj: bpy.types.Object) -> bool:
    """True when any of the mesh's materials carries the SpriteFrameSlicer node."""
    from ..core.sprite_frame_shader import SLICER_GROUP_NAME  # type: ignore[import-not-found]

    materials = getattr(obj.data, "materials", None) or []
    for mat in materials:
        if mat is None or not getattr(mat, "use_nodes", False):
            continue
        nt = getattr(mat, "node_tree", None)
        if nt is None:
            continue
        for node in nt.nodes:
            if node.type == "GROUP" and getattr(node.node_tree, "name", "") == SLICER_GROUP_NAME:
                return True
    return False


def _draw_polygon_body(
    layout: bpy.types.UILayout,
    obj: bpy.types.Object,
    props: bpy.types.AnyType,
) -> None:
    mesh = obj.data
    vg_count = len(getattr(obj, "vertex_groups", []) or [])
    poly_count = len(getattr(mesh, "polygons", []) or [])
    box = layout.box()
    box.label(text="Polygon", icon="MESH_DATA")
    box.label(text=f"{poly_count} polygon(s), {vg_count} vertex group(s)")
    box.operator("proscenio.reproject_sprite_uv", text="Reproject UV", icon="UV")
    box.prop(props, "material_isolated")
    _draw_region_box(layout, props, sprite_type="polygon")


def _draw_weight_paint_brush(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Mirror Blender's weight-paint brush controls inline (5.1.b)."""
    box = layout.box()
    box.label(text="Weight paint", icon="BRUSH_DATA")
    tool_settings = context.tool_settings
    wp = getattr(tool_settings, "weight_paint", None)
    brush = getattr(wp, "brush", None) if wp is not None else None
    if brush is None:
        box.label(text="no active brush", icon="INFO")
        return
    ups = tool_settings.unified_paint_settings
    box.prop(ups, "use_unified_size", text="Unified size")
    box.prop(ups if ups.use_unified_size else brush, "size", slider=True)
    box.prop(ups, "use_unified_strength", text="Unified strength")
    box.prop(ups if ups.use_unified_strength else brush, "strength", slider=True)
    box.prop(ups if ups.use_unified_weight else brush, "weight", slider=True)
    box.prop(brush, "use_auto_normalize", text="Auto-normalize")


class PROSCENIO_PT_active_sprite(bpy.types.Panel):
    """Per-sprite settings — sprite type dropdown + sprite_frame metadata."""

    bl_label = "Active Sprite"
    bl_idname = "PROSCENIO_PT_active_sprite"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            return False
        return context.mode in _OBJECT_FRIENDLY_MODES

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "active_sprite", "active_sprite")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            return

        props = getattr(obj, "proscenio", None)
        if props is None:
            layout.label(text="proscenio property group not registered", icon="ERROR")
            return

        layout.prop(props, "sprite_type")
        _draw_active_sprite_body(layout, context, obj, props)
        _draw_driver_shortcut(layout, context, props)

        for issue in validation.validate_active_sprite(obj):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


def _draw_driver_shortcut(
    layout: bpy.types.UILayout,
    _context: bpy.types.Context,
    props: bpy.types.AnyType,
) -> None:
    """Render the 5.1.d.1 driver-shortcut box.

    Panel-side pickers replace the original "active object + selection"
    flow so the user does not need to switch between Object / Pose modes
    just to pick a source bone. The armature dropdown lists every
    ARMATURE in the file (poll filter); the bone field is a
    ``prop_search`` against the selected armature's bones.
    """
    box = layout.box()
    header = box.row(align=True)
    header.label(text="Drive from bone", icon="DRIVER")
    right = header.row()
    right.alignment = "RIGHT"
    badge = badge_for("drive_from_bone")
    status = status_for("drive_from_bone")
    op_status = right.operator(_STATUS_OP_IDNAME, text="", icon=badge.icon, emboss=False)
    op_status.band = status.value
    op = right.operator(_HELP_OP_IDNAME, text="", icon="QUESTION", emboss=False)
    op.topic = "drive_from_bone"
    box.prop(props, "driver_target", text="Target")
    box.prop(props, "driver_source_armature", text="Armature")
    box.prop(props, "driver_source_bone", text="Bone")
    box.prop(props, "driver_source_axis", text="Axis")
    box.prop(props, "driver_expression", text="Expression")
    row = box.row()
    armature = props.driver_source_armature
    has_bones = armature is not None and bool(getattr(armature.data, "bones", None))
    row.enabled = has_bones and bool(props.driver_source_bone)
    row.operator("proscenio.create_driver", text="Drive from Bone", icon="DRIVER")


class PROSCENIO_PT_active_slot(bpy.types.Panel):
    """Slot authoring -- visible when the active Empty is flagged as a slot (SPEC 004)."""

    bl_label = "Active Slot"
    bl_idname = "PROSCENIO_PT_active_slot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None or obj.type != "EMPTY":
            return False
        props = getattr(obj, "proscenio", None)
        if props is None:
            return False
        return bool(getattr(props, "is_slot", False))

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "slot_system", "slot_system")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        empty = context.active_object
        if empty is None:
            return
        props = empty.proscenio
        children = sorted(
            (c for c in empty.children if c.type == "MESH"),
            key=lambda c: c.name,
        )

        col = layout.column()
        col.label(text=f"Slot '{empty.name}'", icon="LINK_BLEND")
        col.label(
            text=f"bone: {empty.parent_bone or '(unparented)'}",
            icon="BONE_DATA",
        )

        layout.separator()
        layout.label(text=f"Attachments ({len(children)}):", icon="OUTLINER_OB_MESH")
        if not children:
            row = layout.row()
            row.alert = True
            row.label(text="empty slot -- add child meshes", icon="INFO")

        current_default = props.slot_default or (children[0].name if children else "")
        for child in children:
            row = layout.row(align=True)
            is_default = child.name == current_default
            icon = "SOLO_ON" if is_default else "SOLO_OFF"
            op = row.operator(
                "proscenio.set_slot_default",
                text="",
                icon=icon,
                emboss=is_default,
            )
            op.attachment_name = child.name
            row.label(text=child.name)
            kind = _attachment_kind_for(child)
            row.label(text=kind, icon=_attachment_icon_for(kind))

        layout.separator()
        row = layout.row()
        row.operator(
            "proscenio.add_slot_attachment",
            text="Add Selected Mesh",
            icon="ADD",
        )

        for issue in validation.validate_active_slot(empty):
            row = layout.row()
            icon = "ERROR" if issue.severity == "error" else "INFO"
            row.alert = issue.severity == "error"
            row.label(text=issue.message, icon=icon)


def _attachment_kind_for(mesh_obj: bpy.types.Object) -> str:
    """Read the kind ("polygon" / "sprite_frame") of a slot attachment mesh."""
    props = getattr(mesh_obj, "proscenio", None)
    if props is None:
        return "polygon"
    return str(getattr(props, "sprite_type", "polygon"))


def _attachment_icon_for(kind: str) -> str:
    return "MESH_DATA" if kind == "polygon" else "IMAGE_DATA"


class PROSCENIO_PT_skeleton(bpy.types.Panel):
    """Skeleton summary — bone count + presence checks."""

    bl_label = "Skeleton"
    bl_idname = "PROSCENIO_PT_skeleton"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.mode in _POSE_FRIENDLY_MODES

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "skeleton", "skeleton")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        if not armatures:
            row = layout.row()
            row.alert = True
            row.label(text="no Armature in scene", icon="ERROR")
            return
        first = armatures[0]
        bones = getattr(first.data, "bones", [])
        layout.label(text=f"Armature '{first.name}' — {len(bones)} bone(s)")
        if len(armatures) > 1:
            row = layout.row()
            row.alert = True
            row.label(
                text=f"{len(armatures)} armatures — writer uses the first only",
                icon="ERROR",
            )
        if bones:
            scene_props = getattr(context.scene, "proscenio", None)
            if scene_props is not None:
                layout.template_list(
                    "PROSCENIO_UL_bones",
                    "",
                    first.data,
                    "bones",
                    scene_props,
                    "active_bone_index",
                    rows=min(max(len(bones), 3), 8),
                )
        # Pose-mode-only helpers (5.1.a + 5.1.b + 5.1.d.2).
        if context.mode == "POSE":
            layout.separator()
            layout.operator("proscenio.bake_current_pose", text="Bake Current Pose", icon="KEY_HLT")
            layout.operator("proscenio.toggle_ik_chain", text="Toggle IK", icon="CON_KINEMATIC")
            layout.operator(
                "proscenio.save_pose_asset",
                text="Save Pose to Library",
                icon="ASSET_MANAGER",
            )
        # 5.1.d.3 quick armature -- modal viewport bone draw. Available in
        # any mode; the modal itself transitions the QuickRig in/out of
        # edit-mode per bone so the user does not have to.
        layout.separator()
        layout.operator("proscenio.quick_armature", text="Quick Armature", icon="GREASEPENCIL")
        # SPEC 004: slot creation -- works in any mode, anchors to active bone
        # when in pose mode, otherwise creates an unparented slot Empty.
        layout.operator("proscenio.create_slot", text="Create Slot", icon="LINK_BLEND")


class PROSCENIO_UL_bones(bpy.types.UIList):
    """List view for ``Armature.bones`` — Skeleton subpanel uses this."""

    bl_idname = "PROSCENIO_UL_bones"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        row = layout.row(align=True)
        row.label(text=item.name, icon="BONE_DATA")
        parent_name = item.parent.name if item.parent is not None else "—"
        row.label(text=f"parent: {parent_name}")
        row.label(text=f"len {item.length:.2f}")


class PROSCENIO_UL_actions(bpy.types.UIList):
    """List view for ``bpy.data.actions`` — Animation subpanel uses this."""

    bl_idname = "PROSCENIO_UL_actions"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        start, end = item.frame_range
        row = layout.row(align=True)
        row.label(text=item.name, icon="ACTION")
        row.label(text=f"[{start:.0f}-{end:.0f}]")


_OUTLINER_RANK_HIDDEN = 9


def _outliner_category_rank(obj: bpy.types.Object) -> int:
    """Rank the object for the outliner's sort-by-category pass.

    0 = slot Empty (top of the list, drives a slot).
    1 = slot attachment mesh (rendered indented under its slot).
    2 = sprite mesh (Proscenio polygon / sprite_frame, parented to bone or floating).
    3 = armature.
    9 = irrelevant for Proscenio (cameras, lights, etc.) -- hidden by ``filter_items``.
    """
    obj_props = getattr(obj, "proscenio", None)
    if obj.type == "EMPTY" and obj_props is not None and bool(getattr(obj_props, "is_slot", False)):
        return 0
    if obj.type == "ARMATURE":
        return 3
    if obj.type == "MESH":
        parent = obj.parent
        parent_props = getattr(parent, "proscenio", None) if parent is not None else None
        if (
            parent is not None
            and parent.type == "EMPTY"
            and parent_props is not None
            and bool(getattr(parent_props, "is_slot", False))
        ):
            return 1
        return 2
    return _OUTLINER_RANK_HIDDEN


class PROSCENIO_UL_sprite_outliner(bpy.types.UIList):
    """Sprite-centric outliner — slots, attachments, sprite meshes, armatures (5.1.d.4).

    Backs the Proscenio sidebar's outliner panel. Filters ``bpy.data.objects``
    down to Proscenio-relevant rows, sorts them by category (slots first,
    attachments indented under their slot, then sprite meshes, then
    armatures), and supports a substring text filter + a 'favorites only'
    toggle. Replaces / supplements Blender's native outliner for big rigs
    (doll fixture: 64 bones + 22 sprite meshes + N slots).
    """

    bl_idname = "PROSCENIO_UL_sprite_outliner"

    def draw_item(
        self,
        _context: bpy.types.Context,
        layout: bpy.types.UILayout,
        _data: bpy.types.AnyType,
        item: bpy.types.AnyType,
        _icon: int,
        _active_data: bpy.types.AnyType,
        _active_propname: str,
    ) -> None:
        obj = item
        obj_props = getattr(obj, "proscenio", None)
        is_fav = bool(obj_props is not None and getattr(obj_props, "is_outliner_favorite", False))
        rank = _outliner_category_rank(obj)
        if rank == 0:
            row_icon = "LINK_BLEND"
            label = f"[slot] {obj.name}"
        elif rank == 1:
            row_icon = "OBJECT_DATAMODE"
            label = f"  ↳ {obj.name}"
        elif rank == 2:
            row_icon = "MESH_DATA"
            parent_bone = obj.parent_bone if obj.parent and obj.parent_type == "BONE" else ""
            label = f"{obj.name}{' @ ' + parent_bone if parent_bone else ''}"
        elif rank == 3:
            row_icon = "ARMATURE_DATA"
            label = f"[arm] {obj.name}"
        else:
            row_icon = "OBJECT_DATA"
            label = obj.name
        row = layout.row(align=True)
        op = row.operator(
            "proscenio.select_outliner_object",
            text=label,
            icon=row_icon,
            emboss=False,
        )
        op.obj_name = obj.name
        fav = row.operator(
            "proscenio.toggle_outliner_favorite",
            text="",
            icon="SOLO_ON" if is_fav else "SOLO_OFF",
            emboss=False,
        )
        fav.obj_name = obj.name

    def filter_items(
        self,
        context: bpy.types.Context,
        data: bpy.types.AnyType,
        propname: str,
    ) -> tuple[list[int], list[int]]:
        """Hide non-Proscenio objects, apply text + favorites filter, sort by category."""
        objects = list(getattr(data, propname))
        scene_props = getattr(context.scene, "proscenio", None)
        flt_text = (getattr(scene_props, "outliner_filter", "") or "").lower()
        favorites_only = bool(
            scene_props is not None and getattr(scene_props, "outliner_show_favorites", False)
        )
        n = len(objects)
        flt_flags = [0] * n
        ranks: list[int] = [0] * n
        for i, obj in enumerate(objects):
            rank = _outliner_category_rank(obj)
            ranks[i] = rank
            if rank == _OUTLINER_RANK_HIDDEN:
                continue
            obj_props = getattr(obj, "proscenio", None)
            is_fav = bool(
                obj_props is not None and getattr(obj_props, "is_outliner_favorite", False)
            )
            if favorites_only and not is_fav:
                continue
            if flt_text and flt_text not in obj.name.lower():
                continue
            flt_flags[i] = self.bitflag_filter_item
        # Sort: rank ascending, name ascending. Slots float to the top, their
        # attachments come second so the indented children land right after.
        order = sorted(range(n), key=lambda i: (ranks[i], objects[i].name.lower()))
        flt_neworder = [0] * n
        for new_i, orig_i in enumerate(order):
            flt_neworder[orig_i] = new_i
        return flt_flags, flt_neworder


class PROSCENIO_PT_outliner(bpy.types.Panel):
    """Sprite-centric outliner — replaces Blender's outliner for big rigs (5.1.d.4)."""

    bl_label = "Outliner"
    bl_idname = "PROSCENIO_PT_outliner"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "outliner", "outliner")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="Proscenio scene props not registered", icon="ERROR")
            return
        row = layout.row(align=True)
        row.prop(scene_props, "outliner_filter", text="", icon="VIEWZOOM")
        row.prop(scene_props, "outliner_show_favorites", text="", icon="SOLO_ON")
        layout.template_list(
            "PROSCENIO_UL_sprite_outliner",
            "",
            bpy.data,
            "objects",
            scene_props,
            "active_outliner_index",
            rows=8,
        )


class PROSCENIO_PT_animation(bpy.types.Panel):
    """Read-only summary of the actions the writer would emit."""

    bl_label = "Animation"
    bl_idname = "PROSCENIO_PT_animation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "animation", "animation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        actions = bpy.data.actions
        if not actions:
            layout.label(text="no actions to export", icon="INFO")
            return
        layout.template_list(
            "PROSCENIO_UL_actions",
            "",
            bpy.data,
            "actions",
            context.scene.proscenio,
            "active_action_index",
            rows=min(max(len(actions), 2), 6),
        )
        layout.label(text=f"{len(actions)} action(s) total", icon="INFO")


class PROSCENIO_PT_atlas(bpy.types.Panel):
    """Read-only atlas filename discovered from materials."""

    bl_label = "Atlas"
    bl_idname = "PROSCENIO_PT_atlas"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "atlas", "atlas")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        atlas_name = _discover_atlas_name()
        if atlas_name is None:
            layout.label(text="no atlas linked in materials", icon="INFO")
        else:
            layout.label(text=atlas_name, icon="IMAGE")
        _draw_packer_box(layout, context)


def _draw_packer_box(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    """Atlas packer controls (5.1.c.2): config + pack + apply."""
    scene_props = getattr(context.scene, "proscenio", None)
    if scene_props is None:
        return
    box = layout.box()
    box.label(text="Atlas packer", icon="TEXTURE")
    col = box.column(align=True)
    col.prop(scene_props, "pack_padding_px")
    col.prop(scene_props, "pack_max_size")
    col.prop(scene_props, "pack_pot")
    box.separator()
    box.operator("proscenio.pack_atlas", text="Pack Atlas", icon="MOD_ARRAY")
    if _packed_manifest_exists():
        box.operator("proscenio.apply_packed_atlas", text="Apply Packed Atlas", icon="FILE_REFRESH")
    else:
        sub = box.row()
        sub.enabled = False
        sub.label(text="run Pack Atlas first", icon="INFO")
    if _scene_has_pre_pack_snapshot(context.scene):
        box.operator("proscenio.unpack_atlas", text="Unpack Atlas", icon="LOOP_BACK")


def _scene_has_pre_pack_snapshot(scene: bpy.types.Scene) -> bool:
    """True when at least one mesh carries a pre-pack snapshot (5.1.c.2.2)."""
    return any("proscenio_pre_pack" in obj for obj in scene.objects if obj.type == "MESH")


def _packed_manifest_exists() -> bool:
    """Check whether <blend>.atlas.json is sitting next to the active .blend."""
    blend = bpy.data.filepath
    if not blend:
        return False
    from pathlib import Path as _Path

    return (_Path(blend).parent / f"{_Path(blend).stem}.atlas.json").exists()


def _discover_atlas_name() -> str | None:
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                fp = node.image.filepath
                return (
                    str(bpy.path.abspath(fp)).split("\\")[-1].split("/")[-1]
                    if fp
                    else (f"{node.image.name} (unsaved)")
                )
    return None


class PROSCENIO_PT_validation(bpy.types.Panel):
    """Lazy validation results — populated by the Validate operator."""

    bl_label = "Validation"
    bl_idname = "PROSCENIO_PT_validation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "validation", "validation")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        if not scene_props.validation_ran:
            layout.label(text="run Validate to see issues", icon="INFO")
            return

        issues = list(scene_props.validation_results)
        if not issues:
            layout.label(text="no issues — ready to export", icon="CHECKMARK")
            return

        for issue in issues:
            row = layout.row(align=True)
            row.alert = issue.severity == "error"
            icon = "ERROR" if issue.severity == "error" else "INFO"
            if issue.obj_name:
                op = row.operator(
                    "proscenio.select_issue_object",
                    text=f"[{issue.obj_name}] {issue.message}",
                    icon=icon,
                    emboss=False,
                )
                op.obj_name = issue.obj_name
            else:
                row.label(text=issue.message, icon=icon)


class PROSCENIO_PT_export(bpy.types.Panel):
    """Export panel — sticky path, ppu, validate, export, re-export."""

    bl_label = "Export"
    bl_idname = "PROSCENIO_PT_export"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"

    def draw_header_preset(self, _context: bpy.types.Context) -> None:
        _draw_subpanel_header(self.layout, "export", "export")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is None:
            layout.label(text="proscenio scene props not registered", icon="ERROR")
            return

        layout.prop(scene_props, "last_export_path")
        layout.prop(scene_props, "pixels_per_unit")
        layout.operator(
            "proscenio.create_ortho_camera", text="Preview Camera", icon="OUTLINER_OB_CAMERA"
        )
        layout.separator()
        col = layout.column(align=True)
        col.operator("proscenio.validate_export", text="Validate", icon="CHECKMARK")
        col.operator("proscenio.export_godot", text="Export (.proscenio)", icon="EXPORT")
        if scene_props.last_export_path:
            col.operator("proscenio.reexport_godot", text="Re-export", icon="FILE_REFRESH")
        layout.separator()
        layout.operator(
            "proscenio.import_photoshop",
            text="Import Photoshop Manifest",
            icon="IMPORT",
        )


class PROSCENIO_PT_help(bpy.types.Panel):
    """Shortcut cheat-sheet — every Proscenio operator with its idname."""

    bl_label = "Help"
    bl_idname = "PROSCENIO_PT_help"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Operators (use F3 to search):", icon="QUESTION")
        for idname, label in _OPERATOR_REFERENCE:
            row = layout.row(align=True)
            row.label(text=label)
            row.label(text=idname)


_OPERATOR_REFERENCE: tuple[tuple[str, str], ...] = (
    ("proscenio.validate_export", "Validate"),
    ("proscenio.export_godot", "Export Proscenio (.proscenio)"),
    ("proscenio.reexport_godot", "Re-export"),
    ("proscenio.import_photoshop", "Import Photoshop Manifest"),
    ("proscenio.create_ortho_camera", "Preview Camera"),
    ("proscenio.bake_current_pose", "Bake Current Pose"),
    ("proscenio.toggle_ik_chain", "Toggle IK"),
    ("proscenio.quick_armature", "Quick Armature"),
    ("proscenio.reproject_sprite_uv", "Reproject UV"),
    ("proscenio.snap_region_to_uv", "Snap region to UV bounds"),
    ("proscenio.pack_atlas", "Pack Atlas"),
    ("proscenio.apply_packed_atlas", "Apply Packed Atlas"),
    ("proscenio.unpack_atlas", "Unpack Atlas"),
    ("proscenio.select_issue_object", "Select Issue Object"),
    ("proscenio.select_outliner_object", "Select Outliner Object"),
    ("proscenio.toggle_outliner_favorite", "Toggle Outliner Favorite"),
    ("proscenio.smoke_test", "Smoke test (Hello Proscenio)"),
)


class PROSCENIO_PT_diagnostics(bpy.types.Panel):
    """Smoke test + future addon-health buttons."""

    bl_label = "Diagnostics"
    bl_idname = "PROSCENIO_PT_diagnostics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_parent_id = "PROSCENIO_PT_main"
    bl_options: ClassVar[set[str]] = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator("proscenio.smoke_test", text="Run Smoke Test", icon="PLAY")


_classes: tuple[type, ...] = (
    PROSCENIO_UL_bones,
    PROSCENIO_UL_actions,
    PROSCENIO_UL_sprite_outliner,
    PROSCENIO_PT_main,
    PROSCENIO_PT_active_sprite,
    PROSCENIO_PT_active_slot,
    PROSCENIO_PT_skeleton,
    PROSCENIO_PT_outliner,
    PROSCENIO_PT_animation,
    PROSCENIO_PT_atlas,
    PROSCENIO_PT_validation,
    PROSCENIO_PT_export,
    PROSCENIO_PT_help,
    PROSCENIO_PT_diagnostics,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
