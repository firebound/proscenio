// v2 manifest shape (SPEC 011). Mirrors `schemas/psd_manifest.schema.json`.
//
// v2 adds the tag-driven taxonomy: top-level `anchor` from PSD guides;
// per-entry `origin`, `blend_mode`, `subfolder`; `kind: "mesh"` is a
// polygon superset (deformable hint). The legacy `_<name>` skip and
// the flat `<base>_<index>` sprite_frame fallback are gone - bracket
// tags own the authoring story.

export const MANIFEST_FORMAT_VERSION = 2 as const;
export const DEFAULT_PIXELS_PER_UNIT = 100 as const;

export type BlendMode = "normal" | "multiply" | "screen" | "additive";

export interface PolygonEntry {
    kind: "polygon" | "mesh";
    name: string;
    path: string;
    position: [number, number];
    size: [number, number];
    z_order: number;
    origin?: [number, number];
    blend_mode?: BlendMode;
    subfolder?: string;
}

export interface FrameEntry {
    index: number;
    path: string;
}

export interface SpriteFrameEntry {
    kind: "sprite_frame";
    name: string;
    position: [number, number];
    size: [number, number];
    z_order: number;
    frames: FrameEntry[];
    origin?: [number, number];
    blend_mode?: BlendMode;
    subfolder?: string;
}

export type ManifestEntry = PolygonEntry | SpriteFrameEntry;

export interface Manifest {
    format_version: typeof MANIFEST_FORMAT_VERSION;
    doc: string;
    size: [number, number];
    pixels_per_unit: number;
    anchor?: [number, number];
    layers: ManifestEntry[];
}
