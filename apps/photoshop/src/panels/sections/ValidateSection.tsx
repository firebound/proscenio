// SPEC 011 Wave 11.4: Validate tab. Re-uses the planner's `warnings`
// and `skipped` outputs from a live preview run. Each row is clickable
// (selects the offending layer in PS) so the artist can jump straight
// to the fix.
//
// The section is intentionally read-only - tag edits happen in the
// Tags section. Validate is just an aggregator + a fast lane to the
// affected layer.

import React from "react";

import type { ExportPreview } from "../../controllers/export-flow";
import type { PlanWarning, SkippedLayer } from "../../domain/planner";
import { selectLayerByPath } from "../../io/ps-selection";

interface Props {
    preview: ExportPreview | null;
}

export const ValidateSection: React.FC<Props> = ({ preview }) => {
    if (preview === null) {
        return (
            <section className="section">
                <sp-heading size="XS">Validate</sp-heading>
                <sp-body size="XS" className="muted">Open a document to begin validation.</sp-body>
            </section>
        );
    }
    if (preview.kind === "no-document") {
        return (
            <section className="section">
                <sp-heading size="XS">Validate</sp-heading>
                <sp-body size="XS" className="muted">
                    {preview.errors?.[0] ?? "No document open."}
                </sp-body>
            </section>
        );
    }
    const warnings = preview.warnings ?? [];
    const skipped = preview.skipped ?? [];
    const valErrors = preview.kind === "validation-failed" ? preview.errors ?? [] : [];
    const clean = warnings.length === 0 && skipped.length === 0 && valErrors.length === 0;
    return (
        <section className="section">
            <sp-heading size="XS">Validate</sp-heading>
            {clean ? (
                <sp-body size="XS" className="muted">
                    No issues. Manifest looks ready to export.
                </sp-body>
            ) : (
                <>
                    {valErrors.length > 0 && (
                        <div className="result error">
                            <sp-body size="XS">Manifest invalid:</sp-body>
                            {valErrors.map((err) => (
                                <sp-body size="XS" key={err} className="result-row">
                                    {err}
                                </sp-body>
                            ))}
                        </div>
                    )}
                    {warnings.length > 0 && (
                        <>
                            <sp-body size="XS">Warnings ({warnings.length})</sp-body>
                            {warnings.map((w, i) => (
                                <WarningRow key={`${w.code}-${w.name}-${i}`} warning={w} />
                            ))}
                        </>
                    )}
                    {skipped.length > 0 && (
                        <>
                            <sp-body size="XS">Skipped ({skipped.length})</sp-body>
                            {skipped.map((s) => (
                                <SkippedRow key={`${s.name}-${s.layerPath.join("/")}`} skipped={s} />
                            ))}
                        </>
                    )}
                </>
            )}
        </section>
    );
};

const WarningRow: React.FC<{ warning: PlanWarning }> = ({ warning }) => {
    const onClick = React.useCallback(() => {
        void selectLayerByPath(warning.layerPath);
    }, [warning.layerPath]);
    return (
        <sp-body size="XS" className="preview-row warn clickable" onClick={onClick}>
            [{warning.code}] {warning.name}: {warning.message}
        </sp-body>
    );
};

const SkippedRow: React.FC<{ skipped: SkippedLayer }> = ({ skipped }) => {
    const onClick = React.useCallback(() => {
        void selectLayerByPath(skipped.layerPath);
    }, [skipped.layerPath]);
    return (
        <sp-body size="XS" className="preview-row muted clickable" onClick={onClick}>
            {skipped.name} ({skipped.reason})
        </sp-body>
    );
};
