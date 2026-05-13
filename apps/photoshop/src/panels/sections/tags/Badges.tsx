// Inline badge strip for the Tags row. Surfaces non-default tag
// values (folder, path, scale, origin, name pattern) as compact
// uppercase labels so the artist can see at a glance which tags
// the layer carries without expanding the details panel.

import React from "react";

import type { TagBag } from "../../../domain/tag-parser";

export function hasBadge(tags: TagBag): boolean {
    return (
        tags.folder !== undefined
        || tags.path !== undefined
        || tags.scale !== undefined
        || tags.origin !== undefined
        || tags.originMarker === true
        || tags.namePattern !== undefined
    );
}

export const BadgeStrip: React.FC<{ tags: TagBag }> = ({ tags }) => (
    <>
        {tags.folder !== undefined && <Badge label="F" value={tags.folder} title={`folder: ${tags.folder}`} />}
        {tags.path !== undefined && <Badge label="P" value={tags.path} title={`path: ${tags.path}`} />}
        {tags.scale !== undefined && <Badge label="S" value={String(tags.scale)} title={`scale: ${tags.scale}`} />}
        {tags.origin !== undefined && (
            <Badge
                label="O"
                value={`${tags.origin[0]},${tags.origin[1]}`}
                title={`origin: ${tags.origin[0]}, ${tags.origin[1]} px`}
            />
        )}
        {tags.originMarker === true && (
            <Badge label="OM" value="" title="origin marker - bbox centre used as parent's pivot" />
        )}
        {tags.namePattern !== undefined && (
            <Badge label="NP" value={tags.namePattern} title={`name pattern: ${tags.namePattern}`} />
        )}
    </>
);

const Badge: React.FC<{ label: string; value: string; title: string }> = ({ label, value, title }) => (
    <span className="tag-badge" title={title}>
        <span className="tag-badge-label">{label}</span>
        <span className="tag-badge-value">{value}</span>
    </span>
);
