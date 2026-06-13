// PNG writer. For each `PngWrite` the export plan emits, isolate the
// source PsLayer onto a same-canvas-size temp document, trim the
// transparent border, save as PNG into the target folder, then close
// the temp doc without saving.
//
// All Photoshop document operations have to run inside
// `core.executeAsModal`; `runWrites` must be called from within a modal
// context (the orchestrator wraps the whole batch in one modal so the
// user sees a single banner instead of one per layer).

import { app, constants, type PsDocument, type PsLayer } from "photoshop";
import type { UxpFile, UxpFolder } from "uxp";

import type { PngWrite } from "../lib/planner";
import { findLayerByPath } from "./_layer-find";

export interface PngWriteResult {
    outputPath: string;
    ok: boolean;
    skippedReason?: string;
}

export async function runWrites(
    sourceDoc: PsDocument,
    folder: UxpFolder,
    writes: PngWrite[],
): Promise<PngWriteResult[]> {
    const results: PngWriteResult[] = [];
    for (const write of writes) {
        // Each write is isolated: a UXP rejection on one layer (a bad
        // duplicate / merge / trim / saveAs, or a folder write that
        // fails) records that layer as `ok: false` and the loop moves on,
        // instead of rejecting the whole modal and losing every other
        // layer plus the manifest. The orchestrator then decides
        // full / partial / failed from the per-layer results.
        try {
            const layer = findLayerByPath(sourceDoc, write.layerPath);
            if (layer === null) {
                results.push({
                    outputPath: write.outputPath,
                    ok: false,
                    skippedReason: `source layer not found: ${write.layerPath.join("/")}`,
                });
                continue;
            }
            const file = await ensureOutputFile(folder, write.outputPath);
            await writeLayerPng(sourceDoc, layer, file, write.merge === true);
            results.push({ outputPath: write.outputPath, ok: true });
        } catch (err) {
            results.push({
                outputPath: write.outputPath,
                ok: false,
                skippedReason: err instanceof Error ? err.message : String(err),
            });
        }
    }
    return results;
}

async function writeLayerPng(
    sourceDoc: PsDocument,
    layer: PsLayer,
    file: UxpFile,
    merge: boolean,
): Promise<boolean> {
    // UXP rejects bare string mode / fill names ("RGB", "transparent")
    // with "Invalid constant. Expected 'RGB' to be one of
    // NewDocumentMode." The accepted values are the constant references
    // from `constants.NewDocumentMode` / `constants.DocumentFill`.
    const work = await app.documents.add({
        width: sourceDoc.width,
        height: sourceDoc.height,
        name: "proscenio_export_tmp",
        fill: constants.DocumentFill.TRANSPARENT,
        mode: constants.NewDocumentMode.RGB,
    });
    try {
        const duplicated = await layer.duplicate(work);
        if (merge) {
            // `Layer.merge()` on a group layer flattens it into one pixel
            // layer occupying the union of the descendants.
            await duplicated.merge();
        }
        // UXP Document.trim takes positional args, not an options bag.
        await work.trim(constants.TrimType.TRANSPARENT, true, true, true, true);
        await work.saveAs.png(file, { compression: 9, interlaced: false }, true);
        return true;
    } finally {
        await work.closeWithoutSaving();
    }
}

async function ensureOutputFile(folder: UxpFolder, outputPath: string): Promise<UxpFile> {
    const segments = outputPath.split("/").filter((s) => s.length > 0);
    let dir = folder;
    for (let i = 0; i < segments.length - 1; i++) {
        const segment = segments[i];
        if (segment === undefined) continue;
        dir = await ensureSubfolder(dir, segment);
    }
    const leaf = segments.at(-1);
    if (leaf === undefined) {
        throw new Error(`empty output path: ${outputPath}`);
    }
    return dir.createFile(leaf, { overwrite: true });
}

async function ensureSubfolder(parent: UxpFolder, name: string): Promise<UxpFolder> {
    try {
        return await parent.createFolder(name, { overwrite: false });
    } catch {
        // Folder already exists - resolve it, but a non-folder entry at
        // the same path must hard-fail rather than be cast to UxpFolder.
        const entry = await parent.getEntry(name);
        if (!entry.isFolder) {
            throw new Error(`output path collides with a non-folder entry: ${name}`);
        }
        return entry as UxpFolder;
    }
}
