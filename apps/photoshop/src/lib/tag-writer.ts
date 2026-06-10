// Reverse of `tag-parser.ts`. Given a display name and a target tag
// bag, produces the canonical layer name that the parser will round-
// trip back into the same bag. Canonical ordering keeps tag-driven
// layer names stable across edits so source-control diffs stay
// readable.

import type { BlendMode } from "./manifest";
import type { TagBag } from "./tag-parser";

/** Canonical tag order. Bag entries write in this sequence; unknown
 *  keys fall back to alphabetical. */
const TAG_ORDER = [
    "ignore",
    "merge",
    "kind",
    "folder",
    "path",
    "blend",
    "scale",
    "origin",
    "originMarker",
    "namePattern",
] as const;

export function writeLayerName(displayName: string, tags: TagBag): string {
    const segments = collectSegments(tags);
    if (segments.length === 0) return displayName;
    const left = displayName.trim();
    if (left.length === 0) return segments.join(" ");
    return `${left} ${segments.join(" ")}`;
}

function collectSegments(tags: TagBag): string[] {
    const out: string[] = [];
    for (const key of TAG_ORDER) {
        const segment = segmentFor(key, tags);
        if (segment !== null) out.push(segment);
    }
    return out;
}

/** One serializer per tag key. The mapped type makes the table
 *  exhaustive: adding a key to `TAG_ORDER`'s union without a builder
 *  here is a compile error, so the dispatch stays total without a
 *  switch's per-case branching. */
const SEGMENT_BUILDERS: Record<typeof TAG_ORDER[number], (tags: TagBag) => string | null> = {
    ignore: (tags) => (tags.ignore === true ? "[ignore]" : null),
    merge: (tags) => (tags.merge === true ? "[merge]" : null),
    kind: (tags) => (tags.kind === undefined ? null : kindSegment(tags.kind)),
    folder: (tags) => (tags.folder === undefined ? null : `[folder:${tags.folder}]`),
    path: (tags) => (tags.path === undefined ? null : `[path:${tags.path}]`),
    // `normal` is the default composite mode; emitting `[blend:normal]`
    // clutters the layer name without changing behavior. Treat as no tag.
    blend: (tags) =>
        tags.blend === undefined || tags.blend === "normal" ? null : `[blend:${tags.blend}]`,
    scale: (tags) => (tags.scale === undefined ? null : `[scale:${String(tags.scale)}]`),
    origin: (tags) =>
        tags.origin === undefined
            ? null
            : `[origin:${String(tags.origin[0])},${String(tags.origin[1])}]`,
    // `[origin]` and `[origin:x,y]` are mutually exclusive in the parser;
    // do not emit the marker when explicit coords exist.
    originMarker: (tags) =>
        tags.originMarker === true && tags.origin === undefined ? "[origin]" : null,
    namePattern: (tags) => (tags.namePattern === undefined ? null : `[name:${tags.namePattern}]`),
};

function segmentFor(key: typeof TAG_ORDER[number], tags: TagBag): string | null {
    return SEGMENT_BUILDERS[key](tags);
}

function kindSegment(kind: NonNullable<TagBag["kind"]>): string {
    switch (kind) {
        case "mesh":
            return "[mesh]";
        case "sprite":
            return "[sprite]";
    }
}

/** Merge a partial bag into `tags` and rewrite. Keys whose value is
 *  `undefined` in `changes` are deleted from the result, so callers
 *  can use `undefined` to clear a field. */
export function applyTagChanges(
    displayName: string,
    tags: TagBag,
    changes: Partial<TagBag>,
): string {
    const next: TagBag = { ...tags };
    for (const key of Object.keys(changes) as (keyof TagBag)[]) {
        const value = changes[key];
        if (value === undefined) {
            delete next[key];
        } else {
            (next as Record<string, unknown>)[key] = value;
        }
    }
    return writeLayerName(displayName, next);
}

/** Convenience to flip a boolean tag and rewrite. */
export function toggleTag(
    displayName: string,
    tags: TagBag,
    key: "ignore" | "merge",
    enabled: boolean,
): string {
    const next: TagBag = { ...tags };
    if (enabled) next[key] = true;
    else delete next[key];
    return writeLayerName(displayName, next);
}

/** Convenience to set / clear the element kind override. */
export function setKindTag(
    displayName: string,
    tags: TagBag,
    kind: TagBag["kind"] | undefined,
): string {
    const next: TagBag = { ...tags };
    if (kind === undefined) delete next.kind;
    else next.kind = kind;
    return writeLayerName(displayName, next);
}

/** Convenience to set / clear the blend mode tag. */
export function setBlendTag(
    displayName: string,
    tags: TagBag,
    blend: BlendMode | undefined,
): string {
    const next: TagBag = { ...tags };
    if (blend === undefined) delete next.blend;
    else next.blend = blend;
    return writeLayerName(displayName, next);
}
