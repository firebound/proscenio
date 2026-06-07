// PSD manifest wire types. Re-exports of the generated bindings
// at apps/photoshop/src/schema_bindings/psd_manifest.ts under
// friendlier names the rest of the plugin already uses.
//
// json-schema-to-typescript derives interface names from the JSON
// Schema $defs (MeshLayer, SpriteLayer, FrameEntry,
// ProscenioPSDManifest); the plugin codebase calls them MeshEntry,
// SpriteEntry, FrameEntry, Manifest. Re-export here so the call sites
// stay readable and the names survive a regen of the bindings file.

import type {
    ProscenioPSDManifest,
    MeshLayer,
    SpriteLayer,
    FrameEntry as GeneratedFrameEntry,
} from "../schema_bindings/psd_manifest";

export const MANIFEST_FORMAT_VERSION = 1 as const;
export const DEFAULT_PIXELS_PER_UNIT = 100 as const;

export type BlendMode = "normal" | "multiply" | "screen" | "additive";

export type FrameEntry = GeneratedFrameEntry;
export type MeshEntry = MeshLayer;

// The generated `Frames` type is a non-empty tuple (`[FrameEntry,
// ...FrameEntry[]]`) because the JSON Schema's `minItems: 1` rule
// surfaces as a tuple in TypeScript. The plugin's planner builds the
// array dynamically and validates the length later via ajv; surface
// the field as a regular array here so call sites stay simple.
export type SpriteEntry = Omit<SpriteLayer, "frames"> & {
    frames: FrameEntry[];
};
export type ManifestEntry = MeshEntry | SpriteEntry;

// Same Omit trick as SpriteEntry: the generated `Layers` type
// surfaces the discriminated union as `(MeshLayer | SpriteLayer)[]`,
// but the planner builds `ManifestEntry[]` (which has the looser
// FrameEntry[] for SpriteEntry). Override the `layers` field so call
// sites stay readable.
export type Manifest = Omit<ProscenioPSDManifest, "layers"> & {
    layers: ManifestEntry[];
};
