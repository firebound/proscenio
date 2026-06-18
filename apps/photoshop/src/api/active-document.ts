// Active-document reads for the hooks layer. Reads only - nothing here
// writes or schedules an export.

import { app } from "photoshop";
import type { PsDocument } from "photoshop";

import { adaptDocument, assembleAdapted, type AdaptedDocument } from "./adapt-document";
import { readLayersViaMultiGet } from "./multiget-read";

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

/** Adapts a document via the spec-048 multiGet fast path (one round trip),
 *  falling back to the synchronous DOM walk when the multiGet read fails or
 *  returns an unusable shape. The header + anchor are read synchronously
 *  either way. */
export async function adaptDocumentFast(doc: PsDocument): Promise<AdaptedDocument> {
    const layers = await readLayersViaMultiGet(doc);
    if (layers !== null) return assembleAdapted(doc, layers);
    return adaptDocument(doc);
}

/** Async sibling of `readActiveLayerTree` using the multiGet fast path.
 *  Returns `null` when no document is open. */
export async function readActiveLayerTreeAsync(): Promise<AdaptedDocument | null> {
    const doc = app.activeDocument;
    if (doc === null) return null;
    return adaptDocumentFast(doc);
}
