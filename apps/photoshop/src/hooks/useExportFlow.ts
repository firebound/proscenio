// Owns the Export side of the panel: the toggles, the busy flag and
// the last-run result. The actual orchestration lives in
// `controllers/export-flow.ts`; this hook is the React glue.

import React from "react";
import type { UxpFolder } from "uxp";

import { runExport, type ExportFlowResult } from "../controllers/export-flow";
import type { ExportOptions } from "../domain/planner";

const DEFAULT_OPTS: ExportOptions = {
    skipHidden: true,
};

export interface UseExportFlow {
    opts: ExportOptions;
    busy: boolean;
    last: ExportFlowResult | null;
    setOption: <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => void;
    run: (folder: UxpFolder) => Promise<void>;
}

export function useExportFlow(): UseExportFlow {
    const [opts, setOpts] = React.useState<ExportOptions>(DEFAULT_OPTS);
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<ExportFlowResult | null>(null);

    const setOption = React.useCallback(
        <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => {
            setOpts((prev) => ({ ...prev, [key]: value }));
        },
        [],
    );

    const run = React.useCallback(
        async (folder: UxpFolder) => {
            setBusy(true);
            try {
                const result = await runExport(opts, folder);
                setLast(result);
            } finally {
                setBusy(false);
            }
        },
        [opts],
    );

    return { opts, busy, last, setOption, run };
}
