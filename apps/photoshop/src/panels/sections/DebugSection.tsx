import React from "react";

import type { ExportPreview } from "../../controllers/export-flow";
import type { ManifestEntry, PolygonEntry, SpriteFrameEntry } from "../../domain/manifest";
import type { EntryRef } from "../../domain/planner";

interface Props {
    preview: ExportPreview | null;
    activeLayerPath: readonly string[] | null;
    onRefresh: () => void;
}

export const DebugSection: React.FC<Props> = ({ preview, activeLayerPath, onRefresh }) => (
    <section className="section">
        <sp-heading size="XS">Preview / debug</sp-heading>
        <sp-action-button onClick={onRefresh}>Refresh preview</sp-action-button>
        {preview === null ? (
            <sp-body size="XS" className="muted">
                Click Refresh preview to dry-run the export. Nothing is written.
            </sp-body>
        ) : (
            <PreviewBody preview={preview} activeLayerPath={activeLayerPath} />
        )}
    </section>
);

const PreviewBody: React.FC<{
    preview: ExportPreview;
    activeLayerPath: readonly string[] | null;
}> = ({ preview, activeLayerPath }) => {
    if (preview.kind === "no-document") {
        return (
            <sp-body size="XS" className="muted">
                {preview.errors?.[0] ?? "No document open."}
            </sp-body>
        );
    }
    const manifest = preview.manifest;
    const skipped = preview.skipped ?? [];
    const warnings = preview.warnings ?? [];
    const entryRefs = preview.entryRefs ?? [];
    return (
        <>
            <sp-body size="XS">
                Anchor: {manifest?.anchor === undefined ? "(canvas centre)" : `${manifest.anchor[0]}, ${manifest.anchor[1]} px`}
            </sp-body>
            <sp-body size="XS">
                Entries: {manifest?.layers.length ?? 0} | Skipped: {skipped.length} | Warnings: {warnings.length}
            </sp-body>
            <sp-body size="XS" className="muted">
                Warnings + skipped layers live in the Proscenio Validate panel.
            </sp-body>
            <sp-heading size="XS">Entries</sp-heading>
            {(manifest?.layers ?? []).map((entry, i) => (
                <EntryRow
                    key={`${entry.name}-${i}`}
                    entry={entry}
                    selected={isEntrySelected(entryRefs[i], activeLayerPath)}
                />
            ))}
        </>
    );
};

function isEntrySelected(
    ref: EntryRef | undefined,
    activeLayerPath: readonly string[] | null,
): boolean {
    if (ref === undefined || activeLayerPath === null) return false;
    if (pathsEqual(ref.layerPath, activeLayerPath)) return true;
    if (ref.framePaths === undefined) return false;
    return ref.framePaths.some((p) => pathsEqual(p, activeLayerPath));
}

function pathsEqual(a: readonly string[], b: readonly string[]): boolean {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

const EntryRow: React.FC<{ entry: ManifestEntry; selected: boolean }> = ({ entry, selected }) => {
    const className = selected ? "preview-row selected" : "preview-row";
    if (entry.kind === "sprite_frame") {
        const sf = entry as SpriteFrameEntry;
        return (
            <sp-body size="XS" className={className}>
                [sprite_frame] {sf.name} - {sf.frames.length} frames{badges(sf)}
            </sp-body>
        );
    }
    const p = entry as PolygonEntry;
    return (
        <sp-body size="XS" className={className}>
            [{p.kind}] {p.name} -&gt; {p.path}{badges(p)}
        </sp-body>
    );
};

function badges(entry: ManifestEntry): string {
    const parts: string[] = [];
    if (entry.subfolder !== undefined) parts.push(`folder=${entry.subfolder}`);
    if (entry.blend_mode !== undefined) parts.push(`blend=${entry.blend_mode}`);
    if (entry.origin !== undefined) parts.push(`origin=${entry.origin[0]},${entry.origin[1]}`);
    return parts.length === 0 ? "" : ` (${parts.join(", ")})`;
}

