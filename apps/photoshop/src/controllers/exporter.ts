// Pure manifest builder. Mirrors `apps/photoshop/proscenio_export.jsx`
// semantics in TypeScript, decoupled from the Photoshop API surface so
// it can be unit-tested against synthetic layer trees.
//
// `buildExportPlan` returns the manifest plus a parallel list of PNG
// writes - each one carries the chain of layer names from the document
// root down to the source art layer. The Photoshop adapter walks that
// chain in the live PsDocument to find the layer to duplicate + save.
// Keeping the chain out of the manifest itself preserves the v1
// contract while letting the materialiser stay declarative.
//
// Convention parity with the JSX exporter:
//
// - Hidden layers and `_`-prefixed names are skipped when the matching
//   option is set (`skipHidden` / `skipUnderscorePrefix`).
// - A LayerSet whose visible non-set children all match a uniform
//   indexed-frame convention (digits, `frame_<n>`, or `<base>_<n>`)
//   collapses into a single `sprite_frame` entry. Sprite-frame child
//   filtering ignores the `skipUnderscorePrefix` toggle - it is always
//   on inside a frame group, otherwise users would lose `_underscore`
//   helper frames silently.
// - Top-level siblings matching the flat `<base>_<n>` convention are
//   aggregated post-walk via `aggregateFlatSpriteFrames` (D9 fallback
//   for authors who do not nest their frames in a group).
// - Names join through groups with `__`. The manifest entry `name`
//   keeps the joined human form; `path` uses the sanitized form.

import type { ArtLayer, Layer, LayerBounds, LayerSet } from "../types/layer";
import {
    DEFAULT_PIXELS_PER_UNIT,
    MANIFEST_FORMAT_VERSION,
    type FrameEntry,
    type Manifest,
    type ManifestEntry,
    type PolygonEntry,
    type SpriteFrameEntry,
} from "../types/manifest";

export interface ExportOptions {
    skipHidden: boolean;
    skipUnderscorePrefix: boolean;
    pixelsPerUnit?: number;
}

export interface DocumentInfo {
    name: string;
    width: number;
    height: number;
}

// One PNG the materialiser must write. `layerPath` is the chain of
// layer names from the document root down to the leaf art layer
// (e.g. ["body", "upper", "torso"]); the adapter walks this in the
// live PsDocument to find the source layer. `outputPath` is the
// manifest-relative path the materialiser writes to - matches the
// `path` field on the corresponding polygon or frame entry.
export interface PngWrite {
    layerPath: string[];
    outputPath: string;
}

export interface ExportPlan {
    manifest: Manifest;
    writes: PngWrite[];
}

export function buildManifest(
    doc: DocumentInfo,
    layers: Layer[],
    opts: ExportOptions,
): Manifest {
    return buildExportPlan(doc, layers, opts).manifest;
}

export function buildExportPlan(
    doc: DocumentInfo,
    layers: Layer[],
    opts: ExportOptions,
): ExportPlan {
    const planned: PlannedEntry[] = [];
    const zCounter = { value: 0 };
    walkLayers(layers, "", [], planned, zCounter, opts);
    const aggregated = aggregateFlatSpriteFrames(planned);
    const manifest: Manifest = {
        format_version: MANIFEST_FORMAT_VERSION,
        doc: doc.name,
        size: [doc.width, doc.height],
        pixels_per_unit: opts.pixelsPerUnit ?? DEFAULT_PIXELS_PER_UNIT,
        layers: aggregated.map(toManifestEntry),
    };
    const writes = aggregated.flatMap(toWrites);
    return { manifest, writes };
}

// Planner-internal entry. Mirrors the manifest entry shape but keeps
// the source `layerPath` for each PNG so the materialiser can map back
// to the live PsLayer. Stripped at the manifest boundary - never
// serialised.
type PlannedPolygon = PolygonEntry & { _layerPath: string[] };
type PlannedSpriteFrame = SpriteFrameEntry & { _frameSources: string[][] };
type PlannedEntry = PlannedPolygon | PlannedSpriteFrame;

function toManifestEntry(entry: PlannedEntry): ManifestEntry {
    if (entry.kind === "polygon") {
        return {
            kind: "polygon",
            name: entry.name,
            path: entry.path,
            position: entry.position,
            size: entry.size,
            z_order: entry.z_order,
        };
    }
    return {
        kind: "sprite_frame",
        name: entry.name,
        position: entry.position,
        size: entry.size,
        z_order: entry.z_order,
        frames: entry.frames,
    };
}

