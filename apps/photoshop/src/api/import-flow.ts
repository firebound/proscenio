// Top-level import orchestrator. Caller passes a pre-validated
// manifest and a pre-picked folder; this module owns the modal that
// creates the document and stamps every entry. The resulting PSD is
// left open and unsaved on purpose - the artist saves via File > Save As.
//
// Entries are stamped in z_order DESCENDING order: PS adds new layers
// at the top of the stack, so iterating high -> low leaves the front
// layer (z_order 0) on top.

import { app, constants, core } from "photoshop";
import type { PsDocument } from "photoshop";
import type { UxpFile, UxpFolder } from "uxp";

import { moveLayerIntoGroup, placePngAt } from "./png-placer";
import type { Manifest, ManifestEntry, MeshEntry, SpriteEntry } from "../lib/manifest";

export interface ImportFlowResult {
    kind: "ok" | "failed";
    stamped?: number;
    skipped?: number;
    warnings?: string[];
    errors?: string[];
}

export async function runImport(
    manifest: Manifest,
    folder: UxpFolder,
): Promise<ImportFlowResult> {
    try {
        return await core.executeAsModal(
            async () => doImport(manifest, folder),
            { commandName: "Proscenio import" },
        );
    } catch (err) {
        return {
            kind: "failed",
            errors: [err instanceof Error ? err.message : String(err)],
        };
    }
}

async function doImport(manifest: Manifest, folder: UxpFolder): Promise<ImportFlowResult> {
    const [width, height] = manifest.size;
    const doc = await app.documents.add({
        width,
        height,
        name: manifest.doc,
        fill: constants.DocumentFill.TRANSPARENT,
        mode: constants.NewDocumentMode.RGB,
    });

    const sortedEntries = [...manifest.layers].sort((a, b) => b.z_order - a.z_order);
    const warnings: string[] = [];
    let stamped = 0;
    let skipped = 0;
    for (const entry of sortedEntries) {
        const result = await stampEntry(doc, entry, folder, warnings);
        if (result) stamped += 1;
        else skipped += 1;
    }

    return {
        kind: "ok",
        stamped,
        skipped,
        warnings,
    };
}

async function stampEntry(
    doc: PsDocument,
    entry: ManifestEntry,
    folder: UxpFolder,
    warnings: string[],
): Promise<boolean> {
    if (entry.kind === "sprite") {
        return stampSprite(doc, entry, folder, warnings);
    }
    return stampMesh(doc, entry, folder, warnings);
}

async function stampMesh(
    doc: PsDocument,
    entry: MeshEntry,
    folder: UxpFolder,
    warnings: string[],
): Promise<boolean> {
    const pngFile = await resolveRelativeFile(folder, entry.path);
    if (pngFile === null) {
        warnings.push(`mesh ${entry.name}: missing PNG at ${entry.path}`);
        return false;
    }
    const result = await placePngAt(
        doc,
        pngFile,
        entry.position[0],
        entry.position[1],
        entry.size[0],
        entry.size[1],
    );
    if (result.warning !== undefined) warnings.push(result.warning);
    if (result.layer === null) {
        warnings.push(`mesh ${entry.name}: placement failed`);
        return false;
    }
    result.layer.name = entry.name;
    return true;
}

async function stampSprite(
    doc: PsDocument,
    entry: SpriteEntry,
    folder: UxpFolder,
    warnings: string[],
): Promise<boolean> {
    if (entry.frames.length < 1) {
        warnings.push(`sprite ${entry.name}: needs at least 1 frame; skipped`);
        return false;
    }
    const group = await doc.createLayerGroup({ name: entry.name });
    let placed = 0;
    for (const frame of entry.frames) {
        const pngFile = await resolveRelativeFile(folder, frame.path);
        if (pngFile === null) {
            warnings.push(`sprite ${entry.name} frame ${frame.index}: missing PNG at ${frame.path}`);
            continue;
        }
        const result = await placePngAt(
            doc,
            pngFile,
            entry.position[0],
            entry.position[1],
            entry.size[0],
            entry.size[1],
        );
        if (result.warning !== undefined) warnings.push(result.warning);
        if (result.layer === null) continue;
        result.layer.name = String(frame.index);
        await moveLayerIntoGroup(result.layer, group);
        placed += 1;
    }
    if (placed === 0) {
        await group.delete();
        warnings.push(`sprite ${entry.name}: zero frames placed; group removed`);
        return false;
    }
    return true;
}

async function resolveRelativeFile(folder: UxpFolder, relative: string): Promise<UxpFile | null> {
    const segments = relative.split("/").filter((s) => s.length > 0);
    let current: UxpFolder = folder;
    for (let i = 0; i < segments.length - 1; i++) {
        const segment = segments[i];
        if (segment === undefined) return null;
        try {
            const entry = await current.getEntry(segment);
            if (!entry.isFolder) return null;
            current = entry as UxpFolder;
        } catch {
            return null;
        }
    }
    const leafName = segments.at(-1);
    if (leafName === undefined) return null;
    try {
        const entry = await current.getEntry(leafName);
        return entry.isFile ? (entry as UxpFile) : null;
    } catch {
        return null;
    }
}
