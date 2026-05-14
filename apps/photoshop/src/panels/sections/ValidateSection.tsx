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
                            {valErrors.map((err, i) => (
                                <sp-body size="XS" key={`${i}-${err}`} className="result-row">{err}</sp-body>
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
        <ValidateRow severity="warn" onActivate={onClick}>
            <span className="validate-code">{warning.code}</span>
            <span className="validate-text">
                <strong>{warning.name}</strong>: {warning.message}
            </span>
        </ValidateRow>
    );
};

const SkippedRow: React.FC<{ skipped: SkippedLayer }> = ({ skipped }) => {
    const onClick = React.useCallback(() => {
        void selectLayerByPath(skipped.layerPath);
    }, [skipped.layerPath]);
    return (
        <ValidateRow severity="skipped" onActivate={onClick}>
            <span className="validate-code">{skipped.reason}</span>
            <span className="validate-text">{skipped.name}</span>
        </ValidateRow>
    );
};

const ValidateRow: React.FC<{
    severity: "warn" | "skipped";
    onActivate: () => void;
    children: React.ReactNode;
}> = ({ severity, onActivate, children }) => {
    const onKey = React.useCallback((e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onActivate();
        }
    }, [onActivate]);
    // UXP's native <button> drops text content (verified visually in
    // other panels), so we keep the div + role="button" pattern.
    /* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions, jsx-a11y/role-supports-aria-props */
    return (
        <div
            className={`validate-row ${severity}`}
            role="button"
            tabIndex={0}
            onClick={onActivate}
            onKeyDown={onKey}
        >
            {children}
        </div>
    );
};
