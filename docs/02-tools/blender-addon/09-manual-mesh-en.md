# Manual Mesh

Build a mesh element's silhouette by hand - you click the vertices instead of tracing the image alpha. It is the manual counterpart to [Mesh Generation](05-mesh-generation.md): a separate, mutually-exclusive way to make a mesh (one method per element), so the automesh trace fields do not apply here. This panel is **blender-only** and, like the other mesh panels, it is mesh-only - on a sprite element it warns and points you at bone-parenting (Ctrl+P > Bone) instead. It sits just below Mesh Generation in the sidebar and is collapsed by default.

**When to reach for it.** Use Manual Mesh when the alpha trace cannot find the shape you want - faint or anti-aliased edges, overlapping art, or a silhouette you simply want to place exactly. By default the result is the *simple* triangulation of the contour you draw; an **Interior mode** toggle on the panel switches it to a *dense* uniform fill (using the shared interior-spacing knob) when you want more deformable triangles.

**Drawing (two phases).** Click `Draw with vertices` to enter the modal; while it runs the button turns into `Exit Draw with vertices`, and a collapsible **Shortcuts** section mirrors the gesture cheatsheet from the status bar. You first **draw** the contour, then **close** it to **edit** it:

- **LMB** places a vertex; clicking the first vertex again closes the loop and enters the EDIT phase (it no longer applies immediately - press Enter to apply).
- **Wheel / 0-9** set the subdivision count for the edge being drawn - each edge keeps the count it was drawn with, so you can vary density around the contour.
- **X / Z** lock the next placement to an axis; a coloured guide line shows the locked direction.
- **RMB** drags a placed vertex (in either phase).
- **DEL** (or **Ctrl+Z**) drops the last vertex while drawing.

In the **EDIT phase** (after the loop closes) you refine the closed ring:

- **LMB on an edge** inserts a vertex there, splitting the edge (the two halves inherit its subdivision count).
- **Wheel / 0-9 over an edge** change that edge's subdivision count after the fact.
- **DEL** removes the vertex under the cursor (the ring keeps at least three).
- **Tab** cycles the active tool: **Outer contour** -> **Interior point** -> **Interior fold** (the current tool is shown in the status bar and the panel's Shortcuts header). The two interior tools add detail inside the silhouette, using the same point / fold inputs the interactive auto-gen consumes:
  - **Interior point** - an **LMB** click drops a single interior vertex.
  - **Interior fold** - an **LMB** drag free-draws a fold line, or successive **LMB** clicks build a fold edge-by-edge (a rubber band previews the next segment); **Wheel / 0-9** set the subdivision count baked into the next edge (the same per-edge density as the contour pen); **Enter** finishes the click-chain.
  - Placement is gated **inside the contour**: a gesture that would land outside is denied with a red cursor warning, and a click on the border snaps to the **outer contour** instead (inserting a contour vertex, whichever tool is active).
  - In both tools, **RMB** drags any vertex - interior or contour - and **Alt+LMB** deletes the interior stroke under the cursor (it highlights on hover); **DEL** / **Ctrl+Z** drops the last vertex or stroke. Re-opening the drawing reloads these strokes so you can revisit them.

A live triangulation previews the mesh the contour will build (in both Simple and Dense). **ENTER** builds the mesh on the selected element; **ESC** cancels (an in-progress open line clears first, then a second Esc exits).

**Continuing a drawing.** Manual Mesh remembers the contour you drew (and its interior strokes): re-open `Draw with vertices` on the same element and it loads straight into the EDIT phase so you can keep refining instead of starting over. To throw the mesh away and go back to the bare imported plane, use **Revert to Plane** on the [Element](02-element.md) panel (PSD-imported mesh elements only); it asks for confirmation first, because it destroys the generated mesh and its weight paint.

Manual Mesh is exclusive with the Automesh modes: while one authoring modal runs, the other's button is disabled, so a single element is never half-built two ways. The mesh it writes is an ordinary deformable cutout you weight-paint in the [Weight Paint](06-weight-paint.md) panel, exactly like an automesh result.
