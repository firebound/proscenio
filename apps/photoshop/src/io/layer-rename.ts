// Tag-write side of the Tags tab. The hook computes the new layer
// name from the bag (`domain/tag-writer.ts`) and calls `renameLayer`
// here to persist it.
//
// IMPORTANT: `doc.layers` returns wrappers that go stale inside an
// `executeAsModal` block on this UXP build - find() never matches
// even when adapter-built tree sees the same layers. We therefore
// resolve the target reference OUTSIDE the modal and only do the
// `target.name = ...` mutation inside.

import { app, core } from "photoshop";

import { findLayerByPath } from "./_layer-find";
import { log } from "../util/log";

export interface RenameResult {
    ok: boolean;
    reason?: string;
}

export async function renameLayer(
    layerPath: readonly string[],
    newName: string,
): Promise<RenameResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        log.warn("layer-rename", "no active document");
        return { ok: false, reason: "no active document" };
    }
    const target = findLayerByPath(doc, layerPath);
    if (target === null) {
        return { ok: false, reason: "layer not found" };
    }
    log.debug("layer-rename", "rename", layerPath, "->", newName);
    let result: RenameResult = { ok: false, reason: "rename did not run" };
    try {
        await core.executeAsModal(
            async () => {
                target.name = newName;
                result = { ok: true };
            },
            { commandName: "Update Proscenio tags" },
        );
    } catch (err) {
        result = {
            ok: false,
            reason: err instanceof Error ? err.message : String(err),
        };
    }
    if (!result.ok) log.warn("layer-rename", "failed", layerPath, result.reason);
    return result;
}
