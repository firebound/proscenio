// Unit tests for the SPEC 011 v2 planner. Pure logic, no PS runtime.
// The planner reads the bracket-tag parser and emits the v2 manifest
// shape; tests cover the legacy auto-detection paths that survive
// (visible polygons, digit-named sprite_frame groups) plus the new
// tag-driven semantics (ignore, kind override, folder/path, scale,
// blend, origin).

import { describe, expect, it } from "vitest";

import {
    buildExportPlan,
    buildManifest,
    indicesAreContiguousFromZero,
    sanitize,
} from "../src/domain/planner";
import type { ArtLayer, Layer, LayerSet } from "../src/domain/layer";
import type { PolygonEntry, SpriteFrameEntry } from "../src/domain/manifest";

const DEFAULT_BOUNDS = { x: 0, y: 0, w: 10, h: 10 };

function art(
    name: string,
    bounds: ArtLayer["bounds"] = DEFAULT_BOUNDS,
    visible = true,
): ArtLayer {
    return { kind: "art", name, visible, bounds };
}

function set(name: string, layers: Layer[], visible = true): LayerSet {
    return { kind: "set", name, visible, layers };
}

const doc = { name: "fixture.psd", width: 256, height: 256 };
const opts = { skipHidden: true };

describe("indicesAreContiguousFromZero", () => {
    it("accepts contiguous 0..n sequences in any order", () => {
        expect(indicesAreContiguousFromZero([0, 1, 2])).toBe(true);
        expect(indicesAreContiguousFromZero([2, 0, 1])).toBe(true);
    });

    it("rejects sequences with gaps or wrong start", () => {
        expect(indicesAreContiguousFromZero([1, 2, 3])).toBe(false);
        expect(indicesAreContiguousFromZero([0, 2, 3])).toBe(false);
        expect(indicesAreContiguousFromZero([])).toBe(false);
    });
});

describe("sanitize", () => {
    it("replaces non-alphanumeric with underscore", () => {
        expect(sanitize("a/b.c")).toBe("a_b_c");
        expect(sanitize("hand-01")).toBe("hand-01");
        expect(sanitize("spine.001")).toBe("spine_001");
    });
});

