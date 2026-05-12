// Photoshop -> exporter Layer adapter.
//
// The pure planner (`src/domain/planner.ts`) consumes the
// runtime-agnostic `Layer` shape from `src/domain/layer.ts`. This
// module bridges the live Photoshop document into that shape so the
// planner can run identically against synthetic test data and a real
// PSD. Nothing in here touches the file system or schedules an
// export; it only reads.
//
// Group detection uses the duck-typed shape (presence of a `.layers`
// array) rather than `layer.kind === constants.LayerKind.group`. The
// enum value differs across UXP / PS versions (some return numbers,
// some return strings, some swap the casing); the `.layers` array is
// the universal signal that a layer is a LayerSet.

import { type PsDocument, type PsGuide, type PsLayer, type PsBounds } from "photoshop";

import type { DocumentInfo } from "../domain/planner";
import type { Layer, LayerBounds } from "../domain/layer";

export interface AdaptedDocument {
    info: DocumentInfo;
    layers: Layer[];
    /** First horizontal + vertical PSD guide combined as [x, y] in
     *  document pixels. Undefined when fewer than two guides exist. */
    anchor?: [number, number];
}

export function adaptDocument(doc: PsDocument): AdaptedDocument {
    return {
        info: {
            name: doc.name,
            width: doc.width,
            height: doc.height,
        },
        layers: doc.layers.map(adaptLayer),
        ...optionalAnchor(safeAnchor(doc)),
    };
}

function safeAnchor(doc: PsDocument): [number, number] | undefined {
    try {
        return extractAnchor(doc.guides);
    } catch {
        // Some PS / UXP builds throw on `doc.guides` access instead of
        // returning undefined. Treat any failure as "no anchor".
        return undefined;
    }
}

function optionalAnchor(anchor: [number, number] | undefined): { anchor?: [number, number] } {
    return anchor === undefined ? {} : { anchor };
}

function extractAnchor(guides: readonly PsGuide[] | undefined): [number, number] | undefined {
    if (guides === undefined) return undefined;
    let x: number | undefined;
    let y: number | undefined;
    for (const guide of guides) {
        if (guide.direction === "vertical" && x === undefined) x = guide.coordinate;
        else if (guide.direction === "horizontal" && y === undefined) y = guide.coordinate;
        if (x !== undefined && y !== undefined) break;
    }
    if (x === undefined || y === undefined) return undefined;
    return [Math.round(x), Math.round(y)];
}

export function adaptLayer(layer: PsLayer): Layer {
    if (isGroup(layer)) {
        return {
            kind: "set",
            name: layer.name,
            visible: layer.visible,
            layers: (layer.layers ?? []).map(adaptLayer),
        };
    }
    return {
        kind: "art",
        name: layer.name,
        visible: layer.visible,
        bounds: toBounds(layer.bounds),
    };
}

function isGroup(layer: PsLayer): boolean {
    return Array.isArray(layer.layers);
}

function toBounds(raw: PsBounds | null | undefined): LayerBounds | null {
    if (raw === null || raw === undefined) return null;
    const w = raw.right - raw.left;
    const h = raw.bottom - raw.top;
    if (w <= 0 || h <= 0) return null;
    return { x: raw.left, y: raw.top, w, h };
}
