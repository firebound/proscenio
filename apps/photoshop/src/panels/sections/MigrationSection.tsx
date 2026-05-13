import React from "react";

import type { UnderscoreMigrationCandidate } from "../../domain/legacy-migration";
import type { MigrationPreview, MigrationResult } from "../../io/legacy-migration";
import { selectLayerByPath } from "../../io/ps-selection";

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
        <section className="section">
            <sp-heading size="XS">Legacy migration</sp-heading>
            <sp-body size="XS" className="muted">
                Convert legacy `_layerName` skip conventions to the [ignore] tag.
            </sp-body>
            {count === 0 ? (
                <sp-body size="XS" className="muted">
                    No underscore-prefixed layers found.
                </sp-body>
            ) : (
                <>
                    <sp-body size="XS">{count} layer(s) ready to rename:</sp-body>
                    {preview.candidates.slice(0, 6).map((c) => (
                        <CandidateRow key={c.layerPath.join("/")} candidate={c} />
                    ))}
                    {count > 6 && (
                        <sp-body size="XS" className="muted">
                            ...and {count - 6} more.
                        </sp-body>
                    )}
                    <sp-action-button onClick={onApply} disabled={busy ? true : undefined}>
                        {busy ? "Renaming..." : `Convert ${count} layer(s) to [ignore]`}
                    </sp-action-button>
                </>
            )}
            {lastResult !== null && <ResultView result={lastResult} />}
        </section>
    );
};

const CandidateRow: React.FC<{ candidate: UnderscoreMigrationCandidate }> = ({ candidate }) => {
    const onClick = React.useCallback(() => {
        void selectLayerByPath(candidate.layerPath);
    }, [candidate.layerPath]);
    return (
        <sp-body size="XS" className="preview-row clickable" onClick={onClick}>
            {candidate.oldName} -&gt; {candidate.newName}
        </sp-body>
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
