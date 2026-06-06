// Reads the active document's marquee/lasso/region selection bounds
// for "Set origin from selection" in the Tags panel. PSD coords are
// top-left origin, Y increases down.

import { app } from "photoshop";
import type { PsUnitNumber } from "photoshop";

import { log } from "../util/log";

export interface SelectionCenter {
    x: number;
    y: number;
    bounds: { left: number; top: number; right: number; bottom: number };
}

export function readSelectionCenter(): SelectionCenter | null {
    try {
        const doc = app.activeDocument;
        if (doc === null) return null;
        const rawBounds = doc.selection?.bounds;
        if (rawBounds === undefined) return null;
        const left = numericValue(rawBounds.left);
        const top = numericValue(rawBounds.top);
        const right = numericValue(rawBounds.right);
        const bottom = numericValue(rawBounds.bottom);
        if (left === null || top === null || right === null || bottom === null) return null;
        if (right <= left || bottom <= top) return null;
        return {
            x: Math.round((left + right) / 2),
            y: Math.round((top + bottom) / 2),
            bounds: { left, top, right, bottom },
        };
    } catch (err) {
        log.warn("ps-selection-bounds", "readSelectionCenter threw", err);
        return null;
    }
}

function numericValue(v: number | PsUnitNumber | undefined): number | null {
    if (typeof v === "number" && Number.isFinite(v)) return v;
    if (typeof v === "object") {
        const inner = v.value ?? v._value;
        if (typeof inner === "number" && Number.isFinite(inner)) return inner;
    }
    return null;
}
