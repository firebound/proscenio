# Spec 057: Materials panel

Today a user inspecting or configuring materials hunts through the Shader Editor or Properties > Material per object. There is no Proscenio surface for cross-material inspection or bulk configuration, and the importer default of `HASHED` blend mode produces a dither stipple on semi-transparent pixels that pixel art wants as `CLIP`. This spec decides between a full materials panel and a low-effort pixel-art shortcut, then builds the chosen scope.

This spec is STUDY-first: spec 036 assessed a materials panel and dropped it, and the item was reopened by request, so the drop rationale (path-repair duplicates Blender's native "Find Missing Files", the rest is speculative surface) must be answered before building.

## Scope

- Decide the scope: a full inspection-and-configuration panel, or the low-effort alternative (a "Pixel art" checkbox on the active sprite that sets Closest interpolation and nearest filtering on the active material).
- If full panel: material inspection list (name, users, image-texture nodes, filepath); cross-material quick config (interpolation, blend mode, extension, alpha mode, alpha threshold, mipmaps / anisotropic) applicable to all / selection / regex; bulk image-path repair; a material report (unique, image-sharing, isolated).
- Regardless of scope, address the importer `HASHED` default versus `CLIP` for pixel art.

## Open questions (resolve before coding)

- Full panel versus the low-effort checkbox. The drop rationale from spec 036 argues the panel is mostly speculative and that path-repair duplicates a native tool. Does a real workflow need the full surface, or does the pixel-art shortcut plus the existing native tools cover it?
- The `HASHED` to `CLIP` default: is the current importer blend mode an outright bug to fix for everyone, or a setting the panel/checkbox should control?

## Sources

Drains the `materials-panel` spec-sized item in [`backlog.md`](../backlog.md). The `per-asset-ppu` and other atlas-config items stay in [`gated.md`](../gated.md) and are out of scope.
