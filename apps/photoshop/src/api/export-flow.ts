// Top-level export orchestrator (planner -> validator -> manifest +
// PNG writers).
//
// ajv validation runs before any modal opens, so an invalid manifest
// never reaches disk. The writer leg then runs inside one
// `core.executeAsModal` so PS shows a single modal banner.

import { app, core } from "photoshop";
import type { UxpFolder } from "uxp";

import { adaptDocument } from "./adapt-document";
import {
    buildExportPlan,
    type EntryRef,
    type ExportOptions,
    type ExportPlan,
    type PlanWarning,
    type SkippedLayer,
} from "../lib/planner";
import type { Manifest } from "../lib/manifest";
import { entryMatchesPath } from "../lib/entry-match";
import { validateManifest } from "./manifest-validator";
import { writeManifest } from "./manifest-writer";
import { runWrites, type PngWriteResult } from "./png-writer";
import { log } from "../utils/log";

export interface ExportFlowResult {
    kind: "ok" | "validation-failed" | "no-document" | "failed";
    folder?: string;
    manifestFile?: string;
    entryCount?: number;
    pngResults?: PngWriteResult[];
    errors?: string[];
}

export interface SingleLayerExportResult {
    kind: "ok" | "no-document" | "not-found" | "failed";
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
        // Atomicity: the manifest is persisted only if every PNG
        // landed, else it would reference files that do not exist.
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

/** Re-exports the PNG(s) belonging to a single manifest entry, looked
 *  up by `entryName` (manifest layer name). The manifest JSON is NOT
 *  touched.
 */
export async function runSingleLayerExport(
    opts: ExportOptions,
    folder: UxpFolder,
    entryName: string,
): Promise<SingleLayerExportResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        log.warn("export-flow", "single: no active document");
        return { kind: "no-document", errors: ["No document is open."] };
    }

    const adapted = adaptDocument(doc);
    const plan = buildExportPlan(adapted.info, adapted.layers, {
        ...opts,
        ...(adapted.anchor === undefined ? {} : { anchor: adapted.anchor }),
    });

    const matchingWrites = plan.writes.filter((w) => writeBelongsToEntry(w, entryName, plan));
    if (matchingWrites.length === 0) {
        log.warn("export-flow", "single: entry not found", entryName);
        return { kind: "not-found", errors: [`No manifest entry named "${entryName}".`] };
    }

    try {
        const pngResults = await core.executeAsModal(
            async () => runWrites(doc, folder, matchingWrites),
            { commandName: `Proscenio re-export ${entryName}` },
        );
        log.info("export-flow", "single done", { entryName, files: pngResults.length });
        const failed = pngResults.filter((r) => !r.ok);
        if (failed.length > 0) {
            return {
                kind: "failed",
                pngResults,
                errors: failed.map((r) => `${r.outputPath}: ${r.skippedReason ?? "failed"}`),
            };
        }
        return { kind: "ok", pngResults };
    } catch (err) {
        log.error("export-flow", "single threw", err);
        return {
            kind: "failed",
            errors: [err instanceof Error ? err.message : String(err)],
        };
    }
}

function writeBelongsToEntry(
    write: ExportPlan["writes"][number],
    entryName: string,
    plan: ExportPlan,
): boolean {
    // The planner can emit duplicate names (e.g. two layers tagged
    // `[path:test]`), so walk every matching ref rather than `find`-ing
    // the first - the selected layer need not be the first hit.
    for (const ref of plan.entryRefs) {
        if (ref.name !== entryName) continue;
        if (entryMatchesPath(ref, write.layerPath)) return true;
    }
    return false;
}
