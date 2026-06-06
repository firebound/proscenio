// PSD manifest v2 wire types. Re-exports of the generated bindings
// at apps/photoshop/src/schema_bindings/psd_manifest.ts under
// friendlier names the rest of the plugin already uses.
//
// json-schema-to-typescript derives interface names from the JSON
// Schema $defs (PolygonLayer, SpriteFrameLayer, FrameEntry,
// ProscenioPSDManifest); the plugin codebase historically called
// them PolygonEntry, SpriteFrameEntry, FrameEntry, Manifest. Re-export
// here so the call sites stay readable and the names survive a
// regen of the bindings file.

import type {
    ProscenioPSDManifest,
    PolygonLayer,
    SpriteFrameLayer,
    FrameEntry as GeneratedFrameEntry,
} from "../schema_bindings/psd_manifest";

export const MANIFEST_FORMAT_VERSION = 2 as const;
export const DEFAULT_PIXELS_PER_UNIT = 100 as const;

export type BlendMode = "normal" | "multiply" | "screen" | "additive";

export type FrameEntry = GeneratedFrameEntry;
export type PolygonEntry = PolygonLayer;

// The generated `Frames` type is a tuple (`[FrameEntry, FrameEntry,
// ...FrameEntry[]]`) because the JSON Schema's `minItems: 2` rule
// surfaces as a tuple in TypeScript. The plugin's planner builds the
// array dynamically and validates the length later via ajv; surface
// the field as a regular array here so call sites stay simple. The
// minItems guarantee still rides through ajv at the manifest write
// boundary.
export type SpriteFrameEntry = Omit<SpriteFrameLayer, "frames"> & {
    frames: FrameEntry[];
};
export type ManifestEntry = PolygonEntry | SpriteFrameEntry;

// Same Omit trick as SpriteFrameEntry: the generated `Layers` type
// surfaces the discriminated union as `(PolygonLayer |
// SpriteFrameLayer)[]`, but the planner builds `ManifestEntry[]`
// (which has the looser FrameEntry[] for SpriteFrameEntry). Override
// the `layers` field so call sites stay readable.
export type Manifest = Omit<ProscenioPSDManifest, "layers"> & {
    layers: ManifestEntry[];
};
