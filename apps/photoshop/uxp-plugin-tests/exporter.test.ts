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

    it("group named only with a tag passes through without polluting child names", () => {
        // User names a top-level group literally `[spritesheet]` but
        // the children are not numeric. buildSpriteFrameEntry returns
        // null; the fall-through must NOT prefix children with the
        // empty display name (would collide with manifest schema).
        const layers: Layer[] = [
            set("[spritesheet]", [art("brow.L"), art("brow.R")]),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers.map((e) => e.name)).toEqual(["brow.L", "brow.R"]);
    });

    it("leaf layer named only with a tag falls back to the raw name (manifest stays valid)", () => {
        const layers: Layer[] = [art("[ignore-not-applied]")];
        const m = buildManifest(doc, layers, opts);
        // Tag `[ignore-not-applied]` is not in the recognised
        // vocabulary, so it stays in the display name (unknown
        // brackets pass through). The entry name is the raw name.
        expect(m.layers).toHaveLength(1);
        expect(m.layers[0].name).toBe("[ignore-not-applied]");
    });

    it("unknown brackets pass through as part of the display name", () => {
        const layers: Layer[] = [art("torso [OLD]")];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers[0].name).toBe("torso [OLD]");
    });

    it("[folder:eyes] on a parent group propagates to descendant polygons", () => {
        const layers: Layer[] = [
            set("[folder:eyes]", [art("eye.L"), art("eye.R")]),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers).toHaveLength(2);
        const e0 = m.layers[0] as PolygonEntry;
        const e1 = m.layers[1] as PolygonEntry;
        expect(e0.subfolder).toBe("eyes");
        expect(e0.path).toBe("images/eyes/eye_L.png");
        expect(e1.subfolder).toBe("eyes");
        expect(e1.path).toBe("images/eyes/eye_R.png");
    });

    it("child [folder:other] overrides inherited folder", () => {
        const layers: Layer[] = [
            set("[folder:eyes]", [art("eye.L [folder:special]"), art("eye.R")]),
        ];
        const m = buildManifest(doc, layers, opts);
        const eL = m.layers.find((e) => e.name === "eye.L") as PolygonEntry;
        const eR = m.layers.find((e) => e.name === "eye.R") as PolygonEntry;
        expect(eL.subfolder).toBe("special");
        expect(eR.subfolder).toBe("eyes");
    });

    it("inherited [blend] applies to descendants when child has no blend tag", () => {
        const layers: Layer[] = [
            set("[blend:multiply]", [art("a"), art("b [blend:screen]")]),
        ];
        const m = buildManifest(doc, layers, opts);
        const a = m.layers.find((e) => e.name === "a") as PolygonEntry;
        const b = m.layers.find((e) => e.name === "b") as PolygonEntry;
        expect(a.blend_mode).toBe("multiply");
        expect(b.blend_mode).toBe("screen");
    });

    it("[merge] group emits a single polygon entry with merge flag on the PngWrite", () => {
        const layers: Layer[] = [
            set("hair [merge]", [
                art("strand_back", { x: 10, y: 20, w: 50, h: 60 }),
                art("strand_front", { x: 15, y: 25, w: 40, h: 55 }),
            ]),
        ];
        const plan = buildExportPlan(doc, layers, opts);
        expect(plan.manifest.layers).toHaveLength(1);
        const entry = plan.manifest.layers[0] as PolygonEntry;
        expect(entry.kind).toBe("polygon");
        expect(entry.name).toBe("hair");
        // Bounds = union of children: x 10..60, y 20..80 -> w 50, h 60
        expect(entry.size).toEqual([50, 60]);
        expect(entry.position).toEqual([10, 20]);
        expect(plan.writes).toHaveLength(1);
        expect(plan.writes[0].merge).toBe(true);
        expect(plan.writes[0].layerPath).toEqual(["hair [merge]"]);
    });

    it("[merge] children inside [spritesheet] become flattened frames", () => {
        const layers: Layer[] = [
            set("brow_states [spritesheet]", [
                set("0 [merge]", [
                    art("L0", { x: 0, y: 0, w: 32, h: 16 }),
                    art("R0", { x: 40, y: 0, w: 32, h: 16 }),
                ]),
                set("1 [merge]", [
                    art("L1", { x: 0, y: 0, w: 30, h: 14 }),
                    art("R1", { x: 40, y: 0, w: 30, h: 14 }),
                ]),
            ]),
        ];
        const plan = buildExportPlan(doc, layers, opts);
        expect(plan.manifest.layers).toHaveLength(1);
        const sf = plan.manifest.layers[0] as SpriteFrameEntry;
        expect(sf.kind).toBe("sprite_frame");
        expect(sf.name).toBe("brow_states");
        expect(sf.frames.map((f) => f.index)).toEqual([0, 1]);
        // Both writes carry the merge flag and point at the merge groups.
        expect(plan.writes).toHaveLength(2);
        expect(plan.writes[0].merge).toBe(true);
        expect(plan.writes[0].layerPath).toEqual(["brow_states [spritesheet]", "0 [merge]"]);
        expect(plan.writes[1].merge).toBe(true);
    });

    it("non-merge group inside [spritesheet] disqualifies the sprite_frame and falls through", () => {
        const layers: Layer[] = [
            set("blink [spritesheet]", [
                set("0", [art("a"), art("b")]),
                set("1", [art("c"), art("d")]),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        // No sprite_frame; each inner art layer comes out as polygon.
        expect(m.layers.every((e) => e.kind === "polygon")).toBe(true);
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

describe("document-level anchor (PSD guides)", () => {
    it("emits anchor field when opts.anchor is set", () => {
        const layers: Layer[] = [art("torso")];
        const m = buildManifest(doc, layers, { ...opts, anchor: [100, 200] });
        expect(m.anchor).toEqual([100, 200]);
    });

    it("omits anchor when opts.anchor is not provided", () => {
        const layers: Layer[] = [art("torso")];
        const m = buildManifest(doc, layers, opts);
        expect(m.anchor).toBeUndefined();
    });
});

describe("origin marker inside [merge] group", () => {
    it("uses [origin] marker child as polygon origin when no explicit tag", () => {
        const layers: Layer[] = [
            set("hair [merge]", [
                art("front", { x: 0, y: 0, w: 50, h: 50 }),
                art("pivot [origin]", { x: 10, y: 20, w: 4, h: 4 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        const entry = m.layers[0] as PolygonEntry;
        expect(entry.kind).toBe("polygon");
        expect(entry.origin).toEqual([12, 22]); // marker center
    });

    it("explicit [origin:x,y] on the group beats the inner marker", () => {
        const layers: Layer[] = [
            set("hair [merge] [origin:99,88]", [
                art("front", { x: 0, y: 0, w: 50, h: 50 }),
                art("pivot [origin]", { x: 10, y: 20, w: 4, h: 4 }),
            ]),
        ];
        const m = buildManifest(doc, layers, opts);
        expect(m.layers[0].origin).toEqual([99, 88]);
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
