// Pure manifest builder. Mirrors `apps/photoshop/proscenio_export.jsx`
// semantics in TypeScript, decoupled from the Photoshop API surface so
// it can be unit-tested against synthetic layer trees.
//
// Wave 10.3 will add the Photoshop -> Layer adapter and the PNG writer
// that materialises the paths emitted by `buildManifest`. The paths in
// the manifest are deterministic functions of the (sanitized) entry
// name, so the writer can drive its filesystem layout straight from
// the manifest produced here.
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

export function buildManifest(
    doc: DocumentInfo,
    layers: Layer[],
    opts: ExportOptions,
): Manifest {
    const out: ManifestEntry[] = [];
    const zCounter = { value: 0 };
    walkLayers(layers, "", out, zCounter, opts);
    const aggregated = aggregateFlatSpriteFrames(out);
    return {
        format_version: MANIFEST_FORMAT_VERSION,
        doc: doc.name,
        size: [doc.width, doc.height],
        pixels_per_unit: opts.pixelsPerUnit ?? DEFAULT_PIXELS_PER_UNIT,
        layers: aggregated,
    };
}

function walkLayers(
    layers: Layer[],
    prefix: string,
    out: ManifestEntry[],
    zCounter: { value: number },
    opts: ExportOptions,
): void {
    for (const layer of layers) {
        if (opts.skipHidden && !layer.visible) continue;
        if (opts.skipUnderscorePrefix && layer.name.charAt(0) === "_") continue;
        if (layer.kind === "set") {
            if (qualifiesAsSpriteFrameGroup(layer)) {
                const entry = buildSpriteFrameEntry(layer, prefix, zCounter.value);
                if (entry !== null) {
                    out.push(entry);
                    zCounter.value += 1;
                }
                continue;
            }
            const nested = prefix === "" ? layer.name : `${prefix}__${layer.name}`;
            walkLayers(layer.layers, nested, out, zCounter, opts);
            continue;
        }
        const name = prefix === "" ? layer.name : `${prefix}__${layer.name}`;
        const poly = buildPolygonEntry(layer, name, zCounter.value);
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
    zOrder: number,
): SpriteFrameEntry | null {
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
    }
    if (maxBounds === null || frames.length < 2) return null;
    return {
        kind: "sprite_frame",
        name: meshName,
        position: [Math.round(maxBounds.x), Math.round(maxBounds.y)],
        size: [Math.round(maxBounds.w), Math.round(maxBounds.h)],
        z_order: zOrder,
        frames,
    };
}

function buildPolygonEntry(
    layer: ArtLayer,
    name: string,
    zOrder: number,
): PolygonEntry | null {
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
        return { convention: "digit", base: "", index: parseInt(pure[1], 10) };
    }
    const framed = /^frame[_-](\d+)$/i.exec(name);
    if (framed !== null) {
        return { convention: "frame_prefix", base: "", index: parseInt(framed[1], 10) };
    }
    const grouped = /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(name);
    if (grouped !== null) {
        return {
            convention: "group_prefix",
            base: grouped[1],
            index: parseInt(grouped[2], 10),
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
export function aggregateFlatSpriteFrames(input: ManifestEntry[]): ManifestEntry[] {
    const bucket = new Map<string, { index: number; entry: PolygonEntry }[]>();
    const leftover: ManifestEntry[] = [];
    for (const entry of input) {
        if (entry.kind !== "polygon") {
            leftover.push(entry);
            continue;
        }
        const match = /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(entry.name);
        if (match === null) {
            leftover.push(entry);
            continue;
        }
        const base = match[1];
        const idx = parseInt(match[2], 10);
        const list = bucket.get(base);
        if (list === undefined) {
            bucket.set(base, [{ index: idx, entry }]);
        } else {
            list.push({ index: idx, entry });
        }
    }
    for (const [base, pairs] of bucket) {
        if (pairs.length < 2) {
            for (const p of pairs) leftover.push(p.entry);
            continue;
        }
        pairs.sort((a, b) => a.index - b.index);
        const indices = pairs.map((p) => p.index);
        if (!indicesAreContiguousFromZero(indices)) {
            for (const p of pairs) leftover.push(p.entry);
            continue;
        }
        let maxBounds: { x: number; y: number; w: number; h: number } | null = null;
        const frames: FrameEntry[] = [];
        const zOrder = pairs[0].entry.z_order;
        for (const p of pairs) {
            const e = p.entry;
            const w = e.size[0];
            const h = e.size[1];
            if (maxBounds === null || w * h > maxBounds.w * maxBounds.h) {
                maxBounds = { x: e.position[0], y: e.position[1], w, h };
            }
            frames.push({ index: p.index, path: e.path });
        }
        if (maxBounds === null) continue;
        leftover.push({
            kind: "sprite_frame",
            name: base,
            position: [maxBounds.x, maxBounds.y],
            size: [maxBounds.w, maxBounds.h],
            z_order: zOrder,
            frames,
        });
    }
    leftover.sort((a, b) => a.z_order - b.z_order);
    for (let i = 0; i < leftover.length; i++) leftover[i].z_order = i;
    return leftover;
}

export function sanitize(name: string): string {
    return String(name).replace(/[^A-Za-z0-9_\-]/g, "_");
}
