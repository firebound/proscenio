import React from "react";

import type { ImportFlowResult } from "../../controllers/import-flow";

interface Props {
    busy: boolean;
    last: ImportFlowResult | null;
    manifestErrors: string[] | null;
    onImport: () => void;
}

export const ImportSection: React.FC<Props> = ({ busy, last, manifestErrors, onImport }) => (
    <>
        <section className="section">
            <sp-heading size="XS">Import (manifest to PSD)</sp-heading>
            <sp-body size="XS" className="muted">
                Pick a Proscenio manifest JSON. The plugin recreates the
                PSD with placed layers / sprite_frame groups; saved under
                the manifest folder's photoshop/ subfolder.
            </sp-body>
            <sp-action-button onClick={onImport} disabled={busy ? true : undefined}>
                {busy ? "Importing..." : "Import manifest as PSD"}
            </sp-action-button>
        </section>
        {manifestErrors !== null && <ManifestErrors errors={manifestErrors} />}
        {last !== null && <ImportResultView result={last} />}
    </>
);

const ImportResultView: React.FC<{ result: ImportFlowResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <div className="result ok">
                <sp-body size="XS">
                    Stamped {result.stamped} entry(ies)
                    {result.skipped !== undefined && result.skipped > 0
                        ? ` (${result.skipped} skipped)`
                        : ""}
                    .
                </sp-body>
                {result.psdPath !== undefined && (
                    <sp-body size="XS" className="folder-path">
                        {result.psdPath}
                    </sp-body>
                )}
                {(result.warnings ?? []).map((w) => (
                    <sp-body size="XS" className="result-row warn" key={w}>
                        {w}
                    </sp-body>
                ))}
            </div>
        );
    }
    return (
        <div className="result error">
            <sp-body size="XS">Import failed.</sp-body>
            {(result.errors ?? []).map((err) => (
                <sp-body size="XS" key={err} className="result-row">
                    {err}
                </sp-body>
            ))}
        </div>
    );
};

const ManifestErrors: React.FC<{ errors: string[] }> = ({ errors }) => (
    <div className="result error">
        <sp-body size="XS">Manifest invalid.</sp-body>
        {errors.map((err) => (
            <sp-body size="XS" key={err} className="result-row">
                {err}
            </sp-body>
        ))}
    </div>
);
