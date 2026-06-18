// spec 048 fast read path: one `action.batchPlay` multiGet over the whole
// layer stack, rebuilt into the nested Layer[] tree in JS - replacing the
// per-property synchronous DOM walk in adapt-document.ts.
//
// The descriptor shape (property keys, the `layerSection` enum envelope,
// `count: -1`) was confirmed against a real PSD via the read probe: one
// round trip instead of one IPC call per property per layer. The pure
// flat-to-tree fold lives in lib/layer-descriptor.ts (unit-tested); this
// module is the thin host-call adapter around it.
//
// Contract: returns null on ANY failure (no doc id, batchPlay throws, a
// non-array / wrong-shape result, or an empty list) so the caller can fall
// back to the always-correct synchronous DOM walk. The empty-list case
// also falls back, since a real empty document is just as cheap to walk
// synchronously and a missing/empty `list` is more likely a failed read.

import { action } from "photoshop";
import type { PsDocument } from "photoshop";

import { rebuildLayerTree } from "../lib/layer-descriptor";
import type { Layer } from "../lib/layer";
import { log } from "../utils/log";

function readDocId(doc: PsDocument): number | undefined {
    const id = (doc as { id?: unknown }).id;
    return typeof id === "number" && Number.isFinite(id) ? id : undefined;
}

// Pulls the flat per-layer descriptor list out of the batchPlay result.
// The confirmed shape is `[{ list: [...] }]`; `layers` is accepted as a
// defensive alternative key, and a bare array is taken as-is.
export function extractLayerList(raw: unknown): unknown[] | null {
    if (!Array.isArray(raw)) return null;
    const first = raw[0] as Record<string, unknown> | undefined;
    if (first !== undefined) {
        if (Array.isArray(first["list"])) return first["list"] as unknown[];
        if (Array.isArray(first["layers"])) return first["layers"] as unknown[];
    }
    // A bare array of descriptors (some builds) - only when the entries
    // look like descriptors, not the `{ list }` envelope above.
    if (raw.length === 0 || typeof raw[0] === "object") return raw as unknown[];
    return null;
}

// The validated multiGet command: read name / id / visibility / the group
// marker / bounds for every layer in one round trip.
async function runMultiGet(id: number): Promise<unknown> {
    return action.batchPlay(
        [
            {
                _obj: "multiGet",
                _target: { _ref: "document", _id: id },
                extendedReference: [
                    ["name", "layerID", "visible", "layerSection", "bounds"],
                    { _obj: "layer", index: 1, count: -1 },
                ],
                options: { failOnMissingProperty: false, failOnMissingElement: false },
            },
        ],
        {},
    );
}

export async function readLayersViaMultiGet(doc: PsDocument): Promise<Layer[] | null> {
    const id = readDocId(doc);
    if (id === undefined) return null;
    try {
        const raw = await runMultiGet(id);
        const list = extractLayerList(raw);
        if (list === null || list.length === 0) return null;
        const tree = rebuildLayerTree(list);
        // A non-empty descriptor that folds to nothing means the shape
        // drifted (e.g. an unrecognised section enum); fall back rather
        // than show an empty tree.
        if (tree.length === 0) return null;
        return tree;
    } catch (err) {
        log.warn("multiget-read", "multiGet read failed; falling back to DOM walk", err);
        return null;
    }
}
