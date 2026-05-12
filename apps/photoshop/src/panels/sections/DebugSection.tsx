import React from "react";

import type { ExportPreview } from "../../controllers/export-flow";
import type { ManifestEntry, PolygonEntry, SpriteFrameEntry } from "../../domain/manifest";
import type { SkippedLayer } from "../../domain/planner";

interface Props {
    preview: ExportPreview | null;
    onRefresh: () => void;
}

export const DebugSection: React.FC<Props> = ({ preview, onRefresh }) => (
    <section className="section">
        <sp-heading size="XS">Preview / debug</sp-heading>
        <sp-action-button onClick={onRefresh}>Refresh preview</sp-action-button>
        {preview === null ? (
            <sp-body size="XS" className="muted">
                Click Refresh preview to dry-run the export. Nothing is written.
            </sp-body>
        ) : (
            <PreviewBody preview={preview} />
        )}
    </section>
);

const PreviewBody: React.FC<{ preview: ExportPreview }> = ({ preview }) => {
    if (preview.kind === "no-document") {
        return (
            <sp-body size="XS" className="muted">
                {preview.errors?.[0] ?? "No document open."}
            </sp-body>
        );
    }
    const manifest = preview.manifest;
    const skipped = preview.skipped ?? [];
    return (
        <>
            <sp-body size="XS">
                Anchor: {manifest?.anchor === undefined ? "(canvas centre)" : `${manifest.anchor[0]}, ${manifest.anchor[1]} px`}
            </sp-body>
            <sp-body size="XS">
                Entries: {manifest?.layers.length ?? 0} | Skipped: {skipped.length}
            </sp-body>
            {preview.kind === "validation-failed" && (
                <div className="result error">
                    <sp-body size="XS">Manifest invalid:</sp-body>
                    {(preview.errors ?? []).map((err) => (
                        <sp-body size="XS" key={err} className="result-row">
                            {err}
                        </sp-body>
                    ))}
                </div>
            )}
            {(manifest?.layers ?? []).map((entry, i) => (
                <EntryRow key={`${entry.name}-${i}`} entry={entry} />
            ))}
            {skipped.length > 0 && (
                <>
                    <sp-heading size="XS">Skipped layers</sp-heading>
                    {skipped.map((s) => (
                        <SkippedRow key={`${s.name}-${s.layerPath.join("/")}`} skipped={s} />
                    ))}
                </>
            )}
        </>
    );
};

const EntryRow: React.FC<{ entry: ManifestEntry }> = ({ entry }) => {
    if (entry.kind === "sprite_frame") {
        const sf = entry as SpriteFrameEntry;
        return (
            <sp-body size="XS" className="preview-row">
                [sprite_frame] {sf.name} - {sf.frames.length} frames{badges(sf)}
            </sp-body>
        );
    }
    const p = entry as PolygonEntry;
    return (
        <sp-body size="XS" className="preview-row">
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

const SkippedRow: React.FC<{ skipped: SkippedLayer }> = ({ skipped }) => (
    <sp-body size="XS" className="preview-row muted">
        {skipped.name} ({skipped.reason})
    </sp-body>
);
