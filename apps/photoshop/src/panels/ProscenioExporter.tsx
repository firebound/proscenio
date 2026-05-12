// Proscenio exporter panel. The full UXP equivalent of the JSX
// dialog: lets the user pick the same `skipHidden` / `skipUnderscorePrefix`
// toggles and then invokes `runExport`. Result of the last run is
// rendered inline so the user does not need to chase a Photoshop
// alert dialog for outcomes.
//
// All Photoshop work happens inside `runExport`. This component is
// pure React + UXP storage; it does not touch the photoshop module
// directly, so the panel mounts even when no document is open.

import React from "react";

import { runExport, type ExportFlowResult } from "../controllers/export-flow";
import type { ExportOptions } from "../controllers/exporter";

const DEFAULT_OPTS: ExportOptions = {
    skipHidden: true,
    skipUnderscorePrefix: true,
};

export const ProscenioExporter: React.FC = () => {
    const [opts, setOpts] = React.useState<ExportOptions>(DEFAULT_OPTS);
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<ExportFlowResult | null>(null);

    const onExport = React.useCallback(async () => {
        setBusy(true);
        try {
            const result = await runExport(opts);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, [opts]);

    return (
        <div className="proscenio-panel">
            <h2>Proscenio exporter</h2>
            <p className="hint">
                Writes a v1 manifest + per-layer PNGs into the chosen folder. Pick
                the same output dir between runs to keep the manifest stable.
            </p>
            <label className="toggle">
                <input
                    type="checkbox"
                    checked={opts.skipHidden}
                    onChange={(e) => setOpts((o) => ({ ...o, skipHidden: e.target.checked }))}
                />
                <span>Skip hidden layers</span>
            </label>
            <label className="toggle">
                <input
                    type="checkbox"
                    checked={opts.skipUnderscorePrefix}
                    onChange={(e) =>
                        setOpts((o) => ({ ...o, skipUnderscorePrefix: e.target.checked }))
                    }
                />
                <span>
                    Skip layers starting with <code>_</code>
                </span>
            </label>
            <button type="button" onClick={onExport} disabled={busy}>
                {busy ? "Exporting..." : "Export manifest + PNGs"}
            </button>
            {last !== null && <ExportResult result={last} />}
        </div>
    );
};

const ExportResult: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <p>
                    Wrote {result.entryCount} entry(ies) to {result.manifestFile}
                </p>
                <p className="folder">{result.folder}</p>
                {(result.pngResults ?? []).filter((r) => !r.ok).map((r) => (
                    <p className="result-row warn" key={r.outputPath}>
                        {r.outputPath}: {r.skippedReason ?? "failed"}
                    </p>
                ))}
            </div>
        );
    }
    return (
        <div className="result error">
            <p>Export {result.kind}.</p>
            {(result.errors ?? []).map((err) => (
                <p key={err} className="result-row">
                    {err}
                </p>
            ))}
        </div>
    );
};
