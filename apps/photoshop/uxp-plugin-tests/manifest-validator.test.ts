// ajv contract test for v1 PSD manifest. Mirrors the schema at the
// repo root so any breaking change to the contract fails here before
// the Blender importer breaks.

import { describe, expect, it } from "vitest";

import { buildManifest } from "../src/controllers/exporter";
import { validateManifest } from "../src/io/manifest-validator";
import type { Layer } from "../src/types/layer";
import type { Manifest } from "../src/types/manifest";

const doc = { name: "fixture.psd", width: 256, height: 256 };
const fullOpts = { skipHidden: true, skipUnderscorePrefix: true };

describe("validateManifest", () => {
    it("accepts a manifest produced by buildManifest", () => {
        const layers: Layer[] = [
            { kind: "art", name: "square", visible: true, bounds: { x: 16, y: 32, w: 64, h: 64 } },
            {
                kind: "set",
                name: "arrow",
                visible: true,
                layers: [
                    { kind: "art", name: "0", visible: true, bounds: { x: 144, y: 48, w: 32, h: 32 } },
                    { kind: "art", name: "1", visible: true, bounds: { x: 144, y: 48, w: 32, h: 32 } },
                ],
            },
        ];
        const m = buildManifest(doc, layers, fullOpts);
        expect(validateManifest(m)).toEqual([]);
    });

    it("rejects a manifest with the wrong format_version", () => {
        const bad = { format_version: 2, doc: "x.psd", size: [10, 10], pixels_per_unit: 100, layers: [] } as unknown as Manifest;
        const errors = validateManifest(bad);
        expect(errors.length).toBeGreaterThan(0);
        expect(errors.join(" ")).toMatch(/format_version/);
    });

    it("rejects a polygon layer missing required fields", () => {
        const bad = {
            format_version: 1,
            doc: "x.psd",
            size: [10, 10],
            pixels_per_unit: 100,
            layers: [{ kind: "polygon", name: "torso" }],
        } as unknown as Manifest;
        expect(validateManifest(bad).length).toBeGreaterThan(0);
    });

    it("rejects a sprite_frame with fewer than 2 frames", () => {
        const bad: Manifest = {
            format_version: 1,
            doc: "x.psd",
            size: [10, 10],
            pixels_per_unit: 100,
            layers: [
                {
                    kind: "sprite_frame",
                    name: "blink",
                    position: [0, 0],
                    size: [10, 10],
                    z_order: 0,
                    frames: [{ index: 0, path: "images/blink/0.png" }],
                },
            ],
        };
        const errors = validateManifest(bad);
        expect(errors.length).toBeGreaterThan(0);
        expect(errors.join(" ")).toMatch(/frames/);
    });
});
