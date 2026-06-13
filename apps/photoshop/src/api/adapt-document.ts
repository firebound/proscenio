// Photoshop -> exporter Layer adapter. Read-only.
//
// Group detection uses the duck-typed shape (presence of a `.layers`
// array) rather than `layer.kind === constants.LayerKind.group`: the
// enum value differs across UXP / PS versions (numbers, strings, or
// swapped casing), while `.layers` is the universal LayerSet signal.

import { type PsDocument, type PsGuide, type PsLayer, type PsBounds } from "photoshop";

import type { DocumentInfo } from "../lib/planner";
import type { Layer, LayerBounds } from "../lib/layer";
import { log } from "../utils/log";

export interface AdaptedDocument {
    info: DocumentInfo;
    layers: Layer[];
    /** First horizontal + vertical PSD guide combined as [x, y] in
     *  document pixels. Undefined when fewer than two guides exist. */
    anchor?: [number, number];
}

export function adaptDocument(doc: PsDocument): AdaptedDocument {
    const rawLayers: unknown = doc.layers;
    if (!Array.isArray(rawLayers)) {
        // Diagnostic for the "object null is not iterable" class: the host
        // handed back a non-array layer collection. Hardened to [] below;
        // this line surfaces it under debug logging so a real session can
        // confirm the root cause instead of seeing a silent empty tree.
        log.warn("adapt-document", "doc.layers is not an array; treating as empty", {
            type: typeof rawLayers,
            value: rawLayers,
        });
    }
    const layers = toLayerArray(doc.layers).map(adaptLayer);
    log.trace("adapt-document", "adapted", layers.length, "top-level layer(s)");
    return {
        info: {
            name: doc.name,
            width: doc.width,
            height: doc.height,
        },
        layers,
        ...optionalAnchor(safeAnchor(doc)),
    };
}

// Normalises a UXP layer collection to a real array. A document's or a
// group's `.layers` can come back `null`, `undefined`, or a non-iterable
// stand-in across UXP builds; anything `Array.from` rejects is treated as
// empty so the walk never throws "object null is not iterable".
function toLayerArray(value: ArrayLike<PsLayer> | null | undefined): PsLayer[] {
    if (value === undefined || value === null) return [];
    try {
        return Array.from(value);
    } catch (err) {
        log.warn("adapt-document", "non-iterable .layers; treating as empty", err);
        return [];
    }
}

function safeAnchor(doc: PsDocument): [number, number] | undefined {
    try {
        return extractAnchor(doc.guides);
    } catch {
        // Some PS / UXP builds throw on `doc.guides` access instead of
        // returning undefined; treat any failure as "no anchor".
        return undefined;
    }
}

function optionalAnchor(anchor: [number, number] | undefined): { anchor?: [number, number] } {
    return anchor === undefined ? {} : { anchor };
}

function extractAnchor(guides: readonly PsGuide[] | null | undefined): [number, number] | undefined {
    if (guides === undefined || guides === null) return undefined;
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
            ...optionalId(readLayerId(layer)),
            layers: toLayerArray(layer.layers).map(adaptLayer),
        };
    }
    return {
        kind: "art",
        name: layer.name,
        visible: layer.visible,
        ...optionalId(readLayerId(layer)),
        bounds: toBounds(layer.bounds),
    };
}

function isGroup(layer: PsLayer): boolean {
    return Array.isArray(layer.layers);
}

// PS exposes a stable numeric `id` per layer, but defensively: some builds
// could omit it, so read it as unknown and only keep a real number.
function readLayerId(layer: PsLayer): number | undefined {
    const id = (layer as { id?: unknown }).id;
    return typeof id === "number" ? id : undefined;
}

function optionalId(id: number | undefined): { id?: number } {
    return id === undefined ? {} : { id };
}

function toBounds(raw: PsBounds | null | undefined): LayerBounds | null {
    if (raw === null || raw === undefined) return null;
    const w = raw.right - raw.left;
    const h = raw.bottom - raw.top;
    if (w <= 0 || h <= 0) return null;
    return { x: raw.left, y: raw.top, w, h };
}
