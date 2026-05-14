// Drives the legacy `_<name>` -> `[ignore]` migration UI. Listens to
// `useDocumentChanges` so the candidate count stays current as the
// artist edits the PSD; calling `apply` runs the rename batch and
// re-reads the document.

import React from "react";

import {
    applyUnderscoreMigration,
    previewUnderscoreMigration,
    type MigrationPreview,
    type MigrationResult,
} from "../io/legacy-migration";

export interface UseMigration {
    preview: MigrationPreview;
    busy: boolean;
    lastResult: MigrationResult | null;
    apply: () => Promise<void>;
}

export function useMigration(version: number): UseMigration {
    const [preview, setPreview] = React.useState<MigrationPreview>({
        candidates: [],
        noDocument: true,
    });
    const [busy, setBusy] = React.useState(false);
    const [lastResult, setLastResult] = React.useState<MigrationResult | null>(null);

    React.useEffect(() => {
        setPreview(previewUnderscoreMigration());
    }, [version]);

    const apply = React.useCallback(async () => {
        setBusy(true);
        try {
            const result = await applyUnderscoreMigration();
            setLastResult(result);
            setPreview(previewUnderscoreMigration());
        } catch (err) {
            // applyUnderscoreMigration already absorbs per-candidate
            // failures and returns a MigrationResult; this catch fires
            // only when the outer executeAsModal itself rejects (PS
            // busy / locked / target lost mid-flight). Surface that
            // through the same shape the UI already renders.
            setLastResult({
                renamed: 0,
                failures: [{
                    layerPath: [],
                    reason: err instanceof Error ? err.message : "migration threw exception",
                }],
            });
        } finally {
            setBusy(false);
        }
    }, []);

    return { preview, busy, lastResult, apply };
}
