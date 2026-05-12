// Pure manifest builder (SPEC 011 v2).
//
// Drives the layer walk through the bracket-tag parser:
//
// - `[ignore]` removes a layer / group from the export.
// - `[spritesheet]` marks a group as a sprite_frame source explicitly;
//   auto-detection still triggers for groups whose children are all
//   pure digits (`0`, `1`, ...).
// - `[polygon]` / `[sprite]` / `[mesh]` override `kind` on the entry.
// - `[folder:name]` and `[path:name]` rewrite the on-disk PNG path.
// - `[scale:n]` rescales the bounds before they reach the manifest.
// - `[blend:mode]` writes the v2 `blend_mode` field.
// - `[origin:x,y]` sets an explicit pivot in PSD pixels.
//
// The legacy v1 paths are gone (no `_` prefix skip, no flat
// `<base>_<index>` sprite_frame aggregation). Buildchain tested
// against the synthetic Layer fixture set in
// `uxp-plugin-tests/planner.test.ts`.

import type { Layer, LayerBounds, LayerSet } from "./layer";
import {
    DEFAULT_PIXELS_PER_UNIT,
    MANIFEST_FORMAT_VERSION,
    type BlendMode,
    type FrameEntry,
    type Manifest,
    type ManifestEntry,
    type PolygonEntry,
    type SpriteFrameEntry,
} from "./manifest";
import { parseLayerName, type TagBag } from "./tag-parser";

export interface ExportOptions {
    skipHidden: boolean;
    pixelsPerUnit?: number;
    anchor?: [number, number];
}

export interface DocumentInfo {
    name: string;
    width: number;
    height: number;
}

export interface PngWrite {
    layerPath: string[];
    outputPath: string;
    /** When true, the resolved layer is a `[merge]` group and the
     *  materialiser flattens its descendants into one PNG. */
    merge?: boolean;
}

export interface ExportPlan {
    manifest: Manifest;
    writes: PngWrite[];
}

interface ParsedLayer {
    raw: Layer;
    displayName: string;
    tags: TagBag;
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
    walkLayers(parseChildren(layers), "", [], planned, zCounter, opts);
    const manifest: Manifest = {
        format_version: MANIFEST_FORMAT_VERSION,
        doc: doc.name,
        size: [doc.width, doc.height],
        pixels_per_unit: opts.pixelsPerUnit ?? DEFAULT_PIXELS_PER_UNIT,
        ...(opts.anchor === undefined ? {} : { anchor: opts.anchor }),
        layers: planned.map(toManifestEntry),
    };
    return { manifest, writes: planned.flatMap(toWrites) };
}

interface PngWriteSource {
    layerPath: string[];
    merge: boolean;
}
type PlannedPolygon = PolygonEntry & { _source: PngWriteSource };
type PlannedSpriteFrame = SpriteFrameEntry & { _frameSources: PngWriteSource[] };
type PlannedEntry = PlannedPolygon | PlannedSpriteFrame;

function parseChildren(children: Layer[]): ParsedLayer[] {
    return children.map((raw) => {
        const parsed = parseLayerName(raw.name);
        return { raw, displayName: parsed.displayName, tags: parsed.tags };
    });
}

// Tags inherited from ancestor groups onto descendants. `[folder]`
// and `[blend]` on a group apply to every descendant unless that
// descendant declares its own override. Local tags on the child
// always win.
interface InheritedTags {
    folder?: string;
    blend?: BlendMode;
}

function inherit(parent: InheritedTags, child: TagBag): InheritedTags {
    return {
        folder: child.folder ?? parent.folder,
        blend: child.blend ?? parent.blend,
    };
}

