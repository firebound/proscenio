import React from "react";

import type { UnderscoreMigrationCandidate } from "../../domain/legacy-migration";
import type { MigrationPreview, MigrationResult } from "../../io/legacy-migration";
import { selectLayerByPath } from "../../io/ps-selection";
import { Accordion } from "../common/Accordion";

interface Props {
    preview: MigrationPreview;
    busy: boolean;
    lastResult: MigrationResult | null;
    onApply: () => void;
}

export const MigrationSection: React.FC<Props> = ({ preview, busy, lastResult, onApply }) => {
    if (preview.noDocument) return null;
    const count = preview.candidates.length;
    if (count === 0 && lastResult === null) return null;
    return (
        <Accordion
            title="Legacy migration"
            badge={count > 0 ? String(count) : undefined}
            defaultOpen={count > 0}
            hint="Convert legacy `_layerName` skip conventions to the [ignore] tag."
        >
            {count === 0 ? (
                <sp-body size="XS" className="muted">No underscore-prefixed layers found.</sp-body>
            ) : (
                <>
                    <sp-body size="XS">{count} layer(s) ready to rename:</sp-body>
                    {preview.candidates.slice(0, 6).map((c) => (
                        <CandidateRow key={c.layerPath.join("/")} candidate={c} />
                    ))}
                    {count > 6 && (
                        <sp-body size="XS" className="muted">...and {count - 6} more.</sp-body>
                    )}
                    <sp-action-button onClick={onApply} disabled={busy ? true : undefined}>
                        {busy ? "Renaming..." : `Convert ${count} layer(s) to [ignore]`}
                    </sp-action-button>
                </>
            )}
            {lastResult !== null && <ResultView result={lastResult} />}
        </Accordion>
    );
};

const CandidateRow: React.FC<{ candidate: UnderscoreMigrationCandidate }> = ({ candidate }) => {
    const onClick = React.useCallback(() => {
        void selectLayerByPath(candidate.layerPath);
    }, [candidate.layerPath]);
    const onKey = React.useCallback((e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            void selectLayerByPath(candidate.layerPath);
        }
    }, [candidate.layerPath]);
    /* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */
    return (
        <div
            className="migration-row"
            role="button"
            tabIndex={0}
            onClick={onClick}
            onKeyDown={onKey}
        >
            <span className="migration-old">{candidate.oldName}</span>
            <span className="migration-arrow">-&gt;</span>
            <span className="migration-new">{candidate.newName}</span>
        </div>
    );
};

const ResultView: React.FC<{ result: MigrationResult }> = ({ result }) => {
    const hasFailures = result.failures.length > 0;
    return (
        <div className={hasFailures ? "result error" : "result"}>
            <sp-body size="XS">
                Renamed {result.renamed} layer(s){hasFailures ? `, ${result.failures.length} failed:` : "."}
            </sp-body>
            {result.failures.map((f, i) => (
                <sp-body size="XS" key={`${f.layerPath.join("/")}-${i}`} className="result-row warn">
                    {f.layerPath.join("/")}: {f.reason}
                </sp-body>
            ))}
        </div>
    );
};
