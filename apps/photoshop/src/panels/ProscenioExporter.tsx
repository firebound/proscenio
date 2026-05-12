// Proscenio exporter panel. The full UXP equivalent of the JSX
// dialog: lets the user pick the same `skipHidden` / `skipUnderscorePrefix`
// toggles and then invokes `runExport`. Result of the last run is
// rendered inline so the user does not need to chase a Photoshop
// alert dialog for outcomes.
//
// All Photoshop work happens inside `runExport`. This component is
// pure React + UXP storage; it does not touch the photoshop module
// directly, so the panel mounts even when no document is open.
//
// Spectrum web components (`<sp-checkbox>`, `<sp-action-button>`,
// `<sp-body>`, `<sp-heading>`) render natively in UXP and inherit the
// Photoshop theme. They are not in React's JSX intrinsic table, so we
// declare them as `any` via the module augmentation below - the alt
// is forking the Spectrum typings package, which is not worth the
// build complexity for a few elements.

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

    const onToggleHidden = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipHidden: checked }));
    }, []);

    const onToggleUnderscore = React.useCallback((e: React.SyntheticEvent) => {
        const checked = (e.target as HTMLInputElement).checked;
        setOpts((o) => ({ ...o, skipUnderscorePrefix: checked }));
    }, []);

    return (
        <div className="proscenio-panel">
            <sp-heading size="S">Proscenio exporter</sp-heading>
            <sp-body size="XS">
                Writes a v1 manifest + per-layer PNGs into the chosen folder.
                Pick the same output dir between runs to keep the manifest
                stable.
            </sp-body>
            <sp-checkbox checked={opts.skipHidden ? true : undefined} onChange={onToggleHidden}>
                Skip hidden layers
            </sp-checkbox>
            <sp-checkbox
                checked={opts.skipUnderscorePrefix ? true : undefined}
                onChange={onToggleUnderscore}
            >
                Skip layers starting with _
            </sp-checkbox>
            <sp-action-button onClick={onExport} disabled={busy ? true : undefined}>
                {busy ? "Exporting..." : "Export manifest + PNGs"}
            </sp-action-button>
            {last !== null && <ExportResult result={last} />}
        </div>
    );
};

const ExportResult: React.FC<{ result: ExportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Wrote {result.entryCount} entry(ies) to {result.manifestFile}
                </sp-body>
                <sp-body size="XS" className="folder">
                    {result.folder}
                </sp-body>
                {(result.pngResults ?? []).filter((r) => !r.ok).map((r) => (
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

declare global {
    namespace JSX {
        interface IntrinsicElements {
            "sp-heading": SpectrumElementProps;
            "sp-body": SpectrumElementProps;
            "sp-checkbox": SpectrumCheckboxProps;
            "sp-action-button": SpectrumActionButtonProps;
        }
    }
}

interface SpectrumElementProps extends React.HTMLAttributes<HTMLElement>, React.Attributes {
    size?: "XS" | "S" | "M" | "L" | "XL";
}

interface SpectrumCheckboxProps extends SpectrumElementProps {
    checked?: boolean;
    onChange?: (e: React.SyntheticEvent) => void;
}

interface SpectrumActionButtonProps extends SpectrumElementProps {
    disabled?: boolean;
    onClick?: (e: React.SyntheticEvent) => void;
}
