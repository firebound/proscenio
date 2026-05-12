// PSD-side placer: opens a per-layer PNG as a temporary doc, duplicates
// its single layer into the target document, translates so the
// top-left lands at the manifest-declared (x, y), then closes the
// source doc.
//
// Mirrors the JSX importer's `placeAndPosition`. All Photoshop work
// happens inside `core.executeAsModal` (the import flow wraps the
// whole batch in one modal, same posture as the export PNG writer).
//
// `targetX` / `targetY` are PSD pixels (top-left of the placed
// layer); `expectedW` / `expectedH` are the manifest-declared bbox
// size used only for a soft mismatch warning - we still place at the
// PNG's own bounds if they disagree.

import { app, constants, type PsDocument, type PsLayer } from "photoshop";
import type { UxpFile } from "uxp";

export interface PlaceResult {
    layer: PsLayer | null;
    warning?: string;
}

export async function placePngAt(
    targetDoc: PsDocument,
    pngFile: UxpFile,
    targetX: number,
    targetY: number,
    expectedW: number,
    expectedH: number,
): Promise<PlaceResult> {
    const srcDoc = await app.open(pngFile);
    let warning: string | undefined;
    try {
        const srcLayer = srcDoc.layers[0];
        if (srcLayer === undefined) {
            return { layer: null, warning: `PNG ${pngFile.name} has no layers` };
        }
        const b = srcLayer.bounds;
        const srcW = b.right - b.left;
        const srcH = b.bottom - b.top;
        if (Math.abs(srcW - expectedW) > 1 || Math.abs(srcH - expectedH) > 1) {
            warning = `${pngFile.name} bounds ${srcW}x${srcH} differ from manifest ${expectedW}x${expectedH}; using PNG bounds.`;
        }

        const duped = await srcLayer.duplicate(targetDoc);
        // PS translates by deltas, not absolute coords. After duplicate
        // the layer keeps its source bounds; offset so the new layer's
        // top-left lands at (targetX, targetY).
        const deltaX = targetX - b.left;
        const deltaY = targetY - b.top;
        if (deltaX !== 0 || deltaY !== 0) {
            await duped.translate(deltaX, deltaY);
        }
        return { layer: duped, warning };
    } finally {
        await srcDoc.closeWithoutSaving();
    }
}

// Move a freshly placed layer into a freshly created LayerSet (group).
export async function moveLayerIntoGroup(layer: PsLayer, group: PsLayer): Promise<void> {
    await layer.move(group, constants.ElementPlacement.PLACEATEND);
}
