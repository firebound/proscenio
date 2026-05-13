// Wave 11.5 reveal-output detail surface. When the artist selects a
// PS layer that maps to a manifest entry, this panel shows what the
// export will emit for it (kind, name, manifest path, position, size,
// origin) plus the on-disk path under the current output folder. A
// "Re-export this entry" button runs the writer for that one entry
// only - debugging aid that does not touch the manifest JSON.

import React from "react";
import type { UxpFolder } from "uxp";

import {
    runSingleLayerExport,
    type ExportPreview,
    type SingleLayerExportResult,
} from "../../controllers/export-flow";
import type { ExportOptions } from "../../domain/planner";
import type { EntryRef } from "../../domain/planner";
import type { ManifestEntry, PolygonEntry } from "../../domain/manifest";
import { log } from "../../util/log";

interface Props {
    preview: ExportPreview | null;
    activeLayerPath: readonly string[] | null;
    folder: UxpFolder | null;
    opts: ExportOptions;
}

export const RevealOutputSection: React.FC<Props> = ({
    preview,
    activeLayerPath,
    folder,
    opts,
}) => {
    const [busy, setBusy] = React.useState(false);
    const [last, setLast] = React.useState<SingleLayerExportResult | null>(null);

    const matchedIndex = findMatchingEntry(preview, activeLayerPath);
    const entry = matchedIndex === null ? null : preview?.manifest?.layers[matchedIndex] ?? null;
    const ref = matchedIndex === null ? null : preview?.entryRefs?.[matchedIndex] ?? null;

    const onReexport = React.useCallback(async () => {
        if (entry === null || folder === null) return;
        setBusy(true);
        setLast(null);
        try {
            const result = await runSingleLayerExport(opts, folder, entry.name);
            log.debug("RevealOutput", "single export result", result);
            setLast(result);
        } finally {
            setBusy(false);
        }
    }, [entry, folder, opts]);

    if (preview === null) return null;
    if (activeLayerPath === null || matchedIndex === null || entry === null || ref === null) {
        return (
            <section className="section">
                <sp-heading size="XS">Selected entry</sp-heading>
                <sp-body size="XS" className="muted">
                    Select a layer in Photoshop to inspect what the export will emit for it.
                </sp-body>
            </section>
        );
    }

    const polygon = entry.kind === "sprite_frame" ? null : entry as PolygonEntry;
    const pngPaths = collectPaths(entry, ref);
    const folderPath = folder?.nativePath ?? null;
    const reexportDisabled = busy || folder === null;

    return (
        <section className="section">
            <sp-heading size="XS">Selected entry</sp-heading>
            <DetailRow label="kind" value={entry.kind} />
            <DetailRow label="name" value={entry.name} mono />
            {polygon !== null && <DetailRow label="manifest path" value={polygon.path} mono />}
            <DetailRow
                label="position"
                value={`${entry.position[0]}, ${entry.position[1]} px`}
                mono
            />
            <DetailRow
                label="size"
                value={`${entry.size[0]} x ${entry.size[1]} px`}
                mono
            />
            {entry.origin !== undefined && (
                <DetailRow
                    label="origin"
                    value={`${entry.origin[0]}, ${entry.origin[1]} px`}
                    mono
                />
            )}
            {entry.blend_mode !== undefined && (
                <DetailRow label="blend" value={entry.blend_mode} />
            )}
            {entry.subfolder !== undefined && (
                <DetailRow label="subfolder" value={entry.subfolder} mono />
            )}
            {entry.kind === "sprite_frame" && (
                <DetailRow label="frames" value={String(entry.frames.length)} />
            )}
            <sp-body size="XS">PNG path(s) on disk:</sp-body>
            {pngPaths.map((p) => (
                <sp-body size="XS" className="folder-path" key={p}>
                    {folderPath === null ? p : `${folderPath}/${p}`}
                </sp-body>
            ))}
            <sp-action-button
                onClick={onReexport}
                disabled={reexportDisabled ? true : undefined}
            >
                {busy ? "Re-exporting..." : "Re-export this entry's PNG"}
            </sp-action-button>
            {last !== null && <ReexportResult result={last} />}
        </section>
    );
};

const DetailRow: React.FC<{ label: string; value: string; mono?: boolean }> = ({
    label,
    value,
    mono,
}) => (
    <div className="reveal-row">
        <span className="reveal-label">{label}</span>
        <span className={mono === true ? "reveal-value mono" : "reveal-value"}>{value}</span>
    </div>
);

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
            {(result.errors ?? []).map((err) => (
                <sp-body size="XS" className="result-row" key={err}>{err}</sp-body>
            ))}
        </div>
    );
};

function findMatchingEntry(
    preview: ExportPreview | null,
    activeLayerPath: readonly string[] | null,
): number | null {
    if (preview === null || activeLayerPath === null) return null;
    const refs = preview.entryRefs;
    if (refs === undefined) return null;
    for (let i = 0; i < refs.length; i++) {
        const ref = refs[i];
        if (pathsEqual(ref.layerPath, activeLayerPath)) return i;
        if (ref.framePaths !== undefined && ref.framePaths.some((p) => pathsEqual(p, activeLayerPath))) {
            return i;
        }
    }
    return null;
}

function pathsEqual(a: readonly string[], b: readonly string[]): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

function collectPaths(entry: ManifestEntry, ref: EntryRef): string[] {
    if (entry.kind === "sprite_frame") {
        return entry.frames.map((f) => f.path);
    }
    void ref;
    return [(entry as PolygonEntry).path];
}
