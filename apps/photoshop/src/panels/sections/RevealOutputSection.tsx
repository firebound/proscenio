// Read-only detail surface for the active layer's matched manifest
// entry, plus its resolved on-disk PNG path(s).

import React from "react";
import type { UxpFolder } from "uxp";

import type { ExportPreview } from "../../api/export-flow";
import type { ManifestEntry } from "../../lib/manifest";
import { entryMatchesPath } from "../../lib/entry-match";
import { Accordion } from "../../components/Accordion";
import { KeyValueRow } from "../../components/KeyValueRow";

interface Props {
    preview: ExportPreview | null;
    activeLayerPath: readonly string[] | null;
    folder: UxpFolder | null;
}

export const RevealOutputSection: React.FC<Props> = ({ preview, activeLayerPath, folder }) => {
    const matchedIndex = findMatchingEntry(preview, activeLayerPath);
    const entry = matchedIndex === null ? null : preview?.manifest?.layers[matchedIndex] ?? null;
    const ref = matchedIndex === null ? null : preview?.entryRefs?.[matchedIndex] ?? null;

    if (preview === null) return null;
    if (activeLayerPath === null || matchedIndex === null || entry === null || ref === null) {
        return (
            <Accordion title="Selected entry">
                <div className="placeholder-card">
                    Select a layer in Photoshop to inspect what the export will emit for it.
                </div>
            </Accordion>
        );
    }

    const mesh = entry.kind === "sprite" ? null : entry;
    const pngPaths = collectPaths(entry);
    const folderPath = folder?.nativePath ?? null;

    return (
        <Accordion title="Selected entry" badge={entry.kind === "sprite" ? "spr" : entry.kind}>
            <KeyValueRow label="name" value={entry.name} mono />
            {mesh !== null && <KeyValueRow label="manifest" value={mesh.path} mono />}
            <KeyValueRow label="position" value={`${entry.position[0]}, ${entry.position[1]} px`} mono />
            <KeyValueRow label="size" value={`${entry.size[0]} x ${entry.size[1]} px`} mono />
            {entry.origin != null && (
                <KeyValueRow label="origin" value={`${entry.origin[0]}, ${entry.origin[1]} px`} mono />
            )}
            {entry.blend_mode != null && <KeyValueRow label="blend" value={entry.blend_mode} />}
            {entry.subfolder != null && <KeyValueRow label="subfolder" value={entry.subfolder} mono />}
            {entry.kind === "sprite" && (
                <KeyValueRow label="frames" value={String(entry.frames.length)} />
            )}
            <div className="reveal-paths">
                {pngPaths.map((p) => (
                    <sp-body size="XS" className="folder-path" key={p}>
                        {folderPath === null ? p : `${folderPath}/${p}`}
                    </sp-body>
                ))}
            </div>
        </Accordion>
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
        if (ref === undefined) continue;
        if (entryMatchesPath(ref, activeLayerPath)) return i;
    }
    return null;
}

function collectPaths(entry: ManifestEntry): string[] {
    if (entry.kind === "sprite") return entry.frames.map((f) => f.path);
    return [entry.path];
}
