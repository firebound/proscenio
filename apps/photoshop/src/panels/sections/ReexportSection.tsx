// Wave 11.5 single-layer re-export. Lives in the Exporter panel
// alongside the full export; the Tags panel only INSPECTS the
// selected entry (RevealOutputSection), action moves here.
//
// Reads the active PS layer chain via useActiveLayerPath, matches
// it against the live preview's entryRefs, and exposes a single
// button that writes the PNG(s) for just that entry. Manifest
// stays untouched - debugging aid for iterating on one asset.

import React from "react";
import type { UxpFolder } from "uxp";

import {
    runSingleLayerExport,
    type ExportPreview,
    type SingleLayerExportResult,
} from "../../controllers/export-flow";
import type { ExportOptions } from "../../domain/planner";
import { elementsEqual } from "../../util/arrays";
import { log } from "../../util/log";
import { Accordion } from "../common/Accordion";
import { KeyValueRow } from "../common/KeyValueRow";

interface Props {
    preview: ExportPreview | null;
    activeLayerPath: readonly string[] | null;
    folder: UxpFolder | null;
    opts: ExportOptions;
}

export const ReexportSection: React.FC<Props> = ({ preview, activeLayerPath, folder, opts }) => {
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<SingleLayerExportResult | null>(null);

    const matched = findMatchedEntry(preview, activeLayerPath);

    const onReexport = React.useCallback(async () => {
        if (matched === null || folder === null) return;
        setBusy(true);
        setLast(null);
        try {
            const result = await runSingleLayerExport(opts, folder, matched.name);
            log.debug("ReexportSection", "result", result);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, [matched, folder, opts]);

    return (
        <Accordion
            title="Re-export selected"
            hint="Rewrites the PNG(s) for the layer selected in Photoshop. Manifest JSON is not touched."
        >
            {matched === null ? (
                <div className="placeholder-card">
                    Select a layer in Photoshop that maps to a manifest entry.
                </div>
            ) : (
                <>
                    <KeyValueRow label="entry" value={matched.name} mono />
                    <KeyValueRow label="kind" value={matched.kind} />
                </>
            )}
            <sp-action-button
                onClick={onReexport}
                disabled={busy || matched === null || folder === null ? true : undefined}
            >
                {busy ? "Re-exporting..." : "Re-export this entry's PNG"}
            </sp-action-button>
            {last !== null && <ReexportResult result={last} />}
        </Accordion>
    );
};

interface Matched {
    name: string;
    kind: string;
}

function findMatchedEntry(
    preview: ExportPreview | null,
    activeLayerPath: readonly string[] | null,
): Matched | null {
    if (preview === null || activeLayerPath === null) return null;
    const refs = preview.entryRefs;
    if (refs === undefined) return null;
    for (const ref of refs) {
        if (elementsEqual(ref.layerPath, activeLayerPath)) return { name: ref.name, kind: ref.kind };
        if (ref.framePaths?.some((p) => elementsEqual(p, activeLayerPath))) {
            return { name: ref.name, kind: ref.kind };
        }
    }
    return null;
}

const ReexportResult: React.FC<{ result: SingleLayerExportResult }> = ({ result }) => {
    if (result.kind === "ok") {
        return (
            <sp-body size="XS" className="result-row">
                Wrote {result.pngResults?.length ?? 0} PNG(s).
            </sp-body>
        );
    }
    return (
        <div className="result error">
            <sp-body size="XS">Re-export {result.kind}.</sp-body>
            {(result.errors ?? []).map((err, i) => (
                <sp-body size="XS" className="result-row" key={`${i}-${err}`}>{err}</sp-body>
            ))}
        </div>
    );
};
