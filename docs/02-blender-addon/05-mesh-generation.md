# Mesh Generation

Turn a sprite's alpha into a deformable cutout mesh you can weight-paint. The parent panel holds the Interior Mode selector (Simple = sparse, Dense = filled) and the picker readout.

## Automesh from Alpha

A one-shot trace: it walks the image alpha contour into an annulus mesh, and re-runs preserve the UV-pinned base quad. Key settings:

- **Trace resolution** - an image downscale factor. A *higher* value (1.0 = full image) traces a finer silhouette but costs more; it sets outline fidelity, not the vertex count (use **Contour vertices** for the outline and **Interior spacing** for the fill).
- **Density follows bones** (Dense only, off by default) - packs more triangles near the picker's bones, where the deformation happens.

## Automesh Interactive

A modal preview of the same trace. Advance through the stages to cut / extend the outline and place interior points, then commit; nothing is written until you confirm the final stage.

## Debug Pipeline

A developer aid, shown only with debug mode on (Preferences > Add-ons > Proscenio). Pick a stage of the trace and the next run leaves a wireframe companion in the `Proscenio.Debug` collection; *Clear Debug Companions* removes them.
