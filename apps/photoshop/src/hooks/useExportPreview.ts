// Runs a dry-run of the export pipeline against the active document
// and surfaces the resulting manifest preview + skipped diagnostics.
// Used by the Debug section to give artists a live "what would land"
// view without writing anything to disk.

import React from "react";

import { previewExportAsync, type ExportPreview } from "../api/export-flow";
import type { ExportOptions } from "../lib/planner";
import { log } from "../utils/log";

export interface UseExportPreview {
    preview: ExportPreview | null;
    refresh: (opts: ExportOptions) => void;
}

export function useExportPreview(): UseExportPreview {
    const [preview, setPreview] = React.useState<ExportPreview | null>(null);
    // The preview read is now async (spec-048 multiGet fast path). A
    // monotonic token drops a slow refresh that resolves after a newer one
    // so the displayed preview always reflects the latest request; the ref
    // also lets a write after unmount be skipped.
    const tokenRef = React.useRef<number>(0);
    const mountedRef = React.useRef<boolean>(true);
    React.useEffect(() => () => { mountedRef.current = false; }, []);

    const refresh = React.useCallback((opts: ExportOptions) => {
        const token = ++tokenRef.current;
        void (async () => {
            const result = await previewExportAsync(opts);
            if (!mountedRef.current || token !== tokenRef.current) return;
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
        })();
    }, []);

    return { preview, refresh };
}
