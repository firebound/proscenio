// v1 manifest shape. Mirrors the contract documented in
// `apps/photoshop/proscenio_export.jsx` (and consumed by the Blender
// importer in SPEC 006). A standalone `psd_manifest.schema.json` for
// ajv validation lands in Wave 10.3.

export const MANIFEST_FORMAT_VERSION = 1 as const;
export const DEFAULT_PIXELS_PER_UNIT = 100 as const;

export interface PolygonEntry {
    kind: "polygon";
    name: string;
    path: string;
    position: [number, number];
    size: [number, number];
    z_order: number;
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
}

export type ManifestEntry = PolygonEntry | SpriteFrameEntry;

export interface Manifest {
    format_version: typeof MANIFEST_FORMAT_VERSION;
    doc: string;
    size: [number, number];
    pixels_per_unit: number;
    layers: ManifestEntry[];
}
