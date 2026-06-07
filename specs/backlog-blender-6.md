# Blender 6+ compatibility backlog

Forward-compatibility concerns for Blender 6.0 and later, kept apart from the rolling [`backlog.md`](backlog.md) because they are gated on a future engine release rather than on product demand. The addon currently targets Blender 5.1.1; nothing here is a bug on the supported version. Each entry promotes into a fix (or a numbered spec) when the support matrix actually adds the affected Blender release.

## Material.use_nodes removal in node-tree guards

**What:** material node-tree guards read `material.use_nodes` before walking `material.node_tree.nodes`. Confirmed at `apps/blender/operators/automesh.py` `_find_tex_image` (and its still-duplicated twin in `automesh_authoring.py`); audit any other `use_nodes` reads when this is picked up. CodeRabbit (PR #87) reports that `bpy.types.Material.use_nodes` is removed as a control in Blender 6.0 (it was already non-functional before), so the read breaks on 6.0.

**Why:** on the targeted Blender 5.1.1 the guard is correct - a material can carry a populated `node_tree` with `use_nodes = False`, and the guard avoids reading a texture from an inactive tree. Dropping the guard outright (the literal CodeRabbit suggestion) regresses on 5.1 because it would then walk inactive node trees. The version-robust fix is `getattr(material, "use_nodes", True)`: it preserves the 5.1 behaviour and survives a 6.0 removal. Apply it at every `use_nodes` read, ideally folded into the deferred `_find_tex_image` de-duplication (the spec 016 automesh-operators phase).

**Trigger:** the addon support matrix adds Blender 6.0, or a 6.0 pre-release surfaces the broken `material.use_nodes` access.
