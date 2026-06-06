// Active-document reads for the hooks layer. The panel never touches
// `app.activeDocument` directly: every read of the live PS document
// funnels through here so the PS boundary stays in `api/` and the
// hooks stay runtime-agnostic (testable against the adapted shape).
//
// Nothing here writes or schedules an export - reads only.

import { app } from "photoshop";

import { adaptDocument, type AdaptedDocument } from "./adapt-document";

export interface DocSnapshot {
    name: string;
    width: number;
    height: number;
}

/** Light document header (name + size). Returns `null` when no
 *  document is open. */
export function readDocSnapshot(): DocSnapshot | null {
    const d = app.activeDocument;
    if (d === null) return null;
    return { name: d.name, width: d.width, height: d.height };
}

/** Full adapted layer tree of the active document, ready for the pure
 *  tag-tree builder. Returns `null` when no document is open. */
export function readActiveLayerTree(): AdaptedDocument | null {
    const doc = app.activeDocument;
    if (doc === null) return null;
    return adaptDocument(doc);
}
