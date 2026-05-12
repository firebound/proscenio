// Top-level export orchestrator. Wires the planner, validator,
// manifest writer and PNG writer into one flow the panel button can
// call.
//
// The entire writer leg runs inside one `core.executeAsModal` so the
// user sees a single "Proscenio export" modal banner in Photoshop
// rather than one per layer. ajv validation runs first, before any
// modal opens; an invalid manifest never reaches disk and surfaces in
// the panel as a list of strings.
//
// Folder management lives in `src/io/folder-storage.ts`; this module
// only consumes a pre-resolved `UxpFolder` so the panel can show /
// reset the active folder independently of an export run.

import { app, core } from "photoshop";
import type { UxpFolder } from "uxp";

import { adaptDocument } from "../adapters/photoshop-layer";
import { buildExportPlan, type ExportOptions } from "../domain/planner";
import { validateManifest } from "../io/manifest-validator";
import { writeManifest } from "../io/manifest-writer";
import { runWrites, type PngWriteResult } from "../io/png-writer";

export interface ExportFlowResult {
    kind: "ok" | "validation-failed" | "no-document" | "failed";
    folder?: string;
    manifestFile?: string;
    entryCount?: number;
    pngResults?: PngWriteResult[];
    errors?: string[];
}

export async function runExport(
    opts: ExportOptions,
    folder: UxpFolder,
): Promise<ExportFlowResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        return { kind: "no-document", errors: ["No document is open."] };
    }

    const adapted = adaptDocument(doc);
    const plan = buildExportPlan(adapted.info, adapted.layers, {
        ...opts,
        ...(adapted.anchor === undefined ? {} : { anchor: adapted.anchor }),
    });

    const errors = validateManifest(plan.manifest);
    if (errors.length > 0) {
        return { kind: "validation-failed", errors };
    }

    const manifestFile = manifestFileName(adapted.info.name);

    try {
        // PNG writes happen first; the manifest is only persisted if
        // every PNG landed. Otherwise the manifest on disk would point
        // at files that do not exist, which surfaces as a broken
        // import on the downstream side hours later. Both steps share
        // a single executeAsModal so PS shows one modal banner.
        const { pngResults, manifestWritten } = await core.executeAsModal(
            async () => {
                const results = await runWrites(doc, folder, plan.writes);
                const allOk = results.every((r) => r.ok);
                if (allOk) await writeManifest(folder, plan.manifest, manifestFile);
                return { pngResults: results, manifestWritten: allOk };
            },
            { commandName: "Proscenio export" },
        );
        if (!manifestWritten) {
            const failed = pngResults.filter((r) => !r.ok);
            return {
                kind: "failed",
                pngResults,
                errors: failed.map(
                    (r) => `${r.outputPath}: ${r.skippedReason ?? "failed"}`,
                ),
            };
        }
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