function toWrites(entry: PlannedEntry): PngWrite[] {
    if (entry.kind === "polygon") {
        return [{ layerPath: entry._layerPath, outputPath: entry.path }];
    }
    return entry.frames.map((frame, i) => ({
        layerPath: entry._frameSources[i],
        outputPath: frame.path,
    }));
}

function walkLayers(
    layers: Layer[],
    prefix: string,
    layerPath: string[],
    out: PlannedEntry[],
    zCounter: { value: number },
    opts: ExportOptions,
): void {
    for (const layer of layers) {
        if (opts.skipHidden && !layer.visible) continue;
        if (opts.skipUnderscorePrefix && layer.name.charAt(0) === "_") continue;
        const childLayerPath = [...layerPath, layer.name];
        if (layer.kind === "set") {
            if (qualifiesAsSpriteFrameGroup(layer)) {
                const entry = buildSpriteFrameEntry(layer, prefix, childLayerPath, zCounter.value);
                if (entry !== null) {
                    out.push(entry);
                    zCounter.value += 1;
                }
                continue;
            }
            const nested = prefix === "" ? layer.name : `${prefix}__${layer.name}`;
            walkLayers(layer.layers, nested, childLayerPath, out, zCounter, opts);
            continue;
        }
        const name = prefix === "" ? layer.name : `${prefix}__${layer.name}`;
        const poly = buildPolygonEntry(layer, name, childLayerPath, zCounter.value);
        if (poly !== null) {
            out.push(poly);
            zCounter.value += 1;
        }
    }
}

export function qualifiesAsSpriteFrameGroup(group: LayerSet): boolean {
    const visibleChildren: ArtLayer[] = [];
    for (const child of group.layers) {
        if (!child.visible) continue;
        if (child.name.charAt(0) === "_") continue;
        if (child.kind === "set") return false;
        visibleChildren.push(child);
    }
    if (visibleChildren.length < 2) return false;

    let convention: FrameConvention | null = null;
    let sharedBase: string | null = null;
    const indices: number[] = [];
    for (const child of visibleChildren) {
        const match = matchIndexedFrame(child.name);
        if (match === null) return false;
        if (convention === null) {
            convention = match.convention;
            sharedBase = match.base;
        } else if (convention !== match.convention) {
            return false;
        } else if (sharedBase !== match.base) {
            return false;
        }
        indices.push(match.index);
    }
    return indicesAreContiguousFromZero(indices);
}

function buildSpriteFrameEntry(
    group: LayerSet,
    prefix: string,
    groupLayerPath: string[],
    zOrder: number,
): PlannedSpriteFrame | null {
    const pairs: { index: number; layer: ArtLayer }[] = [];
    for (const child of group.layers) {
        if (!child.visible) continue;
        if (child.name.charAt(0) === "_") continue;
        if (child.kind !== "art") continue;
        const match = matchIndexedFrame(child.name);
        if (match === null) continue;
        pairs.push({ index: match.index, layer: child });
    }
    pairs.sort((a, b) => a.index - b.index);

    const meshName = prefix === "" ? group.name : `${prefix}__${group.name}`;
    const safeName = sanitize(meshName);

    let maxBounds: LayerBounds | null = null;
    const frames: FrameEntry[] = [];
    const sources: string[][] = [];
    for (const pair of pairs) {
        const b = pair.layer.bounds;
        if (b === null || b.w <= 0 || b.h <= 0) continue;
        if (maxBounds === null || b.w * b.h > maxBounds.w * maxBounds.h) {
            maxBounds = b;
        }
        frames.push({
            index: pair.index,
            path: `images/${safeName}/${pair.index}.png`,
        });
        sources.push([...groupLayerPath, pair.layer.name]);
    }
    if (maxBounds === null || frames.length < 2) return null;
    return {
        kind: "sprite_frame",
        name: meshName,
        position: [Math.round(maxBounds.x), Math.round(maxBounds.y)],
        size: [Math.round(maxBounds.w), Math.round(maxBounds.h)],
        z_order: zOrder,
        frames,
        _frameSources: sources,
    };
}

function buildPolygonEntry(
    layer: ArtLayer,
    name: string,
    layerPath: string[],
    zOrder: number,
): PlannedPolygon | null {
    const b = layer.bounds;
    if (b === null || b.w <= 0 || b.h <= 0) return null;
    const safeName = sanitize(name);
    return {
        kind: "polygon",
        name,
        path: `images/${safeName}.png`,
        position: [Math.round(b.x), Math.round(b.y)],
        size: [Math.round(b.w), Math.round(b.h)],
        z_order: zOrder,
        _layerPath: layerPath,
    };
}

