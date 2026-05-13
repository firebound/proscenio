// Wave 11.5 reveal-output detail surface (read-only). When the artist
// selects a PS layer that maps to a manifest entry, this panel shows
// what the export will emit for it - kind, name, manifest path,
// position, size, origin, blend, subfolder - plus the resolved on-disk
// PNG path under the current output folder.
//
// The "Re-export this entry's PNG" action lives in the Exporter panel
// (see ReexportSection); the Tags panel keeps only the inspection.

import React from "react";
import type { UxpFolder } from "uxp";

import type { ExportPreview } from "../../controllers/export-flow";
import type { ManifestEntry, PolygonEntry } from "../../domain/manifest";
import { elementsEqual } from "../../util/arrays";
import { Accordion } from "../common/Accordion";
import { KeyValueRow } from "../common/KeyValueRow";

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
                <sp-body size="XS" className="muted">
                    Select a layer in Photoshop to inspect what the export will emit for it.
                </sp-body>
            </Accordion>
        );
    }

    const polygon = entry.kind === "sprite_frame" ? null : entry as PolygonEntry;
    const pngPaths = collectPaths(entry);
    const folderPath = folder?.nativePath ?? null;

    return (
        <Accordion title="Selected entry" badge={entry.kind === "sprite_frame" ? "sf" : entry.kind}>
            <KeyValueRow label="name" value={entry.name} mono />
            {polygon !== null && <KeyValueRow label="manifest" value={polygon.path} mono />}
            <KeyValueRow label="position" value={`${entry.position[0]}, ${entry.position[1]} px`} mono />
            <KeyValueRow label="size" value={`${entry.size[0]} x ${entry.size[1]} px`} mono />
            {entry.origin !== undefined && (
                <KeyValueRow label="origin" value={`${entry.origin[0]}, ${entry.origin[1]} px`} mono />
            )}
            {entry.blend_mode !== undefined && <KeyValueRow label="blend" value={entry.blend_mode} />}
            {entry.subfolder !== undefined && <KeyValueRow label="subfolder" value={entry.subfolder} mono />}
            {entry.kind === "sprite_frame" && (
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
        if (elementsEqual(ref.layerPath, activeLayerPath)) return i;
        if (ref.framePaths?.some((p) => elementsEqual(p, activeLayerPath))) return i;
    }
    return null;
}

function collectPaths(entry: ManifestEntry): string[] {
    if (entry.kind === "sprite_frame") return entry.frames.map((f) => f.path);
    return [entry.path];
}
