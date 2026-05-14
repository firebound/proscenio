// Runs a dry-run of the export pipeline against the active document
// and surfaces the resulting manifest preview + skipped diagnostics.
// Used by the Debug section to give artists a live "what would land"
// view without writing anything to disk.

import React from "react";

import { previewExport, type ExportPreview } from "../controllers/export-flow";
import type { ExportOptions } from "../domain/planner";
import { log } from "../util/log";

export interface UseExportPreview {
    preview: ExportPreview | null;
    refresh: (opts: ExportOptions) => void;
}

export function useExportPreview(): UseExportPreview {
    const [preview, setPreview] = React.useState<ExportPreview | null>(null);

    const refresh = React.useCallback((opts: ExportOptions) => {
        const result = previewExport(opts);
        log.debug(
            "useExportPreview",
            "refresh",
            result.kind,
            "entries=",
            result.manifest?.layers.length ?? 0,
            "warnings=",
            result.warnings?.length ?? 0,
            "skipped=",
            result.skipped?.length ?? 0,
        );
        setPreview(result);
    }, []);

    return { preview, refresh };
}
