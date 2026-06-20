# Mesh Generation

Turn a sprite's alpha into a deformable cutout mesh you can weight-paint. The panel is mesh-only - on a sprite element it warns and points you at bone-parenting (Ctrl+P > Bone) instead. It shows the target rig (picked in the [Skeleton](04-skeleton.md) panel) and hosts the trace parameters both entry points share: the Interior Mode selector (Simple = sparse, Dense = filled), **Contour vertices** (the outline budget), and **Interior spacing** (the fill spacing, also the free-draw resample and fold-snap radius in the interactive modal). The dense-only fields - **Density follows bones** and its bone radius / factor - grey out under Simple mode.

## Automesh from Alpha

A one-shot trace that walks the image alpha contour into a mesh; re-runs preserve the UV-pinned base quad. Its own settings (the rest live on the parent panel above):

- **Trace resolution** - an image downscale factor. A *higher* value (1.0 = full image) traces a finer silhouette but costs more; it sets outline fidelity, not the vertex count.
- **Alpha threshold** and **Margin pixels** - the alpha cutoff for the contour and how far to inset or outset it.
- **Preserve base quad** - keep the UV-pinned base quad across re-runs.
- **Preserve weights on regen** - snapshot weights by UV before the regen and reproject them onto the new mesh; off, the regen wipes paint. Surfaced here because this button triggers the regen (the same toggle lives in the [Weight Paint](06-weight-paint.md#snapshot) Snapshot subpanel).

## Automesh Interactive

A modal preview of the same trace. Advance through the stages to cut / extend the outline and place interior points, then commit; nothing is written until you confirm the final stage. Its inputs are the inner-loop count and spacing, the cut margin, and the same `Preserve weights on regen` toggle. The button greys out until the active object is a mesh with an image texture.

## Debug Pipeline

A developer aid, shown only with debug mode on (Preferences > Add-ons > Proscenio). Pick a stage of the trace and the next run leaves a wireframe companion in the `Proscenio.Debug` collection; `Clear Debug Companions` removes them.
