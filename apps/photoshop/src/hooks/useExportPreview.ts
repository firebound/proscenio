// Runs a dry-run of the export pipeline against the active document
// and surfaces the resulting manifest preview + skipped diagnostics.
// Used by the Debug section to give artists a live "what would land"
// view without writing anything to disk.

import React from "react";

import { previewExport, type ExportPreview } from "../controllers/export-flow";
import type { ExportOptions } from "../domain/planner";

export interface UseExportPreview {
    preview: ExportPreview | null;
    refresh: (opts: ExportOptions) => void;
}

export function useExportPreview(): UseExportPreview {
    const [preview, setPreview] = React.useState<ExportPreview | null>(null);

    const refresh = React.useCallback((opts: ExportOptions) => {
        setPreview(previewExport(opts));
    }, []);

    return { preview, refresh };
}
