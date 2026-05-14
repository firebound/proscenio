// Shared layer-tree walk: locates the live `PsLayer` reference for a
// name-path chain produced by the planner / tag-tree. Used by every
// PS-side mutation (`layer-rename`, `legacy-migration`) so the walk
// has one implementation - matters because UXP's layer collections
// are not always real Arrays, and the wrapper-to-name match has
// edge cases (Adobe Clean uses NFC; tag-stripped names need exact
// raw equality).

import { type PsDocument, type PsLayer } from "photoshop";

import { log } from "../util/log";

export function findLayerByPath(
    doc: PsDocument,
    layerPath: readonly string[],
): PsLayer | null {
    if (layerPath.length === 0) return null;
    let candidates: PsLayer[] = toArray(doc.layers as ArrayLike<PsLayer> | undefined);
    let target: PsLayer | null = null;
    for (let depth = 0; depth < layerPath.length; depth++) {
        const segment = layerPath[depth];
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
        candidates = toArray((found as { layers?: ArrayLike<PsLayer> }).layers);
    }
    return target;
}

function toArray(value: ArrayLike<PsLayer> | undefined): PsLayer[] {
    if (value === undefined || value === null) return [];
    return Array.from(value);
}

function charCodes(s: string): number[] {
    const out: number[] = [];
    for (const ch of s) {
        const code = ch.codePointAt(0);
        if (code !== undefined) out.push(code);
    }
    return out;
}
