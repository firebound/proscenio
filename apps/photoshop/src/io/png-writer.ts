// PNG writer. For each `PngWrite` the export plan emits, isolate the
// source PsLayer onto a same-canvas-size temp document, trim the
// transparent border, save as PNG into the target folder, then close
// the temp doc without saving. Mirrors the JSX exporter's
// `exportLayerToFile` step.
//
// All Photoshop document operations have to run inside
// `core.executeAsModal` from UXP. The caller is expected to invoke
// `runWrites` from within a modal context (the export-flow orchestrator
// wraps the whole batch in one `executeAsModal` so the user sees a
// single modal banner instead of one per layer).

import { app, constants, type PsDocument, type PsLayer } from "photoshop";
import type { UxpFile, UxpFolder } from "uxp";

import type { PngWrite } from "../domain/planner";

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
        const layer = resolveLayer(sourceDoc, write.layerPath);
        if (layer === null) {
            results.push({
                outputPath: write.outputPath,
                ok: false,
                skippedReason: `source layer not found: ${write.layerPath.join("/")}`,
            });
            continue;
        }
        const file = await ensureOutputFile(folder, write.outputPath);
        const wrote = await writeLayerPng(sourceDoc, layer, file);
        results.push({ outputPath: write.outputPath, ok: wrote });
    }
    return results;
}

async function writeLayerPng(
    sourceDoc: PsDocument,
    layer: PsLayer,
    file: UxpFile,
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
        await layer.duplicate(work);
        // UXP Document.trim takes positional args, not an options bag:
        // trim(trimType, top, bottom, left, right). Passing an object
        // surfaces as "Invalid value of '{...}' for the type
        // 'Constants.TrimType'" since the whole object lands on the
        // first parameter.
        await work.trim(constants.TrimType.TRANSPARENT, true, true, true, true);
        await work.saveAs.png(file, { compression: 9, interlaced: false }, true);
        return true;
    } finally {
        await work.closeWithoutSaving();
    }
}

function resolveLayer(doc: PsDocument, path: string[]): PsLayer | null {
    let current: PsLayer[] = doc.layers;
    let found: PsLayer | null = null;
    for (const segment of path) {
        found = current.find((l) => l.name === segment) ?? null;
        if (found === null) return null;
        current = found.layers ?? [];
    }
    return found;
}

async function ensureOutputFile(folder: UxpFolder, outputPath: string): Promise<UxpFile> {
    const segments = outputPath.split("/").filter((s) => s.length > 0);
    let dir = folder;
    for (let i = 0; i < segments.length - 1; i++) {
        dir = await ensureSubfolder(dir, segments[i]);
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
        // Folder already exists - look it up and confirm it really is
        // a folder. A file at the same path collides with our output
        // layout and must surface as a hard error rather than be
        // silently cast to UxpFolder.
        const entry = await parent.getEntry(name);
        if (!entry.isFolder) {
            throw new Error(`output path collides with a non-folder entry: ${name}`);
        }
        return entry as UxpFolder;
    }
}