function walkLayers(
    children: ParsedLayer[],
    prefix: string,
    layerPath: string[],
    out: PlannedEntry[],
    zCounter: { value: number },
    opts: ExportOptions,
    inherited: InheritedTags = {},
): void {
    for (const parsed of children) {
        if (parsed.tags.ignore === true) continue;
        if (opts.skipHidden && !parsed.raw.visible) continue;
        const childPath = [...layerPath, parsed.raw.name];
        if (parsed.raw.kind === "set") {
            handleGroup(parsed, prefix, childPath, out, zCounter, opts, inherited);
            continue;
        }
        if (parsed.tags.originMarker === true) continue;
        const entry = buildPolygonEntry(
            parsed,
            joinName(prefix, fallbackName(parsed.displayName, parsed.raw)),
            childPath,
            zCounter.value,
            inherit(inherited, parsed.tags),
        );
        if (entry !== null) {
            out.push(entry);
            zCounter.value += 1;
        }
    }
}

function handleGroup(
    parsed: ParsedLayer,
    prefix: string,
    layerPath: string[],
    out: PlannedEntry[],
    zCounter: { value: number },
    opts: ExportOptions,
    inherited: InheritedTags,
): void {
    const group = parsed.raw as LayerSet;
    const parsedChildren = parseChildren(group.layers);
    const tagKind = parsed.tags.kind;
    const explicitSpriteFrame = tagKind === "sprite_frame";
    const groupInherited = inherit(inherited, parsed.tags);

    if (explicitSpriteFrame || (tagKind === undefined && autoDetectSpriteFrame(parsedChildren))) {
        const entry = buildSpriteFrameEntry(
            parsed,
            parsedChildren,
            prefix,
            layerPath,
            zCounter.value,
            groupInherited,
        );
        if (entry !== null) {
            out.push(entry);
            zCounter.value += 1;
            return;
        }
    }
    // `[merge]` on a non-sprite_frame group flattens its descendants
    // into a single polygon entry (the writer composes the PNG by
    // duplicating the group into a temp doc and merging it).
    if (parsed.tags.merge === true) {
        const entry = buildPolygonEntry(
            parsed,
            joinName(prefix, fallbackName(parsed.displayName, parsed.raw)),
            layerPath,
            zCounter.value,
            groupInherited,
        );
        if (entry !== null) {
            out.push(entry);
            zCounter.value += 1;
            return;
        }
    }
    const nested = joinName(prefix, parsed.displayName);
    walkLayers(parsedChildren, nested, layerPath, out, zCounter, opts, groupInherited);
}

function autoDetectSpriteFrame(children: ParsedLayer[]): boolean {
    const candidates: ParsedLayer[] = [];
    for (const child of children) {
        if (child.tags.ignore === true) continue;
        if (!child.raw.visible) continue;
        if (child.tags.originMarker === true) continue;
        // A child is a valid frame source if it is either an art
        // layer with a digit name, or a `[merge]` group with a digit
        // name. Non-merge groups (regular nesting) disqualify.
        if (child.raw.kind === "set" && child.tags.merge !== true) return false;
        candidates.push(child);
    }
    if (candidates.length < 2) return false;
    const indices: number[] = [];
    for (const child of candidates) {
        const match = /^(\d+)$/.exec(child.displayName);
        if (match === null) return false;
        indices.push(Number.parseInt(match[1], 10));
    }
    return indicesAreContiguousFromZero(indices);
}

function buildSpriteFrameEntry(
    group: ParsedLayer,
    children: ParsedLayer[],
    prefix: string,
    layerPath: string[],
    zOrder: number,
    inherited: InheritedTags,
): PlannedSpriteFrame | null {
    const meshName = joinName(prefix, fallbackName(group.displayName, group.raw));
    const folder = group.tags.folder ?? inherited.folder;
    const blend = group.tags.blend ?? inherited.blend;
    const safeName = group.tags.path ?? sanitize(meshName);
    const dirPath = folder === undefined ? `images/${safeName}` : `images/${sanitize(folder)}/${safeName}`;

    const sortedFrames = collectFrameChildren(children);
    if (sortedFrames.length < 2) return null;

    let maxBounds: LayerBounds | null = null;
    const frames: FrameEntry[] = [];
    const sources: PngWriteSource[] = [];
    for (const child of sortedFrames) {
        const bounds = scaledBounds(effectiveBounds(child), child.tags.scale);
        if (bounds === null) continue;
        if (maxBounds === null || bounds.w * bounds.h > maxBounds.w * maxBounds.h) {
            maxBounds = bounds;
        }
        const index = frameIndex(child.displayName);
        frames.push({ index, path: `${dirPath}/${index}.png` });
        sources.push({
            layerPath: [...layerPath, child.raw.name],
            merge: child.tags.merge === true,
        });
    }
    if (maxBounds === null || frames.length < 2) return null;

    const originFromMarker = pickOriginMarker(children);
    return {
        kind: "sprite_frame",
        name: meshName,
        position: [Math.round(maxBounds.x), Math.round(maxBounds.y)],
        size: [Math.round(maxBounds.w), Math.round(maxBounds.h)],
        z_order: zOrder,
        frames,
        ...optionalOrigin(group.tags.origin ?? originFromMarker),
        ...optionalBlend(blend),
        ...(folder === undefined ? {} : { subfolder: folder }),
        _frameSources: sources,
    };
}

