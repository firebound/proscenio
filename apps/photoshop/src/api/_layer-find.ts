// Shared layer-tree walk: locates the live `PsLayer` reference for a
// name-path chain. UXP's layer collections are not always real Arrays
// (hence the `toArray` normalisation), and the name match must be exact
// raw equality - PS stores names in NFC, so a tag-stripped name needs
// byte-identical comparison.

import { type PsDocument, type PsLayer } from "photoshop";

import { log } from "../utils/log";

export function findLayerByPath(
    doc: PsDocument,
    layerPath: readonly string[],
): PsLayer | null {
    if (layerPath.length === 0) return null;
    let candidates: PsLayer[] = toArray(doc.layers);
    let target: PsLayer | null = null;
    for (let depth = 0; depth < layerPath.length; depth++) {
        const segment = layerPath[depth];
        if (segment === undefined) return null;
        let found: PsLayer | null = null;
        for (const layer of candidates) {
            if (layer.name === segment) { found = layer; break; }
        }
        if (found === null) {
            log.warn("layer-find", "no match at depth", depth, "seeking", segment);
            log.trace("layer-find", "miss detail", {
                seekingChars: charCodes(segment),
                liveAtDepth: candidates.map((l) => l.name),
            });
            return null;
        }
        target = found;
        // Only descend when more segments remain. Reading `.layers` on
        // the matched leaf is both wasteful and the prior crash trigger:
        // some UXP builds expose an art layer's `.layers` as `null`, and
        // `Array.from(null)` throws "object null is not iterable".
        if (depth < layerPath.length - 1) {
            candidates = toArray((found as { layers?: ArrayLike<PsLayer> | null }).layers);
        }
    }
    return target;
}

// Normalises a UXP layer collection to a real array. Guards `null` AND
// `undefined` (an art layer's `.layers` can be either across builds) and
// treats anything `Array.from` rejects as empty, so a non-iterable
// stand-in never crashes the walk with "object null is not iterable".
// Resolve a layer by its stable PS id, searching the whole tree. The id
// survives renames + reparenting, so this finds the right layer even when
// the cached name-path went stale (a group renamed between the tree build
// and the click) - the failure observed on `doll_tagged.psd` where a tag
// edit on a layer inside a renamed group missed by name.
export function findLayerById(doc: PsDocument, id: number): PsLayer | null {
    return searchById(toArray(doc.layers), id);
}

function searchById(layers: PsLayer[], id: number): PsLayer | null {
    for (const layer of layers) {
        if (readLayerId(layer) === id) return layer;
        const nested = toArray((layer as { layers?: ArrayLike<PsLayer> | null }).layers);
        const found = searchById(nested, id);
        if (found !== null) return found;
    }
    return null;
}

function readLayerId(layer: PsLayer): number | undefined {
    const id = (layer as { id?: unknown }).id;
    return typeof id === "number" ? id : undefined;
}

function toArray(value: ArrayLike<PsLayer> | null | undefined): PsLayer[] {
    if (value === undefined) return [];
    if (value === null) {
        // The exact spot of the prior "object null is not iterable" crash:
        // surface it at trace level so a debug session sees the host handed
        // back a null collection rather than just observing a silent miss.
        log.trace("layer-find", "normalized null .layers to []");
        return [];
    }
    try {
        return Array.from(value);
    } catch (err) {
        log.warn("layer-find", "non-iterable .layers; treating as empty", err);
        return [];
    }
}

function charCodes(s: string): number[] {
    const out: number[] = [];
    for (const ch of s) {
        const code = ch.codePointAt(0);
        if (code !== undefined) out.push(code);
    }
    return out;
}
