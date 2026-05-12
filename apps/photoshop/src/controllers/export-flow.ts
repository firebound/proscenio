// Top-level export orchestrator. Wires the planner, validator,
// manifest writer and PNG writer into one flow the panel button can
// call.
//
// The entire writer leg runs inside one `core.executeAsModal` so the
// user sees a single "Proscenio export" modal banner in Photoshop
// rather than one per layer. ajv validation runs first, before any
// modal opens; an invalid manifest never reaches disk and surfaces in
// the panel as a list of strings.

import { app, core } from "photoshop";
import { storage } from "uxp";
import type { UxpFolder } from "uxp";

import { adaptDocument } from "../adapters/photoshop-layer";
import { buildExportPlan, type ExportOptions } from "./exporter";
import { validateManifest } from "../io/manifest-validator";
import { writeManifest } from "../io/manifest-writer";
import { runWrites, type PngWriteResult } from "../io/png-writer";

export interface ExportFlowResult {
    kind: "ok" | "validation-failed" | "no-document" | "no-folder" | "failed";
    folder?: string;
    manifestFile?: string;
    entryCount?: number;
    pngResults?: PngWriteResult[];
    errors?: string[];
}

export async function runExport(opts: ExportOptions): Promise<ExportFlowResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        return { kind: "no-document", errors: ["No document is open."] };
    }
    const folder = await pickFolder();
    if (folder === null) {
        return { kind: "no-folder", errors: ["No output folder selected."] };
    }

    const adapted = adaptDocument(doc);
    const plan = buildExportPlan(adapted.info, adapted.layers, opts);

    const errors = validateManifest(plan.manifest);
    if (errors.length > 0) {
        return { kind: "validation-failed", errors };
    }

    const manifestFile = manifestFileName(adapted.info.name);

    try {
        const pngResults = await core.executeAsModal(
            async () => {
                await writeManifest(folder, plan.manifest, manifestFile);
                return runWrites(doc, folder, plan.writes);
            },
            { commandName: "Proscenio export" },
        );
        return {
            kind: "ok",
            folder: folder.nativePath,
            manifestFile,
            entryCount: plan.manifest.layers.length,
            pngResults,
        };
    } catch (err) {
        return {
            kind: "failed",
            errors: [err instanceof Error ? err.message : String(err)],
        };
    }
}

function manifestFileName(docName: string): string {
    const stem = docName.replace(/\.[^.]+$/, "");
    return `${stem}.photoshop_exported.json`;
}

// Cache the folder picked in this plugin session so repeat exports
// do not pop the OS folder picker every time. Reset by reloading the
// plugin or by `clearCachedFolder` (Wave 10.4 wires this to a panel
// "Change folder" button). A persistent token survives across plugin
// reloads via `storage.localFileSystem.createPersistentToken` - parked
// for Wave 10.4 alongside the panel polish.
let cachedFolder: UxpFolder | null = null;

export function clearCachedFolder(): void {
    cachedFolder = null;
}

async function pickFolder(): Promise<UxpFolder | null> {
    if (cachedFolder !== null) return cachedFolder;
    try {
        const folder = await storage.localFileSystem.getFolder();
        cachedFolder = folder;
        return folder;
    } catch {
        return null;
    }
}