function collectFrameChildren(children: ParsedLayer[]): ParsedLayer[] {
    const pairs: { index: number; child: ParsedLayer }[] = [];
    for (const child of children) {
        if (child.tags.ignore === true) continue;
        if (!child.raw.visible) continue;
        if (child.tags.originMarker === true) continue;
        // Accept art layers OR `[merge]` groups; reject regular groups.
        if (child.raw.kind === "set" && child.tags.merge !== true) continue;
        const idx = frameIndex(child.displayName);
        if (Number.isNaN(idx)) continue;
        pairs.push({ index: idx, child });
    }
    pairs.sort((a, b) => a.index - b.index);
    return pairs.map((p) => p.child);
}

// Effective bounds for a frame source: the layer's own bbox for art
// layers; the union of visible art descendants for `[merge]` groups.
function effectiveBounds(parsed: ParsedLayer): LayerBounds | null {
    if (parsed.raw.kind === "art") return parsed.raw.bounds;
    if (parsed.tags.merge === true) return unionArtBounds(parsed.raw);
    return null;
}

function unionArtBounds(set: LayerSet): LayerBounds | null {
    let minX = Number.POSITIVE_INFINITY;
    let minY = Number.POSITIVE_INFINITY;
    let maxX = Number.NEGATIVE_INFINITY;
    let maxY = Number.NEGATIVE_INFINITY;
    let any = false;
    const visit = (layer: Layer): void => {
        if (!layer.visible) return;
        if (layer.kind === "art") {
            const b = layer.bounds;
            if (b === null || b.w <= 0 || b.h <= 0) return;
            any = true;
            minX = Math.min(minX, b.x);
            minY = Math.min(minY, b.y);
            maxX = Math.max(maxX, b.x + b.w);
            maxY = Math.max(maxY, b.y + b.h);
            return;
        }
        for (const child of layer.layers) visit(child);
    };
    for (const child of set.layers) visit(child);
    if (!any) return null;
    return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function frameIndex(name: string): number {
    const match = /^(\d+)$/.exec(name);
    return match === null ? Number.NaN : Number.parseInt(match[1], 10);
}

function pickOriginMarker(children: ParsedLayer[]): [number, number] | undefined {
    for (const child of children) {
        if (child.tags.originMarker !== true) continue;
        const layer = child.raw;
        if (layer.kind !== "art") continue;
        const bounds = layer.bounds;
        if (bounds === null) continue;
        return [Math.round(bounds.x + bounds.w / 2), Math.round(bounds.y + bounds.h / 2)];
    }
    return undefined;
}

function buildPolygonEntry(
    source: ParsedLayer,
    name: string,
    layerPath: string[],
    zOrder: number,
    inherited: InheritedTags,
): PlannedPolygon | null {
    const bounds = scaledBounds(effectiveBounds(source), source.tags.scale);
    if (bounds === null) return null;
    const folder = inherited.folder;
    const blend = inherited.blend;
    const safeName = source.tags.path ?? sanitize(name);
    const path = folder === undefined ? `images/${safeName}.png` : `images/${sanitize(folder)}/${safeName}.png`;
    const kind: "polygon" | "mesh" = source.tags.kind === "mesh" ? "mesh" : "polygon";
    // For `[merge]` groups, an inner `[origin]` marker layer provides
    // the pivot when no explicit `[origin:x,y]` is set on the group.
    const originFromMarker = source.raw.kind === "set"
        ? pickOriginMarker(parseChildren(source.raw.layers))
        : undefined;
    return {
        kind,
        name,
        path,
        position: [Math.round(bounds.x), Math.round(bounds.y)],
        size: [Math.round(bounds.w), Math.round(bounds.h)],
        z_order: zOrder,
        ...optionalOrigin(source.tags.origin ?? originFromMarker),
        ...optionalBlend(blend),
        ...(folder === undefined ? {} : { subfolder: folder }),
        _source: {
            layerPath,
            merge: source.tags.merge === true,
        },
    };
}

function scaledBounds(bounds: LayerBounds | null, scale: number | undefined): LayerBounds | null {
    if (bounds === null || bounds.w <= 0 || bounds.h <= 0) return null;
    if (scale === undefined || scale === 1) return bounds;
    return {
        x: bounds.x * scale,
        y: bounds.y * scale,
        w: bounds.w * scale,
        h: bounds.h * scale,
    };
}

function optionalOrigin(origin: [number, number] | undefined): { origin?: [number, number] } {
    if (origin === undefined) return {};
    return { origin: [Math.round(origin[0]), Math.round(origin[1])] };
}

function optionalBlend(blend: BlendMode | undefined): { blend_mode?: BlendMode } {
    return blend === undefined ? {} : { blend_mode: blend };
}

function joinName(prefix: string, name: string): string {
    // Empty parts (layer / group named only with bracket tags, e.g.
    // `[spritesheet]`) are skipped: the chain just inherits its
    // parent's prefix so children do not pick up an empty segment.
    if (name === "") return prefix;
    if (prefix === "") return name;
    return `${prefix}__${name}`;
}

function fallbackName(displayName: string, raw: Layer): string {
    // Last-ditch guard for manifest entries: when a leaf or group is
    // named only with bracket tags, the display name strips to "" and
    // would violate the schema's `minLength: 1` on `name`. Falling
    // back to the raw (still-bracketed) name keeps the entry valid and
    // makes the issue visible to the artist - the brackets show up in
    // the importer too.
    return displayName.length > 0 ? displayName : raw.name;
}

function toManifestEntry(entry: PlannedEntry): ManifestEntry {
    if (entry.kind === "sprite_frame") {
        return {
            kind: "sprite_frame",
            name: entry.name,
            position: entry.position,
            size: entry.size,
            z_order: entry.z_order,
            frames: entry.frames,
            ...(entry.origin === undefined ? {} : { origin: entry.origin }),
            ...(entry.blend_mode === undefined ? {} : { blend_mode: entry.blend_mode }),
            ...(entry.subfolder === undefined ? {} : { subfolder: entry.subfolder }),
        };
    }
    return {
        kind: entry.kind,
        name: entry.name,
        path: entry.path,
        position: entry.position,
        size: entry.size,
        z_order: entry.z_order,
        ...(entry.origin === undefined ? {} : { origin: entry.origin }),
        ...(entry.blend_mode === undefined ? {} : { blend_mode: entry.blend_mode }),
        ...(entry.subfolder === undefined ? {} : { subfolder: entry.subfolder }),
    };
}

function toWrites(entry: PlannedEntry): PngWrite[] {
    if (entry.kind === "sprite_frame") {
        return entry.frames.map((frame, i) => ({
            layerPath: entry._frameSources[i].layerPath,
            outputPath: frame.path,
            ...(entry._frameSources[i].merge ? { merge: true } : {}),
        }));
    }
    return [{
        layerPath: entry._source.layerPath,
        outputPath: entry.path,
        ...(entry._source.merge ? { merge: true } : {}),
    }];
}

export function indicesAreContiguousFromZero(indices: number[]): boolean {
    if (indices.length === 0) return false;
    const sorted = [...indices].sort((a, b) => a - b);
    for (let i = 0; i < sorted.length; i++) {
        if (sorted[i] !== i) return false;
    }
    return true;
}

export function sanitize(name: string): string {
    return String(name).replace(/[^A-Za-z0-9_\-]/g, "_");
}
