// UXP-side companion to `domain/legacy-migration.ts`. Reads the active
// document, plans the `_<name>` -> `[ignore]` rename batch, and
// applies the renames inside a single `executeAsModal` so PS reports
// one modal banner instead of N.
//
// Layer-tree traversal walks the live `PsDocument.layers` array and
// matches by name path against the planned candidates. This is robust
// to PS layer ID drift (sample fixtures regenerate IDs every export
// run); it does mean a layer renamed by another action mid-flight
// silently slips through, which is acceptable for a one-shot artist
// helper.

import { app, core, type PsDocument, type PsLayer } from "photoshop";

import { adaptDocument } from "../adapters/photoshop-layer";
import {
    planUnderscoreMigration,
    type UnderscoreMigrationCandidate,
} from "../domain/legacy-migration";
import { log } from "../util/log";

export interface MigrationPreview {
    candidates: UnderscoreMigrationCandidate[];
    /** True when no active document is open. UI shows a hint. */
    noDocument: boolean;
}

export interface MigrationResult {
    renamed: number;
    /** Per-candidate failures (layer not found, rename threw). */
    failures: { layerPath: string[]; reason: string }[];
}

export function previewUnderscoreMigration(): MigrationPreview {
    const doc = app.activeDocument;
    if (doc === null) return { candidates: [], noDocument: true };
    const adapted = adaptDocument(doc);
    return {
        candidates: planUnderscoreMigration(adapted.layers),
        noDocument: false,
    };
}

export async function applyUnderscoreMigration(): Promise<MigrationResult> {
    const doc = app.activeDocument;
    if (doc === null) {
        log.warn("legacy-migration", "no active document");
        return { renamed: 0, failures: [] };
    }
    const candidates = planUnderscoreMigration(adaptDocument(doc).layers);
    log.info("legacy-migration", "candidates", candidates.length);
    if (candidates.length === 0) return { renamed: 0, failures: [] };

    const failures: MigrationResult["failures"] = [];
    let renamed = 0;
    await core.executeAsModal(
        async () => {
            for (const candidate of candidates) {
                const layer = findLayerByPath(doc, candidate.layerPath);
                if (layer === null) {
                    failures.push({ layerPath: candidate.layerPath, reason: "layer not found" });
                    continue;
                }
                try {
                    layer.name = candidate.newName;
                    renamed += 1;
                } catch (err) {
                    failures.push({
                        layerPath: candidate.layerPath,
                        reason: err instanceof Error ? err.message : String(err),
                    });
                }
            }
        },
        { commandName: "Convert _ prefixes to [ignore]" },
    );
    log.info("legacy-migration", "renamed", renamed, "failed", failures.length);
    return { renamed, failures };
}

function findLayerByPath(doc: PsDocument, layerPath: readonly string[]): PsLayer | null {
    let layers: PsLayer[] | undefined = doc.layers;
    let target: PsLayer | null = null;
    for (const segment of layerPath) {
        if (layers === undefined) return null;
        const found: PsLayer | undefined = layers.find((l: PsLayer) => l.name === segment);
        if (found === undefined) return null;
        target = found;
        layers = found.layers;
    }
    return target;
}
