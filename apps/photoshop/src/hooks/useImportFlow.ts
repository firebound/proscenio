// Owns the Import side of the panel: picking a manifest, surfacing
// ajv validation errors, running the orchestrator. UI glue around
// `io/manifest-reader` and `controllers/import-flow`.

import React from "react";

import { runImport, type ImportFlowResult } from "../controllers/import-flow";
import { readManifestFromPicker } from "../io/manifest-reader";

export interface UseImportFlow {
    busy: boolean;
    last: ImportFlowResult | null;
    manifestErrors: string[] | null;
    run: () => Promise<void>;
}

export function useImportFlow(): UseImportFlow {
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<ImportFlowResult | null>(null);
    const [manifestErrors, setManifestErrors] = React.useState<string[] | null>(null);

    const run = React.useCallback(async () => {
        setManifestErrors(null);
        const picked = await readManifestFromPicker();
        if (picked.kind === "cancelled") return;
        if (picked.kind === "invalid") {
            setManifestErrors(picked.errors);
            return;
        }
        setBusy(true);
        try {
            const result = await runImport(picked.picked.manifest, picked.picked.folder);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, []);

    return { busy, last, manifestErrors, run };
}
