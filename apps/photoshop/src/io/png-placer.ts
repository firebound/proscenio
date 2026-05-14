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
    let duped: PsLayer;
    let deltaX = 0;
    let deltaY = 0;
    try {
        const srcLayer = srcDoc.layers[0];
        if (srcLayer === undefined) {
            return { layer: null, warning: `PNG ${pngFile.name} has no layers` };
        }
        // UXP returns `bounds` either as plain numbers or as
        // UnitValue-like wrappers ({ _value: N }). The arithmetic
        // below silently yields NaN if a wrapper sneaks through, so
        // every bound is normalised through `unwrap` first - matches
        // the pattern in ps-selection-bounds.ts.
        const left = unwrap(srcLayer.bounds.left);
        const top = unwrap(srcLayer.bounds.top);
        const right = unwrap(srcLayer.bounds.right);
        const bottom = unwrap(srcLayer.bounds.bottom);
        if (left === null || top === null || right === null || bottom === null) {
            return {
                layer: null,
                warning: `${pngFile.name} bounds unreadable; layer skipped`,
            };
        }
        const srcW = right - left;
        const srcH = bottom - top;
        if (Math.abs(srcW - expectedW) > 1 || Math.abs(srcH - expectedH) > 1) {
            warning = `${pngFile.name} bounds ${srcW}x${srcH} differ from manifest ${expectedW}x${expectedH}; using PNG bounds.`;
        }
        duped = await srcLayer.duplicate(targetDoc);
        deltaX = targetX - left;
        deltaY = targetY - top;
    } finally {
        // Close the source PSD BEFORE translating the duped layer so the
        // target document is the active one when `Layer.translate` fires.
        // PS / UXP route translate through the active doc's selection
        // context; with srcDoc still active the call no-ops silently
        // (observed on PS 25 / 2026 during the SPEC 011 round-trip).
        await srcDoc.closeWithoutSaving();
    }
    // Active doc is now targetDoc; safe to translate. `translate` accepts
    // raw pixel deltas per UXP docs.
    if (deltaX !== 0 || deltaY !== 0) {
        await duped.translate(deltaX, deltaY);
    }
    return { layer: duped, warning };
}

function unwrap(v: unknown): number | null {
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "object" && v !== null) {
        const wrapper = v as { _value?: unknown; value?: unknown };
        const inner = wrapper.value ?? wrapper._value;
        if (typeof inner === "number" && Number.isFinite(inner)) return inner;
    }
    return null;
}

// Move a freshly placed layer into a freshly created LayerSet (group).
export async function moveLayerIntoGroup(layer: PsLayer, group: PsLayer): Promise<void> {
    await layer.move(group, constants.ElementPlacement.PLACEATEND);
}
