# Spec 057: Materials panel - TODO

Candidate work, pending the scope call in the STUDY. The two branches are mutually exclusive; the pixel-art default fix is shared.

## Shared (either scope)

- [ ] Resolve the importer blend-mode default: pixel art wants `CLIP`, the importer sets `HASHED` (dither stipple on semi-transparent pixels). Fix the default for everyone, or make it the first thing the chosen surface controls.

## Branch A - low-effort shortcut (if chosen)

- [ ] Add a "Pixel art" checkbox on the active sprite that sets Closest interpolation and nearest filtering on the active material.

## Branch B - full materials panel (if chosen)

- [ ] Material inspection list: name, users, image-texture nodes, filepath.
- [ ] Cross-material quick config applicable to all / selection / regex: interpolation (Closest / Linear / Cubic / Smart), blend mode (Opaque / Clip / Hashed / Blend), extension, alpha mode, alpha threshold, mipmaps, anisotropic.
- [ ] Bulk image-path repair with a file picker.
- [ ] Material report: unique materials, materials sharing an image, `material_isolated=True`.