export type FrameConvention = "digit" | "frame_prefix" | "group_prefix";

export interface FrameMatch {
    convention: FrameConvention;
    base: string;
    index: number;
}

// Mirrors apps/blender/core/psd_naming.py:match_indexed_frame.
export function matchIndexedFrame(name: string): FrameMatch | null {
    const pure = /^(\d+)$/.exec(name);
    if (pure !== null) {
        return { convention: "digit", base: "", index: Number.parseInt(pure[1], 10) };
    }
    const framed = /^frame[_-](\d+)$/i.exec(name);
    if (framed !== null) {
        return { convention: "frame_prefix", base: "", index: Number.parseInt(framed[1], 10) };
    }
    const grouped = /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(name);
    if (grouped !== null) {
        return {
            convention: "group_prefix",
            base: grouped[1],
            index: Number.parseInt(grouped[2], 10),
        };
    }
    return null;
}

export function indicesAreContiguousFromZero(indices: number[]): boolean {
    if (indices.length === 0) return false;
    const sorted = [...indices].sort((a, b) => a - b);
    for (let i = 0; i < sorted.length; i++) {
        if (sorted[i] !== i) return false;
    }
    return true;
}

// Post-walk pass: collapse top-level polygons whose names follow the
// flat `<base>_<n>` convention into a single sprite_frame entry. D9
// fallback for users who do not nest frames in a group.
function aggregateFlatSpriteFrames(input: PlannedEntry[]): PlannedEntry[] {
    const { leftover, buckets } = bucketize(input);
    for (const [base, pairs] of buckets) {
        const merged = mergeFlatBucket(base, pairs);
        if (merged.kind === "merged") {
            leftover.push(merged.entry);
        } else {
            for (const p of merged.pairs) leftover.push(p.entry);
        }
    }
    leftover.sort((a, b) => a.z_order - b.z_order);
    for (let i = 0; i < leftover.length; i++) leftover[i].z_order = i;
    return leftover;
}

interface BucketPair {
    index: number;
    entry: PlannedPolygon;
}

function bucketize(input: PlannedEntry[]): {
    leftover: PlannedEntry[];
    buckets: Map<string, BucketPair[]>;
} {
    const buckets = new Map<string, BucketPair[]>();
    const leftover: PlannedEntry[] = [];
    for (const entry of input) {
        const match = entry.kind === "polygon"
            ? /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(entry.name)
            : null;
        if (entry.kind !== "polygon" || match === null) {
            leftover.push(entry);
            continue;
        }
        const base = match[1];
        const idx = Number.parseInt(match[2], 10);
        const list = buckets.get(base);
        if (list === undefined) buckets.set(base, [{ index: idx, entry }]);
        else list.push({ index: idx, entry });
    }
    return { leftover, buckets };
}

type MergeResult =
    | { kind: "merged"; entry: PlannedSpriteFrame }
    | { kind: "kept"; pairs: BucketPair[] };

function mergeFlatBucket(base: string, pairs: BucketPair[]): MergeResult {
    if (pairs.length < 2) return { kind: "kept", pairs };
    pairs.sort((a, b) => a.index - b.index);
    const indices = pairs.map((p) => p.index);
    if (!indicesAreContiguousFromZero(indices)) return { kind: "kept", pairs };
    const merged = packFrames(base, pairs);
    if (merged === null) return { kind: "kept", pairs };
    return { kind: "merged", entry: merged };
}

function packFrames(base: string, pairs: BucketPair[]): PlannedSpriteFrame | null {
    let maxBounds: { x: number; y: number; w: number; h: number } | null = null;
    const frames: FrameEntry[] = [];
    const sources: string[][] = [];
    for (const p of pairs) {
        const e = p.entry;
        const [w, h] = e.size;
        if (maxBounds === null || w * h > maxBounds.w * maxBounds.h) {
            maxBounds = { x: e.position[0], y: e.position[1], w, h };
        }
        frames.push({ index: p.index, path: e.path });
        sources.push(e._layerPath);
    }
    if (maxBounds === null) return null;
    return {
        kind: "sprite_frame",
        name: base,
        position: [maxBounds.x, maxBounds.y],
        size: [maxBounds.w, maxBounds.h],
        z_order: pairs[0].entry.z_order,
        frames,
        _frameSources: sources,
    };
}

export function sanitize(name: string): string {
    return String(name).replace(/[^A-Za-z0-9_\-]/g, "_");
}