describe("buildManifest - baseline (no tags)", () => {
    it("emits format_version 2 with polygons in scene order", () => {
        const layers: Layer[] = [
            art("torso", { x: 10, y: 20, w: 100, h: 200 }),
            art("head", { x: 40, y: 0, w: 80, h: 80 }),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.format_version).toBe(2);
        expect(m.layers).toHaveLength(2);
        expect(m.layers[0]).toMatchObject({
            kind: "polygon",
            name: "torso",
            path: "images/torso.png",
            z_order: 0,
        });
        expect(m.layers[1].z_order).toBe(1);
    });

    it("respects skipHidden", () => {
        const layers: Layer[] = [art("keep"), art("hidden_flag", undefined, false)];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("keep");
    });

    it("auto-detects digit-named sprite_frame groups", () => {
        const layers: Layer[] = [
            set("blink", [
                art("0", { x: 0, y: 0, w: 32, h: 32 }),
                art("1", { x: 0, y: 0, w: 40, h: 40 }),
                art("2", { x: 0, y: 0, w: 32, h: 32 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        const sf = m.layers.filter(
            (e): e is SpriteFrameEntry => e.kind === "sprite_frame",
        );
        expect(sf).toHaveLength(1);
        expect(sf[0].name).toBe("blink");
        expect(sf[0].size).toEqual([40, 40]);
        expect(sf[0].frames.map((f) => f.index)).toEqual([0, 1, 2]);
        expect(sf[0].frames[0].path).toBe("images/blink/0.png");
    });

    it("does NOT auto-aggregate flat <base>_<index> siblings (SPEC 011 D4)", () => {
        const layers: Layer[] = [
            art("walk_0"),
            art("walk_1"),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers.every((e) => e.kind === "polygon")).toBe(true);
        expect(m.layers.map((e) => e.name)).toEqual(["walk_0", "walk_1"]);
    });

    it("does NOT skip layers with `_` prefix (SPEC 011 D3 drops the legacy convention)", () => {
        const layers: Layer[] = [art("_helper"), art("keep")];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers.map((e) => e.name)).toEqual(["_helper", "keep"]);
    });

    it("joins nested group names with __", () => {
        const layers: Layer[] = [set("body", [set("upper", [art("torso")])])];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("body__upper__torso");
    });
});

describe("bracket tags", () => {
    it("[ignore] skips a layer or group", () => {
        const layers: Layer[] = [art("keep"), art("trash [ignore]"), set("dead [ignore]", [art("inner")])];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers.map((e) => e.name)).toEqual(["keep"]);
    });

    it("[spritesheet] overrides auto-detection and accepts non-digit groups", () => {
        const layers: Layer[] = [
            set("blink [spritesheet]", [
                art("0", { x: 0, y: 0, w: 16, h: 16 }),
                art("1", { x: 0, y: 0, w: 16, h: 16 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].kind).toBe("sprite_frame");
        expect(m.layers[0].name).toBe("blink");
    });

    it("[mesh] overrides kind on a polygon entry", () => {
        const layers: Layer[] = [art("torso [mesh]")];
        const m = buildManifest(doc, layers, opts);
        expect((m.layers[0] as PolygonEntry).kind).toBe("mesh");
        expect(m.layers[0].name).toBe("torso");
    });

    it("[folder:name] writes subfolder and rewrites path", () => {
        const layers: Layer[] = [art("torso [folder:body]")];
        const m = buildManifest(doc, layers, opts);
        const entry = m.layers[0] as PolygonEntry;
        expect(entry.subfolder).toBe("body");
        expect(entry.path).toBe("images/body/torso.png");
    });

    it("[path:name] overrides the filename", () => {
        const layers: Layer[] = [art("torso [path:custom]")];
        const m = buildManifest(doc, layers, opts);
        expect((m.layers[0] as PolygonEntry).path).toBe("images/custom.png");
    });

    it("[folder:x] + [path:y] compose", () => {
        const layers: Layer[] = [art("torso [folder:body] [path:t]")];
        const m = buildManifest(doc, layers, opts);
        expect((m.layers[0] as PolygonEntry).path).toBe("images/body/t.png");
    });

    it("[scale:n] rescales bounds in the emitted entry", () => {
        const layers: Layer[] = [
            art("arm [scale:2]", { x: 10, y: 20, w: 30, h: 40 }),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers[0].position).toEqual([20, 40]);
        expect(m.layers[0].size).toEqual([60, 80]);
    });

    it("[blend:multiply] writes blend_mode", () => {
        const layers: Layer[] = [art("ink [blend:multiply]")];
        const m = buildManifest(doc, layers, opts);
        expect((m.layers[0] as PolygonEntry).blend_mode).toBe("multiply");
    });

    it("[origin:x,y] writes the origin field", () => {
        const layers: Layer[] = [art("arm [origin:50,75]")];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers[0].origin).toEqual([50, 75]);
    });

    it("[origin] marker layer inside a sprite_frame group sets the group origin", () => {
        const layers: Layer[] = [
            set("blink", [
                art("0", { x: 0, y: 0, w: 16, h: 16 }),
                art("1", { x: 0, y: 0, w: 16, h: 16 }),
                art("pivot [origin]", { x: 10, y: 20, w: 4, h: 4 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        const sf = m.layers[0] as SpriteFrameEntry;
        expect(sf.kind).toBe("sprite_frame");
        // marker center: x + w/2 = 12, y + h/2 = 22
        expect(sf.origin).toEqual([12, 22]);
        // marker itself does NOT count as a frame
        expect(sf.frames).toHaveLength(2);
    });

    it("unknown brackets pass through as part of the display name", () => {
        const layers: Layer[] = [art("torso [OLD]")];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers[0].name).toBe("torso [OLD]");
    });

    it("[ignore] inside a sprite_frame group does NOT count toward the frame contiguity check", () => {
        const layers: Layer[] = [
            set("blink", [
                art("0", { x: 0, y: 0, w: 16, h: 16 }),
                art("1", { x: 0, y: 0, w: 16, h: 16 }),
                art("notes [ignore]", { x: 0, y: 0, w: 8, h: 8 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].kind).toBe("sprite_frame");
    });
});

describe("buildExportPlan writes", () => {
    it("emits one PngWrite per polygon with the source layerPath", () => {
        const layers: Layer[] = [
            set("body", [set("upper", [art("torso")])]),
            art("head"),
        ];
        const plan = buildExportPlan(doc, layers, opts);
        expect(plan.writes).toHaveLength(2);
        expect(plan.writes[0]).toEqual({
            layerPath: ["body", "upper", "torso"],
            outputPath: "images/body__upper__torso.png",
        });
        expect(plan.writes[1]).toEqual({
            layerPath: ["head"],
            outputPath: "images/head.png",
        });
    });

    it("emits one PngWrite per frame for a sprite_frame group", () => {
        const layers: Layer[] = [
            set("blink", [art("0"), art("1"), art("2")]),
        ];
        const plan = buildExportPlan(doc, layers, opts);
        expect(plan.writes).toHaveLength(3);
        expect(plan.writes[0]).toEqual({
            layerPath: ["blink", "0"],
            outputPath: "images/blink/0.png",
        });
        expect(plan.writes[2].layerPath).toEqual(["blink", "2"]);
    });
});
