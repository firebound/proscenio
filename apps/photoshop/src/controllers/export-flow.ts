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
import {
    buildExportPlan,
    type EntryRef,
    type ExportOptions,
    type ExportPlan,
    type PlanWarning,
    type SkippedLayer,
} from "../domain/planner";
import type { Manifest } from "../domain/manifest";
import { validateManifest } from "../io/manifest-validator";
import { writeManifest } from "../io/manifest-writer";
import { runWrites, type PngWriteResult } from "../io/png-writer";
import { log } from "../util/log";

export interface ExportFlowResult {
    kind: "ok" | "validation-failed" | "no-document" | "failed";
    folder?: string;
    manifestFile?: string;
    entryCount?: number;
    pngResults?: PngWriteResult[];
    errors?: string[];
}

export interface ExportPreview {
    kind: "ok" | "no-document" | "validation-failed";
    manifest?: Manifest;
    skipped?: SkippedLayer[];
    warnings?: PlanWarning[];
    writes?: ExportPlan["writes"];
    entryRefs?: EntryRef[];
    errors?: string[];
}

export function previewExport(opts: ExportOptions): ExportPreview {
    try {
        const doc = app.activeDocument;
        if (doc === null) return { kind: "no-document", errors: ["No document is open."] };
        const adapted = adaptDocument(doc);
        log.trace("export-flow", "previewExport opts", opts, "layers", adapted.layers.length);
        const plan = buildExportPlan(adapted.info, adapted.layers, {
            ...opts,
            ...(adapted.anchor === undefined ? {} : { anchor: adapted.anchor }),
        });
        const errors = validateManifest(plan.manifest);
        if (errors.length > 0) {
            return {
                kind: "validation-failed",
                manifest: plan.manifest,
                skipped: plan.skipped,
                warnings: plan.warnings,
                writes: plan.writes,
                entryRefs: plan.entryRefs,
                errors,
            };
        }
        return {
            kind: "ok",
            manifest: plan.manifest,
            skipped: plan.skipped,
            warnings: plan.warnings,
            writes: plan.writes,
            entryRefs: plan.entryRefs,
        };
    } catch (err) {
        return {
            kind: "validation-failed",
            errors: [`preview failed: ${err instanceof Error ? err.message : String(err)}`],
        };
    }
}

export async function runExport(
    opts: ExportOptions,
    folder: UxpFolder,
): Promise<ExportFlowResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        log.warn("export-flow", "runExport: no active document");
        return { kind: "no-document", errors: ["No document is open."] };
    }

    log.info("export-flow", "runExport start", { folder: folder.nativePath, opts });
    const adapted = adaptDocument(doc);
    const plan = buildExportPlan(adapted.info, adapted.layers, {
        ...opts,
        ...(adapted.anchor === undefined ? {} : { anchor: adapted.anchor }),
    });

    const errors = validateManifest(plan.manifest);
    if (errors.length > 0) {
        log.warn("export-flow", "validation failed", errors);
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
            log.warn("export-flow", "PNG writes failed", failed.length);
            return {
                kind: "failed",
                pngResults,
                errors: failed.map(
                    (r) => `${r.outputPath}: ${r.skippedReason ?? "failed"}`,
                ),
            };
        }
        log.info("export-flow", "runExport done", {
            entries: plan.manifest.layers.length,
            manifestFile,
        });
        return {
            kind: "ok",
            folder: folder.nativePath,
            manifestFile,
            entryCount: plan.manifest.layers.length,
            pngResults,
        };
    } catch (err) {
        log.error("export-flow", "runExport threw", err);
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
