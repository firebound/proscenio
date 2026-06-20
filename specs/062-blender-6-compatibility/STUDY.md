# Spec 062: Blender 6 compatibility

Forward-compatibility for Blender 6.0 and later. The addon currently targets Blender 5.1.1, and nothing here is a bug on the supported version: a material can carry a populated `node_tree` with `use_nodes = False`, and the guards that read `use_nodes` before walking the tree are correct on 5.1. But `bpy.types.Material.use_nodes` is removed as a control in Blender 6.0, so a raw read raises there. The version-robust form `getattr(material, "use_nodes", True)` preserves the 5.1 behavior and survives a 6.0 removal. This spec sweeps the remaining raw reads to that form.

Scaffolded ahead of its STUDY. This is a small, objective sweep, but it is gated: it proceeds only when the support matrix actually adds Blender 6.0, or a 6.0 pre-release surfaces the broken access. Do not build on 5.1 alone.

## Scope

- Sweep the remaining raw `use_nodes` reads to the `getattr(material, "use_nodes", True)` form, matching the canonical `core/_shared/material_images.py` walk that already uses it.

## Trigger

The addon support matrix adds Blender 6.0, or a 6.0 pre-release surfaces the broken `material.use_nodes` access. Until then this stays parked.

## Sources

Drains [`backlog-blender-6.md`](../backlog-blender-6.md) and the `atlas-bare-use-nodes-blender6` item from [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md), which flags the same two atlas sites.
