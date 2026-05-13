// SPEC 011 Wave 11.4: Validate tab. Re-uses the planner's `warnings`
// and `skipped` outputs from a live preview run. Each row is clickable
// (selects the offending layer in PS) so the artist can jump straight
// to the fix.
//
// Read-only - tag edits happen in the Tags panel.

import React from "react";

import type { ExportPreview } from "../../controllers/export-flow";
import type { PlanWarning, SkippedLayer } from "../../domain/planner";
import { selectLayerByPath } from "../../io/ps-selection";
import { Accordion } from "../common/Accordion";

interface Props {
    preview: ExportPreview | null;
}

export const ValidateSection: React.FC<Props> = ({ preview }) => {
    if (preview === null) {
        return (
            <Accordion title="Validate">
                <sp-body size="XS" className="muted">Open a document to begin validation.</sp-body>
            </Accordion>
        );
    }
    if (preview.kind === "no-document") {
        return (
            <Accordion title="Validate">
                <sp-body size="XS" className="muted">
                    {preview.errors?.[0] ?? "No document open."}
                </sp-body>
            </Accordion>
        );
    }
    const warnings = preview.warnings ?? [];
    const skipped = preview.skipped ?? [];
    const valErrors = preview.kind === "validation-failed" ? preview.errors ?? [] : [];
    const totalIssues = warnings.length + skipped.length + valErrors.length;
    const clean = totalIssues === 0;
    return (
        <Accordion
            title="Validate"
            badge={totalIssues > 0 ? String(totalIssues) : "ok"}
            hint="Planner-emitted warnings + skipped layers. Click any row to jump to the offending layer in Photoshop."
        >
            {clean ? (
                <sp-body size="XS" className="muted">No issues. Manifest looks ready to export.</sp-body>
            ) : (
                <>
                    {valErrors.length > 0 && (
                        <div className="result error">
                            <sp-body size="XS">Manifest invalid:</sp-body>
                            {valErrors.map((err) => (
                                <sp-body size="XS" key={err} className="result-row">{err}</sp-body>
                            ))}
                        </div>
                    )}
                    {warnings.length > 0 && (
                        <SubGroup title={`Warnings (${warnings.length})`}>
                            {warnings.map((w, i) => (
                                <WarningRow key={`${w.code}-${w.name}-${i}`} warning={w} />
                            ))}
                        </SubGroup>
                    )}
                    {skipped.length > 0 && (
                        <SubGroup title={`Skipped (${skipped.length})`}>
                            {skipped.map((s) => (
                                <SkippedRow key={`${s.name}-${s.layerPath.join("/")}`} skipped={s} />
                            ))}
                        </SubGroup>
                    )}
                </>
            )}
        </Accordion>
    );
};

const SubGroup: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div className="subgroup">
        <div className="subgroup-title">{title}</div>
        {children}
    </div>
);

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
