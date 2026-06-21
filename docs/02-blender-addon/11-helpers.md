# Helpers

Viewport authoring aids that set up Blender for 2D cutout work. None of them touch the `.proscenio`; they only change how the scene looks while you author it, so the whole panel is **blender-only**. It sits last in the sidebar and is collapsed by default. The panel currently holds a single tool, the Preview Camera.

**Preview Camera** creates an orthographic front camera framed the way the Godot importer expects, so what you see in the viewport matches the runtime framing. The camera is named `Proscenio.PreviewCam`: the first click adds it, looking down -Y at the Y=0 picture plane, and each later click re-focuses and re-sizes the existing one rather than spawning a second camera.

Its orthographic scale is derived from the scene, not guessed: the longer side of the render resolution divided by the scene's pixels-per-unit (the same ratio the [Export](10-pipeline.md#export) subpanel sets). That ties the camera's visible extent to the export conversion, so a figure that fills the frame here fills the frame in Godot. Re-running after you change the render resolution or pixels-per-unit updates the scale to match.

The operator makes the preview camera the scene camera and selects it. Press <kbd>Numpad 0</kbd> to look through it. It is undoable with <kbd>Ctrl+Z</kbd>.
