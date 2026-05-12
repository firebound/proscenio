import React from "react";

import type { ExportFlowResult } from "../../controllers/export-flow";
import type { ExportOptions } from "../../domain/planner";

interface Props {
    opts: ExportOptions;
    busy: boolean;
    disabled: boolean;
    last: ExportFlowResult | null;
    onToggleOption: <K extends keyof ExportOptions>(key: K, value: ExportOptions[K]) => void;
    onExport: () => void;
}

export const ExportSection: React.FC<Props> = ({
    opts,
    busy,
    disabled,
    last,
    onToggleOption,
    onExport,
}) => {
    const onSkipHidden = React.useCallback(
        (e: React.SyntheticEvent) => {
            onToggleOption("skipHidden", (e.target as HTMLInputElement).checked);
        },
        [onToggleOption],
    );

    return (
        <>
            <section className="section">
                <sp-heading size="XS">Export options</sp-heading>
                <sp-checkbox checked={opts.skipHidden ? true : undefined} onChange={onSkipHidden}>
                    Skip hidden layers
                </sp-checkbox>
                <sp-body size="XS" className="muted">
                    Use the [ignore] tag in a layer or group name to exclude it from the export.
                </sp-body>
            </section>
            <sp-action-button onClick={onExport} disabled={disabled ? true : undefined}>
                {busy ? "Exporting..." : "Export manifest + PNGs"}
            </sp-action-button>
            {last !== null && <ExportResultView result={last} />}
        </>
    );
};

const ExportResultView: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Wrote {result.entryCount} entry(ies) to {result.manifestFile}
                </sp-body>
                {(result.pngResults ?? [])
                    .filter((r) => !r.ok)
                    .map((r) => (
                        <sp-body size="XS" className="result-row warn" key={r.outputPath}>
                            {r.outputPath}: {r.skippedReason ?? "failed"}
                        </sp-body>
                    ))}
            </div>
        );
    }
    return (
        <div className="result error">
            <sp-body size="XS">Export {result.kind}.</sp-body>
            {(result.errors ?? []).map((err) => (
                <sp-body size="XS" key={err} className="result-row">
                    {err}
                </sp-body>
            ))}
        </div>
    );
};
