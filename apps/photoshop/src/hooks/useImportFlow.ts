// Owns the Import side of the panel: picking a manifest, surfacing
// ajv validation errors, running the orchestrator. UI glue around
// `api/manifest-reader` and `api/import-flow`.

import React from "react";

import { runImport, type ImportFlowResult } from "../api/import-flow";
import { readManifestFromPicker } from "../api/manifest-reader";

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
        // Go busy before the picker opens, not just before the modal: the
        // pre-busy window otherwise leaves the button live, so a second
        // click stacks a second picker on top of the first.
        setBusy(true);
        setManifestErrors(null);
        try {
            const picked = await readManifestFromPicker();
            if (picked.kind === "cancelled") return;
            if (picked.kind === "invalid") {
                setManifestErrors(picked.errors);
                return;
            }
            const result = await runImport(picked.picked.manifest, picked.picked.folder);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, []);

    return { busy, last, manifestErrors, run };
}
