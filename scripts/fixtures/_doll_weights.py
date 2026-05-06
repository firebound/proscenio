"""Doll weight assignment — wires sprite meshes to armature bones (SPEC 007).

Most sprites are weighted 1.0 to a single bone (the parent). Two sprites
demonstrate **multi-bone weights** for the SPEC 003 export path:

- ``pelvis_block`` — split 0.5 / 0.5 across ``pelvis.L`` and ``pelvis.R``.
- ``spine_block`` — distributed across ``spine``, ``spine.001``,
  ``spine.002``, ``spine.003`` with falloff (0.4 / 0.4 / 0.15 / 0.05).

Two sprites also get a 0.3 spillover to a sibling bone to cover the
multi-influence path:

- ``forearm.L`` weighted 1.0 on ``forearm.L`` + 0.3 on ``upper_arm.L``.
- ``forearm.R`` mirror.
"""

from __future__ import annotations

import bpy

# Map sprite name → list of (vertex_group_name, weight).
WEIGHT_MAP: dict[str, list[tuple[str, float]]] = {
    "pelvis_block": [("pelvis.L", 0.5), ("pelvis.R", 0.5)],
    "spine_block": [
        ("spine", 0.4),
        ("spine.001", 0.4),
        ("spine.002", 0.15),
        ("spine.003", 0.05),
    ],
    "forearm.L": [("forearm.L", 1.0), ("upper_arm.L", 0.3)],
    "forearm.R": [("forearm.R", 1.0), ("upper_arm.R", 0.3)],
}


def apply(
    sprite_objs: dict[str, bpy.types.Object], armature_obj: bpy.types.Object
) -> None:
    """For each sprite, add an Armature modifier + vertex groups + weights.

    Sprites in ``WEIGHT_MAP`` get the bespoke distribution. All others
    get a single 1.0 weight on the bone they are parented to.
    """
    for name, obj in sprite_objs.items():
        modifier = obj.modifiers.new(name="Armature", type="ARMATURE")
        modifier.object = armature_obj

        bespoke = WEIGHT_MAP.get(name)
        all_indices = list(range(len(obj.data.vertices)))
        if bespoke is not None:
            for bone_name, weight in bespoke:
                vg = obj.vertex_groups.new(name=bone_name)
                vg.add(all_indices, weight, "REPLACE")
        else:
            parent_bone = obj.parent_bone
            if parent_bone:
                vg = obj.vertex_groups.new(name=parent_bone)
                vg.add(all_indices, 1.0, "REPLACE")
