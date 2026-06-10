// Reads the active document, plans the `_<name>` -> `[ignore]` rename
// batch, and applies the renames inside one `executeAsModal`.
//
// Traversal matches candidates by name path (not layer ID) to survive
// PS layer ID drift; a layer renamed by another action mid-flight thus
// slips through, acceptable for a one-shot artist helper.

import { app, core } from "photoshop";

import { findLayerByPath } from "./_layer-find";
import { adaptDocument } from "../api/adapt-document";
import {
    planUnderscoreMigration,
    type UnderscoreMigrationCandidate,
} from "../lib/legacy-migration";
import { log } from "../utils/log";

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
    // Rename deepest-first: renaming an ancestor first would change its
    // name in the live tree, so a descendant's pre-migration `layerPath`
    // would no longer match in findLayerByPath.
    const candidates = planUnderscoreMigration(adaptDocument(doc).layers)
        .slice()
        .sort((a, b) => b.layerPath.length - a.layerPath.length);
    log.info("legacy-migration", "candidates", candidates.length);
    if (candidates.length === 0) return { renamed: 0, failures: [] };

    const failures: MigrationResult["failures"] = [];
    let renamed = 0;
    await core.executeAsModal(
        // eslint-disable-next-line @typescript-eslint/require-await -- modal callback is async by API contract
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
