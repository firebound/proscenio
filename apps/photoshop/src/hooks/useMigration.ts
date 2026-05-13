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
        } finally {
            setBusy(false);
        }
    }, []);

    return { preview, busy, lastResult, apply };
}
