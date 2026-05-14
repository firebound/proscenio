import React from "react";

import type { ExportPreview } from "../../controllers/export-flow";
import type { ManifestEntry, PolygonEntry, SpriteFrameEntry } from "../../domain/manifest";
import type { EntryRef } from "../../domain/planner";
import { elementsEqual } from "../../util/arrays";
import { Accordion } from "../common/Accordion";
import { KeyValueRow } from "../common/KeyValueRow";

interface Props {
    preview: ExportPreview | null;
    activeLayerPath: readonly string[] | null;
    onRefresh: () => void;
}

export const DebugSection: React.FC<Props> = ({ preview, activeLayerPath, onRefresh }) => {
    const entryCount = preview?.manifest?.layers.length ?? 0;
    return (
        <Accordion
            title="Preview"
            badge={entryCount > 0 ? String(entryCount) : undefined}
            hint="Dry-run of the export. Manifest entries listed below; warnings + skipped layers live in the Proscenio Validate panel."
        >
            {preview === null ? (
                <>
                    <sp-body size="XS" className="muted">
                        Click Refresh to dry-run the export. Nothing is written.
                    </sp-body>
                    <sp-action-button onClick={onRefresh}>Refresh</sp-action-button>
                </>
            ) : (
                <PreviewBody preview={preview} activeLayerPath={activeLayerPath} onRefresh={onRefresh} />
            )}
        </Accordion>
    );
};

const PreviewBody: React.FC<{
    preview: ExportPreview;
    activeLayerPath: readonly string[] | null;
    onRefresh: () => void;
}> = ({ preview, activeLayerPath, onRefresh }) => {
    if (preview.kind === "no-document") {
        return (
            <>
                <sp-body size="XS" className="muted">
                    {preview.errors?.[0] ?? "No document open."}
                </sp-body>
                <sp-action-button onClick={onRefresh}>Refresh</sp-action-button>
            </>
        );
    }
    const manifest = preview.manifest;
    const skipped = preview.skipped ?? [];
    const warnings = preview.warnings ?? [];
    const entryRefs = preview.entryRefs ?? [];
    const anchorLabel = manifest?.anchor === undefined
        ? "(canvas centre)"
        : `${manifest.anchor[0]}, ${manifest.anchor[1]} px`;
    return (
        <>
            <KeyValueRow label="anchor" value={anchorLabel} mono />
            <KeyValueRow label="entries" value={String(manifest?.layers.length ?? 0)} />
            <KeyValueRow label="skipped" value={String(skipped.length)} />
            <KeyValueRow label="warnings" value={String(warnings.length)} />
            <sp-action-button onClick={onRefresh}>Refresh</sp-action-button>
            <div className="entries-list">
                {(manifest?.layers ?? []).map((entry, i) => (
                    <EntryRow
                        key={`${entry.name}-${i}`}
                        entry={entry}
                        selected={isEntrySelected(entryRefs[i], activeLayerPath)}
                    />
                ))}
            </div>
        </>
    );
};

function isEntrySelected(
    ref: EntryRef | undefined,
    activeLayerPath: readonly string[] | null,
): boolean {
    if (ref === undefined || activeLayerPath === null) return false;
    if (elementsEqual(ref.layerPath, activeLayerPath)) return true;
    if (ref.framePaths === undefined) return false;
    return ref.framePaths.some((p) => elementsEqual(p, activeLayerPath));
}

const EntryRow: React.FC<{ entry: ManifestEntry; selected: boolean }> = ({ entry, selected }) => {
    const className = selected ? "entry-row selected" : "entry-row";
    if (entry.kind === "sprite_frame") {
        const sf = entry as SpriteFrameEntry;
        return (
            <div className={className}>
                <span className="entry-kind">sprite_frame</span>
                <span className="entry-name">{sf.name}</span>
                <span className="entry-meta">{sf.frames.length} frames{badges(sf)}</span>
            </div>
        );
    }
    const p = entry as PolygonEntry;
    return (
        <div className={className}>
            <span className="entry-kind">{p.kind}</span>
            <span className="entry-name">{p.name}</span>
            <span className="entry-path">{p.path}</span>
            {badges(p) !== "" && <span className="entry-meta">{badges(p)}</span>}
        </div>
    );
};

function badges(entry: ManifestEntry): string {
    const parts: string[] = [];
    if (entry.subfolder !== undefined) parts.push(`folder=${entry.subfolder}`);
    if (entry.blend_mode !== undefined) parts.push(`blend=${entry.blend_mode}`);
    if (entry.origin !== undefined) parts.push(`origin=${entry.origin[0]},${entry.origin[1]}`);
    return parts.length === 0 ? "" : ` (${parts.join(", ")})`;
}
