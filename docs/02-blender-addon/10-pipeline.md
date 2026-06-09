# Pipeline

The import and export ends of the Blender stage. The body splits into Import and Export.

## Import

*Import Photoshop Manifest* reads a manifest from the Proscenio Photoshop plugin, stamps one mesh per layer (composing spritesheet textures for sprite_frame groups), and parents everything to a stub root armature. Re-importing the same manifest reuses existing meshes, so rotation, parenting, and weights survive the round trip.

## Export

*Export (.proscenio)* runs the writer, validates against the schema, and writes the JSON next to the `.blend`. The path is sticky, so *Re-export* skips the file dialog. **Pixels per unit** sets the Blender-world-to-Godot-pixel ratio (default 100). The generated scene uses native nodes only - no GDExtension, no plugin runtime dependency.
