// Click-to-select helper for the Validate / Debug surfaces. UXP
// exposes layer selection through `action.batchPlay` rather than a
// direct Layer.select() method, so this module wraps the descriptor
// so the panel can stay focused on UI concerns.
//
// `layerPath` is the chain of layer names from the document root down
// to the leaf - the same shape `PngWrite.layerPath` carries. Names
// must match the live PSD (the planner uses display-name semantics on
// the manifest, but selection has to use the raw PS layer name).

import { action, app, core } from "photoshop";
import type { PsDocument, PsLayer } from "photoshop";

import { log } from "../util/log";

const MAX_DEPTH = 64;

/** Reads the layer-path chain of the single currently-selected PS
 *  layer. Returns `null` when no document is open, the user has
 *  multiple layers selected, or the selection cannot be resolved. */
export function readActiveLayerPath(): string[] | null {
    try {
        const doc = app.activeDocument;
        if (doc === null) return null;
        const active = doc.activeLayers;
        if (active === undefined || active.length !== 1) {
            log.trace("ps-selection", "no single active layer", active?.length);
            return null;
        }
        const chain: string[] = [];
        let cur: PsLayer | PsDocument | null | undefined = active[0];
        for (let i = 0; i < MAX_DEPTH; i++) {
            if (cur === undefined || cur === null) break;
            if (cur === doc) break;
            // Doc-shaped sentinel: has width/height but no parent.
            // Some UXP builds return a fresh wrapper for the document
            // on the parent chain that fails reference equality with
            // `doc`. Stop there too.
            if (isDocumentShape(cur)) break;
            const name = (cur as PsLayer).name;
            if (typeof name !== "string") {
                log.warn("ps-selection", "layer has no name at depth", i, cur);
                break;
            }
            chain.unshift(name);
            cur = (cur as PsLayer).parent ?? null;
        }
        return chain.length === 0 ? null : chain;
    } catch (err) {
        log.warn("ps-selection", "readActiveLayerPath threw", err);
        return null;
    }
}

function isDocumentShape(value: PsLayer | PsDocument): boolean {
    return (
        "width" in value
        && "height" in value
        && !("parent" in (value as object))
    );
}

export async function selectLayerByPath(layerPath: readonly string[]): Promise<void> {
    if (layerPath.length === 0) return;
    const leaf = layerPath.at(-1);
    if (leaf === undefined) return;
    await core.executeAsModal(
        async () => {
            await action.batchPlay(
                [
                    {
                        _obj: "select",
                        _target: [{ _ref: "layer", _name: leaf }],
                        makeVisible: false,
                        _options: { dialogOptions: "dontDisplay" },
                    },
                ],
                {},
            );
        },
        { commandName: "Select Proscenio layer" },
    );
}
