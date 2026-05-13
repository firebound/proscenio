// Reads the active document's marquee/lasso/region selection bounds
// for "Set origin from selection" in the Tags panel. PSD coords are
// top-left origin, Y increases down.

import { app } from "photoshop";

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
        const selection = (doc as unknown as { selection?: { bounds?: unknown } }).selection;
        const rawBounds = selection?.bounds as
            | { left?: number; top?: number; right?: number; bottom?: number }
            | undefined;
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

function numericValue(v: unknown): number | null {
    if (typeof v === "number" && Number.isFinite(v)) return v;
    // UXP sometimes wraps coords in `UnitValue`-like objects; their
    // numeric value lives on a `_value` field, else stringify.
    if (typeof v === "object" && v !== null) {
        const wrapper = v as { _value?: unknown; value?: unknown };
        const inner = wrapper.value ?? wrapper._value;
        if (typeof inner === "number" && Number.isFinite(inner)) return inner;
    }
    return null;
}
